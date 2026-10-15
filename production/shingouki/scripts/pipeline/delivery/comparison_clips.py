#!/usr/bin/env python3
"""Render source (left) and Chinese performance (right) for editable clip list."""
from ..paths import PROJECT
from pathlib import Path
import json,subprocess,sys,tomllib
root = PROJECT;media=root/Path(tomllib.loads((root/'session.toml').read_text())['input']['media'])
out=root/'deliverables/comparisons';out.mkdir(exist_ok=True,parents=True)
clips=json.loads((root/'design/clips.json').read_text())
for c in clips:
    if len(sys.argv)>1 and sys.argv[1] not in c['name']:continue
    a=c['start'];dur=c['end']-a
    vf=f"[0:v]setpts=PTS+{a}/TB,split=2[base][sub];[base]scale=960:540[left];[sub]ass=deliverables/zh.performance.ass:fontsdir=.cache/render-fonts,scale=960:540[right];[left][right]hstack=inputs=2,setpts=PTS-STARTPTS[v]"
    subprocess.run(['ffmpeg','-y','-v','error','-ss',str(a),'-i',str(media),'-t',str(dur),'-filter_complex',vf,'-map','[v]','-map','0:a','-c:v','libx264','-preset','fast','-crf','20','-pix_fmt','yuv420p','-c:a','aac','-b:a','128k','-movflags','+faststart',str(out/(c['name']+'.mp4'))],cwd=root,check=True)
    print(c['name'],flush=True)
