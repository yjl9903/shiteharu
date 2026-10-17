import concurrent.futures,json,os,subprocess,sys,tomllib
from pathlib import Path
from ..paths import PROJECT, CONFIG, research, path, source_media, design_files, setting_path, read_config
RESEARCH=research()
H=path(RESEARCH['directory']);ROOT=PROJECT
from ..subtitles import build as B
E=json.loads((H/'proposed-events.json').read_text());F=read_config(H/'font-config.proposed.toml');byid={e['id']:e for e in E}
from ..paths import source_media
source=source_media()
D=H/'reel';D.mkdir(exist_ok=True)
ids=RESEARCH['reel_ids']
env={**os.environ,'XDG_CACHE_HOME':str(H/'cache')}
def clip(pair):
 i,id=pair;e=byid[id];start=e['start'];duration=min(3,e['end']-start)
 lines=[]
 for x in E:
  if x['end']<=start or x['start']>=start+duration:continue
  v={**x,'start':max(0,x['start']-start),'end':min(duration,x['end']-start)};lines.append(B.render_event(v,F))
 ass=D/f'{i:02}.ass';ass.write_text(B.header(F[RESEARCH['default_role']]['family'])+''.join(lines));out=D/f'{i:02}.mp4'
 label=f'{id}  {start:.2f}s'
 filt=f"[0:v]split[raw][v];[raw]scale=640:-2,drawtext=fontfile={path(RESEARCH['label_font'])}:text='ORIGINAL':x=12:y=10:fontsize=18:fontcolor=white:box=1:boxcolor=black@0.7[left];[v]ass=filename={ass}:fontsdir={H/'render-fonts'},scale=640:-2,drawtext=fontfile={path(RESEARCH['label_font'])}:text='PROPOSED - {label}':x=12:y=10:fontsize=18:fontcolor=white:box=1:boxcolor=black@0.7[right];[left][right]hstack=inputs=2[out]"
 p=subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-ss',str(start),'-i',str(source),'-t',str(duration),'-filter_complex_threads','1','-filter_complex',filt,'-map','[out]','-map','0:a:0?','-c:v','libx264','-preset','veryfast','-crf','20','-threads','2','-pix_fmt','yuv420p','-c:a','aac','-b:a','128k','-movflags','+faststart','-y',str(out)],capture_output=True,env=env)
 if p.returncode:raise RuntimeError(p.stderr.decode()[-3000:])
 return out,duration,id,start
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:res=list(pool.map(clip,enumerate(ids)))
(D/'concat.txt').write_text('\n'.join("file '"+p.name+"'" for p,*_ in res))
subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-f','concat','-safe','0','-i',str(D/'concat.txt'),'-c','copy','-movflags','+faststart','-y',str(H/'font-proof-reel.mp4')],check=True)
chapters=[];offset=0
for p,d,id,s in res:chapters.append({'id':id,'reel_start':offset,'original_start':s,'duration':d});offset+=d
(H/'reel-chapters.json').write_text(json.dumps(chapters,indent=2))
print('Reel ready:',round(offset,2),'seconds',len(res),'scenes')
