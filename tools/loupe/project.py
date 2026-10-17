"""Declarative inputs, normalized timeline and media metadata. No project imports."""
from fractions import Fraction
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import math
import os
import subprocess
import tomllib
from fonts import font_runs

REPOSITORY = Path(__file__).resolve().parents[2]
CACHE_ROOT = REPOSITORY / ".cache/loupe"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def relative_path(root, value):
    if not isinstance(value, str) or not value or Path(value).is_absolute() or "\\" in value:
        raise ValueError("配置路径必须是相对于工程目录的路径")
    return (root / value).resolve()


def probe(path):
    result = subprocess.run([
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=codec_name,width,height,avg_frame_rate,r_frame_rate,sample_aspect_ratio:stream_side_data=rotation:format=duration",
        "-of", "json", str(path),
    ], capture_output=True, text=True)
    if result.returncode:
        raise ValueError(f"视频无法读取：{path.name}")
    raw = json.loads(result.stdout)
    if not raw.get("streams"):
        raise ValueError(f"没有视频流：{path.name}")
    stream = raw["streams"][0]
    rate = stream.get("avg_frame_rate", "0/0")
    if rate in ("0/0", "0/1"):
        rate = stream["r_frame_rate"]
    fps = float(Fraction(rate))
    duration = float(raw["format"]["duration"])
    if not math.isfinite(duration) or duration <= 0 or fps <= 0:
        raise ValueError(f"无效的媒体时长或帧率：{path.name}")
    width, height = stream["width"], stream["height"]
    sar = stream.get("sample_aspect_ratio", "1:1")
    aspect = float(Fraction(sar.replace(":", "/"))) if sar not in ("N/A", "0:1") else 1
    display_ratio = width * aspect / height
    rotation = next((s.get("rotation", 0) for s in stream.get("side_data_list", []) if "rotation" in s), 0)
    if abs(rotation) % 180 == 90:
        display_ratio = 1 / display_ratio
    return dict(width=width, height=height, duration=duration, fps=fps,
                frame_rate=rate, display_ratio=display_ratio, codec=stream["codec_name"])


class Project:
    def __init__(self, config_path):
        self.path = Path(config_path).resolve()
        # The configuration lives directly in production/<project>/.
        self.root = self.path.parent
        self.snapshots = {}
        self.config = self.read_config(self.path)
        if self.config.get("version") != 1:
            raise ValueError("预览配置 version 必须为 1")
        if "output" in self.config:
            self.output = self.resolve(self.config["output"])
            if self.output == self.root or not self.output.is_relative_to(self.root):
                raise ValueError("output 必须位于工程目录的子目录中")
        else:
            identity = os.path.relpath(self.path, REPOSITORY)
            self.output = CACHE_ROOT / (self.root.name + "-" + digest(identity.encode())[:12])

    def resolve(self, value):
        return relative_path(self.root, value)

    def read(self, path):
        raw = path.read_bytes()
        self.snapshots[os.path.relpath(path, self.root)] = digest(raw)
        return tomllib.loads(raw.decode("utf-8")) if path.suffix == ".toml" else json.loads(raw)

    def read_config(self, path):
        if path.suffix != ".toml":
            raise ValueError(f"配置文件必须使用 TOML：{path.name}")
        return self.read(path)

    def timeline(self):
        spec = self.config["timeline"]
        data = self.read(self.resolve(spec["file"]))
        rows = data[spec["collection"]] if spec.get("collection") else data
        defaults = {}
        if spec.get("defaults"):
            defaults = self.read_config(self.resolve(spec["defaults"]))
            if spec.get("defaults_key"):
                defaults = defaults[spec["defaults_key"]]
        overrides, extras = {}, []
        for pattern in spec.get("overlays", []):
            self.resolve(pattern)  # Validate before globbing; paths are project relative.
            for path in sorted(self.root.glob(pattern)):
                data = self.read_config(path)
                for row in data[spec.get("overlay_collection", "events")]:
                    if row.get(spec.get("supplemental_flag", "supplemental")):
                        extras.append(row)
                    else:
                        if row["id"] in overrides:
                            raise ValueError(f"重复覆盖事件：{row['id']}")
                        overrides[row["id"]] = row
        unknown = overrides.keys() - {row["id"] for row in rows}
        if unknown:
            raise ValueError("覆盖事件没有时间轴来源：" + ", ".join(sorted(unknown)))
        events, seen = [], set()
        for row, extra in [(r, False) for r in rows] + [(r, True) for r in extras]:
            item = {**defaults, **row, **overrides.get(row["id"], {})}
            prefix = "supplemental_" if extra else ""
            source_key = spec.get(prefix + "source_text", spec.get("source_text", "source_text"))
            text_key = spec.get(prefix + "text", spec.get("text", "text"))
            event = {"id": item["id"], "start": item["start"], "end": item["end"],
                     "source_text": item.get(source_key, ""), "text": item.get(text_key, ""),
                     "style": {**defaults, **item.get("style", {})}}
            reserved = {"id", "start", "end", source_key, text_key, "style"}
            event["style"].update({k: v for k, v in item.items() if k not in reserved})
            if not isinstance(event["id"], str) or not event["id"] or event["id"] in seen:
                raise ValueError("时间轴 ID 必须是非空且唯一的字符串")
            seen.add(event["id"])
            if not all(isinstance(event[k], (float, int)) and not isinstance(event[k], bool)
                       and math.isfinite(event[k]) for k in ("start", "end")) or not 0 <= event["start"] < event["end"]:
                raise ValueError(f"无效时间区间：{event['id']}")
            if not all(isinstance(event[k], str) for k in ("text", "source_text")):
                raise ValueError(f"字幕必须是文本：{event['id']}")
            event['font_roles'] = sorted({run['font_role'] for run in
                font_runs(event['text'], event['style'], None, event['id']) if run['font_role']})
            events.append(event)
        return sorted(events, key=lambda e: (e["start"], e["id"]))

    def inputs(self):
        events = self.timeline()
        videos, metadata, stamps = [], {}, {}
        for side in ("original", "rendered"):
            name = self.config["media"][side]
            path = self.resolve(name)
            if not path.is_file():
                raise ValueError(f"配置的 {side} 视频不存在：{name}；不会回退其他文件")
            before = path.stat()
            metadata[side] = {**probe(path), "source": name,
                              "source_modified": datetime.fromtimestamp(before.st_mtime, timezone.utc).isoformat()}
            after = path.stat()
            if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
                raise ValueError(f"{side} 视频正在写入，请稍后重试")
            stamps[name] = (after.st_size, after.st_mtime_ns)
            videos.append(path)
        tolerance = float(self.config.get("duration_tolerance", .25))
        if tolerance < 0 or not math.isfinite(tolerance):
            raise ValueError("duration_tolerance 必须是非负有限数")
        if abs(metadata["original"]["duration"] - metadata["rendered"]["duration"]) > tolerance:
            raise ValueError("两路视频时长不一致，成片可能尚未完成；请检查配置来源")
        limit = min(m["duration"] for m in metadata.values())
        frame = 1 / metadata["rendered"]["fps"]
        if any(e["end"] > limit + frame for e in events):
            raise ValueError("字幕超出视频时长，成片可能尚未完成")
        fonts = self.read_config(self.resolve(self.config["fonts"])) if self.config.get("fonts") else {}
        for role, font in fonts.items():
            path = self.resolve(font["file"])
            if not path.is_file():
                raise ValueError(f"字体不存在：{role} / {font['file']}")
            stat = path.stat()
            stamps[font["file"]] = (stat.st_size, stat.st_mtime_ns)
        if fonts:
            unknown = {role for e in events for role in e['font_roles']} - fonts.keys()
            if unknown:
                raise ValueError("未知字体角色：" + ", ".join(sorted(unknown)))
        content = self.read_config(self.resolve(self.config["content"])) if self.config.get("content") else {}
        # UI and pipeline changes also invalidate generated snapshots.
        tool_files = (sorted(Path(__file__).parent.glob("*.py"))
                      + sorted((Path(__file__).parent / "assets").glob("*"))
                      + sorted((REPOSITORY / 'tools/captions').glob('*.py')))
        tool_hash = digest(b"".join(p.read_bytes() for p in tool_files if p.is_file()))
        revision = digest(json.dumps([self.snapshots, stamps, tool_hash], sort_keys=True).encode())[:20]
        return dict(revision=revision, timeline=events, videos=videos, media=metadata,
                    fonts=fonts, content=content)
