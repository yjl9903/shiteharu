#!/usr/bin/env python3
"""Forge: shared subtitle production and font research commands."""
import argparse
from pathlib import Path
import runpy
import sys

COMMANDS = {
    'build': ('subtitles.build', '生成 ASS 和 SRT 字幕'),
    'check-inputs': ('review.inputs', '只读检查迁移所需输入、字体校验值及视频工具'),
    'calibrate-top': ('subtitles.calibrate_top', '测量顶部字形并修改设计位置'),
    'fonts-prepare': ('fonts.prepare_fonts', '准备本地渲染字体缓存'),
    'fonts-merge': ('fonts.merge_font_proposal', '合入已审阅的字体提案，修改设计及共享字体'),
    'render': ('delivery.render', '导出 preview、full 或 soft 视频'),
    'compare-clips': ('review.comparison_clips', '生成原片／中文字幕对照视频'),
    'compare-stills': ('review.comparison_stills', '从对照视频生成截图'),
    'source-frames': ('review.source_frames', '提取原片采样帧与联系表，不自动确认字幕边界'),
    'source-boundary': ('review.source_boundary', '提取边界附近全部解码帧与真实 PTS'),
    'source-atlas': ('review.source_atlas', '按 TOML 窗口采样或排序像素变化候选，供人工审阅'),
    'review-stills': ('review.stills', '逐事件生成原片与中文字幕对照截图'),
    'audit': ('review.audit', '检查字形、设计、证据与路径；不代替人工审阅'),
    'audit-layout': ('review.layout', '测量中文实际墨迹并标记原字重叠与越界候选'),
    'research-discover': ('research.discover_fonts', '查询候选字体发布记录，写入 research/fonts'),
    'research-download': ('research.download_fonts', '下载研究候选字体，写入 research/fonts/candidates'),
    'research-download-extra': ('research.download_extra', '下载额外候选字体，写入 research/fonts/candidates'),
    'research-capture': ('research.capture', '提取配置工程重点字幕的研究画面'),
    'research-diamond': ('research.make_diamond', '重建配置工程菱形笔锋派生字库'),
    'research-fracture': ('research.make_fracture', '重建配置工程破损及变形派生字库'),
    'research-propose': ('research.build_proposal', '按工程数据规则生成字体提案及试排，不修改设计'),
    'research-sheets': ('research.proof_sheets', '生成研究对照图及候选字体清单'),
    'research-specimens': ('research.specimens', '生成候选字体试样图'),
    'research-reel': ('research.make_reel', '生成配置工程字体提案的动态摘录'),
    'research-render': ('research.render_proposal', '生成独立字体提案视频，不发布到 Loupe'),
}


def parser():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--config', required=True, help='工程 Forge TOML 配置；其中路径相对配置所在目录')
    commands = cli.add_subparsers(dest='command', required=True)
    for name, (_, description) in COMMANDS.items():
        cmd = commands.add_parser(name, help=description, description=description)
        if name == 'build':
            cmd.add_argument('--output', help='输出目录，默认使用工程配置；相对工程目录解析')
        elif name == 'check-inputs':
            cmd.add_argument('--no-media', action='store_true', help='跳过原片及 FFmpeg 检查，仅检查字幕和字体输入')
        elif name == 'render':
            cmd.add_argument('mode', nargs='?', choices=['preview', 'full', 'soft'], default='preview')
        elif name == 'compare-clips':
            cmd.add_argument('filter', nargs='?', help='只生成名称包含此字符串的片段')
        elif name == 'source-frames':
            cmd.add_argument('--start', type=float, required=True)
            cmd.add_argument('--end', type=float)
            cmd.add_argument('--step', type=float, default=1)
            cmd.add_argument('--label', default='source')
            cmd.add_argument('--width', type=int, default=640)
        elif name == 'source-atlas':
            cmd.add_argument('--plan', required=True)
            cmd.add_argument('--label', required=True)
        elif name == 'source-boundary':
            cmd.add_argument('time', type=float)
            cmd.add_argument('--radius', type=float, default=0.3)
            cmd.add_argument('--label')
            cmd.add_argument('--crop', help='源画面 x,y,width,height')
        elif name in ('review-stills', 'audit-layout'):
            cmd.add_argument('--start', type=float, default=0)
            cmd.add_argument('--end', type=float)
            cmd.add_argument('--label', default='all')
            if name == 'review-stills':
                cmd.add_argument('--at', type=float)
        elif name == 'audit':
            cmd.add_argument('--output', default='review/technical-audit.json')
    return cli


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    args = parser().parse_args(argv)  # Validate before importing any mutating tool.
    from pipeline.paths import configure
    configure(args.config)
    target = COMMANDS[args.command][0]
    previous = sys.argv
    try:
        options = []
        if args.command == 'build' and args.output:
            options = ['--output', args.output]
        elif args.command == 'render':
            options = [args.mode]
        elif args.command == 'compare-clips' and args.filter:
            options = [args.filter]
        elif args.command in ('check-inputs', 'source-frames', 'source-boundary', 'source-atlas', 'review-stills', 'audit', 'audit-layout'):
            options = argv[argv.index(args.command)+1:]
        sys.argv = [f'{Path(__file__).name} {args.command}', *options]
        runpy.run_module('pipeline.' + target, run_name='__main__')
    finally:
        sys.argv = previous
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
