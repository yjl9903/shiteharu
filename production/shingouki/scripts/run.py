#!/usr/bin/env python3
"""Single CLI for this production project's scripts."""
import argparse
import os
from pathlib import Path
import runpy
import subprocess
import sys

SCRIPTS = Path(__file__).resolve().parent
COMMANDS = {
    'build': ('subtitles.build', '生成 ASS 和 SRT 字幕'),
    'calibrate-top': ('subtitles.calibrate_top', '测量顶部字形并修改设计位置'),
    'fonts-prepare': ('fonts.prepare_fonts', '准备本地渲染字体缓存'),
    'fonts-merge': ('fonts.merge_font_proposal', '合入已审阅的字体提案，修改设计及共享字体'),
    'render': ('delivery/render.sh', '导出 preview、full 或 soft 视频'),
    'compare-clips': ('delivery.comparison_clips', '生成原片／中文字幕对照视频'),
    'compare-stills': ('delivery.comparison_stills', '从对照视频生成截图'),
    'package': ('delivery.package', '打包可编辑工程'),
}


def parser():
    cli = argparse.ArgumentParser(description=__doc__)
    commands = cli.add_subparsers(dest='command', required=True)
    for name, (_, description) in COMMANDS.items():
        cmd = commands.add_parser(name, help=description, description=description)
        if name == 'build':
            cmd.add_argument('--output', help='输出目录，默认 deliverables；相对工程目录解析')
        elif name == 'render':
            cmd.add_argument('mode', nargs='?', choices=['preview', 'full', 'soft'], default='preview')
        elif name == 'compare-clips':
            cmd.add_argument('filter', nargs='?', help='只生成名称包含此字符串的片段')
    return cli


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    args = parser().parse_args(argv)  # Validate before importing any mutating tool.
    target = COMMANDS[args.command][0]
    if target.endswith('.sh'):
        env = {**os.environ, 'PYTHON': sys.executable}
        return subprocess.run(['zsh', str(SCRIPTS / 'pipeline' / target), *argv[1:]], env=env).returncode
    previous = sys.argv
    try:
        sys.argv = [f'{Path(__file__).name} {args.command}', *argv[1:]]
        runpy.run_module('pipeline.' + target, run_name='__main__')
    finally:
        sys.argv = previous
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
