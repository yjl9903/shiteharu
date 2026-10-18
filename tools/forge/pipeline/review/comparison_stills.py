#!/usr/bin/env python3
"""Extract a source/translation comparison still from each rendered clip."""
import json, subprocess
from ..paths import PROJECT, setting_path, read_config
from pathlib import Path

root = PROJECT
for clip in read_config(setting_path('clips'))['clips']:
    path = setting_path('comparisons') / (clip['name'] + '.mp4')
    t = (clip['end'] - clip['start']) / 2
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-ss', str(t), '-i',
                    str(path), '-frames:v', '1', '-q:v', '2', '-update', '1',
                    str(path.with_suffix('.jpg'))], check=True)
print('Extracted comparison stills')
