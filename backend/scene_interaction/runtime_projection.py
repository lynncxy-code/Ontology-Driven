import copy
import hashlib
import json
import math

from coord_transform import apply_transform, build_ue_matrix, canonical_to_ue, invert_affine

from .routes import find_project_route, runtime_route_projection


class RuntimeProjectionError(ValueError):
    def __init__(self, code, message):
        self.code = code
        super().__init__(message)


def _matrix_from_frame(frame):
    value = (frame or {}).get("to_ue")
    if isinstance(value, dict):
        value = value.get("matrix")
    if not isinstance(value, list) or len(value) < 2:
        raise RuntimeProjectionError("frame_not_calibrated", "图片 Frame 缺少可用的 to_ue 标定矩阵")
    try:
        matrix = [
            [float(value[0][0]), float(value[0][1]), float(value[0][2])],
            [float(value[1][0]), float(value[1][1]), float(value[1][2])],
            [0.0, 0.0, 1.0],
        ]
    except (IndexError, TypeError, ValueError) as exc:
        raise RuntimeProjectionError("frame_not_calibrated", "图片 Frame 标定矩阵格式非法") from exc
    if invert_affine(matrix) is None:
        raise RuntimeProjectionError("frame_matrix_singular", "图片 Frame 标定矩阵不可逆")
    return matrix


def _find_frame(project, frame_id):
    for frame in project.get("frames") or []:
        if frame.get("id") == frame_id:
            return frame
    raise RuntimeProjectionError("frame_not_found", "当前项目中找不到出生点引用的图片 Frame")


def calibration_material(project, frame_id):
    frame = _find_frame(project, frame_id)
    frame_to_ue = _matrix_from_frame(frame)
    canonical_to_ue_matrix = build_ue_matrix(project.get("spatial_profile") or {})
    ue_to_canonical = invert_affine(canonical_to_ue_matrix)
    if ue_to_canonical is None:
        raise RuntimeProjectionError("canonical_matrix_singular", "项目规范坐标到 UE 的矩阵不可逆")
    material = {
        "frame_id": frame_id,
        "frame_to_ue": frame_to_ue,
        "canonical_to_ue": canonical_to_ue_matrix,
    }
    serialized = json.dumps(material, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    fingerprint = "sha256:" + hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    return frame, frame_to_ue, ue_to_canonical, fingerprint


def prepare_spawn_for_save(project, spawn):
    if not isinstance(spawn, dict):
        return spawn
    result = copy.deepcopy(spawn)
    if result.get("mode") == "ue_anchor":
        return {
            "mode": "ue_anchor",
            "anchor_id": str(result.get("anchor_id") or "").strip(),
        }
    frame_id = str(result.get("frame_id") or "").strip()
    if not frame_id:
        return result
    _, frame_to_ue, ue_to_canonical, fingerprint = calibration_material(project, frame_id)
    source = result.get("source_px")
    if isinstance(source, dict) and source.get("x") is not None and source.get("y") is not None:
        ue_xy = apply_transform(frame_to_ue, [float(source["x"]), float(source["y"])])
        canonical_xy = apply_transform(ue_to_canonical, ue_xy)
        result["source_px"] = {"x": float(source["x"]), "y": float(source["y"])}
        result["canonical_position_mm"] = {"x": canonical_xy[0], "y": canonical_xy[1]}
    result["calibration_fingerprint"] = fingerprint
    return result


def calibration_state(project, spawn):
    if isinstance(spawn, dict) and spawn.get("mode") == "ue_anchor":
        return {"state": "not_required", "current_fingerprint": None}
    if not isinstance(spawn, dict) or not spawn.get("frame_id"):
        return {"state": "missing", "current_fingerprint": None}
    try:
        _, _, _, fingerprint = calibration_material(project, spawn.get("frame_id"))
    except RuntimeProjectionError as exc:
        return {"state": "invalid", "current_fingerprint": None, "error": {"code": exc.code, "message": str(exc)}}
    stored = str(spawn.get("calibration_fingerprint") or "")
    return {
        "state": "valid" if stored and stored == fingerprint else "needs_review",
        "current_fingerprint": fingerprint,
    }


def _yaw_to_ue(matrix, canonical_yaw_deg):
    radians = math.radians(float(canonical_yaw_deg or 0.0))
    x = math.cos(radians)
    y = math.sin(radians)
    ue_x = matrix[0][0] * x + matrix[0][1] * y
    ue_y = matrix[1][0] * x + matrix[1][1] * y
    if abs(ue_x) < 1e-12 and abs(ue_y) < 1e-12:
        return 0.0
    return round(math.degrees(math.atan2(ue_y, ue_x)), 3)


def _floor_for_frame(frame):
    try:
        return int(frame.get("floor") or 1)
    except (TypeError, ValueError):
        return 1


def _selected_resources(project, config, catalog, projected_route=None):
    resources = {
        "character": catalog.get("characters", config.get("character_id")),
        "skins": [
            value for value in (
                catalog.get("skins", skin_id) for skin_id in config.get("allowed_skin_ids") or []
            ) if value
        ],
        "spawn_anchor": None,
        "route": None,
        "god_camera": None,
    }
    spawn = config.get("spawn") or {}
    if spawn.get("mode") == "ue_anchor" and spawn.get("anchor_id"):
        resources["spawn_anchor"] = catalog.get("spawn_anchors", spawn.get("anchor_id"))
    route = config.get("route") or {}
    if route.get("enabled") and route.get("route_id"):
        project_route = find_project_route(project, route.get("route_id"))
        if project_route:
            resources["route"] = {
                "id": project_route.get("id"),
                "display_name": project_route.get("name"),
                "kind": "project_route",
                "route_revision": project_route.get("revision"),
                "runtime_ready": projected_route is not None,
            }
        else:
            resources["route"] = catalog.get("routes", route.get("route_id"))
    god = ((config.get("camera") or {}).get("god") or {})
    if god.get("camera_id"):
        resources["god_camera"] = catalog.get("god_cameras", god.get("camera_id"))
    return resources


def _route_start_spawn(project, route, projected_route):
    points = (projected_route or {}).get("waypoints_ue_cm") or []
    if len(points) < 2:
        raise RuntimeProjectionError(
            "route_start_missing",
            "默认项目路线缺少可用于人物出生的起点和方向",
        )
    first = points[0]
    second = points[1]
    dx = float(second[0]) - float(first[0])
    dy = float(second[1]) - float(first[1])
    yaw = 0.0 if abs(dx) < 1e-12 and abs(dy) < 1e-12 else math.degrees(math.atan2(dy, dx))
    frame = _find_frame(project, route.get("frame_id"))
    return {
        "mode": "coordinates",
        "source": "route_start",
        "route_id": route.get("id"),
        "x_cm": round(float(first[0]), 3),
        "y_cm": round(float(first[1]), 3),
        "trace_origin_z_cm": round(float(first[2]) + 1000.0, 2),
        "yaw_deg": round(yaw, 3),
        "z_hint_cm": round(float(first[2]), 3),
        "floor": _floor_for_frame(frame),
    }


def _available_runtime_routes(project, default_route_id):
    result = []
    for route in (project.get("scene_interactions") or {}).get("routes") or []:
        if not isinstance(route, dict) or not route.get("enabled", True):
            continue
        projected, state = runtime_route_projection(project, route)
        if projected is None or state != "ready":
            continue
        item = copy.deepcopy(projected)
        item.update({
            "display_name": str(route.get("name") or route.get("id") or "漫游路线"),
            "is_default": route.get("id") == default_route_id,
        })
        result.append(item)
    return result


def build_runtime_projection(project, config, catalog, revision):
    result = copy.deepcopy(config)
    spawn = config.get("spawn") or {}
    projected_route = None
    route_config = config.get("route") or {}
    route_state = None
    project_route = None
    block_reason = None
    route_enabled = bool(config.get("enabled") and route_config.get("enabled"))
    route_id = str(route_config.get("route_id") or "").strip()
    if route_enabled:
        if not route_id:
            route_state = "missing"
            block_reason = "default_route_missing"
        else:
            project_route = find_project_route(project, route_id)
            if project_route:
                projected_route, route_state = runtime_route_projection(project, project_route)
                if projected_route is None:
                    block_reason = (
                        "default_route_needs_review"
                        if route_state == "needs_review"
                        else "default_route_invalid"
                    )
            elif catalog.get("routes", route_id) is None:
                route_state = "missing"
                block_reason = "default_route_missing"
        if block_reason:
            result.setdefault("route", {})["enabled"] = False

    if projected_route is not None:
        # Route spawn is independent of auto_start and does not require a
        # duplicate manual image point.
        spawn_mode = "route_start"
        state = {"state": "not_required", "current_fingerprint": None}
        result["spawn_ue"] = _route_start_spawn(project, project_route, projected_route)
    else:
        spawn_mode = spawn.get("mode") or ("image" if spawn.get("frame_id") else "")
        state = calibration_state(project, config.get("spawn")) if config.get("enabled") else {
            "state": "not_required", "current_fingerprint": None,
        }
        # A selected but unusable project route is a hard error.  Do not emit
        # a manual/anchor spawn that an older client could silently consume.
        if config.get("enabled") and not block_reason:
            if spawn_mode == "ue_anchor":
                anchor_resource = catalog.get("spawn_anchors", spawn.get("anchor_id"))
                if not anchor_resource:
                    block_reason = "spawn_anchor_resource_missing"
                else:
                    result["spawn_ue"] = {
                        "mode": "ue_anchor",
                        "anchor_id": anchor_resource.get("ue_spawn_id") or anchor_resource.get("id"),
                    }
            elif spawn_mode == "image":
                if state["state"] != "valid":
                    block_reason = (
                        "calibration_needs_review"
                        if state["state"] == "needs_review"
                        else "calibration_invalid"
                    )
                else:
                    frame = _find_frame(project, spawn.get("frame_id"))
                    floor = _floor_for_frame(frame)
                    canonical = spawn.get("canonical_position_mm") or {}
                    profile = project.get("spatial_profile") or {}
                    ue = canonical_to_ue(profile, [canonical.get("x"), canonical.get("y")], floor=floor)
                    matrix = build_ue_matrix(profile)
                    scale = float(((profile.get("ue_transform") or {}).get("scale_to_cm", 0.1)) or 0.1)
                    z_hint = spawn.get("z_hint_mm")
                    result["spawn_ue"] = {
                        "mode": "coordinates",
                        "source": "manual_image",
                        "x_cm": ue[0],
                        "y_cm": ue[1],
                        "trace_origin_z_cm": round(ue[2] + 1000.0, 2),
                        "yaw_deg": _yaw_to_ue(matrix, spawn.get("yaw_deg", 0.0)),
                        "z_hint_cm": round(float(z_hint) * scale, 2) if z_hint is not None else None,
                        "floor": floor,
                    }
            else:
                block_reason = "spawn_missing"

    character_resource = catalog.get("characters", config.get("character_id")) if config.get("enabled") else None
    if config.get("enabled") and not character_resource and block_reason is None:
        block_reason = "character_resource_missing"

    if block_reason:
        result["enabled"] = False
        result.pop("spawn_ue", None)
    result.pop("spawn", None)

    available_routes = _available_runtime_routes(project, route_id)

    token_material = {
        "project_id": project.get("id"),
        "revision": int(revision),
        "catalog_version": catalog.version,
        "spawn_mode": spawn_mode,
        "spawn_reference": (
            route_id if spawn_mode == "route_start"
            else spawn.get("anchor_id") or state.get("current_fingerprint")
        ),
        "calibration_state": state.get("state"),
        "route_id": route_config.get("route_id"),
        "route_revision": (projected_route or {}).get("route_revision"),
        "route_state": route_state,
        "available_routes": [
            [item.get("route_id"), item.get("route_revision")]
            for item in available_routes
        ],
    }
    token_json = json.dumps(token_material, sort_keys=True, separators=(",", ":"))
    token = "sha256:" + hashlib.sha256(token_json.encode("utf-8")).hexdigest()[:20]
    return {
        "runtime_token": token,
        "calibration": state,
        "blocked_reason": block_reason,
        "config": result,
        "resources": _selected_resources(project, config, catalog, projected_route),
        "runtime_route": projected_route,
        "available_routes": available_routes,
    }
