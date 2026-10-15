"""Resolve runtime paths from this file, never from the caller's directory."""
from pathlib import Path
import tomllib

PROJECT = Path(__file__).resolve().parents[2]
REPOSITORY = PROJECT.parents[1]


def source_media():
    """Use the configured source instead of picking the first downloaded MKV."""
    session = tomllib.loads((PROJECT / 'session.toml').read_text())
    return (PROJECT / session['input']['media']).resolve()
