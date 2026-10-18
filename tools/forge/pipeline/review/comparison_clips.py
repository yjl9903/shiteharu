#!/usr/bin/env python3
"""Render source (left) and Chinese performance (right) for editable clip list."""
from ..paths import PROJECT, CONFIG, source_media, setting_path, read_config
from pathlib import Path
import json,subprocess,sys,tomllib
root = PROJECT;media=source_media()
out=setting_path('comparisons');out.mkdir(exist_ok=True,parents=True)
clips=read_config(setting_path('clips'))['clips']
for c in clips:
    if len(sys.argv)>1 and sys.argv[1] not in c['name']:continue
    a=c['start'];dur=c['end']-a
    vf=f"[0:v]setpts=PTS+{a}/TB,split=2[base][sub];[base]scale={CONFIG['comparison_width']}:-2[left];[sub]ass={CONFIG['output']}/{CONFIG['performance_ass']}:fontsdir={CONFIG['font_cache']},scale={CONFIG['comparison_width']}:-2[right];[left][right]hstack=inputs=2,setpts=PTS-STARTPTS[v]"
    subprocess.run(['ffmpeg','-y','-v','error','-ss',str(a),'-i',str(media),'-t',str(dur),'-filter_complex',vf,'-map','[v]','-map','0:a?','-c:v','libx264','-preset','fast','-crf','20','-pix_fmt','yuv420p','-c:a','aac','-b:a','128k','-movflags','+faststart',str(out/(c['name']+'.mp4'))],cwd=root,check=True)
    print(c['name'],flush=True)
