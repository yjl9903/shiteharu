"""Package editable inputs plus shared tools, preserving repository layout."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from ..paths import PROJECT, REPOSITORY, CONFIG, CONFIG_FILE, path, setting_path, design_files


def main():
    files = set()
    def add(item):
        if not item.exists():
            raise FileNotFoundError(f'Missing package input: {item.name}')
        candidates = item.rglob('*') if item.is_dir() else [item]
        for file in candidates:
            if not file.is_file():
                continue
            relative = file.relative_to(REPOSITORY)
            if any(part in {'.cache', '.venv', '__pycache__', 'local'} for part in relative.parts):
                continue
            if file.is_symlink():
                raise ValueError(f'Package inputs must be real files: {relative}')
            files.add(file)
    for name in ['pyproject.toml', 'uv.lock', '.python-version', 'docs/reproducibility.md',
                 'tools/forge', 'tools/loupe', 'fonts']:
        add(REPOSITORY / name)
    add(CONFIG_FILE)
    for key in ['timeline', 'fonts', 'defaults']:
        add(setting_path(key))
    for file in design_files():
        add(file)
    if CONFIG.get('research'):
        add(setting_path('research'))
    for name in CONFIG['package']['include']:
        add(path(name))
    if CONFIG['package'].get('include_evidence', False):
        from ..subtitles.build import load
        events, _ = load()
        for event in events:
            for reference in event.get('evidence', []):
                add(path(reference))
    for key in ['performance_ass', 'review_ass', 'source_srt', 'text_srt']:
        add(setting_path('output') / CONFIG[key])
    target = path(CONFIG['package']['file'])
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix('.building.zip')
    with ZipFile(temporary, 'w', ZIP_DEFLATED, compresslevel=6) as archive:
        for file in sorted(files):
            archive.write(file, file.relative_to(REPOSITORY))
    temporary.replace(target)
    print(f'{target}: {len(files)} files, {target.stat().st_size:,} bytes')


if __name__ == '__main__':
    main()
