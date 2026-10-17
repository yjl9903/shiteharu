#!/usr/bin/env python3
"""Deterministic ASS/SRT export from manually reviewed text + editable design TOML."""
import argparse, html, json, math, re, subprocess, tomllib
from ..paths import PROJECT, CONFIG, setting_path, design_files, read_config
from pathlib import Path
from ..subtitles.shadow_render import render_with_shadow
from captions import font_runs
ROOT = PROJECT

def ass_time(t):
    n=math.floor(t*100+1e-7); return f'{n//360000}:{n//6000%60:02}:{n//100%60:02}.{n%100:02}'
def srt_time(t):
    n=round(t*1000); return f'{n//3600000:02}:{n//60000%60:02}:{n//1000%60:02},{n%1000:03}'
def rgb(c):
    c=c.lstrip('#');return '&H'+c[4:6]+c[2:4]+c[0:2]+'&'
def esc(t):
    return t.replace('\\','\\\\').replace('{','｛').replace('}','｝').replace('\n',r'\N')

def header(font):
    style=CONFIG['ass_style']
    return f'''[Script Info]
Title: {CONFIG['title']}
ScriptType: v4.00+
PlayResX: {CONFIG['canvas'][0]}
PlayResY: {CONFIG['canvas'][1]}
WrapStyle: 2
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font},{style['fontsize']},&H00FFFFFF,&H00FFFFFF,&H00000000,&H90000000,{style['bold']},0,0,0,100,100,0,0,1,{style['outline']},{style['shadow']},{style['align']},{style['margin_left']},{style['margin_right']},{style['margin_vertical']},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''

def line(e,text,tags,layer=0,start=None,end=None):
    return f"Dialogue: {layer},{ass_time(e['start'] if start is None else start)},{ass_time(e['end'] if end is None else end)},Default,{e['id']},0,0,0,,{{{tags}}}{text}\n"

def tags(e,fonts):
    f=fonts[e['font_role']]; fs=e['fontsize']; x=e['x'];y=e['y'];sx=e.get('scale_x',100);sy=e.get('scale_y',100)
    longest=max(len(s) for s in e['zh'].splitlines())
    # Scale width only when text would exceed the explicit design envelope.
    sx=min(sx,100*e.get('max_width',CONFIG['max_width'])/max(1,longest*fs))
    s=fr"\an{e['align']}\fn{f['family']}\fs{fs}\b{1 if e.get('bold',f.get('bold',False)) else 0}\fscx{sx:.2f}\fscy{sy}\fsp{e.get('spacing',0)}\bord{e['outline']}\shad{e['shadow']}\1c{rgb(e['color'])}\3c{rgb(e['outline_color'])}\frz{e.get('rotation',0)}"
    if e.get('italic'):s+=r'\i1'
    effect=e.get('effect','none'); dur=round((e['end']-e['start'])*1000)
    if effect=='slide':s+=fr"\move({e.get('from_x',x+180)},{e.get('from_y',y)},{x},{y},0,{e.get('in_ms',220)})"
    elif effect not in ['shake']:s+=fr'\pos({x},{y})'
    if effect=='fade':s+=fr"\fad({e.get('in_ms',120)},{e.get('out_ms',100)})"
    if effect=='wipe':
        box=e.get('reveal_box',[]);ms=e.get('in_ms',0)
        if len(box)!=4 or box[2]<=box[0] or box[3]<=box[1] or ms<=0:
            raise ValueError(f'Invalid wipe reveal_box or in_ms for {e["id"]}')
        left,top,right,bottom=box
        initial=e.get('reveal_initial_width',0)
        if not 0<=initial<=right-left:raise ValueError(f'Invalid initial wipe width for {e["id"]}')
        s+=fr'\clip({left},{top},{left+initial},{bottom})\t(0,{ms},\clip({left},{top},{right},{bottom}))'
    if effect=='pop':
        sc=e.get('initial_scale',135); ms=e.get('in_ms',140)
        s+=fr'\fscx{sx*sc/100:.2f}\fscy{sy*sc/100:.2f}\t(0,{ms},\fscx{sx:.2f}\fscy{sy})'
    if effect=='pulse':
        period=e.get('period_ms',600)
        for t in range(0,dur,period):
            s+=fr'\t({t},{min(dur,t+period//2)},\fscx{sx*1.08:.2f}\fscy{sy*1.08:.2f})\t({min(dur,t+period//2)},{min(dur,t+period)},\fscx{sx:.2f}\fscy{sy})'
    if effect=='glow':s+=fr"\blur{e.get('glow',2)}"
    if 'blur' in e:s+=fr"\blur{e['blur']}"
    if 'extra_tags' in e:s+=e['extra_tags']
    return s

def render_event(e,fonts):
    if 'text_runs' in e and ('line_breaks' in e or 'line_advance' in e or e.get('text_layout')=='vertical'):
        raise ValueError(f'text_runs cannot combine with per-row layout in {e["id"]}')
    if 'line_breaks' in e:
        # Per-scene editorial wrapping; wording stays in the reviewed work file.
        chars=e['zh'].replace('\n',''); lengths=e['line_breaks']
        if e.get('text_layout')=='vertical' or not lengths or any(not isinstance(n,int) or n<1 for n in lengths) or sum(lengths)!=len(chars):
            raise ValueError(f'Invalid line_breaks for {e["id"]}')
        rows=[]; offset=0
        for n in lengths:
            rows.append(chars[offset:offset+n]); offset+=n
        e={**e,'zh':'\n'.join(rows)}
        e.pop('line_breaks')
    if 'line_advance' in e and e.get('text_layout') != 'vertical':
        rows=e['zh'].splitlines(); advance=e['line_advance']; result=''
        sx=min(e.get('scale_x',100),100*e.get('max_width',CONFIG['max_width'])/max(1,max(map(len,rows))*e['fontsize']))
        for i,row in enumerate(rows):
            offset=(i-len(rows)+1)*advance if e['align']<=3 else (i-(len(rows)-1)/2)*advance if e['align']<=6 else i*advance
            item={**e,'zh':row,'y':e['y']+offset,'scale_x':sx}
            item.pop('line_advance')
            if 'from_y' in item:item['from_y']+=offset
            result+=render_event(item,fonts)
        return result
    if e.get('text_layout')=='vertical':
        # Layout only: reviewed text remains unchanged in the source/timeline.
        chars=list(e['zh'].replace('\n',''))
        lengths=e.get('vertical_columns')
        if lengths is None:
            n=e.get('column_chars',8)
            if n<1:raise ValueError('column_chars must be positive')
            lengths=[min(n,len(chars)-i) for i in range(0,len(chars),n)]
        if sum(lengths)!=len(chars) or any(n<1 for n in lengths):
            raise ValueError(f'Invalid vertical column lengths for {e["id"]}')
        result='';offset=0
        for col,count in enumerate(lengths):
            for row,ch in enumerate(chars[offset:offset+count]):
                dx=-col*e['fontsize']*e.get('column_gap',1.25)
                dy=row*e['fontsize']*e.get('row_gap',1.05)
                item={**e,'zh':ch,'text_layout':'horizontal','x':e['x']+dx,'y':e['y']+dy,'align':8}
                if 'from_x' in e:item['from_x']=e['from_x']+dx
                if 'from_y' in e:item['from_y']=e['from_y']+dy
                if ch in e.get('vertical_rotate_punctuation','…—～'):
                    item.update(rotation=e.get('rotation',0)-90,align=5,y=item['y']+e['fontsize']*.5)
                    if 'from_y' in item:item['from_y']+=e['fontsize']*.5
                result+=render_event(item,fonts)
            offset+=count
        return result
    text=esc(e['zh']); base=tags(e,fonts); effect=e.get('effect','none'); layer=e.get('layer',1 if e.get('supplemental') else 0)
    if 'text_runs' in e:
        # Typography spans reference character counts, never duplicate subtitle wording.
        text=''
        for run in font_runs(e['zh'],e,fonts,e['id']):
            text+=fr"{{\fn{fonts[run['font_role']]['family']}\b{int(run['bold'])}}}"
            text+=esc(run['text'])
    if effect=='shake':
        result='';step=e.get('period_ms',65)/1000;amp=e.get('amplitude',5);t=e['start'];i=0
        while t<e['end']-.001:
            x=e['x']+amp*math.sin(i*2.399); y=e['y']+amp*.6*math.cos(i*3.7)
            result+=line(e,text,base+fr'\pos({x:.2f},{y:.2f})',layer,t,min(e['end'],t+step));t+=step;i+=1
        return result
    if effect=='typewriter':
        if 'text_runs' in e: raise ValueError('text_runs and typewriter cannot be combined')
        ms=e.get('char_ms',70);vis=0; txt=''
        schedule=e.get('reveal_ms')
        if schedule is not None and (len(schedule)!=len(e['zh'].replace('\n','')) or schedule!=sorted(schedule) or any(t<0 for t in schedule)):
            raise ValueError(f'Invalid reveal_ms for {e["id"]}')
        for ch in e['zh']:
            if ch=='\n':txt+=r'\N';continue
            at=schedule[vis] if schedule is not None else vis*ms
            txt+=fr'{{\alpha&HFF&\t({at},{at+1},\alpha&H00&)}}'+esc(ch);vis+=1
        return line(e,txt,base,layer)
    if effect=='distress':
        # Editable clipped horizontal displacements approximate fractured letterforms.
        result='';fs=e['fontsize'];lines=len(e['zh'].splitlines());height=fs*lines*1.3
        top=e['y']-(height if e['align']<=3 else height/2 if e['align']<=6 else 0)-10
        for i in range(max(1,math.ceil((height+30)/8))):
            y1=top+i*8;y2=y1+8;dx=((i*7)%5-2)*e.get('amplitude',1.4)
            b=re.sub(r'\\pos\([^)]*\)',fr'\\pos({e["x"]+dx},{e["y"]})',base)
            result+=line(e,text,b+fr'\clip(0,{int(y1)},{CONFIG['canvas'][0]},{int(y2)})',layer)
        return result
    return line(e,text,base,layer)

def load():
    src=setting_path('timeline')
    data=tomllib.loads(src.read_text()) if src.suffix == '.toml' else json.loads(src.read_text()); rows=data[CONFIG['collection']] if CONFIG.get('collection') else data
    rows=[{**r,'ja':r[CONFIG['source_text']],'zh':r[CONFIG['text']]} for r in rows]
    if not rows:raise SystemExit('No reviewed translation segments')
    fonts=read_config(setting_path('fonts')); defaults=read_config(setting_path('defaults'))['default']
    overrides={};extras=[]
    for p in design_files():
        arr=read_config(p)['events']
        for e in arr:
            e['_design_file']=p.name
            if e.get('supplemental'): extras.append(e)
            else:
                if e['id'] in overrides:raise ValueError(f'Duplicate design id {e["id"]}')
                if any(k in e for k in ('ja','zh','text_ja','text_zh',CONFIG['source_text'],CONFIG['text'])):
                    raise ValueError(f'Main caption text must remain in the reviewed timeline: {e["id"]}')
                overrides[e['id']]=e
    known={r['id'] for r in rows}
    if set(overrides)-known:raise ValueError(f'Unknown design ids {set(overrides)-known}')
    events=[]
    for row in rows:
        if not row.get('zh'):raise ValueError(f'Untranslated {row["id"]}')
        e={**defaults,**row,**overrides.get(row['id'],{})};events.append(e)
    for row in extras:
        e={**defaults,**row,'ja':row['text_ja'],'zh':row['text_zh']};events.append(e)
    events.sort(key=lambda e:(e['start'],e.get('layer',0),e['id']))
    if len({e['id'] for e in events})!=len(events):raise ValueError('Duplicate event IDs')
    for e in events:
        if not 0<=e['start']<e['end']<=CONFIG['duration']:raise ValueError(f'Bad timing {e["id"]}')
        if e['font_role'] not in fonts:raise ValueError(f'Unknown font role {e["font_role"]}')
        font_runs(e['zh'],e,fonts,e['id'])
        if not e.get('ja') or not e.get('zh'):raise ValueError(f'Missing bilingual text {e["id"]}')
        if e.get('effect','none') not in ['none','fade','pop','slide','shake','pulse','typewriter','wipe','glow','distress']:raise ValueError(f'Unknown effect in {e["id"]}')
        if e.get('text_layout','horizontal') not in ['horizontal','vertical']:raise ValueError(f'Unknown text layout in {e["id"]}')
    return events,fonts

def main(output=None):
    events,fonts=load(); out=ROOT/(output or CONFIG['output']);out.mkdir(exist_ok=True,parents=True)
    (out/CONFIG['performance_ass']).write_text(header(fonts[CONFIG['default_font']]['family'])+''.join(render_with_shadow(e,fonts,render_event) for e in events))
    ja=[]; review_slots=[]; review=CONFIG['review']; fs=review['fontsize']
    for e in events:
        # Japanese review is independently toggleable, and never burned into Chinese preview.
        sx=min(100,100*review['max_width']/max(1,max(len(x) for x in e['ja'].splitlines())*fs))
        # Concurrent balloons/labels must also remain readable in the separate
        # review track. Reuse vertical space only after a prior event ends.
        review_slots=[slot for slot in review_slots if slot[0]>e['start']]
        height=fs*review['line_height']*len(e['ja'].splitlines())+review['gap']
        y=review['y']
        for _,top,bottom in sorted(review_slots,key=lambda slot:slot[1]):
            if y+height<=top:break
            if y<bottom:y=bottom
        review_slots.append((e['end'],y,y+height))
        ja.append(line(e,esc(e['ja']),fr'\an8\pos({review['x']},{y})\fs{fs}\fscx{sx:.2f}\bord{review['outline']}\shad{review['shadow']}'))
    (out/CONFIG['review_ass']).write_text(header(fonts[CONFIG['review']['font']]['family'])+''.join(ja))
    for lang,filename in [('ja',CONFIG['source_srt']),('zh',CONFIG['text_srt'])]:
        (out/filename).write_text('\n'.join(f'{i}\n{srt_time(e["start"])} --> {srt_time(e["end"])}\n{e[lang]}\n' for i,e in enumerate(events,1)))
    print(f'Built {len(events)} events; {sum(bool(e.get("supplemental")) for e in events)} supplemental; '+str(out))
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output')
    main(parser.parse_args().output)
