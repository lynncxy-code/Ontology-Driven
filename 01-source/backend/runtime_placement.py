"""Create an F10 placement and its per-instance model in one project transaction."""
import math
import os
import re
import time
from uuid import UUID

from flask import g, jsonify, request

from project_store import _default_raw_state, apply_instance_metadata
from tenant_api import ApiError
from ue_project_binding import check_request_can_write_active, lookup_with_heal

TYPE_RID = "ontotwin.scene_object"
CAPABILITIES = ["I3D_Representable", "I3D_Spatial"]


def _model(key):
    if not isinstance(key, str) or len(key) > 255:
        raise ApiError(400, "模型标识无效")
    if re.fullmatch(r"/Game/(?:[\w-]+/)*([\w-]+)\.\1", key):
        return "ue_cooked"
    name = key.removeprefix("models:")
    if key.startswith("models:") and re.fullmatch(r'[^\\/:*?"<>|\x00-\x1f]+\.glb', name, re.I):
        return "local"
    raise ApiError(400, "模型必须来自工程模型库或本地 Models 目录")


def _place(project, iid, key, source, label, position):
    instances = project.setdefault("instances", {})
    previous = instances.get(iid)
    if previous:
        override = previous.get("render_config", {}).get("model_override", {})
        if override.get("ue_asset_path") != key or previous.get("object_type_rid") != TYPE_RID:
            raise ApiError(409, "该放置编号已被其他模型使用")
        return False
    types = project.setdefault("object_types", {})
    typ = types.setdefault(TYPE_RID, {"rid": TYPE_RID, "name": "场景对象", "category": "Core",
                                     "injected_interfaces": CAPABILITIES.copy()})
    if not set(CAPABILITIES).issubset(typ.get("injected_interfaces", [])):
        raise ApiError(409, "场景对象类型缺少三维表现或空间能力")
    now = time.time()
    rec = {"id": iid, "object_type_rid": TYPE_RID, "object_type_name": typ["name"],
           "raw_state": _default_raw_state(TYPE_RID, typ["name"], position),
           "created_at": now, "last_seen": now, "status": "online",
           "render_config": {"injected_interfaces": CAPABILITIES.copy(), "object_type_name": typ["name"],
                             "model_override": {"schema_version": 1, "revision": 1, "updated_at": now,
                                                "asset_id": key, "ue_asset_path": key,
                                                "label": label, "source": source}}}
    apply_instance_metadata(rec, {"display_name": label})
    instances[iid] = rec
    return True


def register_runtime_placement_routes(app, get_store, snapshot):
    @app.post("/api/v2/runtime-editor/placements")
    def create_runtime_placement():
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify(error="invalid_payload"), 400
        pid = getattr(g, "ontotwin_project_id", "")
        if not pid or data.get("expected_project_id") != pid:
            return jsonify(error="project_context_mismatch"), 409
        if not request.headers.get("X-OntoTwin-UE-Project-Id") or not request.headers.get("X-OntoTwin-UE-Scene-Id"):
            return jsonify(error="ue_scene_required"), 403
        store = get_store()
        canonical = getattr(store, "base", store)
        pg_mode = os.environ.get("ONTOTWIN_STORE", "pg").lower() == "pg"
        if not pg_mode and lookup_with_heal(canonical, request.headers["X-OntoTwin-UE-Project-Id"]) != pid:
            return jsonify(error="ue_project_mismatch"), 403
        ok, info, status = check_request_can_write_active(store, request)
        if not ok:
            return jsonify(info), status
        try:
            operation_id = UUID(str(data.get("placement_id", "")))
            position = data.get("position")
            if not isinstance(position, dict) or any(
                type(position.get(k)) not in (int, float) or not math.isfinite(position[k])
                or abs(position[k]) > 1e10 for k in ("x", "y", "z")
            ):
                raise ValueError
        except (ValueError, OverflowError):
            return jsonify(error="invalid_placement"), 400
        key = data.get("model")
        label = data.get("label")
        if not isinstance(label, str) or not 1 <= len(label.strip()) <= 255:
            return jsonify(error="invalid_label"), 400
        iid = "scene-" + operation_id.hex
        try:
            source = _model(key)

            def update(project):
                created = _place(project, iid, key, source, label.strip(), position)
                return snapshot(iid, project), created

            # PG reloads under its row lock. File stores must share the base object's lock.
            target = store if pg_mode else canonical
            snap, created = target.transact_project(pid, update)
        except ApiError as exc:
            return jsonify(error=exc.code, message=exc.message), exc.status
        return jsonify(instance_id=iid, snapshot=snap), 201 if created else 200
