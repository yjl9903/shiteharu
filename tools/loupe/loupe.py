#!/usr/bin/env python3
"""Build and serve a portable preview from a project-relative configuration."""
import argparse
from datetime import datetime, timezone
import fcntl
from html import escape
from io import BytesIO
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import threading
from urllib.parse import unquote, urlsplit

from project import Project, probe
from fonts import export_fonts

ASSETS = Path(__file__).resolve().parent / "assets"


def render_index(snapshot):
    """Include measured geometry and the first caption in the initial document."""
    page = (ASSETS / "index.html").read_text(encoding="utf-8")
    payload = json.dumps(snapshot, ensure_ascii=False).replace("<", "\\u003c")
    page = page.replace('<script id="initialSnapshot" type="application/json">null</script>',
                        f'<script id="initialSnapshot" type="application/json">{payload}</script>')
    title = escape(snapshot["title"])
    page = page.replace('<title>Loupe</title>', f'<title>{title}</title>')
    page = page.replace('<h1 id="title">正在读取工程…</h1>', f'<h1 id="title">{title}</h1>')
    labels = {"original": "原片", "rendered": "当前版", "source_text": "原文", "text": "译文", **snapshot.get("labels", {})}
    for side in ("original", "rendered"):
        ratio = float(snapshot["media"][side]["display_ratio"])
        page = page.replace(f'id="{side}"', f'id="{side}" style="--video-aspect:{ratio}"')
        page = page.replace(f'<p id="{side}Label">' + ("原片" if side == "original" else "当前版") + '</p>',
                            f'<p id="{side}Label">{escape(labels[side])}</p>')
    if snapshot["timeline"]:
        event = snapshot["timeline"][0]
        caption = ('<div class="caption-meta"><span>所选字幕</span>'
                   f'<strong>{escape(event["id"])}</strong><span>{event["start"]:.3f} — {event["end"]:.3f} s</span></div>'
                   '<div class="caption-text">')
        for key in ("source_text", "text"):
            caption += (f'<div class="caption-row"><span class="caption-language">{escape(labels[key])}</span>'
                        f'<p>{escape(event[key])}</p></div>')
        caption += '</div>'
    else:
        caption = '<p class="muted">没有匹配的字幕</p>'
    page = page.replace('<div id="current" class="current-caption"></div>',
                        f'<div id="current" class="current-caption">{caption}</div>')
    return page.encode("utf-8")


def atomic(path, value):
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as f:
        temp = Path(f.name)
        json.dump(value, f, ensure_ascii=False, indent=2)
    try:
        temp.replace(path)
    finally:
        temp.unlink(missing_ok=True)


def ffmpeg(args):
    result = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *map(str, args)],
                            capture_output=True, text=True)
    if result.returncode:
        # ffmpeg stderr may contain machine-specific paths. Do not persist it.
        raise ValueError("ffmpeg 处理失败，请检查媒体格式及磁盘空间")


def snapshot_video(source, metadata, folder, side):
    webm = metadata["codec"] in ("vp8", "vp9")
    name = side + (".webm" if webm else ".mp4")
    dest = folder / name
    command = ["-i", source, "-map", "0:v:0"]
    if side == "original":
        command += ["-map", "0:a:0?", "-c:a", "libopus" if webm else "aac"]
    else:
        command += ["-an"]
    command += ["-c:v", "copy"] if webm or metadata["codec"] == "h264" else ["-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p"]
    if not webm:
        command += ["-movflags", "+faststart"]
    ffmpeg([*command, dest])
    return name, probe(dest)


def extract_frames(inputs, folder, width):
    fps = inputs["media"]["rendered"]["fps"]
    rate = inputs["media"]["rendered"]["frame_rate"]
    limit = min(m["duration"] for m in inputs["media"].values())
    rows = []
    for event in inputs["timeline"]:
        t = event["start"] + min(.6, (event["end"] - event["start"]) / 2)
        frame = max(0, min(round(t * fps), math.ceil(limit * fps) - 1))
        rows.append({"id": event["id"], "time": frame / fps, "frame": frame})
    frames = sorted({r["frame"] for r in rows})
    if not frames:
        return []
    expression = "+".join(f"eq(n,{n})" for n in frames)
    for side, source in zip(("original", "rendered"), inputs["videos"]):
        height = max(2, round(width / inputs["media"][side]["display_ratio"] / 2) * 2)
        # A filter script avoids shell quoting and command-line length limits on long timelines.
        filter_path = folder / "frames.filter"
        filter_path.write_text(f"fps={rate},select='{expression}',scale={width}:{height},setsar=1", encoding="utf-8")
        ffmpeg(["-i", source, "-filter_script:v", filter_path, "-fps_mode", "vfr", "-q:v", "3",
                "-threads", "2", folder / f"{side}-%06d.jpg"])
        filter_path.unlink()
        outputs = sorted(folder.glob(f"{side}-*.jpg"))
        if len(outputs) != len(frames):
            raise ValueError(f"{side} 抽帧不完整：{len(outputs)}/{len(frames)}")
        names = dict(zip(frames, (p.name for p in outputs)))
        for row in rows:
            row[side] = names[row["frame"]]
    return rows


class Preview:
    def __init__(self, config):
        self.config = Path(config).resolve()
        self.output = Project(config).output
        self.output.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()

    def status(self, state, **extra):
        atomic(self.output / "status.json", {"state": state, **extra})

    def sync(self):
        with self.lock, (self.output / ".sync.lock").open("w") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            try:
                return self._sync()
            except Exception as exc:
                # Config file paths are already relative; avoid absolute filesystem errors in persisted data.
                message = str(exc) if isinstance(exc, ValueError) else f"输入或处理失败：{type(exc).__name__}"
                self.status("error", message=message)
                raise

    def _sync(self):
        project = Project(self.config)
        if project.output != self.output:
            raise ValueError("output 已变更，请使用新配置重新启动服务")
        inputs = project.inputs()
        revision = inputs["revision"]
        manifest = self.output / "snapshot.json"
        if manifest.exists():
            previous = json.loads(manifest.read_text())
            urls = [m["url"] for m in previous["media"].values()]
            urls += [r[s] for r in previous["frames"] for s in ("original", "rendered")]
            urls += [f["url"] for f in previous["fonts"]]
            if previous["revision"] == revision and all((self.output / p).is_file() for p in urls):
                self.status("ready", revision=revision)
                return previous
        self.status("building", revision=revision)
        versions = self.output / "snapshots"
        versions.mkdir(exist_ok=True)
        # Immutable version folders: a single manifest switch publishes both videos and all frames.
        with tempfile.TemporaryDirectory(prefix="pending-", dir=versions) as tmp:
            stage = Path(tmp)
            media = {}
            for side, source in zip(("original", "rendered"), inputs["videos"]):
                name, metadata = snapshot_video(source, inputs["media"][side], stage, side)
                media[side] = {**inputs["media"][side], **metadata, "url": name}
            width = project.config.get("thumbnail_width", 960)
            if not isinstance(width, int) or width < 2 or width > 4096:
                raise ValueError("thumbnail_width 必须在 2 到 4096 之间")
            frames = extract_frames(inputs, stage, width)
            fonts = export_fonts(project, inputs["fonts"], inputs["timeline"], stage / "fonts")
            # Re-read every input, including overlay inventory and both video sources, before publishing.
            if Project(self.config).inputs()["revision"] != revision:
                raise ValueError("生成期间输入发生变化，保留上一份快照并等待重试")
            # A nonce also permits rebuilding a damaged version without overwriting files in use.
            version = revision + "-" + stage.name.removeprefix("pending-")
            destination = versions / version
            os.rename(stage, destination)
        prefix = "snapshots/" + version + "/"
        for m in media.values():
            m["url"] = prefix + m["url"]
        for row in frames:
            for side in ("original", "rendered"):
                row[side] = prefix + row[side]
        for font in fonts:
            font["url"] = prefix + font["url"]
        payload = dict(revision=revision, generated_at=datetime.now(timezone.utc).isoformat(),
                       title=project.config.get("title", project.root.name),
                       labels=project.config.get("labels", {}), media=media, timeline=inputs["timeline"],
                       content=inputs["content"], frames=frames, fonts=fonts)
        atomic(manifest, payload)
        self.status("ready", revision=revision)
        print(f"Preview ready: {len(frames)} events, {revision}", flush=True)
        return payload

    def watch(self, stop, interval):
        while not stop.wait(interval):
            try:
                self.sync()
            except Exception:
                pass  # status.json reports the error; the next poll retries.


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, preview, **kwargs):
        self.preview = preview
        super().__init__(*args, directory=str(preview.output), **kwargs)

    def translate_path(self, path):
        name = unquote(urlsplit(path).path).lstrip("/")
        if name in ("", "index.html"):
            return str(ASSETS / "index.html")
        base = ASSETS if name.startswith("assets/") else self.preview.output
        if name.startswith("assets/"):
            name = name[len("assets/"):]
        candidate = (base / name).resolve()
        parts = Path(name).parts
        # Only generated public assets are served, never project configs, source code or symlinks escaping the root.
        allowed = base == ASSETS or name in ("snapshot.json", "status.json") or name.startswith("snapshots/")
        if not allowed or any(p.startswith(".") or p.startswith("pending-") for p in parts) or not candidate.is_relative_to(base):
            return str(ASSETS / "__not_found__")
        return str(candidate)

    def list_directory(self, path):
        self.send_error(404)
        return None

    def do_POST(self):
        origin = self.headers.get("Origin")
        if self.path not in ("/api/rebuild", "/api/media") or self.headers.get("X-Preview-Rebuild") != "1" or (origin and origin != "http://" + self.headers.get("Host", "")):
            self.send_error(403)
            return
        try:
            data = self.preview.sync()
            self.reply(200, {"revision": data["revision"]})
        except Exception:
            self.reply(500, json.loads((self.preview.output / "status.json").read_text()))

    def reply(self, code, data):
        raw = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def send_head(self):
        self.remaining = None
        path = Path(self.translate_path(self.path))
        manifest = self.preview.output / "snapshot.json"
        if path == ASSETS / "index.html" and manifest.is_file():
            raw = render_index(json.loads(manifest.read_text(encoding="utf-8")))
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            return BytesIO(raw)
        if path.suffix not in (".mp4", ".webm") or not path.is_file():
            return super().send_head()
        stream = path.open("rb")
        total = os.fstat(stream.fileno()).st_size
        header = self.headers.get("Range")
        match = re.fullmatch(r"bytes=(\d*)-(\d*)", header or "")
        start, end = 0, total - 1
        if header:
            if not match or not any(match.groups()):
                stream.close()
                self.send_error(416)
                return None
            if match[1]:
                start = int(match[1])
                end = min(int(match[2]), end) if match[2] else end
            else:
                start = max(0, total - int(match[2]))
            if start > end or start >= total:
                stream.close()
                self.send_response(416)
                self.send_header("Content-Range", f"bytes */{total}")
                self.send_header("Content-Length", "0")
                self.end_headers()
                return None
        self.send_response(206 if header else 200)
        self.send_header("Content-Type", "video/webm" if path.suffix == ".webm" else "video/mp4")
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(end - start + 1))
        if header:
            self.send_header("Content-Range", f"bytes {start}-{end}/{total}")
        self.end_headers()
        self.remaining = end - start + 1
        stream.seek(start)
        return stream

    def copyfile(self, source, outputfile):
        if self.remaining is None:
            return super().copyfile(source, outputfile)
        try:
            while self.remaining:
                chunk = source.read(min(self.remaining, 1024 * 1024))
                if not chunk:
                    break
                outputfile.write(chunk)
                self.remaining -= len(chunk)
        except (BrokenPipeError, ConnectionResetError):
            pass


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--watch", action="store_true")
    parser.add_argument("--validate", action="store_true", help="Read and validate inputs without generating output")
    parser.add_argument("--port", type=int, default=8973)
    parser.add_argument("--interval", type=float, default=5)
    args = parser.parse_args(argv)
    if args.interval <= 0:
        parser.error("--interval must be positive")
    try:
        if args.validate:
            data = Project(args.config).inputs()
            print(json.dumps({"events": len(data["timeline"]), "media": data["media"], "revision": data["revision"]}, ensure_ascii=False, indent=2))
            return
        preview = Preview(args.config)
        preview.sync()
        stop = threading.Event()
        if args.serve:
            server = ThreadingHTTPServer(("127.0.0.1", args.port), partial(Handler, preview=preview))
            threading.Thread(target=preview.watch, args=(stop, args.interval), daemon=True).start()
            print(f"Open http://127.0.0.1:{server.server_port}/", flush=True)
            try:
                server.serve_forever()
            finally:
                stop.set()
                server.server_close()
        elif args.watch:
            preview.watch(stop, args.interval)
    except (ValueError, OSError, KeyError) as exc:
        parser.exit(1, f"Preview error: {exc}\n")


if __name__ == "__main__":
    main()
