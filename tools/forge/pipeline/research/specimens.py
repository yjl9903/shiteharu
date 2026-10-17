from pathlib import Path
from ..paths import PROJECT, CONFIG, research, path, source_media, design_files, setting_path
RESEARCH=research()
from PIL import Image,ImageDraw,ImageFont
from fontTools.ttLib import TTFont
H=path(RESEARCH['directory'])
paths=sorted({p for pattern in RESEARCH['specimen_font_globs'] for p in PROJECT.glob(pattern) if not any(x in str(p.relative_to(PROJECT)) for x in RESEARCH['specimen_exclude'])})
label=ImageFont.truetype(str(path(RESEARCH['label_font'])),22)
def glyph(p,t,size=90):
 f=ImageFont.truetype(str(p),size);b=f.getbbox(t,stroke_width=3)
 im=Image.new('RGB',(b[2]-b[0]+16,b[3]-b[1]+16),'#363c44');d=ImageDraw.Draw(im);d.text((8-b[0],8-b[1]),t,font=f,fill='white',stroke_width=3,stroke_fill='black');return im
for page in range((len(paths)+7)//8):
 sheet=Image.new('RGB',(1600,8*190),'#171b22');d=ImageDraw.Draw(sheet)
 for row,p in enumerate(paths[page*8:page*8+8]):
  f=TTFont(p);name=f['name'].getDebugName(1);d.text((10,row*190+5),name,font=label,fill='white')
  for col,t in enumerate(RESEARCH['specimens']):
   missing=''.join(ch for ch in t if not ch.isspace() and ord(ch) not in f.getBestCmap())
   im=glyph(p,t);im.thumbnail((510,130));sheet.paste(im,(col*530+10,row*190+40))
   if missing:d.text((col*530+10,row*190+160),'缺字：'+missing,font=label,fill='orange')
 sheet.save(H/f'candidates-sheet-{page+1}.jpg')
