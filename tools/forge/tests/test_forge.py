"""Independent project, relocated checkout and real FFmpeg regression coverage."""
import importlib.util
import json
import tomllib
import tomlkit
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

TOOL = Path(__file__).resolve().parents[1]
FIXTURE = TOOL / 'tests/fixtures/portable'
sys.path.insert(0, str(TOOL))
import forge


def write_data(path, value):
    path.write_text(tomlkit.dumps(value) if path.suffix == '.toml' else json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def create_font(target):
    from fontTools.fontBuilder import FontBuilder
    from fontTools.pens.ttGlyphPen import TTGlyphPen
    target.parent.mkdir(parents=True, exist_ok=True)
    names = ['.notdef', 'space', 'A', 'B']
    glyphs = {}
    for name in names:
        pen = TTGlyphPen(None)
        if name != 'space':
            pen.moveTo((100, 0)); pen.lineTo((500, 0)); pen.lineTo((500, 700)); pen.lineTo((100, 700)); pen.closePath()
        glyphs[name] = pen.glyph()
    font = FontBuilder(1000, isTTF=True)
    font.setupGlyphOrder(names); font.setupCharacterMap({32:'space', 65:'A', 66:'B'})
    font.setupGlyf(glyphs); font.setupHorizontalMetrics({n:(600, 0) for n in names})
    font.setupHorizontalHeader(ascent=800, descent=-200)
    font.setupNameTable({'familyName':'ForgeFixture', 'styleName':'Regular', 'uniqueFontIdentifier':'ForgeFixture', 'fullName':'ForgeFixture', 'psName':'ForgeFixture'})
    font.setupOS2(); font.setupPost(); font.setupMaxp(); font.save(target)


class ForgeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='forge portable ')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.project = self.root / 'project'
        shutil.copytree(FIXTURE, self.project)
        self.config = self.project / 'forge.toml'

    def command(self, *args, tool=TOOL, cwd=None, success=True):
        result = subprocess.run([sys.executable, str(tool / 'forge.py'), '--config', str(self.config), *args],
                                cwd=cwd or self.root, text=True, capture_output=True)
        if success:
            self.assertEqual(result.returncode, 0, result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0)
        return result

    def test_help_and_bad_args_never_load_mutating_modules(self):
        with patch.object(forge.runpy, 'run_module') as module, patch('sys.stdout'), patch('sys.stderr'):
            for command in forge.COMMANDS:
                with self.assertRaises(SystemExit) as caught:
                    forge.main(['--config', 'missing.toml', command, '--help'])
                self.assertEqual(caught.exception.code, 0)
            for args in (['render', 'invalid'], ['fonts-merge', '--unknown'], ['boundary']):
                with self.assertRaises(SystemExit) as caught:
                    forge.main(['--config', 'missing.toml', *args])
                self.assertEqual(caught.exception.code, 2)
        module.assert_not_called()

    def test_second_project_builds_in_relocated_tool_and_any_cwd(self):
        relocated = self.root / 'checkout/tools/forge'
        shutil.copytree(TOOL, relocated, ignore=shutil.ignore_patterns('__pycache__'))
        for cwd, name, tool in [(self.root,'first',TOOL),(self.project,'second',relocated)]:
            self.command('build', '--output', name, cwd=cwd, tool=tool)
        first = {p.name:p.read_bytes() for p in (self.project/'first').iterdir()}
        self.assertEqual(first, {p.name:p.read_bytes() for p in (self.project/'second').iterdir()})
        self.assertEqual(set(first), {'translated.ass','source.ass','source.srt','translated.srt'})
        text = first['translated.ass'].decode()
        self.assertIn('PlayResX: 320',text); self.assertIn('PlayResY: 240',text)
        self.assertIn(',320,',text)  # distress clipping uses the configured canvas
        self.assertIn('00:00:01,000 --> 00:00:02,000\nA',first['translated.srt'].decode())
        self.assertNotIn('shingouki',text)

    def test_missing_input_and_bad_timing_publish_nothing(self):
        (self.project/'timeline.json').unlink()
        self.command('build',success=False)
        self.assertFalse((self.project/'output').exists())
        shutil.copy2(FIXTURE/'timeline.json',self.project/'timeline.json')
        events=json.loads((self.project/'timeline.json').read_text());events[1]['end']=3
        write_data(self.project/'timeline.json',events)
        self.command('build',success=False)
        self.assertFalse((self.project/'output').exists())
        self.command('research-propose',success=False)
        self.assertFalse((self.project/'research').exists())

    def test_proposal_rules_scale_without_changing_editorial_decisions(self):
        from pipeline.research.rules import proposal
        rules={'roles':{'body':{'set':{'font_role':'round','soft_shadow':{'alpha':'20'}},'per_fontsize':{'outline':.04,'soft_shadow':{'blur':.02}},'reason':'reviewed','scale_x_cap':80}},'events':{},'black_outline_roles':[]}
        result,reason=proposal({'id':'caption','font_role':'body','fontsize':50,'scale_x':70},rules)
        self.assertEqual(result,{'font_role':'round','outline':2.0,'soft_shadow':{'alpha':'20','blur':1.0},'scale_x':70})
        self.assertEqual(reason,'reviewed')

    def test_mixed_fonts_and_irregular_reveal_preserve_timeline_text(self):
        rows=json.loads((self.project/'timeline.json').read_text())
        rows[0]['translation']='AB';rows[1]['translation']='BA'
        write_data(self.project/'timeline.json',rows)
        fonts=tomllib.loads((self.project/'fonts.toml').read_text())
        fonts['alternate']={'family':'AlternateFixture','file':'fonts/alternate.ttf','bold':True}
        write_data(self.project/'fonts.toml',fonts)
        events={'events':[
            {'id':'first','text_runs':[{'length':1,'font_role':'plain'},{'length':1,'font_role':'alternate'}]},
            {'id':'second','effect':'typewriter','reveal_ms':[0,650]}]}
        write_data(self.project/'events.toml',events)
        self.command('build')
        ass=(self.project/'output/translated.ass').read_text()
        self.assertIn(r'{\fnAlternateFixture\b1}B',ass)
        self.assertIn(r'\t(650,651,\alpha&H00&)',ass)
        self.assertIn('AB',(self.project/'output/translated.srt').read_text())
        self.assertIn('BA',(self.project/'output/translated.srt').read_text())
        events['events'][1]['reveal_ms']=[650,0]
        write_data(self.project/'events.toml',events)
        self.command('build',success=False)
        events['events'][1]['reveal_ms']=[0,650]
        events['events'][0]['text_runs'][0]['length']=2
        write_data(self.project/'events.toml',events)
        self.command('build',success=False)

    def test_font_merge_preflights_and_uses_effective_size(self):
        config=tomllib.loads(self.config.read_text());config['research']='research/recipe.toml';write_data(self.config,config)
        research=self.project/'research';research.mkdir()
        write_data(research/'recipe.toml',{'directory':'research'})
        (research/'candidate.ttf').write_bytes(b'test font')
        write_data(research/'font-config.proposed.toml',{'new':{'family':'New','file':'research/candidate.ttf'}})
        patch_file=research/'event-font-patches.json'
        patches=[{'id':'second','base_fontsize':12,'set':{'font_role':'new','outline':1,'soft_shadow':{'blur':2},'x':0}}]
        write_data(patch_file,patches)
        events_file=self.project/'events.toml'
        events_file.write_text('# Keep editorial note\n'+events_file.read_text())
        original=events_file.read_bytes()
        self.command('fonts-merge',success=False)
        self.assertEqual(original,(self.project/'events.toml').read_bytes())
        self.assertFalse((self.project/'fonts').exists())
        del patches[0]['set']['x'];write_data(patch_file,patches)
        self.command('fonts-merge')
        event=tomllib.loads((self.project/'events.toml').read_text())['events'][0]
        self.assertIn('# Keep editorial note',events_file.read_text())
        self.assertEqual(event['outline'],2)
        self.assertEqual(event['soft_shadow']['blur'],4)
        self.assertTrue((self.project/'fonts/new/candidate.ttf').is_file())

    @unittest.skipUnless(shutil.which('ffmpeg'), 'FFmpeg required')
    def test_wipe_reveals_partial_ink_without_moving_anchor(self):
        from PIL import Image
        create_font(self.project/'fonts/fixture.ttf')
        rows=json.loads((self.project/'timeline.json').read_text())
        rows[0]['translation']='AB'
        write_data(self.project/'timeline.json',rows)
        write_data(self.project/'events.toml',{'events':[{'id':'first','effect':'wipe',
            'fontsize':100,'align':7,'x':20,'y':20,'outline':0,'shadow':0,
            'reveal_box':[20,0,140,240],'in_ms':700}]})
        self.command('build');self.command('fonts-prepare')
        boxes=[]
        for number,time in enumerate([.2,.5,.8]):
            path=self.project/f'wipe-{number}.png'
            subprocess.run(['ffmpeg','-v','error','-y','-f','lavfi','-i',
                'color=c=black@0:s=320x240,format=rgba','-vf',
                f'setpts=PTS+{time}/TB,ass=output/translated.ass:fontsdir=.cache/fonts:alpha=1',
                '-frames:v','1',str(path)],cwd=self.project,check=True)
            with Image.open(path) as im:boxes.append(im.getchannel('A').getbbox())
        self.assertTrue(all(boxes),boxes)
        self.assertEqual(len({box[0] for box in boxes}),1)
        self.assertLess(boxes[0][2],boxes[1][2])
        self.assertLess(boxes[1][2],boxes[2][2])

    @unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'), 'FFmpeg required')
    def test_video_pipeline_and_package_rebuild(self):
        # This checkout contains no real production project or system font input.
        checkout=self.root/'checkout';tool=checkout/'tools/forge'
        shutil.copytree(TOOL,tool,ignore=shutil.ignore_patterns('__pycache__'))
        (checkout/'tools/loupe').mkdir();(checkout/'tools/loupe/README.md').write_text('Test placeholder')
        (checkout/'docs').mkdir();(checkout/'docs/reproducibility.md').write_text('Test fixture')
        for name in ['pyproject.toml','uv.lock','.python-version']:
            shutil.copy2(TOOL.parents[1]/name,checkout/name)
        self.project=checkout/'production/portable';shutil.copytree(FIXTURE,self.project)
        self.config=self.project/'forge.toml'
        create_font(self.project/'fonts/fixture.ttf')
        (checkout/'fonts/local').mkdir(parents=True);(checkout/'fonts/local/excluded.txt').write_text('excluded')
        config=tomllib.loads(self.config.read_text());config['package']['include'].append('fonts');config['package']['include_evidence']=True;write_data(self.config,config)
        subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=c=blue:s=320x240:r=12:d=2','-f','lavfi','-i','anullsrc=r=48000:cl=stereo','-t','2','-c:v','libx264','-pix_fmt','yuv420p','-c:a','aac',str(self.project/'input.mp4')],check=True)
        event_file=self.project/'events.toml'
        event_file.write_text('# Keep layout note\n[[events]]\nid="second"\nalign=8\nx=160\ny=10\nface_boxes=[[0,0,320,240]]\nevidence=["frames/probe/000000.200.jpg"]\n')
        self.command('calibrate-top',tool=tool)
        self.assertIn('# Keep layout note',event_file.read_text())
        self.assertNotEqual(tomllib.loads(event_file.read_text())['events'][0]['y'],10)
        for mode in ['preview','full','soft']:
            self.command('render',mode,tool=tool)
        def probe(file):
            return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(file)]))
        preview=probe(self.project/'output/preview.mp4')
        video=next(s for s in preview['streams'] if s['codec_type']=='video')
        self.assertEqual((video['width'],video['height']),(160,120))
        self.assertLess(abs(float(preview['format']['duration'])-2),.25)
        tracks=probe(self.project/'output/tracks.mkv')
        self.assertEqual([s['tags']['language'] for s in tracks['streams'] if s['codec_type']=='subtitle'],['deu','eng'])
        self.command('compare-clips',tool=tool);self.command('compare-stills',tool=tool)
        self.assertTrue((self.project/'output/comparisons/sample.jpg').is_file())
        self.command('source-frames','--start','0.2','--end','0.3','--label','probe',tool=tool)
        self.command('source-boundary','1','--radius','0.1','--label','boundary',tool=tool)
        boundary=json.loads((self.project/'frames/boundary/index.json').read_text())
        self.assertTrue(boundary)
        self.assertTrue(all(not Path(frame['file']).is_absolute() for frame in boundary))
        write_data(self.project/'capture.toml', {'windows':[{'start':.5,'end':1.2}],
            'crop':[0,120,320,120],'width':160,'white_threshold':210,'candidate_neighbors':1})
        self.command('source-atlas','--plan','capture.toml','--label','atlas',tool=tool)
        atlas=json.loads((self.project/'frames/atlas/index.json').read_text())
        self.assertEqual(len(atlas['windows']),1)
        self.assertGreaterEqual(atlas['windows'][0]['candidate_pts'],.5)
        self.assertTrue(all(not Path(f['file']).is_absolute() for f in atlas['windows'][0]['frames']))
        self.command('review-stills','--label','probe',tool=tool)
        self.command('audit-layout','--label','probe',tool=tool)
        report=json.loads((self.project/'review/layout-probe.json').read_text())
        self.assertEqual(len(report['samples']),2)
        self.assertTrue(all(sample['ink_bounds'][2]<=320 for sample in report['samples']))
        self.assertEqual(next(sample for sample in report['samples'] if sample['id']=='second')['face_ink_intersections'],[[0,0,320,240]])
        self.command('audit',tool=tool,success=False)  # No manual source evidence in the fixture.
        audit=json.loads((self.project/'review/technical-audit.json').read_text())
        self.assertEqual(audit['missing_glyphs'],[])
        self.assertEqual(audit['event_count'],2)
        self.command('package',tool=tool)
        from zipfile import ZipFile
        extracted=self.root/'unpacked'
        with ZipFile(self.project/'output/editable.zip') as archive:
            self.assertIn('tools/forge/forge.py',archive.namelist())
            self.assertIn('production/portable/frames/probe/000000.200.jpg',archive.namelist())
            self.assertFalse(any('/scripts/' in p or '/local/' in p or '/.cache/' in p for p in archive.namelist()))
            archive.extractall(extracted)
        expected={p.name:p.read_bytes() for p in (self.project/'output').glob('*.ass')}
        self.config=extracted/'production/portable/forge.toml'
        self.command('build','--output','rebuilt',tool=extracted/'tools/forge')
        self.assertEqual(expected,{p.name:p.read_bytes() for p in (self.config.parent/'rebuilt').glob('*.ass')})


if __name__ == '__main__':
    unittest.main()
