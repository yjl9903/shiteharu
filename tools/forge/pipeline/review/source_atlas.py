"""Decode configured windows, optionally rank image changes for human review."""
import argparse
import json
import math
import re
import subprocess
import tomllib
from PIL import Image, ImageChops, ImageDraw
from .source_frames import ROOT, media


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', required=True, help='TOML capture recipe relative to project')
    parser.add_argument('--label', required=True)
    args = parser.parse_args()
    plan = tomllib.loads((ROOT / args.plan).read_text())
    width = int(plan.get('width', 480))
    stride = int(plan.get('stride', 1))
    columns = int(plan.get('columns', 4))
    groups = int(plan.get('groups_per_sheet', 6))
    threshold = plan.get('white_threshold')
    neighbors = int(plan.get('candidate_neighbors', 1))
    if min(width, stride, columns, groups, neighbors) < 1:
        raise ValueError('Capture dimensions and sampling counts must be positive')
    crop = plan.get('crop')
    windows = plan.get('windows', [])
    windows += [{'start': max(0, t + plan['offset']), 'end': t + plan['offset'] + plan['duration']}
                for t in plan.get('centers', [])]
    if not windows or any(w['start'] < 0 or w['end'] <= w['start'] for w in windows):
        raise ValueError('At least one valid capture window is required')
    out = ROOT / 'frames' / args.label
    out.mkdir(parents=True, exist_ok=True)
    entries, rows = [], []
    for number, window in enumerate(windows):
        folder = out / f'{number:03}'
        folder.mkdir(exist_ok=True)
        # Remove only generated numbered images so a shorter rerun cannot retain stale frames.
        for old in folder.glob('[0-9][0-9][0-9][0-9].jpg'):
            old.unlink()
        vf = f'select=not(mod(n\\,{stride})),showinfo'
        if crop:
            x, y, w, h = crop
            vf += f',crop={w}:{h}:{x}:{y}'
        vf += f',scale={width}:-1'
        run = subprocess.run(['ffmpeg','-hide_banner','-y','-ss',str(window['start']),
            '-t',str(window['end']-window['start']),'-copyts','-i',str(media()),
            '-vf',vf,'-fps_mode','passthrough',str(folder/'%04d.jpg')],
            capture_output=True,text=True,check=True)
        pts = [float(v) for v in re.findall(r'pts_time:([0-9.]+)', run.stderr)]
        files = sorted(folder.glob('[0-9][0-9][0-9][0-9].jpg'))
        if not files or len(files) != len(pts):
            raise ValueError('Decoded images and PTS are empty or inconsistent')
        frames = [{'pts': t, 'file': str(f.relative_to(ROOT))} for t, f in zip(pts, files)]
        entry = {'window': window, 'frames': frames}
        selected = list(range(len(files)))
        if threshold is not None:
            masks = []
            for file in files:
                with Image.open(file) as im:
                    masks.append(im.convert('L').point(lambda pixel: 255 if pixel > threshold else 0))
            if len(masks) < 2:
                raise ValueError('Ranking needs at least two decoded frames')
            scores = [sum(ImageChops.difference(a,b).histogram()[1:]) for a,b in zip(masks,masks[1:])]
            change = 1 + max(range(len(scores)), key=scores.__getitem__)
            selected = list(range(max(0,change-neighbors), min(len(files),change+neighbors)))
            entry['candidate_pts'] = pts[change]
            entry['candidate_note'] = 'Maximum white-mask change; not a confirmed caption boundary.'
        entries.append(entry)
        with Image.open(files[0]) as im:
            height = im.height
        row = Image.new('RGB', (width*columns, (height+26)*math.ceil(len(selected)/columns)), '#222222')
        draw = ImageDraw.Draw(row)
        for i, n in enumerate(selected):
            x, y = i%columns*width, i//columns*(height+26)
            with Image.open(files[n]) as im:
                row.paste(im, (x,y+26))
            draw.text((x+4,y+4), f'{pts[n]:.6f}s', fill='white', font_size=17)
        rows.append(row)
    for offset in range(0,len(rows),groups):
        batch = rows[offset:offset+groups]
        sheet = Image.new('RGB',(width*columns,sum(row.height for row in batch)),'#222222')
        y = 0
        for row in batch:
            sheet.paste(row,(0,y)); y += row.height
        target = out / f'sheet-{offset//groups:03}.jpg'
        sheet.save(target,quality=95)
        print(target.relative_to(ROOT),flush=True)
    (out/'index.json').write_text(json.dumps({'capture':plan,'windows':entries,
        'note':'Decoded PTS evidence only; all caption decisions require human inspection.'},indent=2)+'\n')


if __name__ == '__main__':
    main()
