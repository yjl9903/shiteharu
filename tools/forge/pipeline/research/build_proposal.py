"""Read the active project's current design; write only this independent proof directory."""
import concurrent.futures,copy,hashlib,html,json,os,re,shutil,subprocess,sys,time
from pathlib import Path
import tomlkit
from ..paths import PROJECT, CONFIG, research, path, source_media, design_files, setting_path
RESEARCH=research()
from PIL import Image,ImageChops,ImageDraw,ImageFont
from fontTools.ttLib import TTFont
H=path(RESEARCH['directory']);ROOT=PROJECT
from ..subtitles import build as B
from ..subtitles.shadow_render import render_with_shadow
events,oldfonts=B.load()
C=H/'candidates';F=H/'render-fonts';F.mkdir(exist_ok=True)
fonts=copy.deepcopy(RESEARCH['fonts'])
for k,v in oldfonts.items():
 p=path(v['file'])
 fonts['old_'+k]={**v,'file':os.path.relpath(p,ROOT)}
for k,v in fonts.items():
 p=path(v['file']);dest=F/(k+p.suffix)
 if not p.is_file():raise FileNotFoundError(f'Missing proposed font: {p.name}')
 if dest.is_symlink() or dest.exists():dest.unlink()
 dest.symlink_to(os.path.relpath(p,F))
cmaps={k:TTFont(ROOT/v['file'],fontNumber=0).getBestCmap() for k,v in fonts.items() if not k.startswith('old_')}
from .rules import proposal as apply_proposal
def proposal(e):
 return apply_proposal(e,RESEARCH['proposal_rules'])

def render(e,allfonts=fonts):
 """Use project ASS engine, with explicit optional white expansion layer for rounded ink."""
 expand=e.get('fill_expand',0)
 if not expand:return render_with_shadow(e,allfonts,B.render_event)
 bottom={**e,'outline':e['outline']+expand}
 top={**e,'outline':expand,'outline_color':e['color'],'shadow':0,'layer':e.get('layer',0)+1}
 return B.render_event(bottom,allfonts)+B.render_event(top,allfonts)

patches=[];proposed=[];missing=[]
for e in events:
 p,reason=proposal(e);new={**e,**p};proposed.append(new)
 absent=sorted({c for c in e['zh'] if not c.isspace() and p['font_role'] in cmaps and ord(c) not in cmaps[p['font_role']]})
 if absent:missing.append({'id':e['id'],'font_role':p['font_role'],'characters':''.join(absent)})
 patches.append({'id':e['id'],'set':p,'reason':reason,'base_fontsize':e['fontsize'],'base_design_file':e.get('_design_file',CONFIG['timeline'])})
snapshot={'created_at':time.strftime('%Y-%m-%d %H:%M:%S %z'),'files':{os.path.relpath(p,ROOT):hashlib.sha256(p.read_bytes()).hexdigest() for p in [setting_path('fonts'),setting_path('defaults'),*design_files()]},'warning':'Event fields are a proposal. Recompute outline/fill ratios if production font sizes have changed. Preserve x/y/timings/text/current layout.'}
(H/'baseline-events.json').write_text(json.dumps(events,ensure_ascii=False,indent=2))
(H/'proposed-events.json').write_text(json.dumps(proposed,ensure_ascii=False,indent=2))
(H/'font-config.proposed.toml').write_text(tomlkit.dumps(fonts))
(H/'event-font-patches.json').write_text(json.dumps(patches,ensure_ascii=False,indent=2))
(H/'coverage.json').write_text(json.dumps({'events':len(events),'missing':missing,'snapshot':snapshot},ensure_ascii=False,indent=2))
if missing:raise SystemExit('Missing glyphs: '+str(missing))
(H/'proposed-full.ass').write_text(B.header(fonts[RESEARCH['default_role']]['family'])+''.join(render(e) for e in proposed))
samples=json.loads((H/'source-events.json').read_text());byid={e['id']:e for e in events};newbyid={e['id']:e for e in proposed}
R=H/'renders';R.mkdir(exist_ok=True);env={**os.environ,'XDG_CACHE_HOME':str(H/'cache')}
def proof(sample):
 id=sample['id'];e=byid[id];new=newbyid[id];frame=ROOT/sample['source_frame']
 for kind,event in [('after',new)]:
  # Isolate this caption at a settled time; source frame is unchanged in the contextual view.
  item={**event,'start':0,'end':2};
  if item.get('effect') in ['slide','pop','fade','typewriter']:item['effect']='none'
  ass=R/f'{id}-{kind}.ass';ass.write_text(B.header(fonts[item['font_role']]['family'])+render(item))
  out=R/f'{id}-{kind}.png';flt=f'ass=filename={ass}:fontsdir={F}'
  proc=subprocess.run(['ffmpeg','-hide_banner','-loglevel','verbose','-i',str(frame),'-vf',flt,'-frames:v','1','-threads','1','-y',str(out)],capture_output=True,env=env)
  (R/f'{id}-{kind}.log').write_text(proc.stderr.decode(errors='replace').replace(str(ROOT)+os.sep,''))
  if proc.returncode:raise RuntimeError(proc.stderr.decode()[-2000:])
  # A neutral, same-size real libass specimen lets the viewer assess glyph shapes without background clutter.
  item={**item,'x':CONFIG['canvas'][0]/2,'y':CONFIG['canvas'][1]/2,'align':5,'text_layout':'horizontal','rotation':0,'effect':'none','max_width':CONFIG['max_width']}
  item.pop('extra_tags',None)
  plate=R/f'{id}-{kind}-type.ass';plate.write_text(B.header(fonts[item['font_role']]['family'])+render(item))
  image=R/f'{id}-{kind}-type.png'
  proc=subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-f','lavfi','-i',f"color=c=0x303640:s={CONFIG['canvas'][0]}x{CONFIG['canvas'][1]}:d=0.1",'-vf',f'ass=filename={plate}:fontsdir={F}','-frames:v','1','-threads','1','-y',str(image)],capture_output=True,env=env)
  if proc.returncode:raise RuntimeError(proc.stderr.decode())
  im=Image.open(image).convert('RGB');bg=Image.new('RGB',im.size,im.getpixel((0,0)));box=ImageChops.difference(im,bg).getbbox()
  if box:im.crop((max(0,box[0]-16),max(0,box[1]-16),min(im.width,box[2]+16),min(im.height,box[3]+16))).save(image)
 return id
if __name__=='__main__':
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
  for id in pool.map(proof,samples):print('Rendered',id,flush=True)
 print('Coverage passed:',len(events),'events. All writes confined to',H)
