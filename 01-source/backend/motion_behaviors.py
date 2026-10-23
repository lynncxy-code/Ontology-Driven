"""Finite basic-motion presets, shared by catalog validation and routing.

Values are local-space display offsets, never business position writebacks.
No new persistence format: params lives inside an existing resource selection.
"""
import math

TARGET = {"key": "target", "label": "作用对象", "type": "select", "default": "model",
          "options": [{"value": "model", "label": "设备整体"}, {"value": "tagged", "label": "项目预设可动部件"}]}

AXIS = {"key": "axis", "label": "方向", "type": "select", "default": "z",
        "options": [{"value": "x", "label": "前后 X"}, {"value": "y", "label": "左右 Y"}, {"value": "z", "label": "上下 Z"}]}
DIRECTION = {"key": "direction", "label": "正反方向", "type": "select", "default": "positive",
             "options": [{"value": "positive", "label": "正向"}, {"value": "negative", "label": "反向"}]}
SPEED = {"key": "speed", "label": "转速（度/秒）", "type": "number", "default": 90, "min": 1, "max": 720, "step": 1}
DISTANCE = {"key": "distance", "label": "行程（厘米）", "type": "number", "default": 100, "min": 0, "max": 10000, "step": 1}
ANGLE = {"key": "angle", "label": "角度（度）", "type": "number", "default": 90, "min": 0, "max": 360, "step": 1}
DURATION = {"key": "duration", "label": "单程时长（秒）", "type": "number", "default": 2, "min": 0.1, "max": 120, "step": 0.1}

PRESETS = {
    "rotate": ("持续旋转", "模型围绕自身原点持续旋转，不改变实时定位坐标。", [AXIS, DIRECTION, SPEED]),
    "translate": ("平移到指定位置", "从模型原位沿选定方向移动指定行程，到达后保持。", [AXIS, DIRECTION, DISTANCE, DURATION]),
    "rotate_to": ("旋转到指定角度", "从模型原始朝向旋转指定角度，到达后保持。", [AXIS, DIRECTION, ANGLE, DURATION]),
    "pingpong": ("往复移动", "在模型原位与行程终点之间循环移动。", [AXIS, DIRECTION, DISTANCE, DURATION]),
    "swing": ("往复摆动", "在原始角度与指定角度之间循环摆动。", [AXIS, DIRECTION, ANGLE, DURATION]),
    "reset": ("恢复原位", "停止基础运动，恢复模型相对于实时定位点的原始姿态。", []),
}
PRESETS = {key: (name, description, ([TARGET] + schema) if schema else [])
           for key, (name, description, schema) in PRESETS.items()}

BELT_SCHEMA = [TARGET, {"key":"speed", "label":"滚动速度（纹理周期/秒）", "type":"number", "default":0.5, "min":-5, "max":5, "step":0.1}]


def belt_resource():
    return {"resource_id":"ot.material.belt_scroll", "revision":1, "display_name":"皮带条纹滚动",
            "description":"临时使用内置条纹材质展示皮带循环；停用后恢复原材质，不移动物料。",
            "channel":"visual", "resource_type":"dynamic_material", "source":"ontotwin_common", "source_label":"行为库",
            "supported_states":["*"], "supported_object_types":["*"], "slot":"status_indicator",
            "status":"published", "available":True, "parameter_schema":BELT_SCHEMA,
            "target_note":"建议选择项目预设的皮带部件。此行为替换显示材质，不模拟物料输送。",
            "runtime_package":"OntoTwinIndustrialBehavior", "package_version":"基础运动 0.2"}


def motion_resources():
    return [{"resource_id": "ot.motion." + key, "behavior_id": "motion." + key,
             "revision": 1, "display_name": name, "description": description,
             "channel": "animation", "resource_type": "animation", "source": "ontotwin_common",
             "source_label": "行为库", "supported_states": ["*"], "supported_object_types": ["*"],
             "slot": "motion", "status": "published", "available": True,
             "runtime_package": "OntoTwinIndustrialBehavior", "package_version": "基础运动 0.2",
             "parameter_schema": schema, "example": False,
             "target_note": "整体绕模型原点运动；部件绕各自原点运动，需项目预设可动部件。没有预设时不会改动整机。实时定位坐标不变。"}
            for key, (name, description, schema) in PRESETS.items()]


def normalize_motion_params(resource_id, params=None):
    """Reject non-finite/out-of-range/unknown parameters rather than clamp silently."""
    key = str(resource_id).removeprefix("ot.motion.")
    if key not in PRESETS and resource_id != 'ot.material.belt_scroll':
        raise ValueError("未知基础运动")
    if params is None:
        params = {}
    if not isinstance(params, dict):
        raise ValueError("运动参数格式错误")
    schema = BELT_SCHEMA if resource_id == 'ot.material.belt_scroll' else PRESETS[key][2]
    if set(params) - {p["key"] for p in schema}:
        raise ValueError("包含不支持的运动参数")
    result = {}
    for spec in schema:
        value = params.get(spec["key"], spec["default"])
        if spec["type"] == "select":
            if value not in [option["value"] for option in spec["options"]]:
                raise ValueError(spec["label"] + "选项无效")
        else:
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError(spec["label"] + "必须是有效数字")
            if not spec["min"] <= value <= spec["max"]:
                raise ValueError(f'{spec["label"]}范围为 {spec["min"]}–{spec["max"]}')
        result[spec["key"]] = value
    return result
