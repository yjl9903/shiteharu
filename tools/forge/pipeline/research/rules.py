"""Apply font proposal decisions stored as data in a project's research recipe."""
from copy import deepcopy


def proposal(event, rules):
    rule = rules['events'].get(event['id'], rules['roles'].get(event['font_role']))
    if rule is None:
        return {'font_role': 'old_' + event['font_role']}, '保留未配置提案规则的字体角色。'
    result = deepcopy(rule['set'])
    def scale(target, coefficients):
        for key, value in coefficients.items():
            if isinstance(value, dict):
                scale(target.setdefault(key, {}), value)
            else:
                target[key] = round(event['fontsize'] * value, 2)
    scale(result, rule['per_fontsize'])
    if event.get('color') == '000000' and result['font_role'] in rules['black_outline_roles']:
        result['outline'] = 0
    if 'scale_x_cap' in rule:
        result['scale_x'] = min(event.get('scale_x', 100), rule['scale_x_cap'])
    return result, rule['reason']
