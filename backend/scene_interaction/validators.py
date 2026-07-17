import copy
import math


class SceneInteractionValidationError(ValueError):
    def __init__(self, errors):
        if isinstance(errors, str):
            errors = [{"path": "config", "message": errors}]
        self.errors = errors
        super().__init__("; ".join(item.get("message", "invalid") for item in errors))


def default_roaming_config():
    return {"enabled": False, "auto_enter": False}


def _error(errors, path, message):
    errors.append({"path": path, "message": message})


def _bool(value, path, errors, default=False):
    if value is None:
        return default
    if not isinstance(value, bool):
        _error(errors, path, "必须是布尔值")
        return default
    return value


def _number(value, path, errors, minimum=None, maximum=None, required=True, default=None):
    if value is None:
        if required:
            _error(errors, path, "不能为空")
        return default
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        _error(errors, path, "必须是有限数值")
        return default
    number = float(value)
    if minimum is not None and number < minimum:
        _error(errors, path, f"不能小于 {minimum}")
    if maximum is not None and number > maximum:
        _error(errors, path, f"不能大于 {maximum}")
    return number


def _resource(catalog, kind, resource_id, path, errors, required=True):
    resource_id = str(resource_id or "").strip()
    if not resource_id:
        if required:
            _error(errors, path, "必须选择资源")
        return None, None
    resource = catalog.get(kind, resource_id)
    if resource is None:
        _error(errors, path, "资源不在当前受控目录中")
    return resource_id, resource


def validate_roaming_config(config, catalog, project_routes=None):
    if not isinstance(config, dict):
        raise SceneInteractionValidationError("人物漫游配置必须是对象")

    errors = []
    result = copy.deepcopy(config)
    result["enabled"] = _bool(config.get("enabled"), "enabled", errors, False)
    result["auto_enter"] = _bool(config.get("auto_enter"), "auto_enter", errors, False)

    character_id, character = _resource(
        catalog, "characters", config.get("character_id"), "character_id", errors,
        required=result["enabled"],
    )
    if character_id:
        result["character_id"] = character_id

    allowed = config.get("allowed_skin_ids", [])
    if not isinstance(allowed, list):
        _error(errors, "allowed_skin_ids", "必须是皮肤 ID 数组")
        allowed = []
    normalized_allowed = []
    for index, value in enumerate(allowed):
        skin_id, skin = _resource(catalog, "skins", value, f"allowed_skin_ids[{index}]", errors)
        if not skin_id or skin_id in normalized_allowed:
            continue
        normalized_allowed.append(skin_id)
        if character and skin:
            if skin.get("character_id") != character_id:
                _error(errors, f"allowed_skin_ids[{index}]", "皮肤不属于当前基础人物")
            if skin.get("skeleton_id") != character.get("skeleton_id"):
                _error(errors, f"allowed_skin_ids[{index}]", "皮肤 Skeleton 与基础人物不一致")
    result["allowed_skin_ids"] = normalized_allowed

    default_skin_id, default_skin = _resource(
        catalog, "skins", config.get("default_skin_id"), "default_skin_id", errors,
        required=result["enabled"],
    )
    if default_skin_id:
        result["default_skin_id"] = default_skin_id
        if default_skin_id not in normalized_allowed:
            _error(errors, "default_skin_id", "默认皮肤必须包含在允许皮肤中")
        if character and default_skin:
            if default_skin.get("character_id") != character_id:
                _error(errors, "default_skin_id", "默认皮肤不属于当前基础人物")
            if default_skin.get("skeleton_id") != character.get("skeleton_id"):
                _error(errors, "default_skin_id", "默认皮肤 Skeleton 与基础人物不一致")

    spawn = config.get("spawn")
    if result["enabled"] and not isinstance(spawn, dict):
        _error(errors, "spawn", "启用人物漫游前必须配置出生点")
    elif isinstance(spawn, dict):
        inferred_mode = "image" if spawn.get("frame_id") else ""
        mode = str(spawn.get("mode") or inferred_mode).strip()
        if mode == "ue_anchor":
            anchor_id, _ = _resource(
                catalog, "spawn_anchors", spawn.get("anchor_id"),
                "spawn.anchor_id", errors, required=result["enabled"],
            )
            result["spawn"] = {
                "mode": "ue_anchor",
                "anchor_id": anchor_id or "",
            }
        elif mode == "image":
            normalized_spawn = copy.deepcopy(spawn)
            normalized_spawn["mode"] = "image"
            normalized_spawn["frame_id"] = str(spawn.get("frame_id") or "").strip()
            if not normalized_spawn["frame_id"]:
                _error(errors, "spawn.frame_id", "必须引用一个已标定图片 Frame")
            position = spawn.get("canonical_position_mm")
            if not isinstance(position, dict):
                _error(errors, "spawn.canonical_position_mm", "缺少规范坐标")
            else:
                normalized_spawn["canonical_position_mm"] = {
                    "x": _number(position.get("x"), "spawn.canonical_position_mm.x", errors),
                    "y": _number(position.get("y"), "spawn.canonical_position_mm.y", errors),
                }
            source_px = spawn.get("source_px")
            if source_px is not None:
                if not isinstance(source_px, dict):
                    _error(errors, "spawn.source_px", "必须是像素坐标对象")
                else:
                    normalized_spawn["source_px"] = {
                        "x": _number(source_px.get("x"), "spawn.source_px.x", errors),
                        "y": _number(source_px.get("y"), "spawn.source_px.y", errors),
                    }
            normalized_spawn["yaw_deg"] = _number(
                spawn.get("yaw_deg"), "spawn.yaw_deg", errors,
                minimum=-360.0, maximum=360.0, required=False, default=0.0,
            )
            normalized_spawn["z_hint_mm"] = _number(
                spawn.get("z_hint_mm"), "spawn.z_hint_mm", errors,
                minimum=-1000000.0, maximum=1000000.0, required=False, default=None,
            )
            fingerprint = str(spawn.get("calibration_fingerprint") or "").strip()
            if not fingerprint:
                _error(errors, "spawn.calibration_fingerprint", "缺少标定指纹")
            normalized_spawn["calibration_fingerprint"] = fingerprint
            result["spawn"] = normalized_spawn
        else:
            _error(errors, "spawn.mode", "只支持 ue_anchor 或 image")

    camera = config.get("camera")
    if result["enabled"] and not isinstance(camera, dict):
        _error(errors, "camera", "启用人物漫游前必须配置视角")
    elif isinstance(camera, dict):
        normalized_camera = copy.deepcopy(camera)
        default_mode = str(camera.get("default_mode") or "near_follow")
        if default_mode not in ("near_follow", "god"):
            _error(errors, "camera.default_mode", "只支持 near_follow 或 god")
            default_mode = "near_follow"
        normalized_camera["default_mode"] = default_mode

        near = camera.get("near_follow") or {}
        if not isinstance(near, dict):
            _error(errors, "camera.near_follow", "必须是对象")
            near = {}
        normalized_camera["near_follow"] = {
            "distance_cm": _number(near.get("distance_cm"), "camera.near_follow.distance_cm", errors, 20, 500, default=120),
            "height_cm": _number(near.get("height_cm"), "camera.near_follow.height_cm", errors, -50, 250, default=35),
            "look_sensitivity": _number(near.get("look_sensitivity"), "camera.near_follow.look_sensitivity", errors, 0.1, 5, default=1),
        }

        god = camera.get("god") or {}
        if not isinstance(god, dict):
            _error(errors, "camera.god", "必须是对象")
            god = {}
        camera_id, _ = _resource(catalog, "god_cameras", god.get("camera_id"), "camera.god.camera_id", errors)
        normalized_camera["god"] = {
            "camera_id": camera_id or "",
            "move_speed_cm_s": _number(god.get("move_speed_cm_s"), "camera.god.move_speed_cm_s", errors, 100, 10000, default=1800),
            "look_sensitivity": _number(god.get("look_sensitivity"), "camera.god.look_sensitivity", errors, 0.1, 5, default=1),
        }
        result["camera"] = normalized_camera

    movement = config.get("movement")
    if result["enabled"] and not isinstance(movement, dict):
        _error(errors, "movement", "启用人物漫游前必须配置移动参数")
    elif isinstance(movement, dict):
        walk = _number(movement.get("walk_speed_cm_s"), "movement.walk_speed_cm_s", errors, 50, 800, default=250)
        sprint = _number(movement.get("sprint_speed_cm_s"), "movement.sprint_speed_cm_s", errors, 100, 1500, default=500)
        if walk is not None and sprint is not None and sprint < walk:
            _error(errors, "movement.sprint_speed_cm_s", "奔跑速度不能小于行走速度")
        result["movement"] = {
            "walk_speed_cm_s": walk,
            "sprint_speed_cm_s": sprint,
            "auto_route_speed_cm_s": _number(movement.get("auto_route_speed_cm_s"), "movement.auto_route_speed_cm_s", errors, 20, 800, default=180),
            "jump_height_cm": _number(movement.get("jump_height_cm"), "movement.jump_height_cm", errors, 0, 300, default=80),
        }

    route = config.get("route")
    if result["enabled"] and not isinstance(route, dict):
        _error(errors, "route", "启用人物漫游前必须配置默认路线规则")
    elif isinstance(route, dict):
        route_enabled = _bool(route.get("enabled"), "route.enabled", errors, True)
        route_id = str(route.get("route_id") or "").strip()
        project_route = next(
            (item for item in (project_routes or []) if item.get("id") == route_id),
            None,
        )
        if route_enabled and not route_id:
            _error(errors, "route.route_id", "必须选择资源")
        elif route_id and project_route is not None:
            if project_route.get("review_state") != "ready":
                _error(errors, "route.route_id", "项目路线尚未就绪或需要复核")
            if not project_route.get("enabled", True):
                _error(errors, "route.route_id", "项目路线当前未启用")
        elif route_id and catalog.get("routes", route_id) is None:
            _error(errors, "route.route_id", "路线不在当前项目或受控资源目录中")
        completion = str(route.get("completion_mode") or "stop")
        if completion not in ("stop", "loop"):
            _error(errors, "route.completion_mode", "只支持 stop 或 loop")
            completion = "stop"
        result["route"] = {
            "enabled": route_enabled,
            "route_id": route_id or "",
            "auto_start": _bool(route.get("auto_start"), "route.auto_start", errors, True),
            "completion_mode": completion,
            "takeover_enabled": _bool(route.get("takeover_enabled"), "route.takeover_enabled", errors, True),
        }

    if errors:
        raise SceneInteractionValidationError(errors)
    return result


ALLOWED_RUNTIME_STATES = {
    "disabled", "available", "starting", "auto_route", "manual", "god_view",
    "ui_interaction", "reload_required", "degraded", "blocked", "offline",
}

ALLOWED_REALTIME_CONNECTION_STATES = {
    "disabled", "connecting", "connected", "reconnecting", "disconnected", "error",
}
ALLOWED_REALTIME_ACTIVE_SOURCES = {"none", "http_snapshot", "websocket"}


def _validate_realtime_channel(value, errors):
    if value is None:
        return None
    if not isinstance(value, dict):
        _error(errors, "realtime_channel", "必须是对象或 null")
        return None

    enabled = value.get("enabled")
    if not isinstance(enabled, bool):
        _error(errors, "realtime_channel.enabled", "必须是布尔值")
        enabled = False

    connection_state = str(value.get("connection_state") or "").strip().lower()
    if connection_state not in ALLOWED_REALTIME_CONNECTION_STATES:
        _error(errors, "realtime_channel.connection_state", "未知连接状态")

    active_source = str(value.get("active_source") or "").strip().lower()
    if active_source not in ALLOWED_REALTIME_ACTIVE_SOURCES:
        _error(errors, "realtime_channel.active_source", "未知活动数据源")

    last_frame_age_ms = value.get("last_frame_age_ms")
    if (
        last_frame_age_ms is not None
        and (
            isinstance(last_frame_age_ms, bool)
            or not isinstance(last_frame_age_ms, (int, float))
            or last_frame_age_ms < 0
        )
    ):
        _error(errors, "realtime_channel.last_frame_age_ms", "必须是非负数或 null")
        last_frame_age_ms = None

    integer_fields = {}
    for field in ("frame_count", "source_timestamp_ms", "target_count", "applied_target_count"):
        field_value = value.get(field, 0)
        if (
            isinstance(field_value, bool)
            or not isinstance(field_value, (int, float))
            or field_value < 0
            or int(field_value) != field_value
        ):
            _error(errors, f"realtime_channel.{field}", "必须是非负整数")
            field_value = 0
        integer_fields[field] = int(field_value)

    raw_targets = value.get("targets") or []
    targets = []
    if not isinstance(raw_targets, list):
        _error(errors, "realtime_channel.targets", "必须是数组")
        raw_targets = []
    for index, target in enumerate(raw_targets):
        path = f"realtime_channel.targets[{index}]"
        if not isinstance(target, dict):
            _error(errors, path, "必须是对象")
            continue
        forbidden = {"position", "world_position", "location", "x", "y", "z"}.intersection(target)
        if forbidden:
            _error(errors, f"{path}.{sorted(forbidden)[0]}", "实时心跳禁止上传目标坐标")
        instance_id = str(target.get("instance_id") or "").strip()
        if not instance_id:
            _error(errors, f"{path}.instance_id", "不能为空")
        state = str(target.get("state") or "unknown").strip().lower()[:64]
        applied = target.get("applied")
        if not isinstance(applied, bool):
            _error(errors, f"{path}.applied", "必须是布尔值")
            applied = False
        targets.append({
            "instance_id": instance_id[:256],
            "state": state,
            "applied": applied,
        })

    error = value.get("error") or ""
    if not isinstance(error, str):
        _error(errors, "realtime_channel.error", "必须是字符串")
        error = ""

    return {
        "enabled": enabled,
        "connection_state": connection_state,
        "active_source": active_source,
        "last_frame_age_ms": last_frame_age_ms,
        **integer_fields,
        "targets": targets,
        "error": error[:500],
    }


def validate_runtime_status(payload):
    if not isinstance(payload, dict):
        raise SceneInteractionValidationError("运行状态必须是对象")
    forbidden = {"position", "world_position", "character_position", "location"}.intersection(payload)
    if forbidden:
        raise SceneInteractionValidationError([{
            "path": sorted(forbidden)[0],
            "message": "运行心跳禁止上传人物位置",
        }])
    errors = []
    state = str(payload.get("runtime_state") or "").strip()
    if state not in ALLOWED_RUNTIME_STATES:
        _error(errors, "runtime_state", "未知运行状态")
    applied = payload.get("applied_revision")
    pending = payload.get("pending_revision")
    for value, path in ((applied, "applied_revision"), (pending, "pending_revision")):
        if value is not None and (isinstance(value, bool) or not isinstance(value, int) or value < 0):
            _error(errors, path, "必须是非负整数或 null")
    degraded = payload.get("degraded_features") or []
    if not isinstance(degraded, list) or any(not isinstance(item, str) for item in degraded):
        _error(errors, "degraded_features", "必须是字符串数组")
        degraded = []
    error = payload.get("error")
    if error is not None and not isinstance(error, dict):
        _error(errors, "error", "必须是对象或 null")
        error = None
    realtime_channel = _validate_realtime_channel(payload.get("realtime_channel"), errors)
    if errors:
        raise SceneInteractionValidationError(errors)
    return {
        "applied_revision": applied,
        "pending_revision": pending,
        "catalog_version": str(payload.get("catalog_version") or ""),
        "runtime_state": state,
        "camera_mode": str(payload.get("camera_mode") or ""),
        "route_state": str(payload.get("route_state") or ""),
        "active_skin_id": str(payload.get("active_skin_id") or ""),
        "degraded_features": list(dict.fromkeys(degraded)),
        "error": copy.deepcopy(error),
        "realtime_channel": realtime_channel,
    }
