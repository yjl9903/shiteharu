"""Real ffmpeg integration: a second project needs no tool changes."""
from functools import partial
from http.server import ThreadingHTTPServer
import tomlkit
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
import urllib.error
import urllib.request

TOOL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL))
from project import Project, probe
from loupe import Handler, Preview, ffmpeg, render_index
from fonts import export_fonts


class FontSpans(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        fixture = TOOL/'tests/fixtures/portable'
        for name in ('preview.toml', 'timeline.json'):
            shutil.copyfile(fixture/name, self.root/name)

    def font(self, name, chars):
        from fontTools.fontBuilder import FontBuilder
        from fontTools.pens.ttGlyphPen import TTGlyphPen
        builder = FontBuilder(1000, isTTF=True)
        names = ['.notdef', *chars]
        builder.setupGlyphOrder(names)
        builder.setupCharacterMap({ord(c): c for c in chars})
        builder.setupGlyf({n: TTGlyphPen(None).glyph() for n in names})
        builder.setupHorizontalMetrics({n: (600, 0) for n in names})
        builder.setupHorizontalHeader(ascent=800, descent=-200)
        builder.setupNameTable({'familyName': name, 'styleName': 'Regular',
            'uniqueFontIdentifier': name, 'fullName': name, 'psName': name})
        builder.setupOS2(); builder.setupPost(); builder.save(self.root/(name+'.ttf'))
        return {'file': name+'.ttf', 'family': name}

    def timeline(self, runs):
        rows = [{'id': 'mixed', 'start': 0, 'end': 1, 'text': 'AB',
                 'style': {'font_role': 'base', 'text_runs': runs}}]
        (self.root/'timeline.json').write_text(json.dumps(rows))
        project = Project(self.root/'preview.toml')
        return project, project.timeline()

    def test_mixed_font_coverage_and_secondary_role(self):
        config = {'base': self.font('base', 'A'), 'secondary': self.font('secondary', 'B')}
        project, events = self.timeline([{'length': 1}, {'length': 1, 'font_role': 'secondary'}])
        self.assertEqual(events[0]['font_roles'], ['base', 'secondary'])
        faces = export_fonts(project, config, events, self.root/'export')
        self.assertEqual([f['missing'] for f in faces], [[], []])
        self.font('secondary', 'A')
        faces = export_fonts(project, config, events, self.root/'export')
        self.assertEqual(faces[1]['missing'], [{'id': 'mixed', 'characters': 'B'}])
        self.assertEqual(faces[0]['missing'], [])

    def test_malformed_or_unknown_font_runs_fail(self):
        for runs in ([], [{'length': 1}], [{'length': True}, {'length': 1}],
                     [{'length': -1}, {'length': 3}]):
            with self.subTest(runs=runs), self.assertRaisesRegex(ValueError, 'text_runs'):
                self.timeline(runs)
        config = {'base': self.font('base', 'AB')}
        project, events = self.timeline([{'length': 1}, {'length': 1, 'font_role': 'unknown'}])
        with self.assertRaisesRegex(ValueError, 'Unknown font role unknown'):
            export_fonts(project, config, events, self.root/'export')


class InitialDocument(unittest.TestCase):
    def test_geometry_caption_and_safe_embedded_snapshot(self):
        snapshot = dict(title='Title </script><script>alert(1)</script>',
                        media={"original": {"display_ratio": 4 / 3}, "rendered": {"display_ratio": 9 / 16}},
                        timeline=[dict(id='caption-1', start=0, end=2, source_text='A & B', text='<字幕>\n第二行')])
        page = render_index(snapshot).decode()
        self.assertIn('--video-aspect:1.3333333333333333', page)
        self.assertIn('--video-aspect:0.5625', page)
        self.assertIn('<p>A &amp; B</p>', page)
        self.assertIn('<p>&lt;字幕&gt;\n第二行</p>', page)
        self.assertNotIn('<script>alert(1)</script>', page)
        embedded = page.split('<script id="initialSnapshot" type="application/json">', 1)[1].split('</script>', 1)[0]
        self.assertEqual(json.loads(embedded), snapshot)

    def test_empty_timeline(self):
        snapshot = dict(title='Empty', media={side: {"display_ratio": 1} for side in ('original', 'rendered')}, timeline=[])
        self.assertIn('没有匹配的字幕', render_index(snapshot).decode())


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "ffmpeg and ffprobe required")
class PreviewIntegration(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        fixture = Path(__file__).resolve().parent / "fixtures/portable"
        for name in ("preview.toml", "timeline.json"):
            shutil.copyfile(fixture / name, self.root / name)
        (self.root / "media").mkdir()
        self.video("original", "red", "180x320", 12)
        self.video("rendered", "blue", "320x240", 24)
        self.preview = Preview(self.root / "preview.toml")

    def tearDown(self):
        self.temp.cleanup()

    def video(self, name, color, size, fps, duration=2):
        ffmpeg(["-f", "lavfi", "-i", f"color=c={color}:s={size}:r={fps}:d={duration}",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", self.root / "media" / (name + ".mp4")])

    def test_second_project_and_source_switch(self):
        first = self.preview.sync()
        self.assertEqual(len(first["timeline"]), 2)
        self.assertEqual(first["labels"]["source_text"], "English")
        self.assertEqual(first["media"]["rendered"]["fps"], 24)
        self.assertEqual(first["fonts"], [])
        for row in first["frames"]:
            self.assertAlmostEqual(row["time"] * 24, row["frame"])
        # The two sides have different aspect ratios; neither becomes a 16:9 thumbnail.
        def image_size(side):
            return json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "stream=width,height", "-of", "json", str(self.preview.output / first["frames"][0][side])]))["streams"][0]
        a, b = image_size("original"), image_size("rendered")
        self.assertEqual((a["width"], a["height"]), (240, 426))
        self.assertEqual((b["width"], b["height"]), (240, 180))
        self.assertEqual(self.preview.sync()["revision"], first["revision"])
        self.video("original", "green", "180x320", 12)
        second = self.preview.sync()
        self.assertNotEqual(first["revision"], second["revision"])
        for side in ("original", "rendered"):
            self.assertNotEqual(first["media"][side]["url"], second["media"][side]["url"])
            self.assertTrue((self.preview.output / first["media"][side]["url"]).exists())

    def test_failure_preserves_snapshot_and_never_falls_back(self):
        self.preview.sync()
        before = (self.preview.output / "snapshot.json").read_bytes()
        source = self.root / "media/rendered.mp4"
        source.rename(source.with_name("old-preview.mp4"))
        with self.assertRaisesRegex(ValueError, "不会回退"):
            self.preview.sync()
        self.assertEqual((self.preview.output / "snapshot.json").read_bytes(), before)
        self.assertEqual(json.loads((self.preview.output / "status.json").read_text())["state"], "error")
        self.video("rendered", "blue", "320x240", 24, duration=.5)
        with self.assertRaisesRegex(ValueError, "时长不一致"):
            self.preview.sync()
        self.video("rendered", "green", "320x240", 24)
        with patch("loupe.extract_frames", side_effect=ValueError("模拟抽帧失败")):
            with self.assertRaisesRegex(ValueError, "模拟抽帧失败"):
                self.preview.sync()
        self.assertEqual((self.preview.output / "snapshot.json").read_bytes(), before)
        self.assertFalse(list((self.preview.output / "snapshots").glob("pending-*")))

    def test_declarative_toml_overlay_and_new_file(self):
        cfg = self.root / "preview.toml"
        text = cfg.read_text().replace('file = "timeline.json"', '''file = "segments.toml"
collection = "rows"
text = "translated"
source_text = "original"
overlays = ["styles/*.toml"]
supplemental_text = "extra_text"
supplemental_source_text = "extra_original"''')
        cfg.write_text(text)
        (self.root / "segments.toml").write_text('[[rows]]\nid="a"\nstart=0\nend=1\ntranslated="Hola"\noriginal="Hello"\n')
        (self.root / "styles").mkdir()
        first = Project(cfg).inputs()
        (self.root / "styles/a.toml").write_text(tomlkit.dumps({"events": [
            {"id": "a", "fontsize": 42},
            {"id": "b", "start": 1, "end": 1.9, "supplemental": True, "extra_text": "Adiós", "extra_original": "Goodbye"},
        ]}))
        second = Project(cfg).inputs()
        self.assertNotEqual(first["revision"], second["revision"])
        self.assertEqual(second["timeline"][0]["style"]["fontsize"], 42)
        self.assertEqual(second["timeline"][1]["text"], "Adiós")
        (self.root / "styles/b.toml").write_text('[[events]]\nid="unknown"\n')
        with self.assertRaisesRegex(ValueError, "没有时间轴来源"):
            Project(cfg).inputs()

    def test_validation_and_empty_timeline(self):
        file = self.root / "timeline.json"
        for events in ([{"id":"bad","start":0,"end":-1}], [{"id":"same","start":0,"end":1}]*2):
            file.write_text(json.dumps(events))
            with self.assertRaises(ValueError):
                Project(self.root / "preview.toml").inputs()
        file.write_text('[]')
        self.assertEqual(self.preview.sync()["frames"], [])
        cfg = self.root / "preview.toml"
        cfg.write_text(cfg.read_text().replace('output = "preview-output"', 'output = "../outside"'))
        with self.assertRaisesRegex(ValueError, "子目录"):
            Project(cfg)

    def test_input_changes_during_build_are_not_published(self):
        first = self.preview.sync()
        self.video("rendered", "green", "320x240", 24)
        from loupe import extract_frames
        def mutate(*args):
            result = extract_frames(*args)
            (self.root / "timeline.json").write_text('[]')
            return result
        with patch("loupe.extract_frames", side_effect=mutate):
            with self.assertRaisesRegex(ValueError, "输入发生变化"):
                self.preview.sync()
        self.assertEqual(json.loads((self.preview.output / "snapshot.json").read_text())["revision"], first["revision"])

    def test_default_cache_is_outside_project(self):
        cfg = self.root / "preview.toml"
        cfg.write_text(cfg.read_text().replace('output = "preview-output"\n', ''))
        with tempfile.TemporaryDirectory() as cache_dir, patch("project.CACHE_ROOT", Path(cache_dir)):
            preview = Preview(cfg)
            result = preview.sync()
            self.assertEqual(preview.output.parent, Path(cache_dir))
            self.assertFalse(preview.output.is_relative_to(self.root))
            self.assertTrue((preview.output / result["media"]["rendered"]["url"]).is_file())
            self.assertFalse((self.root / "preview-output/snapshot.json").exists())
            other = self.root / "alternate.toml"
            other.write_text(cfg.read_text())
            self.assertNotEqual(Project(other).output, preview.output)

    def test_server_range_and_private_paths(self):
        data = self.preview.sync()
        server = ThreadingHTTPServer(("127.0.0.1", 0), partial(Handler, preview=self.preview))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f"http://127.0.0.1:{server.server_port}/"
        try:
            url = base + data["media"]["rendered"]["url"]
            for value, expected in (("bytes=0-31", 32), ("bytes=-16", 16)):
                with urllib.request.urlopen(urllib.request.Request(url, headers={"Range":value})) as r:
                    self.assertEqual(r.status, 206)
                    self.assertEqual(len(r.read()), expected)
            for path in (".sync.lock", "snapshots/", "assets/../loupe.py", "snapshots/../../preview.toml"):
                with self.assertRaises(urllib.error.HTTPError) as e:
                    urllib.request.urlopen(base + path)
                self.assertEqual(e.exception.code, 404)
                e.exception.close()
            request = urllib.request.Request(base+"api/rebuild", data=b"", headers={"X-Preview-Rebuild":"1","Origin":"http://untrusted.invalid"})
            with self.assertRaises(urllib.error.HTTPError) as e:
                urllib.request.urlopen(request)
            self.assertEqual(e.exception.code, 403)
            e.exception.close()
            with urllib.request.urlopen(base) as r:
                page = r.read()
                self.assertIn(b'assets/preview.js', page)
                self.assertIn(data['revision'].encode(), page)
                self.assertNotIn(b'<script id="initialSnapshot" type="application/json">null</script>', page)
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

    def test_font_coverage_uses_configured_face(self):
        try:
            from fontTools.fontBuilder import FontBuilder
            from fontTools.pens.ttGlyphPen import TTGlyphPen
        except ImportError:
            self.skipTest("fonttools is optional for projects without fonts")
        builder = FontBuilder(1000, isTTF=True)
        builder.setupGlyphOrder([".notdef", "A"])
        builder.setupCharacterMap({65: "A"})
        builder.setupGlyf({name: TTGlyphPen(None).glyph() for name in (".notdef", "A")})
        builder.setupHorizontalMetrics({name: (600, 0) for name in (".notdef", "A")})
        builder.setupHorizontalHeader(ascent=800, descent=-200)
        builder.setupNameTable({"familyName":"Fixture Face","styleName":"Regular","uniqueFontIdentifier":"fixture","fullName":"Fixture Face","psName":"FixtureFace"})
        builder.setupOS2(sTypoAscender=800, sTypoDescender=-200, usWinAscent=800, usWinDescent=200)
        builder.setupPost()
        builder.save(self.root / "fixture.ttf")
        (self.root / "fonts.toml").write_text(tomlkit.dumps({"title":{"file":"fixture.ttf","family":"Fixture Face"}}))
        cfg = self.root / "preview.toml"
        cfg.write_text('fonts = "fonts.toml"\n' + cfg.read_text())
        (self.root / "timeline.json").write_text(json.dumps([{"id":"letters","start":0,"end":1,"text":"AB","style":{"font_role":"title"}}]))
        result = self.preview.sync()
        self.assertEqual(result["fonts"][0]["missing"], [{"id":"letters","characters":"B"}])
        self.assertTrue((self.preview.output / result["fonts"][0]["url"]).is_file())


if __name__ == "__main__":
    unittest.main()
