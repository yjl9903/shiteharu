"""Preflight reviewed font proposals before applying them to current design files."""
import copy
import hashlib
import json
import tomlkit
import os
from ..paths import PROJECT, CONFIG, path, setting_path, design_files, research, read_config
from .assets import companions
from captions import font_runs


def main():
    proposal = path(research()['directory'])
    fonts = tomlkit.parse(setting_path('fonts').read_text())
    new = read_config(proposal / 'font-config.proposed.toml')
    rows = json.loads((proposal / 'event-font-patches.json').read_text())
    patches = {p['id']: p for p in rows}
    if len(patches) != len(rows):
        raise ValueError('Duplicate font proposal event IDs')
    original = copy.deepcopy(fonts)
    aliases = {}
    copies = []
    for role, config in new.items():
        if role.startswith('old_'):
            retained = role[4:]
            if retained not in original or dict(config) != dict(original[retained]):
                raise ValueError(f'Stale retained font proposal: {role}; regenerate the proposal')
            aliases[role] = retained
            continue
        source = path(config['file'])
        if not source.is_file():
            raise FileNotFoundError(f'Missing proposed font: {source.name}')
        shared = setting_path('shared_fonts')
        identity = source.stem + '-' + hashlib.sha256(source.read_bytes()).hexdigest()[:16]
        destination = source.parent if source.is_relative_to(shared) else shared / identity
        copies.append((source, destination / source.name))
        copies.extend((extra, destination / extra.name) for extra in companions(source))
        fonts[role] = {**config, 'file': os.path.relpath(destination / source.name, PROJECT)}
    from ..subtitles.build import load
    current = {event['id']: event for event in load()[0]}
    if patches.keys() - current.keys():
        raise ValueError('Font proposal contains unknown event IDs')
    def restore_role(role):
        if role not in aliases:
            return role
        retained = aliases[role]
        if dict(fonts[retained]) != dict(original[retained]):
            raise ValueError(f'Cannot retain and replace the same font role: {retained}')
        return retained
    updates = []
    count = 0
    for filename in design_files():
        data = tomlkit.parse(filename.read_text())
        events = data['events']
        for event in events:
            if event['id'] not in patches:
                continue
            patch = patches[event['id']]
            change = copy.deepcopy(patch['set'])
            if 'font_role' in change:
                change['font_role'] = restore_role(change['font_role'])
            for run in change.get('text_runs', []):
                if 'font_role' in run:
                    run['font_role'] = restore_role(run['font_role'])
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
            current[event['id']].update(change)
            count += 1
        updates.append((filename, data))
    # Validate the complete effective typography before publishing any changes.
    for event in current.values():
        if event['font_role'] not in fonts:
            raise ValueError(f'Unknown font role {event["font_role"]}')
        font_runs(event['zh'], event, fonts, event['id'])
    planned = {}
    for source, destination in copies:
        content = source.read_bytes()
        if destination in planned and planned[destination] != content:
            raise ValueError(f'Conflicting font asset: {destination.name}')
        if destination.exists() and destination.read_bytes() != content:
            raise ValueError(f'Refusing to overwrite font asset: {destination.name}')
        planned[destination] = content
    for destination, content in planned.items():
        destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            with destination.open('xb') as stream:
                stream.write(content)
        except FileExistsError:
            if destination.read_bytes() != content:
                raise ValueError(f'Refusing to overwrite font asset: {destination.name}')
    for filename, data in [(setting_path('fonts'), fonts), *updates]:
        filename.write_text(tomlkit.dumps(data))
    print(f'Merged font proposal for {count} events; retained positions, sizes, times and text.')


if __name__ == '__main__':
    main()
