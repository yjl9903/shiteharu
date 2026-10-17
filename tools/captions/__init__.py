"""Font spans shared by subtitle rendering and review; no project state."""


def font_runs(text, style, fonts, event_id):
    """Resolve character-count spans using the same roles and bold defaults."""
    runs = style.get('text_runs')
    if runs is None:
        if style.get('font_role') is None:
            return []
        runs = [{'length': len(text), 'font_role': style.get('font_role')}]
        if 'bold' in style:
            runs[0]['bold'] = style['bold']
    else:
        if ('line_breaks' in style or 'line_advance' in style
                or style.get('text_layout') == 'vertical'
                or style.get('effect') == 'typewriter'):
            raise ValueError(f'text_runs cannot combine with per-row layout or typewriter: {event_id}')
        if (not runs or any(type(r.get('length')) is not int or r['length'] < 1 for r in runs)
                or sum(r['length'] for r in runs) != len(text)):
            raise ValueError(f'Invalid text_runs for {event_id}')
    result, offset = [], 0
    for run in runs:
        role = run.get('font_role', style.get('font_role'))
        if fonts is not None and role not in fonts:
            raise ValueError(f'Unknown font role {role} in {event_id}')
        spec = (fonts or {}).get(role, {})
        end = offset + run['length']
        result.append({'text': text[offset:end], 'font_role': role,
                       'bold': run.get('bold', spec.get('bold', False))})
        offset = end
    return result
