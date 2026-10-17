#!/usr/bin/env python3
"""Read-only source evidence: contact sheets or individual frames, never subtitle edits."""
import argparse
import json
from pathlib import Path
import subprocess
import tomllib

from ..paths import PROJECT as ROOT, CONFIG, source_media


def media():
    return source_media()


def capture(t, path, width=960):
    path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(t), '-i', str(media()),
                    '-frames:v', '1', '-vf', f'scale={width}:-1', str(path)], check=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--start', type=float, required=True)
    p.add_argument('--end', type=float)
    p.add_argument('--step', type=float, default=1)
    p.add_argument('--label', default='source')
    p.add_argument('--width', type=int, default=640)
    args = p.parse_args()
    if args.step <= 0 or args.start < 0:
        p.error('start must be nonnegative and step positive')
    out = ROOT / 'frames' / args.label
    out.mkdir(parents=True, exist_ok=True)
    end = args.end if args.end is not None else args.start + args.step / 2
    times = []
    t = args.start
    while t < end - 0.00001:
        times.append(round(t, 6)); t += args.step
    from PIL import Image, ImageDraw
    entries = []
    for offset in range(0, len(times), 12):
        batch = times[offset:offset+12]
        height = round(args.width * CONFIG['canvas'][1] / CONFIG['canvas'][0])
        sheet = Image.new('RGB', (args.width*3, (height+28)*((len(batch)+2)//3)), '#202020')
        draw = ImageDraw.Draw(sheet)
        for i, t in enumerate(batch):
            name = f'{t:010.3f}.jpg'
            capture(t, out / name, args.width)
            x, y = i % 3 * args.width, i // 3 * (height+28)
            with Image.open(out / name) as im:
                sheet.paste(im, (x,y+28))
            draw.text((x+10,y+5), f'{t:.3f}s', fill='white', font_size=18)
            entries.append({'requested_time':t, 'file':str((out/name).relative_to(ROOT))})
        sheet.save(out / f'sheet-{offset//12:03}.jpg', quality=90)
        print((out / f'sheet-{offset//12:03}.jpg').relative_to(ROOT), flush=True)
    (out/'index.json').write_text(json.dumps({'note':'Requested seek times, not certified frame PTS. Manual inspection required.',
        'capture':{'start':args.start,'end':end,'step':args.step,'width':args.width,'label':args.label},
        'frames':entries}, indent=2)+'\n')


if __name__ == '__main__':
    main()
