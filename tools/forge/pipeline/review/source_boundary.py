#!/usr/bin/env python3
"""Extract every source frame near a boundary, with real decoded PTS labels."""
import argparse
import json
from pathlib import Path
import re
import subprocess
from PIL import Image, ImageDraw
from .source_frames import ROOT, media

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('time', type=float)
p.add_argument('--radius', type=float, default=0.3)
p.add_argument('--label')
p.add_argument('--crop', help='x,y,width,height at native source resolution')
a = p.parse_args()
if a.time < 0 or a.radius <= 0:
    p.error('time must be nonnegative and radius positive')
start, end = max(0, a.time-a.radius), a.time+a.radius
out = ROOT/'frames'/(a.label or f'boundary-{a.time:.3f}')
out.mkdir(parents=True, exist_ok=True)
vf = 'showinfo'
if a.crop:
    x,y,w,h=map(int,a.crop.split(',')); vf += f',crop={w}:{h}:{x}:{y}'
vf += ',scale=480:-1'
run = subprocess.run(['ffmpeg','-hide_banner','-y','-ss',str(start),'-t',str(end-start),'-copyts','-i',str(media()),
                      '-vf',vf,'-fps_mode','passthrough',str(out/'%04d.jpg')],
                     capture_output=True,text=True)
if run.returncode:
    raise SystemExit(run.stderr)
pts = [float(v) for v in re.findall(r'pts_time:([0-9.]+)',run.stderr)]
files = sorted(out.glob('[0-9][0-9][0-9][0-9].jpg'))
if not files or len(pts) != len(files):
    raise ValueError('Source frame/PTS extraction is empty or inconsistent')
entries=[]
for offset in range(0,len(files),24):
    batch=files[offset:offset+24]
    with Image.open(batch[0]) as im: w,h=im.size
    sheet=Image.new('RGB',(w*4,(h+26)*((len(batch)+3)//4)),'#222222');draw=ImageDraw.Draw(sheet)
    for i,path in enumerate(batch):
        n=offset+i; x=i%4*w;y=i//4*(h+26)
        with Image.open(path) as im: sheet.paste(im,(x,y+26))
        draw.text((x+4,y+4),f'{pts[n]:.6f}s',fill='white',font_size=17)
        entries.append({'pts':pts[n],'file':str(path.relative_to(ROOT))})
    target=out/f'sheet-{offset//24:03}.jpg';sheet.save(target,quality=92)
    print(target.relative_to(ROOT))
(out/'index.json').write_text(json.dumps(entries,indent=2)+'\n')
(out/'capture.json').write_text(json.dumps({'time':a.time,'radius':a.radius,'crop':a.crop,'label':a.label,
    'note':'Each frame has decoded source PTS. Caption boundaries require manual inspection.'},indent=2)+'\n')
