"""Create an F10 placement and its per-instance model in one project transaction."""
import math
import os
import re
import time
from uuid import UUID

from flask import g, jsonify, request

from project_store import _default_raw_state, apply_instance_metadata
from runtime_object_changes import attachment_reasons, register_object_changes
from scenery_number_binding import register_scenery_number_binding
from tenant_api import ApiError
from ue_project_binding import check_request_can_write_active, lookup_with_heal

TYPE_RID = "ontotwin.scene_object"
SCENERY_NAME = "场景陈设"
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


def _scenery_name(records, key, label):
    prefix = label + " "
    highest = 0
    for record in records:
        if record.get("object_type_rid") != TYPE_RID:
            continue
        override = record.get("render_config", {}).get("model_override", {})
        name = record.get("display_name", "")
        if override.get("ue_asset_path") == key and name.startswith(prefix):
            suffix = name[len(prefix):]
            if suffix.isascii() and suffix.isdecimal():
                highest = max(highest, int(suffix))
    return f"{prefix}{highest + 1:02d}"


def _place(project, deleted, operation_id, business_id, type_id, name, key, source, label, position):
    instances = project.setdefault("instances", {})
    iid = business_id or "scene-" + operation_id.hex
    for existing_id, record in instances.items():
        if record.get("source") == "runtime_editor" and record.get("ext_guid") == str(operation_id):
            if record.get("render_config", {}).get("model_override", {}).get("ue_asset_path") != key:
                raise ApiError(409, "同一次放置不能改用其他模型", "placement_conflict")
            return existing_id, False
    if iid in deleted:
        raise ApiError(409, "此编号位于回收站，请先恢复或彻底删除", "in_trash")
    previous = instances.get(iid)
    if previous:
        override = previous.get("render_config", {}).get("model_override", {})
        same_operation = previous.get("source") == "runtime_editor" and previous.get("ext_guid") == str(operation_id)
        legacy_retry = not business_id and previous.get("object_type_rid") == TYPE_RID
        if override.get("ue_asset_path") == key and (same_operation or legacy_retry):
            return iid, False
        raise ApiError(409, "此编号已投产", "already_placed")
    types = project.setdefault("object_types", {})
    if business_id:
        roster = project.setdefault("instance_roster", [])
        row = next((item for item in roster if item.get("instance_id") == business_id), None)
        if row and row.get("type"):
            for rid, candidate in types.items():
                if rid != TYPE_RID and row["type"] in (rid, candidate.get("name")) and set(CAPABILITIES).issubset(candidate.get("injected_interfaces", [])):
                    type_id = rid
                    break
        typ = types.get(type_id)
        if not typ or type_id == TYPE_RID:
            raise ApiError(400, "请选择可用的业务类型", "invalid_type")
        name = name or (row or {}).get("name") or label
        if not row:
            roster.append({"instance_id": iid, "type": typ["name"], "name": name, "source": "runtime_editor"})
    else:
        type_id = TYPE_RID
        typ = types.setdefault(TYPE_RID, {"rid": TYPE_RID, "name": SCENERY_NAME, "category": "Core",
                                         "injected_interfaces": CAPABILITIES.copy()})
        if not name:
            name = _scenery_name((*instances.values(), *deleted.values()), key, label)
    if not set(CAPABILITIES).issubset(typ.get("injected_interfaces", [])):
        raise ApiError(409, "所选类型缺少三维表现或空间能力", "type_not_spatial")
    now = time.time()
    type_name = SCENERY_NAME if type_id == TYPE_RID else typ["name"]
    rec = {"id": iid, "object_type_rid": type_id, "object_type_name": type_name,
           "source": "runtime_editor", "ext_guid": str(operation_id),
           "raw_state": _default_raw_state(type_id, type_name, position),
           "created_at": now, "last_seen": now, "status": "online",
           "render_config": {"injected_interfaces": list(typ["injected_interfaces"]), "object_type_name": type_name,
                             "model_override": {"schema_version": 1, "revision": 1, "updated_at": now,
                                                "asset_id": key, "ue_asset_path": key,
                                                "label": label, "source": source}}}
    apply_instance_metadata(rec, {"display_name": name})
    instances[iid] = rec
    return iid, True


def register_runtime_placement_routes(app, get_store, snapshot, get_runtime_status):
    def scene_store(data):
        pid = getattr(g, "ontotwin_project_id", "")
        if not pid or data.get("expected_project_id") != pid:
            raise ApiError(409, "数据集已切换，请重新选择模型", "project_context_mismatch")
        if not request.headers.get("X-OntoTwin-UE-Project-Id") or not request.headers.get("X-OntoTwin-UE-Scene-Id"):
            raise ApiError(403, "缺少关卡标识", "ue_scene_required")
        store = get_store()
        canonical = getattr(store, "base", store)
        pg_mode = os.environ.get("ONTOTWIN_STORE", "pg").lower() == "pg"
        if not pg_mode and lookup_with_heal(canonical, request.headers["X-OntoTwin-UE-Project-Id"]) != pid:
            raise ApiError(403, "关卡与数据集不匹配", "ue_project_mismatch")
        ok, info, status = check_request_can_write_active(store, request)
        if not ok:
            raise ApiError(status, info.get("message", "关卡没有写入权限"), info.get("error", "forbidden"))
        return pid, store if pg_mode else canonical

    register_object_changes(app, scene_store, TYPE_RID, CAPABILITIES, snapshot, get_runtime_status)
    register_scenery_number_binding(app, get_store, TYPE_RID, CAPABILITIES, get_runtime_status)

    @app.get("/api/v2/runtime-editor/placement-options")
    def placement_options():
        try:
            pid, target = scene_store(request.args)
            selected = request.args.get("selected_id", "")
            if not selected:
                _model(request.args.get("model"))
            project = target.read_project(pid)
            if not project:
                raise ApiError(404, "数据集不存在", "not_found")
            instances = project.get("instances", {})
            deleted = target._trashed_instances(pid)
            types = [{"rid": rid, "name": row.get("name", rid)}
                     for rid, row in project.get("object_types", {}).items()
                     if rid != TYPE_RID and set(CAPABILITIES).issubset(row.get("injected_interfaces", []))]
            occupied = set(instances) | set(deleted)
            available = [row for row in project.get("instance_roster", []) if row.get("instance_id") not in occupied]
            identity = {}
            if selected:
                rec = instances.get(selected)
                if not rec:
                    raise ApiError(404, "对象已删除", "not_found")
                default_name = rec.get("display_name", "")
                identity = {"instance_id": selected, "object_type_rid": rec["object_type_rid"],
                            "scenery": rec["object_type_rid"] == TYPE_RID,
                            "reasons": attachment_reasons(project, selected, rec, get_runtime_status(pid))}
            else:
                default_name = _scenery_name((*instances.values(), *deleted.values()), request.args["model"],
                                             request.args.get("label", "")[:255])
            return jsonify(types=types, roster=available, active_ids=list(instances), deleted_ids=list(deleted),
                           default_name=default_name, identity=identity)
        except ApiError as exc:
            return jsonify(error=exc.code, message=exc.message), exc.status

    @app.post("/api/v2/runtime-editor/placements")
    def create_runtime_placement():
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify(error="invalid_payload"), 400
        try:
            pid, target = scene_store(data)
            operation_id = UUID(str(data.get("placement_id", "")))
            position = data.get("position")
            if not isinstance(position, dict) or any(
                type(position.get(k)) not in (int, float) or not math.isfinite(position[k])
                or abs(position[k]) > 1e10 for k in ("x", "y", "z")
            ):
                raise ValueError
        except ApiError as exc:
            return jsonify(error=exc.code, message=exc.message), exc.status
        except (ValueError, OverflowError):
            return jsonify(error="invalid_placement"), 400
        key = data.get("model")
        label = data.get("label")
        if not isinstance(label, str) or not 1 <= len(label.strip()) <= 255:
            return jsonify(error="invalid_label"), 400
        try:
            source = _model(key)
            values = [data.get(k, "") for k in ("instance_id", "object_type_rid", "display_name")]
            if any(not isinstance(v, str) or len(v) > 255 or any(ord(c) < 32 for c in v) for v in values):
                raise ApiError(400, "编号、类型或名称无效")
            business_id, type_id, name = (v.strip() for v in values)
            def update(project, deleted):
                iid, created = _place(project, deleted, operation_id, business_id, type_id, name,
                                      key, source, label.strip(), position)
                return iid, snapshot(iid, project), created

            # PG reloads under its row lock. File stores must share the base object's lock.
            iid, snap, created = target.transact_project(pid, update, include_trash=True)
        except ApiError as exc:
            return jsonify(error=exc.code, message=exc.message), exc.status
        return jsonify(instance_id=iid, snapshot=snap), 201 if created else 200
