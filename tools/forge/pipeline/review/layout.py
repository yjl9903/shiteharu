#!/usr/bin/env python3
"""Measure rendered caption ink; flag overlap/offscreen candidates for human review."""
import argparse
import json
from pathlib import Path
import subprocess
from PIL import Image
from ..paths import PROJECT, CONFIG, setting_path
from ..subtitles.build import load, header, render_event
from ..subtitles.shadow_render import render_with_shadow


def intersects(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--start', type=float, default=0)
    parser.add_argument('--end', type=float, default=CONFIG['duration'])
    parser.add_argument('--label', default='all')
    args = parser.parse_args()
    events, fonts = load()
    width,height=CONFIG['canvas']
    font_cache=setting_path('font_cache').relative_to(PROJECT)
    out = PROJECT / '.cache' / 'layout-audit' / args.label
    out.mkdir(parents=True, exist_ok=True)
    results = []
    for event in events:
        if not args.start <= event['start'] < args.end:
            continue
        duration = event['end'] - event['start']
        local = {**event, 'start':0, 'end':duration}
        ass = out / (event['id'] + '.ass')
        ass.write_text(header(fonts[CONFIG['default_font']]['family']) + render_with_shadow(local, fonts, render_event))
        samples = [duration / 2]
        if event.get('effect', 'none') not in ('none', 'glow', 'distress'):
            samples = [min(0.067, duration / 4), duration / 2, max(0, duration - 0.067)]
        for number, time in enumerate(samples):
            png = out / f'{event["id"]}-{number}.png'
            vf = (f'setpts=PTS+{time}/TB,ass={ass.relative_to(PROJECT)}:'
                  f'fontsdir={font_cache}:alpha=1')
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i',
                            f'color=c=black@0:s={width}x{height}:r=30,format=rgba',
                            '-vf', vf, '-frames:v', '1', str(png)], cwd=PROJECT, check=True)
            with Image.open(png) as image:
                mask = image.getchannel('A').point(lambda value:255 if value > 32 else 0)
                bounds = mask.getbbox()
            collisions = []
            face_collisions = []
            if bounds:
                for kind,box in [('source',box) for box in event.get('source_boxes', [])] + [('face',box) for box in event.get('face_boxes', [])]:
                    if intersects(bounds, box):
                        # Check actual ink pixels; a multirow bounding box may contain empty space.
                        region = [max(bounds[0],box[0]), max(bounds[1],box[1]),
                                  min(bounds[2],box[2]), min(bounds[3],box[3])]
                        if mask.crop(tuple(map(int,region))).getbbox():
                            (collisions if kind=='source' else face_collisions).append(box)
            edge = bool(bounds and (bounds[0] <= 0 or bounds[1] <= 0 or bounds[2] >= width or bounds[3] >= height))
            results.append({'id':event['id'], 'time':round(event['start'] + time,3),
                            'ink_bounds':bounds, 'source_ink_intersections':collisions,
                            'face_ink_intersections':face_collisions,'allow_face_overlap':event.get('allow_face_overlap',False),
                            'touches_edge':edge, 'allow_offscreen':event.get('allow_offscreen',False),
                            'mask':str(png.relative_to(PROJECT))})
    target = PROJECT / 'review' / f'layout-{args.label}.json'
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps({'note':'Candidate flags only; source boxes and visual results require human review.',
                                 'samples':results},ensure_ascii=False,indent=2)+'\n')
    flags = [item for item in results if item['source_ink_intersections'] or (item['touches_edge'] and not item['allow_offscreen']) or (item['face_ink_intersections'] and not item['allow_face_overlap'])]
    print(json.dumps({'samples':len(results),'flagged_ids':sorted({item['id'] for item in flags}),
                      'report':str(target.relative_to(PROJECT))},ensure_ascii=False))


if __name__ == '__main__':
    main()
