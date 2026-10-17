import json,html,hashlib
from pathlib import Path
from ..paths import PROJECT, CONFIG, research, path, source_media, design_files, setting_path
RESEARCH=research()
from PIL import Image,ImageDraw,ImageFont
from fontTools.ttLib import TTFont
H=path(RESEARCH['directory'])
samples=json.loads((H/'source-events.json').read_text())
label=ImageFont.truetype(str(path(RESEARCH['label_font'])),22)
for page in range((len(samples)+7)//8):
 im=Image.new('RGB',(1600,1440),'#171b22');d=ImageDraw.Draw(im)
 for i,e in enumerate(samples[page*8:page*8+8]):
  id=e['id'];d.text((8,i*180+3),id+'  原片 / 当前中文',font=label,fill='white')
  for j,p in enumerate([H/'source'/f'{id}-crop.png',H/'renders'/f'{id}-after-type.png']):
   v=Image.open(p);v.thumbnail((780,135));im.paste(v,(j*800+8,i*180+40))
 im.save(H/f'proof-sheet-{page+1}.jpg')
rows=[]
for eid,text,pattern,label_text in RESEARCH['identification']:
 matches=sorted(PROJECT.glob(pattern))
 if len(matches)!=1:raise ValueError(f'Expected one identification font for {eid}, got {len(matches)}')
 rows.append((eid,text,matches[0],label_text))
im=Image.new('RGB',(1600,len(rows)*260),'#242a33');d=ImageDraw.Draw(im)
for i,(id,t,p,name) in enumerate(rows):
 src=Image.open(H/'source'/f'{id}-crop.png');src.thumbnail((770,205));im.paste(src,(10,i*260+40));d.text((10,i*260+5),'原视频 '+id,font=label,fill='white')
 f=ImageFont.truetype(str(p),120);b=f.getbbox(t,stroke_width=4);v=Image.new('RGB',(b[2]-b[0]+24,b[3]-b[1]+24),'#363c44');ImageDraw.Draw(v).text((12-b[0],12-b[1]),t,font=f,fill='white',stroke_width=4,stroke_fill='black');v.thumbnail((770,205));im.paste(v,(810,i*260+40));d.text((810,i*260+5),name,font=label,fill='white')
im.save(H/'identification.jpg')
inventory=[]
for p in (H/'candidates').rglob('*'):
 if p.suffix.lower() not in ['.ttf','.otf']:continue
 f=TTFont(p);inventory.append({'file':str(p.relative_to(PROJECT)),'family':f['name'].getDebugName(1),'style':f['name'].getDebugName(2),'characters':len(f.getBestCmap()),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(H/'candidate-inventory.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2))
print('Proof sheets:',len(samples),'proofs;',len(inventory),'candidate font files.')
