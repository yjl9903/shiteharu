#!/usr/bin/env python3
"""Calibrate explicitly top-centered captions to a visible 20px ink margin.

Only layout fields change. Font metrics are measured with the production libass
renderer, including soft shadows. This is a design aid, not visual approval.
"""
import io, subprocess
import tomlkit
from ..paths import PROJECT, CONFIG, design_files, setting_path
from pathlib import Path
import numpy as np
from PIL import Image
from ..subtitles.build import load, header, render_event
from ..subtitles.shadow_render import render_with_shadow

from ..fonts.prepare_fonts import main as prepare_fonts
prepare_fonts()
root = PROJECT
out=root/'.cache/top-calibration';out.mkdir(parents=True,exist_ok=True)
events,fonts=load();adjustments={};report=[]
for event in events:
    if event['align']!=8 or event['x']!=CONFIG['canvas'][0]/2 or event['y']>CONFIG['calibration']['max_y']:
        continue
    e={**event,'start':0,'end':1,'effect':'none'}
    e.pop('extra_tags',None)
    ass=out/'measure.ass'
    ass.write_text(header(fonts[CONFIG['default_font']]['family'])+render_with_shadow(e,fonts,render_event))
    data=subprocess.check_output(['ffmpeg','-v','error','-f','lavfi','-i',
        f"color=c=0xFF00FF:s={CONFIG['canvas'][0]}x{CONFIG['canvas'][1]}:d=1",'-vf',
        f"format=rgb24,ass=.cache/top-calibration/measure.ass:fontsdir={CONFIG['font_cache']}",
        '-frames:v','1','-f','image2pipe','-vcodec','png','-'],cwd=root)
    im=np.array(Image.open(io.BytesIO(data)).convert('RGB')).astype(np.int16)
    mask=np.max(abs(im-im[-1,0]),axis=2)>18
    ys,xs=np.where(mask)
    if not len(ys):raise RuntimeError('No visible ink: '+e['id'])
    y=round(event['y']+CONFIG['calibration']['margin']-int(ys.min()),2)
    adjustments[e['id']]=y
    report.append({'id':e['id'],'old_y':event['y'],'ink_top':int(ys.min()),'new_y':y})
for path in design_files():
    data=tomlkit.parse(path.read_text());rows=data['events']
    for e in rows:
        if e['id'] in adjustments:e['y']=adjustments[e['id']]
    path.write_text(tomlkit.dumps(data))
ass.unlink(missing_ok=True)
print('Calibrated',len(report),'top-centered events')
