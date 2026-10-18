"""Read-only migration preflight; never repair inputs or use cached substitutes."""
import argparse
import hashlib
from pathlib import Path
import subprocess

from ..paths import PROJECT, REPOSITORY, CONFIG, read_config


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--no-media', action='store_true')
    args = parser.parse_args()
    errors = []
    checked = set()

    def require(value, sha256=None):
        relative = Path(value)
        if relative.is_absolute():
            errors.append(f'{relative.name}: expected project-relative path')
            return None
        file = PROJECT / relative
        if not file.resolve().is_relative_to(REPOSITORY):
            errors.append(f'{value}: outside repository')
            return None
        if any(p.is_symlink() for p in [file, *file.parents]):
            errors.append(f'{value}: symlink input; prepare real files')
            return None
        if not file.is_file():
            errors.append(f'{value}: missing input')
            return None
        if sha256:
            with file.open('rb') as stream:
                actual = hashlib.file_digest(stream, 'sha256').hexdigest()
            if actual != sha256:
                errors.append(f'{value}: SHA-256 mismatch (expected {sha256}, got {actual})')
        checked.add(file.resolve())
        return file

    for key in ('timeline', 'defaults', 'clips'):
        if key in CONFIG:
            require(CONFIG[key])
    for pattern in CONFIG['overlays']:
        if Path(pattern).is_absolute():
            errors.append('overlays: expected project-relative pattern')
            continue
        matches = sorted(PROJECT.glob(pattern))
        if not matches:
            errors.append(f'{pattern}: no design inputs')
        for file in matches:
            require(str(file.relative_to(PROJECT)))

    manifest = REPOSITORY / 'fonts/local-fonts.toml'
    local_fonts = {f['file']: f for f in read_config(manifest)['fonts']} if manifest.is_file() else {}

    def font(value):
        file = (PROJECT / value).resolve()
        record = None
        if file.is_relative_to(REPOSITORY / 'fonts/local'):
            record = local_fonts.get(file.name)
            if not record:
                errors.append(f'{value}: missing identity in fonts/local-fonts.toml')
        require(value, record['sha256'] if record else None)

    fonts_file = require(CONFIG['fonts'])
    if fonts_file:
        for item in read_config(fonts_file).values():
            font(item['file'])
    if CONFIG.get('research'):
        recipe_file = require(CONFIG['research'])
        if recipe_file:
            recipe = read_config(recipe_file)
            for section, keys in [('diamond', ('source', 'license')),
                                  ('fracture', ('original', 'fallback', 'license'))]:
                for key in keys:
                    if key in recipe.get(section, {}):
                        require(recipe[section][key])
            if recipe.get('label_font'):
                font(recipe['label_font'])

    session = None
    if CONFIG.get('media_session'):
        session_file = require(CONFIG['media_session'])
        if session_file:
            session = read_config(session_file)['input']
    if not args.no_media:
        if session:
            if not session.get('media_sha256'):
                errors.append('session input: missing media_sha256')
            require(session['media'], session.get('media_sha256'))
        elif CONFIG.get('media'):
            require(CONFIG['media'])
            print('NOTE: direct media configuration has no session SHA-256 baseline')
        for executable, option, capabilities in [
            ('ffmpeg', '-filters', ('ass',)),
            ('ffmpeg', '-encoders', ('libx264', 'aac')),
            ('ffprobe', '-version', ()),
        ]:
            try:
                result = subprocess.run([executable, '-hide_banner', option],
                                        capture_output=True, text=True, timeout=20, check=True)
                names = {fields[1] for line in result.stdout.splitlines() if len(fields := line.split()) >= 2}
                for capability in capabilities:
                    if capability not in names:
                        errors.append(f'{executable}: missing {capability}')
            except (OSError, subprocess.SubprocessError):
                errors.append(f'{executable}: unavailable or failed {option}')

    for error in errors:
        print(f'ERROR: {error}')
    print(f'{len(checked)} input files checked; {len(errors)} errors. '
          + ('Media/tool checks SKIPPED.' if args.no_media else 'Media/tool checks included.'))
    print('Preparation: docs/migration.md and fonts/SOURCES.md. '
          'This does not validate rendered output, evidence images or optional research candidates.')
    raise SystemExit(1 if errors else 0)


if __name__ == '__main__':
    main()
