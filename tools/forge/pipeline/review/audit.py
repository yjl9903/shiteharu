#!/usr/bin/env python3
"""Check delivery completeness and font coverage; does not certify visual quality."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import tomllib
from fontTools.ttLib import TTFont, TTCollection
from ..paths import PROJECT, CONFIG, setting_path
from ..subtitles.build import load


def glyphs(path, spec):
    if path.suffix.lower() == '.ttc':
        collection = TTCollection(path)
        fonts = collection.fonts
    else:
        collection = None
        fonts = [TTFont(path)]
    try:
        eligible = [(i, font) for i,font in enumerate(fonts)
                    if spec['family'] in {font['name'].getDebugName(1),font['name'].getDebugName(16)}
                    and ('face_index' not in spec or i == spec['face_index'])]
        if not eligible:
            raise ValueError(f'Configured font family/face is absent: {spec["family"]}')
        index,font = min(eligible, key=lambda item: abs(item[1]['OS/2'].usWeightClass - spec.get('weight',700 if spec.get('bold') else 400)))
        return set((font.getBestCmap() or {}).keys()),index
    finally:
        if collection:
            collection.close()
        else:
            fonts[0].close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default='review/technical-audit.json')
    args = parser.parse_args()
    events, fonts = load()
    faces = {role: glyphs(PROJECT / f['file'],f) for role, f in fonts.items()}
    style_faces = {}
    missing = []
    unverified = []
    undesigned = []
    missing_evidence = []
    for e in events:
        targets=[('ja',CONFIG['review']['font'],e['ja'],bool(CONFIG['ass_style']['bold']))]
        if e.get('text_runs'):
            offset=0
            for run in e['text_runs']:
                role=run.get('font_role',e['font_role'])
                targets.append(('zh',role,e['zh'][offset:offset+run['length']],run.get('bold',fonts[role].get('bold',False))))
                offset+=run['length']
        else:
            targets.append(('zh',e['font_role'],e['zh'],e.get('bold',fonts[e['font_role']].get('bold',False))))
        for language,role,content,bold in targets:
            key=(role,bool(bold))
            if key not in style_faces:
                style_faces[key]=glyphs(PROJECT/fonts[role]['file'],{**fonts[role],'bold':bool(bold)})
            chars = sorted({c for c in content if not c.isspace() and ord(c) not in style_faces[key][0]})
            if chars:
                missing.append({'id':e['id'],'language':language,'role':role,'characters':''.join(chars)})
        if not e.get('timing_status','').startswith('frame-confirmed'):
            unverified.append({'id':e['id'],'status':e.get('timing_status','unreviewed')})
        if not e.get('source_style'):
            undesigned.append(e['id'])
        refs=e.get('evidence',[])
        if not refs:
            missing_evidence.append({'id':e['id'],'reason':'no evidence references'})
        for ref in refs:
            if Path(ref).is_absolute() or not (PROJECT/ref).is_file():
                missing_evidence.append({'id':e['id'],'reference':ref})
    machine_paths=[]
    for path in PROJECT.rglob('*'):
        if not path.is_file() or any(part in {'.venv','.cache','frames','audio'} for part in path.relative_to(PROJECT).parts):
            continue
        if path.suffix not in {'.md','.json','.toml','.py','.sh','.txt','.ass','.srt'}:
            continue
        # Runtime test expression below is split so the scanner does not flag itself.
        bad=re.compile('/'+'Users/|/'+'System/Library/|/'+'Library/Fonts/')
        if bad.search(path.read_text(errors='replace')):
            machine_paths.append(str(path.relative_to(PROJECT)))
    manifest=[{'role':role,'family':f['family'],'file':f['file'],'face_index':faces[role][1],
               'sha256':hashlib.sha256((PROJECT/f['file']).read_bytes()).hexdigest()}
              for role,f in fonts.items()]
    data={'event_count':len(events),'supplemental_count':sum(bool(e.get('supplemental')) for e in events),
          'missing_glyphs':missing,'timing_not_frame_confirmed':unverified,
          'missing_source_style':undesigned,'machine_specific_paths':machine_paths,
          'missing_evidence':missing_evidence,
          'fonts':manifest,
          'used_font_faces':[{'role':role,'bold':bold,'face_index':face[1]} for (role,bold),face in style_faces.items()],
          'note':'Technical audit only. Full visual review and comparison clips are separately required.'}
    target=PROJECT/args.output;target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:len(v) if isinstance(v,list) else v for k,v in data.items()},ensure_ascii=False))
    return 1 if missing or machine_paths or unverified or undesigned or missing_evidence else 0


if __name__ == '__main__':
    sys.exit(main())
