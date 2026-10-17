"""Render a separate soft black shadow while keeping caption ink sharp.

Pass the production render_event function as the third argument. Coordinates,
timings, wrapping, font selection and animation remain owned by that renderer.
"""
def render_with_shadow(event, fonts, render_event):
    spec = event.get('soft_shadow')
    if not spec:
        return render_event(event, fonts)
    base = {k: v for k, v in event.items() if k != 'soft_shadow'}
    layer = base.get('layer', 1 if base.get('supplemental') else 0)
    shadow = {
        **base, 'color': '000000', 'outline_color': '000000',
        'outline': spec['spread'], 'shadow': 0, 'blur': spec['blur'],
        'x': base['x'] + spec['x'], 'y': base['y'] + spec['y'],
        'layer': layer - 1,
        'extra_tags': base.get('extra_tags', '') + fr"\alpha&H{spec['alpha']}&",
    }
    for key, delta in [('from_x', spec['x']), ('from_y', spec['y'])]:
        if key in shadow:
            shadow[key] += delta
    ink = {**base, 'shadow': 0, 'blur': 0, 'layer': layer}
    return render_event(shadow, fonts) + render_event(ink, fonts)
