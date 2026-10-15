#!/usr/bin/env python3
"""Merge reviewed font-only proposals into the latest scene layouts."""
import json, os, shutil
from ..paths import PROJECT
from pathlib import Path
ROOT = PROJECT
proposal = ROOT / 'font-style-preview/font-match'
fonts = json.loads((ROOT / 'design/fonts.json').read_text())
new = json.loads((proposal / 'font-config.proposed.json').read_text())
for role, config in new.items():
    if role.startswith('old_'):
        continue
    src = (ROOT / config['file']).resolve()
    dst_dir = ROOT.parents[1] / 'fonts' / role
    dst_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst_dir / src.name)
    for extra in src.parent.iterdir():
        if extra.suffix.lower() in ('.txt', '.json', '.md'):
            shutil.copyfile(extra, dst_dir / extra.name)
    fonts[role] = {**config, 'file': os.path.relpath(dst_dir / src.name, ROOT)}
(ROOT / 'design/fonts.json').write_text(json.dumps(fonts, ensure_ascii=False, indent=2) + '\n')
patches = {p['id']: p for p in json.loads((proposal / 'event-font-patches.json').read_text())}
count = 0
for path in sorted((ROOT / 'design').glob('events-*.json')):
    events = json.loads(path.read_text())
    for event in events:
        p = patches[event['id']]
        change = dict(p['set'])
        assert not set(change) & {'zh','ja','x','y','fontsize','start','end','line_breaks'}
        ratio = event['fontsize'] / p['base_fontsize']
        for field in ('outline', 'shadow'):
            if field in change:
                change[field] = round(change[field] * ratio, 2)
        if 'scale_x' in change:
            change['scale_x'] = min(event.get('scale_x',100), change['scale_x'])
        event.update(change)
        count += 1
    path.write_text(json.dumps(events, ensure_ascii=False, indent=2) + '\n')
print(f'Merged font proposal for {count} events; retained current positions, sizes, times and text.')
