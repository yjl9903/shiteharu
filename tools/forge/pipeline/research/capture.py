from pathlib import Path
from ..paths import PROJECT, CONFIG, research, path, source_media, design_files, setting_path
RESEARCH=research()
from concurrent.futures import ThreadPoolExecutor
import json,subprocess,tomllib
from PIL import Image,ImageDraw,ImageFont
HERE=path(RESEARCH['directory']);ROOT=PROJECT
import sys
from ..subtitles.build import load
rows=load()[0];lookup={e['id']:e for e in rows}
ids=RESEARCH['capture_ids']
src=str(source_media())
(HERE/'source').mkdir(exist_ok=True)
def capture(eid):
 e=lookup[eid];t=e['start']+min(.6,(e['end']-e['start'])/2);out=HERE/'source'/f'{eid}.png'
 subprocess.run(['ffmpeg','-v','error','-ss',str(t),'-i',src,'-frames:v','1','-update','1',str(out)],check=True)
 return {**e,'sample_time':t,'source_frame':str(out.relative_to(ROOT))}
with ThreadPoolExecutor(max_workers=4) as ex:items=list(ex.map(capture,ids))
(HERE/'source-events.json').write_text(json.dumps(items,ensure_ascii=False,indent=2))
font=ImageFont.truetype(str(path(RESEARCH['label_font'])),20)
for pg in range((len(items)+15)//16):
 page=Image.new('RGB',(1600,1200),'#161b22');draw=ImageDraw.Draw(page)
 for k,e in enumerate(items[pg*16:(pg+1)*16]):
  x=(k%4)*400;y=(k//4)*300;im=Image.open(ROOT/e['source_frame'])
  boxes=e.get('source_boxes',[])
  if boxes:
   b=max(boxes,key=lambda b:(b[2]-b[0])*(b[3]-b[1]));left,top,right,bottom=b
   crop=im.crop((max(0,left-15),max(0,top-15),min(im.width,right+15),min(im.height,bottom+15)))
  else:crop=im.crop((0,round(im.height*5/9),im.width,im.height))
  crop.save(HERE/'source'/f'{e["id"]}-crop.png')
  crop.thumbnail((390,235));page.paste(crop,(x+(400-crop.width)//2,y+35+(235-crop.height)//2))
  draw.text((x+8,y+5),f'{e["id"]} / {e["sample_time"]:.2f}s',font=font,fill='white')
  draw.text((x+8,y+270),e['ja'].replace('\n',' ')[:21],font=font,fill='#b5f38f')
 page.save(HERE/f'source-sheet-{pg+1}.jpg')
print('Captured',len(items))
