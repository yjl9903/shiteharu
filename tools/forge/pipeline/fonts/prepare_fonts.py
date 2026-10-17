"""Stage exactly the configured fonts for libass, without system font discovery."""
import shutil
from ..paths import PROJECT, path, setting_path, read_config


def main():
    fonts = read_config(setting_path('fonts'))
    sources = {role: path(font['file']) for role, font in fonts.items()}
    for source in sources.values():
        if not source.is_file():
            raise FileNotFoundError(f'Missing configured font: {source.name}')
    output = setting_path('font_cache')
    output.mkdir(parents=True, exist_ok=True)
    expected = set()
    for role, source in sources.items():
        target = output / (role + source.suffix)
        expected.add(target)
        if not target.exists() or target.read_bytes() != source.read_bytes():
            shutil.copyfile(source, target)
    for target in output.iterdir():
        if target.is_file() and target not in expected:
            target.unlink()
    print(output)


if __name__ == '__main__':
    main()
