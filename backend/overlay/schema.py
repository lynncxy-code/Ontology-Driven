import copy
import re


TEMPLATES = [
    {
        "id": "title_body",
        "label": "标题 + 正文",
        "description": "用于简介、说明和备注。",
        "slots": [
            {"id": "title", "type": "text", "required": True},
            {"id": "body", "type": "long_text", "required": False},
        ],
    },
    {
        "id": "title_subtitle_body",
        "label": "标题 + 小标题 + 正文",
        "description": "用于具有两级信息层次的说明。",
        "slots": [
            {"id": "title", "type": "text", "required": True},
            {"id": "subtitle", "type": "text", "required": False},
            {"id": "body", "type": "long_text", "required": False},
        ],
    },
    {
        "id": "title_metrics",
        "label": "标题 + 指标",
        "description": "用于展示一至四项设备指标。",
        "slots": [
            {"id": "title", "type": "text", "required": True},
            {"id": "metrics", "type": "metrics", "required": False, "max_items": 4},
        ],
    },
    {
        "id": "title_status_metrics",
        "label": "标题 + 状态 + 指标",
        "description": "用于展示标准状态和关键指标。",
        "slots": [
            {"id": "title", "type": "text", "required": True},
            {"id": "status", "type": "status", "required": True},
            {"id": "metrics", "type": "metrics", "required": False, "max_items": 4},
        ],
    },
]

TEMPLATE_MAP = {item["id"]: item for item in TEMPLATES}
DISPLAY_MODES = {"selected", "always"}
BINDING_SOURCES = {"literal", "instance", "object_type", "raw_state"}
STATUS_LEVELS = {"normal", "info", "warning", "critical", "offline", "unknown"}
INSTANCE_PATHS = {
    "id", "display_name", "status", "last_seen", "object_type_rid", "object_type_name"
}
OBJECT_TYPE_PATHS = {"rid", "name", "category", "description"}
FORMAT_KEYS = {"precision", "unit", "datetime_format", "empty_text", "max_length"}
OVERRIDE_KEYS = {"enabled", "template_id", "slots"}
_SAFE_PATH = re.compile(r"^[^\s.\[\]/\\]+(?:\.[^\s.\[\]/\\]+)*$")


class OverlayValidationError(ValueError):
    def __init__(self, errors):
        self.errors = errors if isinstance(errors, list) else [{"path": "", "message": str(errors)}]
        super().__init__(self.errors[0].get("message", "overlay validation failed"))


def default_overlay_values():
    return {
        "enabled": False,
        "template_id": "title_body",
        "display_mode": "selected",
        "anchor": {
            "strategy": "bounds_top",
            "offset_cm": {"x": 0.0, "y": 0.0, "z": 20.0},
        },
        "slots": {
            "title": {
                "required": True,
                "binding": {"source": "instance", "path": "display_name"},
                "format": {"empty_text": "--", "max_length": 80},
            },
            "body": {
                "required": False,
                "binding": {"source": "literal", "value": ""},
                "format": {"empty_text": "--", "max_length": 300},
            },
        },
    }


def clone_templates():
    return copy.deepcopy(TEMPLATES)


def _error(errors, path, message):
    errors.append({"path": path, "message": message})


def _validate_binding(binding, path, errors):
    if not isinstance(binding, dict):
        _error(errors, path, "字段绑定必须是对象")
        return
    source = binding.get("source")
    if source not in BINDING_SOURCES:
        _error(errors, f"{path}.source", "不支持的字段来源")
        return
    if source == "literal":
        value = binding.get("value")
        if isinstance(value, (dict, list)):
            _error(errors, f"{path}.value", "固定内容必须是标量")
        return

    field_path = binding.get("path")
    if not isinstance(field_path, str) or not _SAFE_PATH.match(field_path) or len(field_path) > 160:
        _error(errors, f"{path}.path", "字段路径格式不正确")
        return
    if source == "instance" and field_path not in INSTANCE_PATHS:
        _error(errors, f"{path}.path", "不支持的实例字段")
    if source == "object_type" and field_path not in OBJECT_TYPE_PATHS:
        _error(errors, f"{path}.path", "不支持的类型字段")


def _validate_format(fmt, path, errors):
    if fmt is None:
        return
    if not isinstance(fmt, dict):
        _error(errors, path, "展示格式必须是对象")
        return
    for key in fmt:
        if key not in FORMAT_KEYS:
            _error(errors, f"{path}.{key}", "不支持的展示格式")
    precision = fmt.get("precision")
    if precision is not None and (isinstance(precision, bool) or not isinstance(precision, int) or not 0 <= precision <= 6):
        _error(errors, f"{path}.precision", "小数位数必须为 0 至 6")
    max_length = fmt.get("max_length")
    if max_length is not None and (isinstance(max_length, bool) or not isinstance(max_length, int) or not 1 <= max_length <= 500):
        _error(errors, f"{path}.max_length", "最大长度必须为 1 至 500")
    for key, limit in (("unit", 24), ("datetime_format", 64), ("empty_text", 32)):
        value = fmt.get(key)
        if value is not None and (not isinstance(value, str) or len(value) > limit):
            _error(errors, f"{path}.{key}", f"{key} 长度超过限制")


def _validate_text_slot(slot, path, errors, force_required=False):
    if not isinstance(slot, dict):
        _error(errors, path, "槽位配置必须是对象")
        return
    required = slot.get("required", force_required)
    if not isinstance(required, bool):
        _error(errors, f"{path}.required", "required 必须为布尔值")
    if force_required and required is not True:
        _error(errors, f"{path}.required", "该模板槽位必须保留")
    _validate_binding(slot.get("binding"), f"{path}.binding", errors)
    _validate_format(slot.get("format"), f"{path}.format", errors)


def _validate_metrics(metrics, path, errors):
    if metrics is None:
        return
    if not isinstance(metrics, list):
        _error(errors, path, "指标槽位必须是数组")
        return
    if len(metrics) > 4:
        _error(errors, path, "指标最多四项")
    seen = set()
    for index, item in enumerate(metrics):
        item_path = f"{path}.{index}"
        if not isinstance(item, dict):
            _error(errors, item_path, "指标必须是对象")
            continue
        item_id = item.get("id")
        if not isinstance(item_id, str) or not item_id.strip() or len(item_id) > 64:
            _error(errors, f"{item_path}.id", "指标 ID 不能为空且最长 64 字符")
        elif item_id in seen:
            _error(errors, f"{item_path}.id", "指标 ID 不能重复")
        else:
            seen.add(item_id)
        if not isinstance(item.get("label", ""), str) or len(item.get("label", "")) > 48:
            _error(errors, f"{item_path}.label", "指标名称最长 48 字符")
        if not isinstance(item.get("required", False), bool):
            _error(errors, f"{item_path}.required", "required 必须为布尔值")
        _validate_binding(item.get("binding"), f"{item_path}.binding", errors)
        _validate_format(item.get("format"), f"{item_path}.format", errors)


def _validate_status(status, path, errors):
    if not isinstance(status, dict):
        _error(errors, path, "状态槽位必须是对象")
        return
    if status.get("required") is not True:
        _error(errors, f"{path}.required", "状态槽位必须保留")
    _validate_binding(status.get("label_binding"), f"{path}.label_binding", errors)
    _validate_binding(status.get("level_binding"), f"{path}.level_binding", errors)
    _validate_format(status.get("format"), f"{path}.format", errors)


def validate_full_config(config):
    errors = []
    if not isinstance(config, dict):
        raise OverlayValidationError("面板配置必须是对象")

    if not isinstance(config.get("enabled"), bool):
        _error(errors, "enabled", "enabled 必须为布尔值")
    template_id = config.get("template_id")
    template = TEMPLATE_MAP.get(template_id)
    if not template:
        _error(errors, "template_id", "不支持的模板")
    if config.get("display_mode") not in DISPLAY_MODES:
        _error(errors, "display_mode", "显示模式必须为 selected 或 always")

    anchor = config.get("anchor")
    if not isinstance(anchor, dict) or anchor.get("strategy") != "bounds_top":
        _error(errors, "anchor", "3.7 仅支持 bounds_top 锚点")
    else:
        offset = anchor.get("offset_cm")
        if not isinstance(offset, dict):
            _error(errors, "anchor.offset_cm", "锚点偏移必须是对象")
        else:
            for axis in ("x", "y", "z"):
                value = offset.get(axis, 0)
                if isinstance(value, bool) or not isinstance(value, (int, float)) or abs(value) > 100000:
                    _error(errors, f"anchor.offset_cm.{axis}", "锚点偏移必须是有效数字")

    slots = config.get("slots")
    if not isinstance(slots, dict):
        _error(errors, "slots", "槽位配置必须是对象")
        slots = {}

    if template:
        allowed_slots = {item["id"] for item in template["slots"]}
        for slot_id in slots:
            if slot_id not in allowed_slots:
                _error(errors, f"slots.{slot_id}", "当前模板不包含该槽位")
        for slot_def in template["slots"]:
            slot_id = slot_def["id"]
            slot = slots.get(slot_id)
            if slot_def.get("required") and slot is None:
                _error(errors, f"slots.{slot_id}", "缺少模板必填槽位")
                continue
            if slot is None:
                continue
            if slot_def["type"] in ("text", "long_text"):
                _validate_text_slot(slot, f"slots.{slot_id}", errors, slot_def.get("required", False))
            elif slot_def["type"] == "metrics":
                _validate_metrics(slot, f"slots.{slot_id}", errors)
            elif slot_def["type"] == "status":
                _validate_status(slot, f"slots.{slot_id}", errors)

    if errors:
        raise OverlayValidationError(errors)
    return config


def validate_override(values):
    if not isinstance(values, dict):
        raise OverlayValidationError("实例覆盖必须是对象")
    errors = []
    for key in values:
        if key not in OVERRIDE_KEYS:
            _error(errors, key, "实例不能覆盖该配置")
    if "enabled" in values and not isinstance(values["enabled"], bool):
        _error(errors, "enabled", "enabled 必须为布尔值")
    if "template_id" in values and values["template_id"] not in TEMPLATE_MAP:
        _error(errors, "template_id", "不支持的模板")
    if "slots" in values and not isinstance(values["slots"], dict):
        _error(errors, "slots", "槽位覆盖必须是对象")
    if errors:
        raise OverlayValidationError(errors)
    return values
