"""Explicit project context for the Forge CLI; configuration paths are project-relative."""
from pathlib import Path
import tomllib

REPOSITORY = Path(__file__).resolve().parents[3]
PROJECT = None
CONFIG = None
CONFIG_FILE = None


def configure(filename):
    global PROJECT, CONFIG, CONFIG_FILE
    CONFIG_FILE = Path(filename).resolve()
    PROJECT = CONFIG_FILE.parent
    CONFIG = read_config(CONFIG_FILE)
    if CONFIG.get('version') != 1:
        raise ValueError('Unsupported Forge configuration version')
    for field in ('canvas', 'duration', 'timeline', 'fonts', 'defaults', 'overlays', 'output'):
        if field not in CONFIG:
            raise ValueError(f'Missing Forge configuration: {field}')
    if len(CONFIG['canvas']) != 2 or any(n <= 0 for n in CONFIG['canvas']):
        raise ValueError('canvas must contain two positive dimensions')
    if ('media' in CONFIG) == ('media_session' in CONFIG):
        raise ValueError('Configure exactly one of media or media_session')
    if CONFIG['duration'] <= 0:
        raise ValueError('duration must be positive')


def path(value):
    value = Path(value)
    if value.is_absolute():
        raise ValueError(f'Configured paths must be project-relative: {value.name}')
    return (PROJECT / value).resolve()


def setting_path(key):
    return path(CONFIG[key])


def design_files():
    return sorted({p for pattern in CONFIG['overlays'] for p in PROJECT.glob(pattern)})


def source_media():
    if 'media' in CONFIG:
        return setting_path('media')
    session = tomllib.loads(setting_path('media_session').read_text())
    return path(session['input']['media'])


def research():
    if 'research' not in CONFIG:
        raise ValueError('This project has no research recipe; configure research first')
    recipe = read_config(setting_path('research'))
    path(recipe['directory']).mkdir(parents=True, exist_ok=True)
    return recipe


def read_config(filename):
    """Read TOML configuration only; JSON is reserved for data and reports."""
    filename = Path(filename)
    if filename.suffix != '.toml':
        raise ValueError(f'Configuration must use .toml: {filename.name}')
    with filename.open('rb') as stream:
        return tomllib.load(stream)
