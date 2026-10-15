#!/usr/bin/env python3
"""Stage exactly configured local fonts for deterministic libass rendering."""
import json,shutil
from ..paths import PROJECT
from pathlib import Path
root = PROJECT;fonts=json.loads((root/'design/fonts.json').read_text());out=root/'.cache/render-fonts';out.mkdir(parents=True,exist_ok=True)
for role,f in fonts.items():
    src=root/Path(f['file']);dst=out/(role+src.suffix)
    if not src.is_file():raise SystemExit(f'Missing {src}; update design/fonts.json')
    if not dst.exists() or dst.read_bytes()!=src.read_bytes():shutil.copyfile(src,dst)
print(out)
