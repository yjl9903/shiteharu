#!/usr/bin/env python3
"""Package editable sources and subtitles, excluding local review artifacts."""
from ..paths import PROJECT
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

root = PROJECT
repo = root.parents[1]
files = set()
files.update(p for p in (repo / 'fonts').rglob('*') if p.is_file()
             and 'local' not in p.relative_to(repo / 'fonts').parts)
for directory in ['design', 'scripts', 'translation/work', 'patches']:
    files.update(p for p in (root / directory).rglob('*') if p.is_file()
                 and '__pycache__' not in p.parts)
for name in ['README.md', 'description.md', 'session.toml']:
    files.add(root / name)
for name in ['zh.performance.ass', 'ja.review.ass', 'zh.srt', 'ja.srt']:
    files.add(root / 'deliverables' / name)
target = root / 'deliverables/editable-project.zip'
with ZipFile(target, 'w', ZIP_DEFLATED, compresslevel=6) as archive:
    for path in sorted(files):
        archive.write(path, path.relative_to(repo))
print(f'{target}: {len(files)} files, {target.stat().st_size:,} bytes')
