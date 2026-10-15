#!/usr/bin/env python3
"""Extract a source/translation comparison still from each rendered clip."""
import json, subprocess
from ..paths import PROJECT
from pathlib import Path

root = PROJECT
for clip in json.loads((root / 'design/clips.json').read_text()):
    path = root / 'deliverables/comparisons' / (clip['name'] + '.mp4')
    t = (clip['end'] - clip['start']) / 2
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-ss', str(t), '-i',
                    str(path), '-frames:v', '1', '-q:v', '2', '-update', '1',
                    str(path.with_suffix('.jpg'))], check=True)
print('Extracted 20 source/Chinese comparison stills')
