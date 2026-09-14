"""Curated 4.6 presentation resource catalog used by Nexus.

The catalog is deliberately metadata-only.  Executable UE assets stay in the
project/content package; Nexus stores a stable logical resource id and
revision.  The built-in records make the first industrial workflow usable in
an offline/demo environment and are also a contract for a future publisher.
"""
from __future__ import annotations

import copy
from typing import Any, Iterable, Mapping

CATALOG_VERSION = "industrial-4.6.examples.1"

_COMMON = "OntoTwin 通用表现"
_PROJECT = "当前项目表现"

MOCK_PRESENTATION_RESOURCES = [
    {"resource_id": "ot.industrial.agv.running_motion", "revision": 1, "display_name": "AGV 平稳运行", "resource_type": "animation", "channel": "animation", "source": "ontotwin_common", "source_label": _COMMON, "supported_states": ["running", "industrial.machine.running"], "supported_object_types": ["AGV", "工业车辆", "agv"], "slot": "motion", "preview": {"kind": "animation", "thumbnail": "mock://presentation/agv-running"}, "status": "published", "available": True},
    {"resource_id": "ot.industrial.agv.fault_stop", "revision": 1, "display_name": "AGV 故障停止", "resource_type": "animation", "channel": "animation", "source": "ontotwin_common", "source_label": _COMMON, "supported_states": ["fault", "industrial.machine.fault"], "supported_object_types": ["AGV", "工业车辆", "agv"], "slot": "motion", "preview": {"kind": "animation", "thumbnail": "mock://presentation/agv-fault-stop"}, "status": "published", "available": True},
    {"resource_id": "ot.industrial.machine.idle", "revision": 1, "display_name": "设备待机", "resource_type": "animation", "channel": "animation", "source": "ontotwin_common", "source_label": _COMMON, "supported_states": ["idle", "standby", "industrial.machine.idle"], "supported_object_types": ["*"], "slot": "motion", "preview": {"kind": "animation", "thumbnail": "mock://presentation/idle"}, "status": "published", "available": True},
    {"resource_id": "ot.industrial.alarm_flash", "revision": 1, "display_name": "工业告警闪烁", "resource_type": "fx", "channel": "fx", "source": "ontotwin_common", "source_label": _COMMON, "supported_states": ["fault", "warning", "industrial.machine.fault"], "supported_object_types": ["*"], "slot": "alarm", "preview": {"kind": "loop", "thumbnail": "mock://presentation/alarm-flash"}, "status": "published", "available": True},
    {"resource_id": "ot.industrial.critical_flash", "revision": 1, "display_name": "严重故障红色闪烁", "resource_type": "fx", "channel": "fx", "source": "ontotwin_common", "source_label": _COMMON, "supported_states": ["fault", "critical", "industrial.machine.fault"], "supported_object_types": ["*"], "slot": "alarm", "preview": {"kind": "loop", "thumbnail": "mock://presentation/critical-flash"}, "status": "published", "available": True},
    {"resource_id": "ot.industrial.maintenance_glow", "revision": 1, "display_name": "维护状态高亮", "resource_type": "fx", "channel": "fx", "source": "ontotwin_common", "source_label": _COMMON, "supported_states": ["maintenance", "industrial.maintenance"], "supported_object_types": ["*"], "slot": "maintenance", "preview": {"kind": "loop", "thumbnail": "mock://presentation/maintenance-glow"}, "status": "published", "available": True},
    {"resource_id": "ot.industrial.warning_material", "revision": 1, "display_name": "警告黄色外观", "resource_type": "dynamic_material", "channel": "visual", "source": "ontotwin_common", "source_label": _COMMON, "supported_states": ["warning", "low_battery", "industrial.visual.warning"], "supported_object_types": ["*"], "slot": "status_indicator", "preview": {"kind": "material", "thumbnail": "mock://presentation/warning-material"}, "status": "published", "available": True},
    {"resource_id": "ot.industrial.critical_material", "revision": 1, "display_name": "故障红色外观", "resource_type": "dynamic_material", "channel": "visual", "source": "ontotwin_common", "source_label": _COMMON, "supported_states": ["fault", "critical", "industrial.visual.critical"], "supported_object_types": ["*"], "slot": "status_indicator", "preview": {"kind": "material", "thumbnail": "mock://presentation/critical-material"}, "status": "published", "available": True},
    {"resource_id": "ot.industrial.maintenance_material", "revision": 1, "display_name": "维护蓝色外观", "resource_type": "dynamic_material", "channel": "visual", "source": "ontotwin_common", "source_label": _COMMON, "supported_states": ["maintenance", "industrial.visual.maintenance"], "supported_object_types": ["*"], "slot": "status_indicator", "preview": {"kind": "material", "thumbnail": "mock://presentation/maintenance-material"}, "status": "published", "available": True},
    {"resource_id": "project.agv.running_motion", "revision": 1, "display_name": "项目 AGV 运行动画", "resource_type": "animation", "channel": "animation", "source": "project", "source_label": _PROJECT, "supported_states": ["running", "industrial.machine.running"], "supported_object_types": ["AGV", "agv"], "slot": "motion", "preview": {"kind": "animation", "thumbnail": "mock://project/agv-running"}, "status": "published", "available": True},
    {"resource_id": "project.agv.red_material", "revision": 1, "display_name": "项目 AGV 故障材质", "resource_type": "dynamic_material", "channel": "visual", "source": "project", "source_label": _PROJECT, "supported_states": ["fault", "industrial.machine.fault"], "supported_object_types": ["AGV", "agv"], "slot": "status_indicator", "preview": {"kind": "material", "thumbnail": "mock://project/agv-red"}, "status": "published", "available": True},
    {"resource_id": "project.agv.alarm_fx", "revision": 1, "display_name": "项目 AGV 告警特效", "resource_type": "fx", "channel": "fx", "source": "project", "source_label": _PROJECT, "supported_states": ["fault", "industrial.machine.fault"], "supported_object_types": ["AGV", "agv"], "slot": "alarm", "preview": {"kind": "loop", "thumbnail": "mock://project/agv-alarm"}, "status": "published", "available": True},
    {"resource_id": "ot.industrial.pump.running_motion", "revision": 1, "display_name": "泵组运行循环", "resource_type": "animation", "channel": "animation", "source": "ontotwin_common", "source_label": _COMMON, "supported_states": ["running", "industrial.machine.running"], "supported_object_types": ["泵组", "Pump", "pump"], "slot": "motion", "preview": {"kind": "animation", "thumbnail": "mock://presentation/pump-running"}, "status": "published", "available": True},
    {"resource_id": "ot.industrial.pump.alarm_fx", "revision": 1, "display_name": "泵组压力告警", "resource_type": "fx", "channel": "fx", "source": "ontotwin_common", "source_label": _COMMON, "supported_states": ["fault", "warning", "industrial.machine.fault"], "supported_object_types": ["泵组", "Pump", "pump"], "slot": "alarm", "preview": {"kind": "loop", "thumbnail": "mock://presentation/pump-alarm"}, "status": "published", "available": True},
    {"resource_id": "ot.industrial.conveyor.running_motion", "revision": 1, "display_name": "输送线运行循环", "resource_type": "animation", "channel": "animation", "source": "ontotwin_common", "source_label": _COMMON, "supported_states": ["running", "industrial.machine.running"], "supported_object_types": ["输送线", "Conveyor", "conveyor"], "slot": "motion", "preview": {"kind": "animation", "thumbnail": "mock://presentation/conveyor-running"}, "status": "published", "available": True},
    {"resource_id": "ot.industrial.conveyor.jam_fx", "revision": 1, "display_name": "输送线卡滞告警", "resource_type": "fx", "channel": "fx", "source": "ontotwin_common", "source_label": _COMMON, "supported_states": ["fault", "warning", "industrial.machine.fault"], "supported_object_types": ["输送线", "Conveyor", "conveyor"], "slot": "alarm", "preview": {"kind": "loop", "thumbnail": "mock://presentation/conveyor-jam"}, "status": "published", "available": True},
]


# Executable examples shipped in the OntoTwinIndustrialBehavior plugin.
# Legacy mock IDs remain readable, but fabricated project entries are not selectable.
_EXAMPLES = {
    "ot.industrial.agv.running_motion": ("运行旋转指示（示例）", "模型上方的横杆持续旋转；不移动设备本体"),
    "ot.industrial.agv.fault_stop": ("停止运行指示（示例）", "停止并隐藏附加旋转指示"),
    "ot.industrial.machine.idle": ("待机：停止指示（示例）", "停止并隐藏附加旋转指示，不产生运行动画"),
    "ot.industrial.alarm_flash": ("告警闪烁（示例）", "模型上方的告警方块每秒闪烁"),
    "ot.industrial.critical_flash": ("严重告警闪烁（示例）", "模型上方的红色告警方块每秒闪烁"),
    "ot.industrial.warning_material": ("黄色高亮（示例）", "为模型叠加黄色半透明高亮，保留原材质"),
    "ot.industrial.critical_material": ("红色高亮（示例）", "为模型叠加红色半透明高亮，保留原材质"),
    "ot.industrial.maintenance_material": ("蓝色高亮（示例）", "为模型叠加蓝色半透明高亮，保留原材质"),
}
for _resource in MOCK_PRESENTATION_RESOURCES:
    _example = _EXAMPLES.get(_resource['resource_id'])
    _resource['available'] = _example is not None
    _resource['status'] = 'published' if _example else 'unimplemented'
    if _example:
        _resource['display_name'], _resource['description'] = _example
        _resource['supported_object_types'] = ['*']
        _resource['package_version'] = '工业示例包 0.1'
        _resource['runtime_package'] = 'OntoTwinIndustrialBehavior'
        _resource['preview'] = {'kind': _resource['channel']}
        _resource['example'] = True
MOCK_PRESENTATION_RESOURCES.append({
    'resource_id': 'ot.industrial.label.demo', 'revision': 1,
    'display_name': '示例标签', 'description': '在模型上方显示 DEMO 标签',
    'resource_type': 'label', 'channel': 'label', 'source': 'ontotwin_common',
    'source_label': _COMMON, 'supported_states': ['*'], 'supported_object_types': ['*'],
    'slot': 'label', 'status': 'published', 'available': True, 'example': True,
    'runtime_package': 'OntoTwinIndustrialBehavior', 'package_version': '工业示例包 0.1',
})


def list_resources(*, source: str | None = None, channel: str | None = None,
                   object_type: str | None = None, state: str | None = None,
                   include_unavailable: bool = False) -> list[dict[str, Any]]:
    """Return filtered copies; callers cannot mutate the catalog singleton."""
    source = str(source or "").strip().lower()
    if source in {"platform", "common", "ontotwin"}:
        source = "ontotwin_common"
    elif source in {"current_project", "project_local", "local"}:
        source = "project"
    channel = str(channel or "").strip().lower()
    if channel == "material":
        channel = "visual"
    object_type = str(object_type or "").strip().lower()
    state = str(state or "").strip().lower()
    result = []
    for resource in MOCK_PRESENTATION_RESOURCES:
        if source and resource["source"] != source:
            continue
        if channel and resource["channel"] != channel:
            continue
        if not include_unavailable and resource.get("available") is False:
            continue
        types = [str(value).lower() for value in resource.get("supported_object_types", [])]
        if object_type and "*" not in types and object_type not in types:
            # ObjectType APIs commonly pass a RID (for example
            # ``industrial.agv``) rather than the display name.  Match the
            # catalog token against the RID's final segment as a convenience;
            # the catalog remains explicit and never scans UE assets.
            rid_token = object_type.rsplit(".", 1)[-1].replace("_", "-")
            normalized_types = {value.replace("_", "-") for value in types}
            if not any(token in rid_token or rid_token in token for token in normalized_types if token != "*"):
                continue
        states = [str(value).lower() for value in resource.get("supported_states", [])]
        if state and state not in states:
            continue
        result.append(copy.deepcopy(resource))
    return result


def get_resource(resource_id: str, revision: int | None = None) -> dict[str, Any] | None:
    for resource in MOCK_PRESENTATION_RESOURCES:
        if resource["resource_id"] != resource_id:
            continue
        if revision is not None and int(resource["revision"]) != int(revision):
            continue
        return copy.deepcopy(resource)
    return None


def catalog_payload(**filters: Any) -> dict[str, Any]:
    resources = list_resources(**filters)
    return {
        "catalog_version": CATALOG_VERSION,
        "sources": [
            {"id": "ontotwin_common", "label": _COMMON},
            {"id": "project", "label": _PROJECT},
        ],
        "channels": ["animation", "fx", "visual", "label"],
        "resources": resources,
        "resource_count": len(resources),
        "mock": False,
        "example": True,
        "runtime_note": "需要 UE 加载工业示例包；配置已保存不代表当前 PIE 已应用。",
    }


def validate_selection(selection: Mapping[str, Any], *, channel: str | None = None) -> tuple[bool, str | None, dict[str, Any] | None]:
    """Validate a channel selection against the catalog, returning its record."""
    if not isinstance(selection, Mapping):
        return False, "selection must be an object", None
    resource_id = str(selection.get("resource_id") or selection.get("id") or "").strip()
    if not resource_id:
        return False, "resource_id is required", None
    resource = get_resource(resource_id, selection.get("revision"))
    if not resource:
        return False, "resource is not available", None
    if channel and resource["channel"] != channel:
        return False, "resource channel does not match selection channel", None
    requested_source = str(selection.get("source") or "").strip().lower()
    if requested_source in {"platform", "common", "ontotwin"}:
        requested_source = "ontotwin_common"
    elif requested_source in {"current_project", "project_local", "local"}:
        requested_source = "project"
    if requested_source and requested_source != resource.get("source"):
        return False, "resource source does not match selection source", None
    if resource.get("available") is False or resource.get("status") != "published":
        return False, "resource is not published", None
    return True, None, resource
