"""Build limited-coverage diamond-terminal derivatives from configured outlines."""
import json,math,shutil
from pathlib import Path
from ..paths import PROJECT, CONFIG, research, path, source_media, design_files, setting_path
RESEARCH=research()
import pathops
from fontTools.ttLib import TTFont
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.cu2quPen import Cu2QuPen
H=path(RESEARCH['directory']);D=H/'derived';D.mkdir(exist_ok=True)
job=RESEARCH['diamond']
source=TTFont(path(job['source']));gs=source.getGlyphSet();cm=source.getBestCmap()
IDS=job['events']
from ..subtitles.build import load
events=load()[0];text=''.join(e['zh'] for e in events if e['id'] in IDS)
name=job['family'];chars=sorted(set(text.replace('\n','')+' '));glyphs={'.notdef':TTGlyphPen(None).glyph()};metrics={'.notdef':(1000,0)};cmap={};order=['.notdef'];details={}
for ch in chars:
 gn=cm[ord(ch)];p=pathops.Path();gs[gn].draw(p.getPen());rec=RecordingPen();gs[gn].draw(rec)
 contours=[];contour=[]
 for op,pts in rec.value:
  if op=='moveTo':contour=[('start',pts[0])]
  elif op=='lineTo':contour.append(('line',pts[0]))
  elif op in ('qCurveTo','curveTo'):contour.append(('curve',pts[-1]))
  elif op=='closePath':contours.append(contour);contour=[]
 caps=[]
 for c in contours:
  area=sum(c[i-1][1][0]*v[1][1]-v[1][0]*c[i-1][1][1] for i,v in enumerate(c))
  for i,(kind,b) in enumerate(c):
   a=c[i-1][1];prev=c[i-2][1];nxt=c[(i+1)%len(c)][1]
   if kind not in ('line','start'):continue
   if area<0 and abs(b[1]-a[1])<abs(b[0]-a[0])*.12 and abs(b[0]-a[0])>150 and nxt[1]<b[1]-100 and abs(nxt[0]-b[0])<10:
    caps.append((b[0]-18 if b[0]>a[0] else b[0]+18,b[1]-5,41,29))
   dx=b[0]-a[0];dy=b[1]-a[1]
   if abs(dx)<=12 and 14<=abs(dy)<=46:
    # Flat end of a thin horizontal stroke, with two long returning edges.
    v1=(a[0]-prev[0],a[1]-prev[1]);v2=(nxt[0]-b[0],nxt[1]-b[1])
    if abs(v1[0])>65 and abs(v2[0])>65 and abs(v1[1])<abs(v1[0])*.14 and abs(v2[1])<abs(v2[0])*.14 and v1[0]*v2[0]<0:
     direction=1 if nxt[0]>b[0] else -1
     caps.append(((a[0]+b[0])/2+direction*13,(a[1]+b[1])/2,46,39))
   elif 60<=abs(dx)<=125 and abs(dy)<15:
    # A small pointed crown on an upright stem; do not shear the skeleton.
    if prev[1]<a[1]-80 and nxt[1]<b[1]-80:
     caps.append(((a[0]+b[0])/2,(a[1]+b[1])/2-2,abs(dx)*.58,22))
 # Strengthen the thin Chinese horizontals before adding sharp terminal ornaments.
 ink=pathops.Path(p);ink.stroke(16,pathops.LineCap.ROUND_CAP,pathops.LineJoin.ROUND_JOIN,2);ink.convertConicsToQuads();p=pathops.op(p,ink,pathops.PathOp.UNION)
 for x,y,rx,ry in caps:
  ornament=pathops.Path();ornament.moveTo(x-rx,y);ornament.lineTo(x+5,y+ry);ornament.lineTo(x+rx,y);ornament.lineTo(x-5,y-ry);ornament.close();p=pathops.op(p,ornament,pathops.PathOp.UNION)
 pen=TTGlyphPen(None);p.draw(Cu2QuPen(pen,max_err=.7));glyph=pen.glyph();key='uni%04X'%ord(ch);order.append(key);glyphs[key]=glyph;metrics[key]=(gs[gn].width,0);cmap[ord(ch)]=key;details[ch]={'decorations':len(caps)}
fb=FontBuilder(1000,isTTF=True);fb.setupGlyphOrder(order);fb.setupCharacterMap(cmap);fb.setupGlyf(glyphs);fb.setupHorizontalMetrics(metrics);fb.setupHorizontalHeader(ascent=880,descent=-120)
fb.setupNameTable({'familyName':name,'styleName':'Regular','uniqueFontIdentifier':name+'-1.0','fullName':name,'psName':name,'version':'Version 1.0','copyright':str(source['name'].getDebugName(0))+'; caption-specific diamond-terminal adaptation','licenseDescription':'SIL Open Font License 1.1; see '+job['license_name'],'licenseInfoURL':'https://openfontlicense.org/'})
fb.setupOS2(sTypoAscender=880,sTypoDescender=-120,usWinAscent=1050,usWinDescent=250,usWeightClass=700);fb.setupPost(italicAngle=0);fb.setupMaxp();fb.save(D/(name+'.ttf'))
shutil.copy2(path(job['license']),D/job['license_name'])
(D/(name+'.json')).write_text(json.dumps({**job['provenance'],'family':name,'events':IDS,'coverage':text,'italic':False,'synthesis':False,'glyphs':details},ensure_ascii=False,indent=2))
print('Built',len(chars),'characters;',sum(x['decorations'] for x in details.values()),'terminal decorations')
