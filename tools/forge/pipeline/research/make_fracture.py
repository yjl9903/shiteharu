"""Build configured limited-coverage fracture and melt font derivatives."""
import json,math,random,shutil
from pathlib import Path
from ..paths import PROJECT, CONFIG, research, path, source_media, design_files, setting_path
RESEARCH=research()
import pathops
from fontTools.ttLib import TTFont
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen
H=path(RESEARCH['directory']);D=H/'derived';D.mkdir(exist_ok=True)
job=RESEARCH['fracture']
gen=TTFont(path(job['original']))
sc=TTFont(path(job['fallback']))
def make(name,text,melt=False):
 chars=sorted(set(text+' ')); order=['.notdef'];glyphs={};metrics={};cmap={};sources={}
 empty=TTGlyphPen(None).glyph();glyphs['.notdef']=empty;metrics['.notdef']=(1000,0)
 for ch in chars:
  source=sc if melt or ord(ch) not in gen.getBestCmap() else gen
  if source is gen and not ch.isspace():
   bounds=BoundsPen(gen.getGlyphSet())
   gen.getGlyphSet()[gen.getBestCmap()[ord(ch)]].draw(bounds)
   if bounds.bounds is None:source=sc
  gn=source.getBestCmap()[ord(ch)]; gs=source.getGlyphSet(); scale=1000/source['head'].unitsPerEm
  if not ch.isspace():
   bounds=BoundsPen(gs);gs[gn].draw(bounds)
   if bounds.bounds is None:raise ValueError(f'No visible glyph for {ch!r} in configured source or fallback')
  g=pathops.Path();gs[gn].draw(TransformPen(g.getPen(),(scale,0,0,scale,0,0)))
  if source is sc and ch!=' ':
   r=random.Random(ord(ch)+704)
   # Angular pinholes and interrupted strokes, fixed in glyph coordinates.
   for _ in range(44 if not melt else 18):
    x=r.uniform(50,940);y=r.uniform(-65,820);w=r.uniform(12,52);h=r.uniform(8,38)
    cut=pathops.Path();cut.moveTo(x,y);cut.lineTo(x+w,y+h*.2);cut.lineTo(x+w*.6,y+h);cut.lineTo(x-w*.2,y+h*.5);cut.close()
    g=pathops.op(g,cut,pathops.PathOp.DIFFERENCE)
  pen=TTGlyphPen(None);g.draw(Cu2QuPen(pen,max_err=1,reverse_direction=False));glyph=pen.glyph()
  if melt and ch!=' ':
   # Static organic displacement; deliberately no time jitter.
   for i,(x,y) in enumerate(glyph.coordinates):
    glyph.coordinates[i]=(round(x+24*math.sin(y/67)+11*math.sin(y/24)),round(y+17*math.sin(x/83)))
  advance,bearing=round(gs[gn].width*scale),0
  if not melt and ch in '「」':
   # Full-width quote advances left a large empty cell after the opening mark.
   # Keep the original outline, with symmetric 20 em-unit side bearings.
   xmin=min(x for x,y in glyph.coordinates);xmax=max(x for x,y in glyph.coordinates)
   for i,(x,y) in enumerate(glyph.coordinates):glyph.coordinates[i]=(x-xmin+20,y)
   advance,bearing=round(xmax-xmin+40),20
  nameg='uni%04X'%ord(ch);order.append(nameg);glyphs[nameg]=glyph;metrics[nameg]=(advance,bearing);cmap[ord(ch)]=nameg
  sources[ch]=job['fallback_label'] if source is sc else job['original_label']
 fb=FontBuilder(1000,isTTF=True);fb.setupGlyphOrder(order);fb.setupCharacterMap(cmap);fb.setupGlyf(glyphs);fb.setupHorizontalMetrics(metrics);fb.setupHorizontalHeader(ascent=880,descent=-120)
 fb.setupNameTable({'familyName':name,'styleName':'Regular','uniqueFontIdentifier':name+'-1.0','fullName':name,'psName':name,'version':'Version 1.0','copyright':str(gen['name'].getDebugName(0))+'; '+str(sc['name'].getDebugName(0))+'; derivative outlines for caption proof','licenseDescription':'Licensed under SIL Open Font License, Version 1.1. See bundled OFL and provenance.','licenseInfoURL':'https://openfontlicense.org/'})
 fb.setupOS2(sTypoAscender=880,sTypoDescender=-120,usWinAscent=1050,usWinDescent=250,usWeightClass=900);fb.setupPost();fb.setupMaxp()
 # Keep the derivative byte-reproducible instead of stamping each rebuild's wall clock.
 fb.font['head'].created=gen['head'].created
 fb.font['head'].modified=max(gen['head'].modified,sc['head'].modified)
 fb.font.recalcTimestamp=False
 fb.save(D/(name+'.ttf'))
 (D/(name+'.json')).write_text(json.dumps({**job['provenance'],'font':name,'coverage':text,'glyph_sources':sources},ensure_ascii=False,indent=2))
for item in job['jobs']:make(item['family'],item['text'],item['melt'])
shutil.copy2(path(job['license']),D/job['fallback_license_name'])
license_text=path(job['license']).read_text()
(D/job['original_license_name']).write_text(str(gen['name'].getDebugName(0))+'\n'+job['original_license_note']+'\n\n'+license_text[license_text.index('SIL OPEN FONT LICENSE Version'):])
print('Built',len(job['jobs']),'limited-coverage caption fonts; glyph provenance recorded.')
