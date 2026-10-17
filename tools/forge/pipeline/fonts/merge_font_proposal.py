"""Preflight reviewed font proposals before applying them to current design files."""
import copy
import json
import tomlkit
import os
import shutil
from ..paths import PROJECT, CONFIG, path, setting_path, design_files, research, read_config


def main():
    proposal = path(research()['directory'])
    fonts = tomlkit.parse(setting_path('fonts').read_text())
    new = read_config(proposal / 'font-config.proposed.toml')
    patches = {p['id']: p for p in json.loads((proposal / 'event-font-patches.json').read_text())}
    copies = []
    for role, config in new.items():
        if role.startswith('old_'):
            continue
        source = path(config['file'])
        if not source.is_file():
            raise FileNotFoundError(f'Missing proposed font: {source.name}')
        destination = setting_path('shared_fonts') / role
        copies.append((source, destination / source.name))
        copies.extend((extra, destination / extra.name) for extra in source.parent.iterdir()
                      if extra.suffix.lower() in ('.txt', '.json', '.toml', '.md'))
        fonts[role] = {**config, 'file': os.path.relpath(destination / source.name, PROJECT)}
    from ..subtitles.build import load
    current = {event['id']: event for event in load()[0]}
    updates = []
    count = 0
    for filename in design_files():
        data = tomlkit.parse(filename.read_text())
        events = data['events']
        for event in events:
            patch = patches[event['id']]
            change = copy.deepcopy(patch['set'])
            protected = {'zh', 'ja', 'text_zh', 'text_ja', CONFIG['text'], CONFIG['source_text'],
                         'x', 'y', 'fontsize', 'start', 'end', 'line_breaks'}
            if set(change) & protected:
                raise ValueError(f'Font proposal changes protected content/layout: {event["id"]}')
            ratio = current[event['id']]['fontsize'] / patch['base_fontsize']
            for field in ('outline', 'shadow'):
                if field in change:
                    change[field] = round(change[field] * ratio, 2)
            if 'soft_shadow' in change:
                for field in ('x', 'y', 'spread', 'blur'):
                    if field in change['soft_shadow']:
                        change['soft_shadow'][field] = round(change['soft_shadow'][field] * ratio, 2)
            if 'scale_x' in change:
                change['scale_x'] = min(current[event['id']].get('scale_x', 100), change['scale_x'])
            event.update(change)
            count += 1
        updates.append((filename, data))
    # All inputs and patches are valid before any shared font or design changes.
    for source, destination in copies:
        destination.parent.mkdir(parents=True, exist_ok=True)
        if source.resolve() != destination.resolve():
            shutil.copyfile(source, destination)
    for filename, data in [(setting_path('fonts'), fonts), *updates]:
        filename.write_text(tomlkit.dumps(data))
    print(f'Merged font proposal for {count} events; retained positions, sizes, times and text.')


if __name__ == '__main__':
    main()
