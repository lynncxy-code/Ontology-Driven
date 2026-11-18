"""Browser workflow for assigning the first business number to placed scenery."""
import os

from flask import g, jsonify, request

from runtime_object_changes import assign_business_number, attachment_reasons
from tenant_api import ApiError


def _scenery(project, iid, scene_type):
    record = project.get("instances", {}).get(iid)
    if record is None:
        raise ApiError(404, "该陈设已绑定或已移除，请刷新实例列表", "not_found")
    if record.get("object_type_rid") != scene_type:
        raise ApiError(409, "此对象已有业务编号", "already_numbered")
    return record


def _component_numbers(project):
    return {c.get("bound_instance_id") for c in project.get("components", {}).values()}


def register_scenery_number_binding(app, get_store, scene_type, caps, get_runtime_status):
    @app.route("/api/v2/instances/<path:iid>/business-number", methods=["GET", "POST"])
    def scenery_business_number(iid):
        # The v2 request gate checks the session and project role (edit for POST).
        if not (request.cookies.get("ontotwin_session") or request.headers.get("X-OntoTwin-Session")):
            return jsonify(error="auth_required", message="请先登录后台"), 401
        pid = getattr(g, "ontotwin_project_id", None)
        if not pid:
            return jsonify(error="project_id_required", message="请先选择数据集"), 400
        store = get_store()
        if os.environ.get("ONTOTWIN_STORE", "pg").lower() != "pg":
            store = getattr(store, "base", store)
        try:
            if request.method == "GET":
                project = store.read_project(pid)
                _scenery(project, iid, scene_type)
                occupied = set(project["instances"]) | set(store._trashed_instances(pid)) | _component_numbers(project)
                return jsonify(project_id=pid, roster=[
                    {"instance_id": row["instance_id"], "name": row.get("name"), "type": row.get("type")}
                    for row in project.get("instance_roster", [])
                    if row.get("instance_id") and row["instance_id"] not in occupied
                ], types=[
                    {"rid": rid, "name": typ.get("name", rid)} for rid, typ in project["object_types"].items()
                    if rid != scene_type and set(caps).issubset(typ.get("injected_interfaces", []))
                ])

            data = request.get_json(silent=True)
            if not isinstance(data, dict) or data.get("mode") not in ("roster", "new"):
                raise ApiError(400, "请选择编号来源")
            if data.get("expected_project_id") != pid:
                raise ApiError(409, "数据集已切换，请重新打开绑定表单", "project_context_mismatch")
            number = data.get("instance_id")
            if not isinstance(number, str) or not number.strip() or len(number) > 255 or any(ord(c) < 32 for c in number):
                raise ApiError(400, "请输入有效的业务编号")
            number = number.strip()

            def bind(project, deleted):
                record = _scenery(project, iid, scene_type)
                if number in _component_numbers(project):
                    raise ApiError(409, "该编号已绑定构件，请选择其他编号", "component_bound")
                on_roster = any(row.get("instance_id") == number for row in project.get("instance_roster", []))
                # Active and recycled numbers get their more specific conflict from the shared writer.
                if number not in project["instances"] and number not in deleted:
                    if data["mode"] == "roster" and not on_roster:
                        raise ApiError(409, "该编号已移出待投产清单，请重新选择", "roster_changed")
                    if data["mode"] == "new" and on_roster:
                        raise ApiError(409, "该编号已在待投产清单，请从清单选择", "on_roster")
                reasons = attachment_reasons(project, iid, record, get_runtime_status(pid))
                assign_business_number(project, deleted, iid, number, data.get("object_type_rid", ""),
                                       record.get("display_name") or number, reasons, scene_type, caps, "manual")

            store.edit_runtime_objects(pid, "identity", [iid], number, bind)
            return jsonify(instance_id=number)
        except ApiError as exc:
            return jsonify(error=exc.code, message=exc.message), exc.status
