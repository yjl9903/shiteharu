"""Render configured video outputs, publishing only completed encodes."""
import json
import os
import subprocess
import sys
from ..paths import PROJECT, CONFIG, source_media, setting_path
from ..subtitles.build import main as build
from ..fonts.prepare_fonts import main as prepare_fonts


def main(mode):
    source = source_media()
    if not source.is_file():
        raise FileNotFoundError(f'Missing source media: {source.name}')
    build()
    prepare_fonts()
    options = CONFIG['render'][mode]
    output = setting_path('output')
    target = output / options['file']
    temporary = target.with_name(target.stem + '.rendering' + target.suffix)
    args = ['ffmpeg', '-hide_banner', '-y', '-i', str(source)]
    if mode == 'soft':
        args += ['-i', str(output / CONFIG['performance_ass']), '-i', str(output / CONFIG['review_ass']),
                 '-map', '0:v', '-map', '0:a?', '-map', '1:0', '-map', '2:0', '-c', 'copy',
                 '-metadata:s:s:0', 'language=' + options['text_language'],
                 '-metadata:s:s:0', 'title=' + options['text_title'],
                 '-metadata:s:s:1', 'language=' + options['source_language'],
                 '-metadata:s:s:1', 'title=' + options['source_title'],
                 '-disposition:s:0', 'default', '-disposition:s:1', '0']
    else:
        filters = f"ass={CONFIG['output']}/{CONFIG['performance_ass']}:fontsdir={CONFIG['font_cache']}"
        if options.get('width'):
            filters += f",scale={options['width']}:-2"
        args += ['-vf', filters, '-c:v', 'libx264', '-preset', 'fast', '-crf', str(options['crf']),
                 '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', options['audio_bitrate'], '-movflags', '+faststart']
    log_dir = PROJECT / '.cache/logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, 'XDG_CACHE_HOME': str(PROJECT / '.cache/fontconfig')}
    with (log_dir / f'render-{mode}.log').open('w') as log:
        subprocess.run([*args, str(temporary)], cwd=PROJECT, env=env, stderr=log, check=True)
    def duration(path):
        return float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries',
                    'format=duration', '-of', 'default=nw=1:nk=1', str(path)]))
    if abs(duration(source) - duration(temporary)) > .25:
        raise RuntimeError('Rendered duration differs from source; output was not published')
    temporary.replace(target)
    print(target)


if __name__ == '__main__':
    main(sys.argv[1])
