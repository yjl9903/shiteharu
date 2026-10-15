"""Integration checks for directory moves; never overwrite production outputs."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1]
PROJECT = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))
import run


class EntrypointTests(unittest.TestCase):
    def command(self, *args, cwd=None):
        return subprocess.run(
            [sys.executable, str(SCRIPTS / 'run.py'), *args],
            cwd=cwd or PROJECT, capture_output=True, text=True,
        )

    def test_help_and_invalid_arguments_do_not_run_tools(self):
        # Importing some tools changes design files immediately. All help and
        # parser failures must be handled before module loading or shell launch.
        with patch.object(run.runpy, 'run_module') as module, patch.object(run.subprocess, 'run') as shell:
            with patch('sys.stdout'), patch('sys.stderr'):
                for command in run.COMMANDS:
                    with self.subTest(command=command), self.assertRaises(SystemExit) as error:
                        run.main([command, '--help'])
                    self.assertEqual(error.exception.code, 0)
                for args in (['render', 'invalid'], ['fonts-merge', '--unknown'], ['boundary']):
                    with self.subTest(args=args), self.assertRaises(SystemExit) as error:
                        run.main(args)
                    self.assertEqual(error.exception.code, 2)
        module.assert_not_called()
        shell.assert_not_called()

    def test_exports_are_independent_of_cwd(self):
        # Real project data exercises all production typography and timing.
        with tempfile.TemporaryDirectory(prefix='subtitle-cli-test-') as tmp:
            root = Path(tmp)
            first, second = (root / name for name in ('first', 'second'))
            for cwd, output in ((PROJECT, first), (root, second)):
                result = self.command('build', '--output', str(output), cwd=cwd)
                self.assertEqual(result.returncode, 0, result.stderr)
            expected = {p.name: p.read_bytes() for p in first.iterdir()}
            self.assertEqual(set(expected), {'zh.performance.ass', 'ja.review.ass',
                                            'zh.srt', 'ja.srt'})
            self.assertEqual(expected, {p.name: p.read_bytes() for p in second.iterdir()})

    def test_module_import_and_shell_dispatch(self):
        from pipeline.subtitles import build as builder
        self.assertEqual(builder.ROOT, PROJECT)
        events, fonts = builder.load()
        self.assertTrue(events)
        self.assertTrue(fonts)
        self.assertTrue(callable(builder.render_event))
        with patch.object(run.subprocess, 'run') as shell:
            shell.return_value.returncode = 0
            self.assertEqual(run.main(['render', 'soft']), 0)
            args, kwargs = shell.call_args
            self.assertEqual(args[0], ['zsh', str(SCRIPTS / 'pipeline/delivery/render.sh'), 'soft'])
            self.assertEqual(kwargs['env']['PYTHON'], sys.executable)


if __name__ == '__main__':
    unittest.main()
