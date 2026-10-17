import concurrent.futures, hashlib, json, urllib.request, zipfile
from pathlib import Path
from ..paths import PROJECT, CONFIG, research, path, source_media, design_files, setting_path
RESEARCH=research()
H=path(RESEARCH['directory']); D=H/'candidates';D.mkdir(exist_ok=True)
def fetch(url,path):
    if not path.exists():
        req=urllib.request.Request(url,headers={'User-Agent':'font-style-research'})
        with urllib.request.urlopen(req,timeout=180) as r:path.write_bytes(r.read())
    return path
jobs=list(RESEARCH['downloads'])
for release in RESEARCH['releases']:
    rel=json.loads((H/(release['name']+'-release.json')).read_text())
    for asset in rel['assets']:
        if release['assets'] and asset['name'] not in release['assets']:continue
        jobs.append((release['name'],asset['browser_download_url'],asset['name']))
def run(job):
    group,url,name=job;p=D/group/name;p.parent.mkdir(exist_ok=True)
    try:
        fetch(url,p)
        if p.suffix=='.zip':
            with zipfile.ZipFile(p) as z:
                for member in z.infolist():
                    dest=(p.parent/member.filename).resolve()
                    if dest.is_relative_to(p.parent.resolve()):z.extract(member,p.parent)
        print('OK',group,name,p.stat().st_size,flush=True)
        return {'group':group,'url':url,'file':str(p.relative_to(PROJECT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
    except Exception as e:print('FAILED',name,str(e),flush=True);return {'url':url,'error':type(e).__name__}
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:results=list(ex.map(run,jobs))
(H/'downloads.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
