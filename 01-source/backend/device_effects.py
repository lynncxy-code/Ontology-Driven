"""State-driven industrial effects exposed through the existing behavior form."""
from math import isfinite

SCAN = 'ot.industrial.region_scan'
HIGHLIGHT = 'ot.industrial.target_highlight'


def choice(key, label, options):
    return dict(key=key, label=label, type='select', default=options[0][0],
                options=[dict(value=value, label=name) for value, name in options])


def number(key, label, default, low, high):
    return dict(key=key, label=label, type='number', default=default, min=low, max=high, step=0.1)


EFFECTS = {
    SCAN: ('区域扫描', 'fx', 'alarm', '以设备为中心展开扫描；全场景共享一个扫描。', [
        choice('style', '样式', [('security', '安全蓝'), ('rehearsal', '预演绿')]),
        number('radius', '半径（米）', 8.5, 1, 50), number('duration', '展开时长（秒）', 4, 0.5, 30),
        choice('finish', '扫完后', [('restore', '恢复原景'), ('hold', '保留网格')]),
        number('interval', '重复间隔（秒；0 表示仅一次，否则为 2–120）', 0, 0, 120)]),
    HIGHLIGHT: ('目标高亮', 'visual', 'status_indicator', '在设备表面叠加颜色，离开状态时恢复原外观。', [
        choice('color', '颜色', [('found', '发现绿'), ('blocked', '阻断红（慢速呼吸）'), ('granted', '放行绿')]),
        number('duration', '持续（秒；0 表示随状态）', 0, 0, 600)]),
}


def effect_resources():
    return [dict(resource_id=rid, revision=1, display_name=name, description=note, target_note=note,
                 channel=channel, resource_type='fx' if channel == 'fx' else 'dynamic_material',
                 slot=slot, source='ontotwin_common', source_label='行为库', supported_states=['*'],
                 supported_object_types=['*'], available=True, status='published', parameter_schema=schema,
                 runtime_package='OntoTwinIndustrialBehavior', package_version='设备特效 1.1')
            for rid, (name, channel, slot, note, schema) in EFFECTS.items()]


def validate_effect_params(resource_id, params):
    schema = EFFECTS[resource_id][-1]
    if params is None:
        params = {}
    if not isinstance(params, dict) or set(params) - {s['key'] for s in schema}:
        raise ValueError('包含不支持的特效参数')
    for s in schema:
        v = params.get(s['key'], s['default'])
        if s['type'] == 'select':
            valid = v in [o['value'] for o in s['options']]
        else:
            valid = type(v) in (int, float) and s['min'] <= v <= s['max'] and isfinite(v)
        if not valid or (s['key'] == 'interval' and 0 < v < 2):
            raise ValueError(s['label'] + '无效')
