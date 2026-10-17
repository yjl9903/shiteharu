"""Export configured faces and report missing glyphs without system fallback."""
import hashlib
from pathlib import Path


def export_fonts(project, config, events, folder):
    if not config:
        return []
    try:
        from fontTools.ttLib import TTFont, TTCollection
    except ImportError as exc:
        raise ValueError("字体检查需要 fonttools；请在仓库根目录运行 uv sync --locked，并通过 uv run --locked python 启动") from exc
    folder.mkdir(exist_ok=True)
    faces = []
    for role, spec in config.items():
        path = project.resolve(spec["file"])
        collection = TTCollection(path, lazy=True) if path.suffix.lower() in (".ttc", ".otc") else None
        fonts = collection.fonts if collection else [TTFont(path, lazy=True)]
        try:
            eligible = []
            for index, font in enumerate(fonts):
                names = font["name"]
                aliases = {names.getDebugName(1), names.getDebugName(16)}
                if spec.get("family") and spec["family"] not in aliases:
                    continue
                if "face_index" in spec and index != spec["face_index"]:
                    continue
                eligible.append((index, font))
            if not eligible:
                raise ValueError(f"字体文件中没有配置的字面：{role}")
            index, font = min(eligible, key=lambda pair: abs(pair[1]["OS/2"].usWeightClass - spec.get("weight", 700 if spec.get("bold") else 400)))
            coverage = set(font.getBestCmap() or {})
            missing = []
            for event in events:
                if event["style"].get("font_role") != role:
                    continue
                chars = sorted({ch for ch in event["text"] if not ch.isspace() and ord(ch) not in coverage})
                if chars:
                    missing.append({"id": event["id"], "characters": "".join(chars)})
            ranges = []
            for cp in sorted(coverage):
                if ranges and cp == ranges[-1][1] + 1:
                    ranges[-1][1] = cp
                else:
                    ranges.append([cp, cp])
            key = hashlib.sha256(path.read_bytes() + str(index).encode()).hexdigest()[:20]
            dest = folder / (key + ".woff")
            font.flavor = "woff"
            if not dest.exists():
                font.save(dest)
            faces.append(dict(role=role, family=spec.get("family") or font["name"].getDebugName(1),
                              weight=font["OS/2"].usWeightClass, italic=bool(font["head"].macStyle & 2),
                              source=spec["file"], face_index=index, url="fonts/" + dest.name,
                              coverage=ranges, missing=missing))
        finally:
            if collection:
                collection.close()
            else:
                fonts[0].close()
    return faces
