"""Render the complete current font proof without modifying production output."""
from pathlib import Path
from ..paths import PROJECT, CONFIG, research, path, source_media, design_files, setting_path
RESEARCH=research()
from datetime import datetime
from zoneinfo import ZoneInfo
import hashlib,json,os,subprocess,tomllib,sys
H=path(RESEARCH['directory']);ROOT=PROJECT
source=source_media()
ass=H/'proposed-full.ass';out=H/'current-full.mp4';temp=H/'current-full.rendering.mp4'
with (H/'full-render.log').open('w') as log:
 subprocess.run(['ffmpeg','-hide_banner','-y','-i',str(source),'-vf',f'ass=filename={ass}:fontsdir={H/"render-fonts"},scale=1280:-2','-c:v','libx264','-preset','veryfast','-crf','21','-threads','4','-pix_fmt','yuv420p','-an','-movflags','+faststart','-progress',str(H/'full-render-progress.txt'),str(temp)],stderr=log,stdout=subprocess.DEVNULL,env={**os.environ,'XDG_CACHE_HOME':str(H/'cache')},check=True)
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration:stream=width,height,codec_name','-of','json',str(temp)]))
source_info=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','json',str(source)]))
if abs(float(probe['format']['duration'])-float(source_info['format']['duration']))>.25:raise RuntimeError('Incomplete full render')
temp.replace(out)
print('Font proposal video ready:',probe['format']['duration'],'seconds',flush=True)
