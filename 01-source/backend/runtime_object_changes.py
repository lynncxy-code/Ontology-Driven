"""Scene-authorized F10 delete, restore and identity editing."""
from flask import jsonify, request

from project_store import apply_instance_metadata
from tenant_api import ApiError


def attachment_reasons(project, iid, record):
    reasons = []
    config = record.get("render_config") or {}
    panel = (config.get("interface_overrides") or {}).get("I3D_Overlay") or {}
    if panel.get("values"):
        reasons.append("已配置信息面板")
    if record.get("zone_id"):
        reasons.append("已设置业务分区")
    if record.get("component_id") or any(c.get("bound_instance_id") == iid for c in project.get("components", {}).values()):
        reasons.append("已绑定构件")
    web = project.get("web_interactions") or {}
    for version in ("draft", "published", "previous_published"):
        cfg = web.get(version) or {}
        for view in cfg.get("business_views") or []:
            for group in view.get("rule_groups") or view.get("groups") or []:
                if iid in (group.get("instance_ids") or []) or iid in (group.get("exclude_instance_ids") or []):
                    reasons.append("已加入业务视图")
            if iid in (view.get("exclude_instance_ids") or []):
                reasons.append("已加入业务视图排除清单")
        for binding in cfg.get("bindings") or []:
            if (binding.get("scope") or {}).get("instance_id") == iid:
                reasons.append("已挂接网页")
    return list(dict.fromkeys(reasons))


def checked_ids(data):
    ids = data.get("ids")
    if not isinstance(ids, list) or not 1 <= len(ids) <= 500 or any(
            not isinstance(i, str) or not i or len(i) > 255 for i in ids):
        raise ApiError(400, "请选择有效对象")
    return list(dict.fromkeys(ids))


def register_object_changes(app, scene_store, scene_type, caps, snapshot):
    @app.post("/api/v2/runtime-editor/objects/<action>")
    def change_objects(action):
        if action not in {"inspect", "delete", "restore", "identity"}:
            return jsonify(error="unknown_action"), 404
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify(error="invalid_payload"), 400
        try:
            pid, store = scene_store(data)
            ids = checked_ids(data)
            destination = data.get("instance_id", "")
            if action == "identity" and (len(ids) != 1 or not isinstance(destination, str) or
                    len(destination) > 255 or any(ord(c) < 32 for c in destination)):
                raise ApiError(400, "编号无效")
            destination = destination.strip() if isinstance(destination, str) else ""

            def update(project, deleted):
                instances = project["instances"]
                info = []
                for iid in ids:
                    rec = instances.get(iid)
                    if rec is None and action in {"delete", "restore"}:
                        rec = deleted.get(iid)
                    if rec is None:
                        raise ApiError(404, "该对象已删除，请刷新", "not_found")
                    reasons = attachment_reasons(project, iid, rec)
                    info.append({"id": iid, "name": rec.get("display_name") or iid,
                                 "scenery": rec.get("object_type_rid") == scene_type, "reasons": reasons})
                if action == "delete" and any(i["reasons"] for i in info) and data.get("confirm_business") is not True:
                    raise ApiError(409, "该实例已挂接业务数据，请确认后删除", "confirmation_required", objects=info)
                if action != "identity":
                    return info
                iid = ids[0]
                rec = instances[iid]
                new_name = data.get("display_name", rec.get("display_name", ""))
                if not isinstance(new_name, str) or not 0 < len(new_name.strip()) <= 255:
                    raise ApiError(400, "名称无效")
                if not destination or destination == iid:
                    rec["display_name"] = new_name.strip()
                    for row in project.get("instance_roster", []):
                        if row.get("instance_id") == iid:
                            row["name"] = rec["display_name"]
                    return info
                if info[0]["reasons"]:
                    raise ApiError(409, "、".join(info[0]["reasons"]), "identifier_locked")
                if destination in deleted:
                    raise ApiError(409, "该编号位于回收站", "in_trash")
                if destination in instances:
                    raise ApiError(409, "该编号已投产", "already_placed")
                roster = project.setdefault("instance_roster", [])
                target = next((x for x in roster if x.get("instance_id") == destination), None)
                types = project["object_types"]
                rid = data.get("object_type_rid", rec.get("object_type_rid"))
                if not isinstance(rid,str):
                    raise ApiError(400, "类型无效")
                if target and target.get("type"):
                    rid = next((k for k, v in types.items() if target["type"] in (k,v.get("name"))
                                and k != scene_type and set(caps).issubset(v.get("injected_interfaces",[]))),rid)
                typ = types.get(rid) or {}
                if rid == scene_type or not set(caps).issubset(typ.get("injected_interfaces", [])):
                    raise ApiError(400, "请选择具备三维和空间能力的业务类型", "invalid_type")
                rec.update(id=destination, object_type_rid=rid, object_type_name=typ["name"])
                rec["render_config"].update(object_type_name=typ["name"],injected_interfaces=list(typ["injected_interfaces"]))
                apply_instance_metadata(rec, {"display_name": (target or {}).get("name") or new_name.strip(),
                                              "hierarchy_path": [typ["name"]]})
                instances[destination] = instances.pop(iid)
                roster[:] = [x for x in roster if x.get("instance_id") != iid]
                if not target:
                    roster.append({"instance_id": destination, "type": typ["name"], "name": rec["display_name"], "source":"runtime_editor"})
                return info

            if action == "inspect":
                objects = update(store.read_project(pid), {})
            else:
                objects = store.edit_runtime_objects(pid, action, ids, destination or ids[0], update)
            snaps = []
            if action in {"restore", "identity"}:
                current = store.read_project(pid)
                for iid in ([destination or ids[0]] if action == "identity" else ids):
                    if iid in current["instances"]:
                        snaps.append(snapshot(iid, current))
            return jsonify(objects=objects, ids=ids, instance_id=destination or ids[0], snapshots=snaps)
        except ApiError as exc:
            return jsonify(error=exc.code, message=exc.message, **exc.extra), exc.status
        except ValueError as exc:
            return jsonify(error="invalid_change", message=str(exc)), 409
