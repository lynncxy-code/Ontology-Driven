"""Preview and apply CAD component updates without changing the project schema."""

import copy
import hashlib
import json
import math
from collections import Counter, defaultdict

from coord_transform import apply_transform, invert_affine
from project_store import ProjectMismatch


class CadUpdateError(ValueError):
    def __init__(self, code, message, status=400):
        super().__init__(message)
        self.code, self.status = code, status


def _hash(value):
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")).hexdigest()


def _number(value):
    try:
        result = float(value)
    except (ValueError, TypeError):
        raise CadUpdateError("invalid_coordinate", "坐标、楼层和朝向必须是有效数字")
    if not math.isfinite(result):
        raise CadUpdateError("invalid_coordinate", "坐标、楼层和朝向必须是有限数字")
    return result


def _equipment(comp):
    return str((comp.get("attribs") or {}).get("EQUIP_ID") or "").strip()


def _geometry(comp):
    xy = comp.get("source_xy") or comp.get("cad_xy")
    if not isinstance(xy, (list, tuple)) or len(xy) < 2:
        return None
    return (comp.get("object_type_rid"), comp.get("floor", 1),
            round(_number(xy[0]), 3), round(_number(xy[1]), 3))


def _pose(comp, instance=None):
    raw = (instance or {}).get("raw_state") or {}
    xy = comp.get("ue_xy") or [0, 0]
    return [raw.get("translation_x", xy[0]), raw.get("translation_y", xy[1]),
            raw.get("translation_z", comp.get("ue_z", 0)),
            raw.get("rotation_z", comp.get("rotation", 0))]


def _different(left, right):
    deltas = [_number(a) - _number(b) for a, b in zip(left, right)]
    deltas[3] = (deltas[3] + 180) % 360 - 180
    return any(abs(delta) > 0.001 for delta in deltas)


def plan_cad_update(project, data, render_config):
    """Pure plan. Neither previews nor rejected requests alter the snapshot."""
    expected = data.get("expected_project_id")
    if expected is not None and expected != project.get("id"):
        raise ProjectMismatch(expected, project.get("id"))
    profile = copy.deepcopy(project.get("spatial_profile") or {})
    frame_id = str(data.get("frame_id") or "frame_cad")
    label = str(data.get("source_label") or "").strip()
    frame = next((f for f in project.get("frames", []) if f.get("id") == frame_id), None)
    if data.get("frame_id"):
        if not frame or frame.get("kind") != "cad":
            raise CadUpdateError("frame_missing", "找不到当前 CAD 对应的空间底图")
        if frame.get("status") != "published":
            raise CadUpdateError("frame_unpublished", "请先复核标定并发布当前 CAD 底图")
        to_ue = frame.get("to_ue") or {}
        matrix = to_ue.get("matrix") if isinstance(to_ue, dict) else to_ue
        label = label or (frame.get("cad") or {}).get("original_name") or frame.get("name", "")
    else:
        matrix = data.get("transform_matrix")
    try:
        matrix = [[_number(n) for n in row] for row in matrix]
        if len(matrix) not in (2, 3) or any(len(row) != 3 for row in matrix):
            raise ValueError()
        if not invert_affine(matrix):
            raise ValueError()
    except (TypeError, ValueError):
        raise CadUpdateError("invalid_transform", "当前标定矩阵无效，请重新计算")
    origin = (profile.get("canonical_origin") or [0, 0])[:2]
    composed = copy.deepcopy(matrix[:2]) + [[0, 0, 1]]
    for row in composed[:2]:
        row[2] += row[0] * origin[0] + row[1] * origin[1]
    scale = _number((profile.get("ue_transform") or {}).get("scale_to_cm", 0.1))
    if scale <= 0:
        raise CadUpdateError("invalid_scale", "项目坐标比例必须大于零")
    floors = {f.get("floor"): f for f in profile.get("floor_table", [])}
    types = project.get("object_types") or {}
    old = project.get("components") or {}
    instances = project.get("instances") or {}

    def in_scope(comp):
        fid = comp.get("frame_id")
        mode = comp.get("source_mode") or ("image" if fid == "frame_image" else "dxf")
        if mode != "dxf":
            return False
        if frame_id != "frame_cad":
            return fid == frame_id
        return fid in (None, "", "frame_cad") and comp.get("source_label", "") == label

    scoped = {cid: c for cid, c in old.items() if in_scope(c)}
    items = data.get("items") or []
    if not isinstance(items, list):
        raise CadUpdateError("invalid_items", "构件列表格式不正确")
    incoming = []
    for item in items:
        if not isinstance(item, dict):
            raise CadUpdateError("invalid_item", "构件内容格式不正确")
        rid = str(item.get("block_name") or "").strip()
        if rid not in types:
            raise CadUpdateError("type_missing", f"请先将类型 {rid or '（空）'} 并入当前项目")
        xy = item.get("source_xy") or item.get("cad_xy")
        if not isinstance(xy, list) or len(xy) < 2:
            raise CadUpdateError("coordinate_missing", f"{rid} 缺少来源坐标")
        xy = [_number(n) for n in xy[:2]]
        floor = _number(item.get("floor", 1))
        if floor != int(floor) or int(floor) not in floors:
            raise CadUpdateError("floor_not_configured", f"请先保存第 {floor:g} 层的空间配置")
        floor = int(floor)
        attribs = item.get("attribs") or {}
        if not isinstance(attribs, dict):
            raise CadUpdateError("invalid_attributes", "构件属性必须是对象")
        canonical = [xy[i] - origin[i] for i in range(2)]
        ft = floors[floor]
        z = ft.get("ue_ground_z_cm")
        z = _number(z) if z is not None else _number(ft.get("z_base_mm", 0)) * scale
        incoming.append({
            "object_type_rid": rid, "type_name": types[rid].get("name") or rid,
            "frame_id": frame_id, "source_mode": "dxf", "source_label": label,
            "to_ue_matrix": composed, "floor": floor, "source_xy": xy, "cad_xy": xy,
            "canonical_xy": canonical, "canonical_z": z / scale,
            "ue_xy": apply_transform(composed, canonical), "ue_z": z,
            "rotation": _number(item.get("rotation", 0)), "attribs": copy.deepcopy(attribs),
            "asset_path": types[rid].get("asset_id") or "",
        })
    # Business IDs and exact source geometry are evidence; proximity is not.
    new_ids = Counter(_equipment(c) for c in incoming if _equipment(c))
    old_ids = Counter(_equipment(c) for c in scoped.values() if _equipment(c))
    new_geo = Counter(_geometry(c) for c in incoming)
    old_geo = Counter(_geometry(c) for c in scoped.values())
    by_equipment, by_geometry, by_type = defaultdict(list), defaultdict(list), defaultdict(list)
    for cid, comp in scoped.items():
        by_equipment[_equipment(comp)].append(cid)
        by_geometry[_geometry(comp)].append(cid)
        by_type[comp.get("object_type_rid")].append(cid)
    choices = data.get("matches") or {}
    if not isinstance(choices, dict) or any(k not in {str(i) for i in range(len(items))} for k in choices):
        raise CadUpdateError("invalid_matches", "构件对应关系已失效，请重新预览")
    matches, reasons, used = {}, {}, set()
    # Explicit choices reserve their targets before automatic matching.
    for key, cid in choices.items():
        index = int(key)
        if not isinstance(cid, str):
            raise CadUpdateError("invalid_matches", "构件对应编号必须是字符串")
        if cid == "new":
            matches[index], reasons[index] = None, "confirmed_new"
            continue
        if (cid not in scoped or cid in used
                or scoped[cid].get("object_type_rid") != incoming[index]["object_type_rid"]):
            raise CadUpdateError("match_conflict", "对应对象不在本底图、类型不同或被重复选择", 409)
        matches[index], reasons[index] = cid, "manual"
        used.add(cid)
    for index, comp in enumerate(incoming):
        if index in matches:
            continue
        equip = _equipment(comp)
        targets = []
        reason = ""
        if equip and new_ids[equip] == old_ids[equip] == 1:
            targets = [cid for cid in by_equipment[equip]
                       if scoped[cid].get("object_type_rid") == comp["object_type_rid"]]
            reason = "equipment_id"
        elif (not equip or new_ids[equip] == 1) and new_geo[_geometry(comp)] == old_geo[_geometry(comp)] == 1:
            targets = [cid for cid in by_geometry[_geometry(comp)] if _equipment(scoped[cid]) == equip]
            reason = "same_geometry"
        if len(targets) == 1 and targets[0] not in used:
            matches[index], reasons[index] = targets[0], reason
            used.add(targets[0])
    rows, unresolved = [], []
    result = copy.deepcopy(old)  # Missing / filtered / legacy records are never deleted by import.
    pose_updates = {}
    apply_positions = data.get("apply_position_ids") or []
    if not isinstance(apply_positions, list) or any(not isinstance(cid, str) for cid in apply_positions):
        raise CadUpdateError("invalid_positions", "位置更新选择格式不正确")
    applied, eligible = [], set()
    for index, comp in enumerate(incoming):
        cid = matches.get(index)
        candidates = ([key for key in by_type[comp["object_type_rid"]] if key not in used]
                      if index not in matches else [])
        ambiguous = index not in matches and (
            bool(candidates) or new_geo[_geometry(comp)] > 1
            or bool(_equipment(comp) and new_ids[_equipment(comp)] > 1))
        before = scoped.get(cid) if cid else None
        iid = (before or {}).get("bound_instance_id")
        current_pose = _pose(before, instances.get(iid)) if before else None
        # A 2D CAD replacement supplies XY/yaw, not a measured object height.
        # Preserve the on-site height on the same floor. Floor moves still use
        # the explicitly selected floor configuration.
        if before and iid and before.get("floor", 1) == comp["floor"]:
            comp["ue_z"] = _number(current_pose[2])
            comp["canonical_z"] = comp["ue_z"] / scale
        cad_position_changed = bool(before and _different(current_pose, _pose(comp)))
        position_changed = bool(iid and cad_position_changed)
        row = {
            "index": index, "type_name": comp["type_name"], "equipment_id": _equipment(comp),
            "source_xy": comp["source_xy"], "component_id": cid, "instance_id": iid,
            "state": "unresolved" if ambiguous else ("matched" if before else "new"),
            "matched_by": reasons.get(index), "position_changed": position_changed,
            "cad_position_changed": cad_position_changed,
            "current_pose": current_pose, "cad_pose": _pose(comp), "candidates": candidates,
        }
        rows.append(row)
        if ambiguous:
            unresolved.append(index)
            continue
        if before:
            saved = copy.deepcopy(before)
            saved.update(comp)
            saved["id"] = cid
            # Preserve instance-specific model overrides and other existing metadata.
            saved["render_config"] = copy.deepcopy(before.get("render_config") or render_config(comp["object_type_rid"]))
            if position_changed:
                eligible.add(cid)
            if cid in apply_positions:
                if position_changed:
                    applied.append(cid)
                if iid in instances:
                    pose_updates[iid] = dict(zip(
                        ("translation_x", "translation_y", "translation_z", "rotation_z"), _pose(comp)))
            elif iid:
                # Keep the scene position as canonical truth too, so later re-derivation
                # cannot undo a UE adjustment merely because CAD was re-imported.
                xy = apply_transform(invert_affine(composed), current_pose[:2])
                saved.update(canonical_xy=xy, canonical_z=_number(current_pose[2]) / scale,
                             ue_xy=current_pose[:2], ue_z=current_pose[2], rotation=current_pose[3])
        else:
            saved = copy.deepcopy(comp)
            identity = ["cad", frame_id, label if frame_id == "frame_cad" else "",
                        _geometry(comp), _equipment(comp), index if new_geo[_geometry(comp)] > 1 else 0]
            cid = "cmp_" + _hash(identity)[:16]
            if cid in result:
                if reasons.get(index) == "confirmed_new":
                    cid = "cmp_" + _hash([identity, sorted(result), index])[:16]
                else:
                    raise CadUpdateError("identity_conflict", "该位置已有构件，请重新预览并选择对应对象", 409)
            saved.update(id=cid, bound_instance_id=None,
                         render_config=render_config(comp["object_type_rid"]))
            row["component_id"] = cid
        result[cid] = saved
    if set(apply_positions) - eligible:
        raise CadUpdateError("position_choice_changed", "位置更新选择已变化，请重新预览", 409)
    missing = [cid for cid in scoped if cid not in used]
    linked_state = {cid: {"instance_id": c.get("bound_instance_id"),
                          "exists": c.get("bound_instance_id") in instances,
                          "pose": _pose(c, instances.get(c.get("bound_instance_id")))}
                    for cid, c in scoped.items()}
    basis = {
        "project": project.get("id"), "frame": frame, "profile": profile,
        "types": types, "scope": scoped, "instance_positions": linked_state,
        "ids": sorted(old), "items": items, "label": label, "matrix": matrix,
        "matches": choices,
    }
    token = _hash({**basis, "apply_positions": sorted(set(apply_positions))})
    review = {
        "status": "preview", "preview_token": token, "basis_token": _hash(basis),
        "project_id": project.get("id"),
        "frame_name": (frame or {}).get("name") or label, "rows": rows,
        "existing": [{"id": cid, "type_name": c.get("type_name") or c.get("object_type_rid"),
                      "instance_id": c.get("bound_instance_id"), "source_xy": c.get("source_xy") or c.get("cad_xy"),
                      "pose": _pose(c, instances.get(c.get("bound_instance_id")))} for cid, c in scoped.items()],
        "missing": missing, "unresolved": unresolved,
        "summary": {"new": sum(r["state"] == "new" for r in rows),
                    "matched": sum(r["state"] == "matched" for r in rows),
                    "position_changes": sum(r["cad_position_changed"] for r in rows),
                    "unresolved": len(unresolved), "retained_missing": len(missing),
                    "apply_positions": len(applied)},
        "legacy_unassigned": sum(c.get("source_mode", "dxf") == "dxf"
                                 and c.get("frame_id") in (None, "", "frame_cad")
                                 and c.get("source_label") == label
                                 for c in old.values()) if frame_id != "frame_cad" else 0,
    }
    profile.setdefault("ue_transform", {})["matrix"] = composed
    legacy_frame = None if data.get("frame_id") else {
        "id": "frame_cad", "name": "CAD 图纸", "kind": "dxf", "unit": "mm",
        "to_canonical": {"method": "anchor", "matrix": [[1, 0, 0], [0, 1, 0], [0, 0, 1]]},
        "to_ue": {"method": "anchor", "matrix": composed}, "floor": 1, "map_code": None,
    }
    return review, result, pose_updates, profile, legacy_frame, bool(scoped)


def save_cad_components(store, data, render_config):
    snapshot = store.get_active_copy(with_render_parts=True)
    if not snapshot:
        raise CadUpdateError("no_project", "当前无激活项目")
    plan = plan_cad_update(snapshot, data, render_config)
    if data.get("dry_run") is True:
        return plan[0]
    expected = data.get("expected_project_id") or snapshot["id"]

    def commit(working):
        review, components, pose_updates, profile, legacy_frame, has_old = plan_cad_update(
            working, data, render_config)
        if review["unresolved"]:
            raise CadUpdateError("matches_required", "请先确认无法确定对应关系的构件", 409)
        if (has_old or data.get("preview_token") or data.get("matches") or data.get("apply_position_ids")):
            if data.get("preview_token") != review["preview_token"]:
                raise CadUpdateError("preview_stale", "图纸、构件或实例位置已变化，请重新预览后保存", 409)
        working["components"] = components
        working["spatial_profile"] = profile
        if legacy_frame:
            frames = working.setdefault("frames", [])
            frames[:] = [f for f in frames if f.get("id") != legacy_frame["id"]] + [legacy_frame]
        for iid, patch in pose_updates.items():
            working["instances"][iid].setdefault("raw_state", {}).update(patch)
        return {"status": "ok", "saved": len(components), "source_saved": len(review["rows"]),
                "removed": 0, "errors": [], "summary": review["summary"],
                "hint": "构件已保存；未出现的旧构件保留，实例位置仅应用明确选择的项目"}

    return store.transact_expected_active(expected, commit)
