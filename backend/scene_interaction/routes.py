import copy
import datetime
import hashlib
import json
import math
import uuid

from coord_transform import apply_transform, build_ue_matrix, canonical_to_ue, invert_affine

from .narration import (
    DEFAULT_NARRATION_SETTINGS,
    effective_voice_profile,
    normalize_project_defaults,
    normalize_route_profile,
    normalize_waypoint_narration,
    runtime_narration,
)
from .validators import SceneInteractionValidationError


def _utc_now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")


def _error(errors, path, message):
    errors.append({"path": path, "message": message})


def _finite(value, path, errors):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        _error(errors, path, "必须是有限数值")
        return None
    value = float(value)
    if not math.isfinite(value):
        _error(errors, path, "必须是有限数值")
        return None
    return value


def _find_frame(project, frame_id):
    for frame in project.get("frames") or []:
        if isinstance(frame, dict) and frame.get("id") == frame_id:
            return frame
    return None


def _find_floor(project, frame):
    floor_id = str(frame.get("floor_id") or f"floor-{frame.get('floor') or 1}")
    for floor in (project.get("spatial_profile") or {}).get("floor_table") or []:
        if not isinstance(floor, dict):
            continue
        if floor.get("floor_id") == floor_id or floor.get("floor") == frame.get("floor"):
            return floor
    return None


def _matrix(frame, key):
    value = frame.get(key)
    if isinstance(value, dict):
        value = value.get("matrix")
    if not isinstance(value, list) or len(value) < 2:
        return None
    try:
        return [
            [float(value[0][0]), float(value[0][1]), float(value[0][2])],
            [float(value[1][0]), float(value[1][1]), float(value[1][2])],
            [0.0, 0.0, 1.0],
        ]
    except (IndexError, TypeError, ValueError):
        return None


def _multiply_affine(left, right):
    return [
        [
            left[0][0] * right[0][0] + left[0][1] * right[1][0],
            left[0][0] * right[0][1] + left[0][1] * right[1][1],
            left[0][0] * right[0][2] + left[0][1] * right[1][2] + left[0][2],
        ],
        [
            left[1][0] * right[0][0] + left[1][1] * right[1][0],
            left[1][0] * right[0][1] + left[1][1] * right[1][1],
            left[1][0] * right[0][2] + left[1][1] * right[1][2] + left[1][2],
        ],
        [0.0, 0.0, 1.0],
    ]


def route_projection_material(project, frame):
    frame_to_ue = _matrix(frame or {}, "to_ue")
    if not frame_to_ue:
        return None
    canonical_to_ue_matrix = build_ue_matrix(project.get("spatial_profile") or {})
    ue_to_canonical = invert_affine(canonical_to_ue_matrix)
    if ue_to_canonical is None:
        return None
    floor = _find_floor(project, frame)
    material = {
        "frame_id": frame.get("id"),
        "frame_calibration_fingerprint": str(frame.get("calibration_fingerprint") or ""),
        "frame_to_ue": frame_to_ue,
        "canonical_to_ue": canonical_to_ue_matrix,
        "floor": {
            "floor_id": (floor or {}).get("floor_id"),
            "ue_ground_z_cm": (floor or {}).get("ue_ground_z_cm"),
            "ue_level": frame.get("ue_level"),
        },
    }
    serialized = json.dumps(material, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return {
        "fingerprint": "sha256:" + hashlib.sha256(serialized.encode("utf-8")).hexdigest(),
        "to_canonical": _multiply_affine(ue_to_canonical, frame_to_ue),
    }


def route_review_state(project, route):
    if not isinstance(route, dict):
        return "invalid"
    frame = _find_frame(project, route.get("frame_id"))
    if not frame or frame.get("kind") != "image" or frame.get("status") != "published":
        return "invalid"
    waypoints = route.get("waypoints")
    if not isinstance(waypoints, list) or len(waypoints) < 2:
        return "invalid"
    current_fingerprint = str(frame.get("calibration_fingerprint") or "")
    projection = route_projection_material(project, frame)
    if not projection:
        return "invalid"
    if (
        not current_fingerprint
        or str(route.get("calibration_fingerprint") or "") != current_fingerprint
        or str(route.get("projection_fingerprint") or "") != projection["fingerprint"]
    ):
        return "needs_review"
    floor = _find_floor(project, frame)
    if not floor or floor.get("ue_ground_z_cm") is None:
        return "invalid"
    return "ready"


def public_route(project, route, include_waypoints=True):
    value = copy.deepcopy(route)
    value["review_state"] = route_review_state(project, route)
    if not include_waypoints:
        value.pop("waypoints", None)
        value["waypoint_count"] = len(route.get("waypoints") or [])
        narrations = [
            item.get("narration") for item in route.get("waypoints") or []
            if isinstance(item, dict)
            and isinstance(item.get("narration"), dict)
            and item["narration"].get("enabled")
        ]
        value["narration_count"] = len(narrations)
        value["narration_generation_state"] = (
            "failed" if any(item.get("generation_state") == "failed" for item in narrations)
            else "pending" if any(item.get("generation_state") == "pending" for item in narrations)
            else "available" if narrations else "none"
        )
    return value


def list_project_routes(project, include_waypoints=False):
    return [
        public_route(project, route, include_waypoints=include_waypoints)
        for route in (project.get("scene_interactions") or {}).get("routes") or []
        if isinstance(route, dict)
    ]


def find_project_route(project, route_id):
    for route in (project.get("scene_interactions") or {}).get("routes") or []:
        if isinstance(route, dict) and route.get("id") == route_id:
            return route
    return None


def normalize_route(project, payload, current=None):
    if not isinstance(payload, dict):
        raise SceneInteractionValidationError([{"path": "route", "message": "路线配置必须是对象"}])

    errors = []
    name = str(payload.get("name") or "").strip()
    if not name:
        _error(errors, "name", "请填写路线名称")
    elif len(name) > 80:
        _error(errors, "name", "路线名称不能超过 80 个字符")

    frame_id = str(payload.get("frame_id") or "").strip()
    frame = _find_frame(project, frame_id)
    if not frame or frame.get("kind") != "image" or not isinstance(frame.get("image"), dict):
        _error(errors, "frame_id", "请选择当前项目中的空间底图")
        frame = None
    elif frame.get("status") != "published":
        _error(errors, "frame_id", "路线只能使用已发布的空间底图")

    dataset = project.get("dataset") or {}
    if frame:
        bound_project = str(dataset.get("bound_ue_project_id") or "")
        frame_project = str(frame.get("bound_ue_project_id") or "")
        if bound_project and frame_project and bound_project != frame_project:
            _error(errors, "frame_id", "空间底图绑定的 UE 项目与当前项目不一致")
        if not str(frame.get("ue_level") or "").strip():
            _error(errors, "frame_id", "空间底图缺少运行关卡绑定")
        if not str(frame.get("calibration_fingerprint") or "").strip():
            _error(errors, "frame_id", "空间底图缺少已发布标定指纹")

    floor = _find_floor(project, frame) if frame else None
    if frame and not floor:
        _error(errors, "frame_id", "空间底图引用的楼层不存在")
    elif floor and floor.get("ue_ground_z_cm") is None:
        _error(errors, "frame_id", "该楼层尚未确认 UE 地面高度")

    scene = project.get("scene_interactions") or {}
    narration_defaults = normalize_project_defaults(
        scene.get("narration_defaults") or DEFAULT_NARRATION_SETTINGS,
        errors,
    )
    raw_route_profile = (
        payload.get("narration_profile")
        if "narration_profile" in payload
        else (current or {}).get("narration_profile")
    )
    narration_profile = normalize_route_profile(raw_route_profile, errors)
    voice_profile = effective_voice_profile(narration_defaults, narration_profile)

    raw_waypoints = payload.get("waypoints")
    if not isinstance(raw_waypoints, list):
        _error(errors, "waypoints", "路线点必须是数组")
        raw_waypoints = []
    if len(raw_waypoints) < 2:
        _error(errors, "waypoints", "路线至少需要 2 个点")
    if len(raw_waypoints) > 200:
        _error(errors, "waypoints", "单条路线最多支持 200 个点")

    width = float(((frame or {}).get("image") or {}).get("width_px") or 0)
    height = float(((frame or {}).get("image") or {}).get("height_px") or 0)
    projection = route_projection_material(project, frame) if frame else None
    to_canonical = (projection or {}).get("to_canonical")
    if frame and not projection:
        _error(errors, "frame_id", "空间底图缺少可用的规范坐标变换")
    z_base = float((floor or {}).get("z_base_mm") or 0.0)
    waypoints = []
    seen_ids = set()
    current_waypoints = {
        str(item.get("id")): item
        for item in (current or {}).get("waypoints") or []
        if isinstance(item, dict) and item.get("id")
    }
    for index, item in enumerate(raw_waypoints):
        if not isinstance(item, dict):
            _error(errors, f"waypoints[{index}]", "路线点必须是对象")
            continue
        source = item.get("source_px")
        if isinstance(source, dict):
            source = [source.get("x"), source.get("y")]
        if not isinstance(source, (list, tuple)) or len(source) < 2:
            _error(errors, f"waypoints[{index}].source_px", "缺少图片像素坐标")
            continue
        x = _finite(source[0], f"waypoints[{index}].source_px[0]", errors)
        y = _finite(source[1], f"waypoints[{index}].source_px[1]", errors)
        if x is None or y is None:
            continue
        if width and (x < 0 or x > width):
            _error(errors, f"waypoints[{index}].source_px[0]", "路线点超出图片范围")
        if height and (y < 0 or y > height):
            _error(errors, f"waypoints[{index}].source_px[1]", "路线点超出图片范围")
        canonical = apply_transform(to_canonical, [x, y]) if to_canonical else [0.0, 0.0]
        waypoint_id = str(item.get("id") or f"wp-{index + 1}").strip() or f"wp-{index + 1}"
        if waypoint_id in seen_ids:
            waypoint_id = f"wp-{index + 1}"
        seen_ids.add(waypoint_id)
        current_waypoint = current_waypoints.get(waypoint_id) or {}
        raw_narration = (
            item.get("narration")
            if "narration" in item
            else current_waypoint.get("narration")
        )
        narration = normalize_waypoint_narration(
            raw_narration,
            current_waypoint.get("narration"),
            voice_profile,
            errors,
            f"waypoints[{index}].narration",
        )
        waypoint = {
            "id": waypoint_id,
            "order": index + 1,
            "source_px": [round(x, 3), round(y, 3)],
            "canonical_position_mm": [
                round(float(canonical[0]), 3),
                round(float(canonical[1]), 3),
                round(z_base, 3),
            ],
        }
        if narration is not None:
            waypoint["narration"] = narration
        waypoints.append(waypoint)

    if len(waypoints) >= 2:
        distinct = any(
            math.hypot(
                waypoints[index]["source_px"][0] - waypoints[0]["source_px"][0],
                waypoints[index]["source_px"][1] - waypoints[0]["source_px"][1],
            ) > 0.01
            for index in range(1, len(waypoints))
        )
        if not distinct:
            _error(errors, "waypoints", "路线至少需要 2 个不同位置的点")

    speed = _finite(payload.get("speed_cm_s", 150), "speed_cm_s", errors)
    if speed is not None and not 20 <= speed <= 800:
        _error(errors, "speed_cm_s", "路线速度必须在 20–800 cm/s 之间")
    loop = payload.get("loop", False)
    enabled = payload.get("enabled", True)
    if not isinstance(loop, bool):
        _error(errors, "loop", "循环设置必须是布尔值")
    if not isinstance(enabled, bool):
        _error(errors, "enabled", "启用设置必须是布尔值")

    if errors:
        raise SceneInteractionValidationError(errors)

    now = _utc_now()
    route_id = (current or {}).get("id") or ("route." + uuid.uuid4().hex[:16])
    return {
        "id": route_id,
        "name": name,
        "enabled": enabled,
        "frame_id": frame_id,
        "calibration_revision": int(frame.get("calibration_revision") or 0),
        "calibration_fingerprint": str(frame.get("calibration_fingerprint") or ""),
        "projection_fingerprint": projection["fingerprint"],
        "floor_id": str(frame.get("floor_id") or f"floor-{frame.get('floor') or 1}"),
        "z_policy": "project_to_walkable_ground",
        "loop": loop,
        "speed_cm_s": round(speed, 3),
        "narration_profile": narration_profile,
        "review_state": "ready",
        "waypoints": waypoints,
        "revision": int((current or {}).get("revision") or 0) + 1,
        "created_at": (current or {}).get("created_at") or now,
        "updated_at": now,
    }


def runtime_route_projection(project, route):
    state = route_review_state(project, route)
    if state != "ready" or not route.get("enabled", True):
        return None, state
    frame = _find_frame(project, route.get("frame_id"))
    floor = _find_floor(project, frame)
    floor_number = int(frame.get("floor") or 1)
    ground_z = float(floor.get("ue_ground_z_cm"))
    points = []
    runtime_waypoints = []
    scene = project.get("scene_interactions") or {}
    voice_profile = effective_voice_profile(
        scene.get("narration_defaults") or DEFAULT_NARRATION_SETTINGS,
        route.get("narration_profile"),
    )
    default_trigger_radius = float(voice_profile.get("trigger_radius_cm") or 100.0)
    for waypoint in route.get("waypoints") or []:
        canonical = waypoint.get("canonical_position_mm") or []
        ue = canonical_to_ue(
            project.get("spatial_profile") or {},
            [float(canonical[0]), float(canonical[1])],
            floor=floor_number,
        )
        point = [round(ue[0], 3), round(ue[1], 3), round(ground_z, 3)]
        points.append(point)
        runtime_waypoint = {
            "waypoint_id": str(waypoint.get("id") or ""),
            "position_ue_cm": point,
        }
        narration = runtime_narration(
            waypoint.get("narration"), default_trigger_radius
        )
        if narration:
            runtime_waypoint["trigger_radius_cm"] = narration.pop("trigger_radius_cm")
            runtime_waypoint["narration"] = narration
        runtime_waypoints.append(runtime_waypoint)
    return {
        "route_id": route.get("id"),
        "route_revision": int(route.get("revision") or 0),
        "loop": bool(route.get("loop")),
        "speed_cm_s": float(route.get("speed_cm_s") or 150.0),
        "z_policy": "project_to_walkable_ground",
        "floor_id": route.get("floor_id"),
        "floor_ground_z_hint_cm": round(ground_z, 3),
        "ue_level": frame.get("ue_level"),
        "waypoints_ue_cm": points,
        "waypoints": runtime_waypoints,
    }, state
