#!/usr/bin/env python3
"""Render an original/Chinese pair for every chosen event and make review sheets."""
import argparse
import json
from pathlib import Path
import subprocess
from PIL import Image, ImageDraw
from ..paths import PROJECT, CONFIG, setting_path, source_media
from ..subtitles.build import load


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--start',type=float,default=0)
    parser.add_argument('--end',type=float,default=CONFIG['duration'])
    parser.add_argument('--label',default='all')
    parser.add_argument('--at',type=float,help='Render one explicit source time')
    args=parser.parse_args()
    events,_=load()
    height=round(640*CONFIG['canvas'][1]/CONFIG['canvas'][0])
    ass=(setting_path('output')/CONFIG['performance_ass']).relative_to(PROJECT)
    font_cache=setting_path('font_cache').relative_to(PROJECT)
    selected=[(e['id'],(e['start']+e['end'])/2) for e in events if args.start<=e['start']<args.end]
    if args.at is not None: selected=[('explicit',args.at)]
    out=PROJECT/'frames'/f'comparison-{args.label}';out.mkdir(parents=True,exist_ok=True)
    items=[]
    for i,(sid,t) in enumerate(selected):
        name=f'{i:03}-{sid}.jpg'
        # Keep original global timestamps so libass chooses the correct event.
        vf=(f'setpts=PTS+{t}/TB,split=2[a][b];'
            f'[a]scale=640:{height}[left];'
            f'[b]ass={ass}:fontsdir={font_cache},scale=640:{height}[right];'
            '[left][right]hstack=inputs=2')
        subprocess.run(['ffmpeg','-v','error','-y','-ss',str(t),'-i',str(source_media()),
                        '-frames:v','1','-filter_complex',vf,str(out/name)],cwd=PROJECT,check=True)
        items.append({'id':sid,'requested_time':t,'file':str((out/name).relative_to(PROJECT))})
    for offset in range(0,len(items),3):
        sheet=Image.new('RGB',(1280,(height+30)*min(3,len(items)-offset)),'#202020');draw=ImageDraw.Draw(sheet)
        for j,item in enumerate(items[offset:offset+3]):
            draw.text((8,j*(height+30)+5),f"{item['id']}  {item['requested_time']:.3f}s    SOURCE (left) / TRANSLATION (right)",fill='white',font_size=18)
            with Image.open(PROJECT/item['file']) as im: sheet.paste(im,(0,j*(height+30)+30))
        target=out/f'sheet-{offset//3:03}.jpg';sheet.save(target,quality=92)
        print(target.relative_to(PROJECT),flush=True)
    (out/'index.json').write_text(json.dumps(items,ensure_ascii=False,indent=2)+'\n')


if __name__=='__main__':
    main()
