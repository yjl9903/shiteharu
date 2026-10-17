import json,urllib.request,concurrent.futures
from pathlib import Path
from ..paths import PROJECT, CONFIG, research, path, source_media, design_files, setting_path
RESEARCH=research()
H=path(RESEARCH['directory'])
repos=RESEARCH['repositories']
def get(url):
 req=urllib.request.Request(url,headers={'User-Agent':'forge-font-research'})
 return json.load(urllib.request.urlopen(req,timeout=30))
def inspect(repo):
 try:
  r=get('https://api.github.com/repos/'+repo+'/releases/latest')
  print(repo,[(a['name'],a['browser_download_url']) for a in r.get('assets',[])])
  (H/(repo.split('/')[-1]+'-release.json')).write_text(json.dumps(r))
 except Exception as e:print(repo,e)
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:list(ex.map(inspect,repos))
