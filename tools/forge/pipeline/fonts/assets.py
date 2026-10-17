"""Font files and their adjacent license/provenance documents."""


def companions(source):
    """Keep this font's sidecar and shared documentation, not sibling fonts/reports."""
    return sorted(p for p in source.parent.iterdir() if p.is_file()
                  and p.suffix.lower() in {'.txt', '.md', '.json', '.toml'}
                  and (p.stem == source.stem or p.stem.lower() == 'provenance'
                       or p.name.lower().startswith(('ofl', 'license', 'licence', 'copyright', 'readme'))))
