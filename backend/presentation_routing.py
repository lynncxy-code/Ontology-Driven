"""OntoTwin 4.5 semantic presentation normalization and routing.

This module deliberately contains deterministic, finite industrial mappings.  It
does not evaluate user supplied Python, JavaScript, or arbitrary expressions and
it does not know about UE asset paths.  The backend emits logical behaviour IDs;
the UE side decides how a registered executor renders them.
"""

from __future__ import annotations

import copy
import hashlib
import json
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple


PRESENTATION_SCHEMA_VERSION = "1.0"
INDUSTRIAL_PROFILE_VERSION = "industrial.v1"
PRESENTATION_CHANNELS = ("animation", "visual", "fx", "label")
PRESENTATION_BEHAVIOR_LIBRARIES = {
    "industrial.default": "工业设备默认表现",
    "safe_fallback": "安全静态表现",
}

_CORE_STATE_ALIASES = {
    "运行": "industrial.machine.running",
    "待机": "industrial.machine.idle",
    "正常": "industrial.machine.idle",
    "故障": "industrial.machine.fault",
    "离线": "industrial.machine.offline",
    "idle": "industrial.machine.idle",
    "standby": "industrial.machine.idle",
    "normal": "industrial.machine.idle",
    "ready": "industrial.machine.idle",
    "running": "industrial.machine.running",
    "run": "industrial.machine.running",
    "active": "industrial.machine.running",
    "working": "industrial.machine.running",
    "translate": "industrial.machine.running",
    "fault": "industrial.machine.fault",
    "error": "industrial.machine.fault",
    "alarm": "industrial.machine.fault",
    "critical": "industrial.machine.fault",
    "offline": "industrial.machine.offline",
    "disconnected": "industrial.machine.offline",
    "lost": "industrial.machine.offline",
}

DEFAULT_PLATFORM_BEHAVIORS = {
    "animation": {
        "industrial.machine.idle": ("industrial.machine.idle", "motion"),
        "industrial.machine.running": ("industrial.machine.running", "motion"),
        "industrial.machine.fault": ("industrial.machine.fault", "motion"),
        "industrial.machine.offline": ("industrial.machine.offline", "motion"),
    },
    "visual": {
        "industrial.machine.fault": ("industrial.visual.critical", "status_indicator"),
        "industrial.machine.offline": ("industrial.visual.warning", "status_indicator"),
    },
    "fx": {},
    "label": {},
}

DEFAULT_PLATFORM_MODIFIERS = {
    "industrial.warning": {
        "visual": ("industrial.visual.warning", "status_indicator"),
        "fx": ("industrial.fx.warning_flash", "alarm"),
    },
    "industrial.critical": {
        "visual": ("industrial.visual.critical", "status_indicator"),
        "fx": ("industrial.fx.critical_flash", "alarm"),
    },
    "industrial.low_battery": {
        "visual": ("industrial.visual.warning", "status_indicator"),
    },
    "industrial.maintenance": {
        "visual": ("industrial.visual.maintenance", "status_indicator"),
    },
    "industrial.communication_degraded": {
        "visual": ("industrial.visual.warning", "status_indicator"),
    },
}

SAFE_FALLBACKS = {
    "animation": ("safe.idle", "motion"),
    "visual": ("safe.visible", "status_indicator"),
    "fx": ("safe.none", "alarm"),
    "label": ("safe.label", "label"),
}

# The catalog uses stable business resource IDs while the UE executor keeps
# the existing industrial behavior IDs.  Keep this bridge in the core route
# layer so selecting a 4.6 mock card still reaches the executor without
# exposing either naming scheme in Nexus.
_CATALOG_RESOURCE_BEHAVIOR_IDS = {
    "ot.industrial.label.demo": "industrial.label.demo",
    "ot.industrial.agv.running_motion": "industrial.machine.running",
    "ot.industrial.agv.fault_stop": "industrial.machine.fault",
    "ot.industrial.machine.idle": "industrial.machine.idle",
    "ot.industrial.pump.running_motion": "industrial.machine.running",
    "ot.industrial.conveyor.running_motion": "industrial.machine.running",
    "ot.industrial.alarm_flash": "industrial.fx.warning_flash",
    "ot.industrial.critical_flash": "industrial.fx.critical_flash",
    "ot.industrial.pump.alarm_fx": "industrial.fx.warning_flash",
    "ot.industrial.conveyor.jam_fx": "industrial.fx.critical_flash",
    "ot.industrial.maintenance_glow": "industrial.fx.warning_flash",
    "ot.industrial.warning_material": "industrial.visual.warning",
    "ot.industrial.critical_material": "industrial.visual.critical",
    "ot.industrial.maintenance_material": "industrial.visual.maintenance",
}


def _clean_id(value: Any, fallback: str) -> str:
    text = str(value or "").strip()
    return text or fallback


def _as_float(value: Any) -> Optional[float]:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _first(raw: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in raw and raw[key] not in (None, ""):
            return raw[key]
    return None


def _normalize_state(raw: Mapping[str, Any]) -> str:
    value = _first(raw, "presentation_state", "primary_state", "status", "state", "animation_state")
    if isinstance(value, Mapping):
        value = value.get("id") or value.get("name")
    value = str(value or "idle").strip().lower()
    if value.startswith("industrial."):
        return value
    return _CORE_STATE_ALIASES.get(value, "industrial.machine.idle")


def _append_modifier(modifiers: List[Dict[str, Any]], seen: set, modifier_id: str,
                     level: str = "active", priority: int = 0,
                     channels: Optional[Iterable[str]] = None) -> None:
    modifier_id = _clean_id(modifier_id, "industrial.unknown")
    if modifier_id in seen:
        return
    allowed = [str(channel) for channel in (channels or []) if str(channel) in PRESENTATION_CHANNELS]
    try:
        normalized_priority = int(priority)
    except (TypeError, ValueError):
        normalized_priority = 0
    modifiers.append({
        "id": modifier_id,
        "level": _clean_id(level, "active"),
        "active": True,
        "priority": normalized_priority,
        "channels": allowed,
    })
    seen.add(modifier_id)


def _normalize_modifiers(raw: Mapping[str, Any]) -> List[Dict[str, Any]]:
    modifiers: List[Dict[str, Any]] = []
    seen = set()
    supplied = raw.get("presentation_modifiers")
    if isinstance(supplied, Mapping):
        supplied = [dict(value, id=key) if isinstance(value, Mapping) else {"id": key, "level": value}
                    for key, value in supplied.items()]
    if isinstance(supplied, list):
        for item in supplied:
            if isinstance(item, str):
                item = {"id": item}
            if not isinstance(item, Mapping) or item.get("active", True) is False:
                continue
            _append_modifier(
                modifiers,
                seen,
                item.get("id") or item.get("name"),
                item.get("level", "active"),
                item.get("priority", 0),
                item.get("channels") or (),
            )

    battery = _as_float(_first(raw, "battery_level", "battery", "soc"))
    if battery is not None and battery <= 20:
        _append_modifier(modifiers, seen, "industrial.low_battery", "warning", 50, ("visual", "fx"))

    status = str(_first(raw, "status", "state") or "").strip().lower()
    severity = str(_first(raw, "alarm_level", "severity", "warning_level") or "").strip().lower()
    if status in {"warning", "warn", "degraded"} or severity in {"warning", "warn", "degraded"}:
        _append_modifier(modifiers, seen, "industrial.warning", "warning", 60, ("visual", "fx", "label"))
    if status in {"fault", "error", "alarm", "critical"} or severity in {"fault", "error", "alarm", "critical"}:
        _append_modifier(modifiers, seen, "industrial.critical", "critical", 100, ("visual", "fx", "label"))

    maintenance = _first(raw, "maintenance_mode", "maintenance")
    if maintenance is True or str(maintenance).strip().lower() in {"1", "true", "on", "active"}:
        _append_modifier(modifiers, seen, "industrial.maintenance", "active", 40, ("visual", "label"))

    communication = str(_first(raw, "communication_status", "connection_status") or "").strip().lower()
    if communication in {"degraded", "unstable", "timeout"}:
        _append_modifier(modifiers, seen, "industrial.communication_degraded", "warning", 70, ("visual", "fx"))

    modifiers.sort(key=lambda item: (-int(item["priority"]), item["id"]))
    return modifiers


def _normalize_actions(raw: Mapping[str, Any], instance_id: str) -> List[Dict[str, Any]]:
    supplied = raw.get("presentation_actions", raw.get("presentation_action"))
    if isinstance(supplied, Mapping):
        supplied = [supplied]
    if not isinstance(supplied, list):
        return []
    actions: List[Dict[str, Any]] = []
    for index, item in enumerate(supplied):
        if isinstance(item, str):
            item = {"id": item}
        if not isinstance(item, Mapping):
            continue
        action_id = _clean_id(item.get("id") or item.get("action"), "industrial.unknown_action")
        action_seed = json.dumps(dict(item), ensure_ascii=False, sort_keys=True, default=str)
        generated_event_id = f"{instance_id}:action:{hashlib.sha1(action_seed.encode('utf-8')).hexdigest()[:16]}"
        event_id = _clean_id(item.get("event_id"), generated_event_id)
        params = item.get("params") if isinstance(item.get("params"), Mapping) else {}
        try:
            sequence = int(item.get("sequence", index + 1))
        except (TypeError, ValueError):
            sequence = index + 1
        actions.append({
            "id": action_id,
            "event_id": event_id,
            "sequence": sequence,
            "params": copy.deepcopy(dict(params)),
        })
    actions.sort(key=lambda item: (int(item["sequence"]), item["event_id"]))
    return actions


def normalize_industrial(raw_state: Optional[Mapping[str, Any]], instance_id: str = "",
                         profile_version: str = INDUSTRIAL_PROFILE_VERSION) -> Dict[str, Any]:
    """Normalize raw industrial fields into a deterministic presentation intent."""
    raw = raw_state if isinstance(raw_state, Mapping) else {}
    primary_state = _normalize_state(raw)
    modifiers = _normalize_modifiers(raw)
    actions = _normalize_actions(raw, instance_id or "instance")
    source_revision = _first(raw, "presentation_revision", "state_revision", "revision")
    try:
        revision = int(source_revision) if source_revision is not None else 0
    except (TypeError, ValueError):
        revision = 0
    seed = json.dumps({
        "state": primary_state,
        "modifiers": modifiers,
        "actions": actions,
        "revision": revision,
    }, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:16]
    decision_id = _clean_id(_first(raw, "presentation_decision_id", "decision_id"),
                            f"pres-{instance_id or 'instance'}-{digest}")
    return {
        "schema_version": PRESENTATION_SCHEMA_VERSION,
        "profile_version": _clean_id(profile_version, INDUSTRIAL_PROFILE_VERSION),
        "presentation_revision": revision,
        "decision_id": decision_id,
        "primary_state": {"id": primary_state},
        "modifiers": modifiers,
        "actions": actions,
    }


def _route_value(value: Any, default_slot: str) -> Optional[Dict[str, Any]]:
    if isinstance(value, str):
        return {"behavior_id": value, "slot": default_slot}
    if isinstance(value, (tuple, list)) and len(value) >= 1:
        return {
            "behavior_id": str(value[0]),
            "slot": str(value[1] if len(value) > 1 and value[1] else default_slot),
        }
    if not isinstance(value, Mapping):
        return None
    behavior_id = value.get("behavior_id") or value.get("resource_id") or value.get("id")
    if not behavior_id:
        return None
    behavior_id = _CATALOG_RESOURCE_BEHAVIOR_IDS.get(str(behavior_id), str(behavior_id))
    route = {
        "behavior_id": str(behavior_id),
        "slot": str(value.get("slot") or default_slot),
    }
    resource_id = str(value.get('resource_id') or behavior_id)
    if resource_id.startswith('ot.motion.') or resource_id == 'ot.material.belt_scroll':
        from motion_behaviors import normalize_motion_params
        try:
            route['params'] = normalize_motion_params(resource_id, value.get('params'))
            route['behavior_id'] = resource_id.removeprefix('ot.')
        except ValueError:
            return {'behavior_id': 'safe.visible' if resource_id == 'ot.material.belt_scroll' else 'safe.idle', 'slot': default_slot, 'source': 'safe_fallback'}
    elif isinstance(value.get('params'), Mapping):
        route['params'] = copy.deepcopy(dict(value['params']))
    # 4.6 selections carry business resource identity and source.  Preserve
    # these fields in the wire result while keeping behavior_id for old UE
    # executors and snapshots.
    if value.get("resource_id"):
        route["resource_id"] = str(value["resource_id"])
    if value.get("revision") is not None:
        try:
            route["revision"] = int(value["revision"])
        except (TypeError, ValueError):
            route["revision"] = str(value["revision"])
    if value.get("source"):
        route["source"] = str(value["source"])
    return route


def _project_route(profile: Mapping[str, Any], channel: str, state_id: str,
                   modifier_ids: Iterable[str], raw_state=None) -> Optional[Dict[str, str]]:
    channels = profile.get("channels") if isinstance(profile, Mapping) else None
    config = channels.get(channel) if isinstance(channels, Mapping) else None
    # The product language calls this channel “动态材质”; the wire contract
    # historically called it ``visual``.  Accept both spellings at the
    # boundary while emitting the stable ``visual`` channel.
    if config is None and channel == "visual" and isinstance(channels, Mapping):
        config = channels.get("material")
    if isinstance(config, str):
        return _route_value(config, channel)
    if not isinstance(config, Mapping):
        return None
    default_slot = str(config.get("slot") or SAFE_FALLBACKS[channel][1])
    modifiers = config.get("modifiers") or {}
    for modifier_id in modifier_ids:
        candidate = modifiers.get(modifier_id) if isinstance(modifiers, Mapping) else None
        route = _route_value(candidate, default_slot)
        if route:
            return route
    states = config.get("states") or config.get("primary_states") or {}
    if isinstance(states, Mapping):
        # UI keys retain the business field and value, e.g. status:运行.
        # Match against that field, never silently reinterpret another field.
        matches = []
        raw = raw_state or {}
        for key, selection in states.items():
            if ":" not in key:
                continue
            field, expected = key.split(":", 1)
            actual = raw.get(field)
            if actual is None:
                continue
            expected_token = str(expected).strip().lower()
            actual_token = str(actual).strip().lower()
            priority = 0
            match = actual_token == expected_token
            if field in {"status", "state", "animation_state"}:
                match = match or (expected_token in _CORE_STATE_ALIASES and actual_token in _CORE_STATE_ALIASES
                    and _CORE_STATE_ALIASES[expected_token] == _CORE_STATE_ALIASES[actual_token])
                priority = 100 if _CORE_STATE_ALIASES.get(actual_token) == "industrial.machine.fault" else 10
            elif field in {"battery_level", "battery", "soc"} and expected_token in {"低电量", "正常"}:
                number = _as_float(actual)
                match = number is not None and ((number <= 20) == (expected_token == "低电量"))
                priority = 50 if expected_token == "低电量" else 0
            if match:
                matches.append((priority, key, selection))
        for _, _, selection in sorted(matches, key=lambda item: (-item[0], item[1])):
            route = _route_value(selection, default_slot)
            if route:
                return route
        route = _route_value(states.get(state_id), default_slot)
        if route:
            return route
        short_state = state_id.rsplit(".", 1)[-1]
        route = _route_value(states.get(short_state), default_slot)
        if route:
            return route
    return _route_value(config, default_slot)


def resolve_presentation(intent: Mapping[str, Any], profile: Optional[Mapping[str, Any]] = None,
                         platform_behaviors: Optional[Mapping[str, Any]] = None, raw_state=None) -> Dict[str, Any]:
    """Resolve one intent independently for each presentation channel."""
    intent = intent if isinstance(intent, Mapping) else {}
    profile = profile if isinstance(profile, Mapping) else {}
    # The user-facing profile can turn the platform library off without
    # changing the wire contract.  In that mode every channel deliberately
    # reaches the static safe fallback path.
    library_mode = str(profile.get("behavior_library") or "industrial.default").strip()
    library_disabled = library_mode in {"safe_fallback", "none", "disabled"}
    if library_disabled:
        registry = {channel: {} for channel in PRESENTATION_CHANNELS}
        platform_modifiers = {}
    else:
        registry = platform_behaviors if isinstance(platform_behaviors, Mapping) else DEFAULT_PLATFORM_BEHAVIORS
        platform_modifiers = (
            DEFAULT_PLATFORM_MODIFIERS
            if platform_behaviors is None
            else (registry.get("modifiers", {}) if isinstance(registry, Mapping) else {})
        )
    state_value = intent.get("primary_state") or {}
    state_id = state_value.get("id") if isinstance(state_value, Mapping) else str(state_value)
    state_id = _clean_id(state_id, "industrial.machine.idle")
    modifiers = [item for item in intent.get("modifiers", []) if isinstance(item, Mapping) and item.get("active", True)]
    def _modifier_sort_key(item: Mapping[str, Any]) -> Tuple[int, str]:
        try:
            priority = int(item.get("priority", 0))
        except (TypeError, ValueError):
            priority = 0
        return (-priority, str(item.get("id", "")))
    modifiers.sort(key=_modifier_sort_key)

    resolved = {}
    diagnostics = []
    for channel in PRESENTATION_CHANNELS:
        channel_modifier_ids = [
            str(item.get("id")) for item in modifiers
            if not item.get("channels") or channel in item.get("channels", [])
        ]
        route = _project_route(profile, channel, state_id, channel_modifier_ids, raw_state)
        if route:
            # A profile route is a concrete type-level choice.  New 4.6
            # selections carry ``source``; old logical routes default to the
            # project source for backwards compatibility.
            source = route.get("source") or "project"
            if source == "ontotwin_common":
                source = "platform"
        if route is None:
            modifier_route = None
            for modifier_id in channel_modifier_ids:
                candidate_map = platform_modifiers.get(modifier_id, {}) if isinstance(platform_modifiers, Mapping) else {}
                modifier_route = _route_value(candidate_map.get(channel), SAFE_FALLBACKS[channel][1]) \
                    if isinstance(candidate_map, Mapping) else None
                if modifier_route:
                    break
            if modifier_route:
                route = modifier_route
                source = "platform"
        if route is None:
            state_map = registry.get(channel, {}) if isinstance(registry, Mapping) else {}
            candidate = state_map.get(state_id) if isinstance(state_map, Mapping) else None
            route = _route_value(candidate, SAFE_FALLBACKS[channel][1])
            if route:
                source = "platform"
        if route is None:
            route = {"behavior_id": SAFE_FALLBACKS[channel][0], "slot": SAFE_FALLBACKS[channel][1]}
            source = "safe_fallback"
        status = "fallback" if source == "safe_fallback" else "resolved"
        resolved_channel = {
            "source": source,
            "behavior_id": route["behavior_id"],
            "slot": route["slot"],
            "status": status,
            "primary_state": state_id,
            "modifier_ids": channel_modifier_ids,
        }
        for key in ("resource_id", "revision", "params"):
            if key in route:
                resolved_channel[key] = route[key]
        resolved[channel] = resolved_channel
        if status == "fallback":
            diagnostics.append({
                "code": "presentation.safe_fallback",
                "channel": channel,
                "message": "未找到项目或平台执行器，使用静态安全回退。",
            })

    return {
        "channels": resolved,
        "diagnostics": diagnostics,
    }


def build_presentation(instance_id: str, raw_state: Optional[Mapping[str, Any]],
                       profile: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
    """Build the wire-level I3D_Presentation payload."""
    profile = profile if isinstance(profile, Mapping) else {}
    profile_version = profile.get("normalization_profile") or profile.get("profile_version") \
        or INDUSTRIAL_PROFILE_VERSION
    intent = normalize_industrial(raw_state, instance_id, profile_version)
    resolution = resolve_presentation(intent, profile, raw_state=raw_state)
    payload = dict(intent)
    payload["resolution"] = resolution
    return payload


def profile_from_object_type(object_type: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    """Read a profile without requiring a new top-level persistence shape.

    ``presentation_profile`` is preferred when present.  The existing
    ``interface_configs`` extension point remains supported so old ProjectStore
    files do not need a migration.
    """
    if not isinstance(object_type, Mapping):
        return {}
    direct = object_type.get("presentation_profile")
    if isinstance(direct, Mapping):
        return copy.deepcopy(dict(direct))
    configs = object_type.get("interface_configs")
    if isinstance(configs, Mapping):
        # New model stores dynamic behavior under its concrete capability
        # interface.  Keep reading the legacy parent key for old projects.
        value = configs.get("I3D_Behavioral")
        if isinstance(value, Mapping):
            profile = value.get("presentation_profile", value)
            if isinstance(profile, Mapping):
                return copy.deepcopy(dict(profile))
        value = configs.get("I3D_Presentation")
        if isinstance(value, Mapping):
            profile = value.get("presentation_profile", value)
            if isinstance(profile, Mapping):
                return copy.deepcopy(dict(profile))
    return {}


def profile_fingerprint(profile: Optional[Mapping[str, Any]]) -> str:
    value = profile if isinstance(profile, Mapping) else {}
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha1(encoded.encode("utf-8")).hexdigest()[:16]
