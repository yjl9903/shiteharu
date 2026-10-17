import concurrent.futures,hashlib,json,tarfile,urllib.request,zipfile
from pathlib import Path
from ..paths import PROJECT, CONFIG, research, path, source_media, design_files, setting_path
RESEARCH=research()
H=path(RESEARCH['directory']);D=H/'candidates'
jobs=RESEARCH['extra_downloads']
def run(j):
 group,u,n=j;p=D/group/n;p.parent.mkdir(exist_ok=True)
 try:
  if not p.exists():
   with urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=180) as r:p.write_bytes(r.read())
  if p.suffix=='.tgz':
   with tarfile.open(p) as t:t.extractall(p.parent,filter='data')
  if p.suffix=='.zip':
   with zipfile.ZipFile(p) as z:z.extractall(p.parent)
  print(n,p.stat().st_size,flush=True);return {'file':str(p.relative_to(PROJECT)),'url':u,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
 except Exception as e: print(n,e,flush=True);return {'url':u,'error':type(e).__name__}
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:r=list(ex.map(run,jobs))
(H/'downloads-extra.json').write_text(json.dumps(r,indent=2))
