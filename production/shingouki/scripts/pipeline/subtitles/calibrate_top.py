#!/usr/bin/env python3
"""Calibrate explicitly top-centered captions to a visible 20px ink margin.

Only layout fields change. Font metrics are measured with the production libass
renderer, including soft shadows. This is a design aid, not visual approval.
"""
import io, json, subprocess
from ..paths import PROJECT
from pathlib import Path
import numpy as np
from PIL import Image
from ..subtitles.build import load, header, render_event
from ..subtitles.shadow_render import render_with_shadow

root = PROJECT
out=root/'.cache/top-calibration';out.mkdir(parents=True,exist_ok=True)
events,fonts=load();adjustments={};report=[]
for event in events:
    if event['align']!=8 or event['x']!=960 or event['y']>30:
        continue
    e={**event,'start':0,'end':1,'effect':'none'}
    e.pop('extra_tags',None)
    ass=out/'measure.ass'
    ass.write_text(header(fonts['sans']['family'])+render_with_shadow(e,fonts,render_event))
    data=subprocess.check_output(['ffmpeg','-v','error','-f','lavfi','-i',
        'color=c=0xFF00FF:s=1920x1080:d=1','-vf',
        'format=rgb24,ass=.cache/top-calibration/measure.ass:fontsdir=.cache/render-fonts',
        '-frames:v','1','-f','image2pipe','-vcodec','png','-'],cwd=root)
    im=np.array(Image.open(io.BytesIO(data)).convert('RGB')).astype(np.int16)
    mask=np.max(abs(im-im[1079,0]),axis=2)>18
    ys,xs=np.where(mask)
    if not len(ys):raise RuntimeError('No visible ink: '+e['id'])
    y=round(event['y']+20-int(ys.min()),2)
    adjustments[e['id']]=y
    report.append({'id':e['id'],'old_y':event['y'],'ink_top':int(ys.min()),'new_y':y})
for path in (root/'design').glob('events-*.json'):
    rows=json.loads(path.read_text())
    for e in rows:
        if e['id'] in adjustments:e['y']=adjustments[e['id']]
    path.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
ass.unlink(missing_ok=True)
print('Calibrated',len(report),'top-centered events')
