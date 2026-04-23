"""场景管理 API：/api/v3/lite/scenes/*"""
from flask import request, jsonify
from lite.models.db import get_connection


def _scene_row_to_dict(row) -> dict:
    d = dict(row)
    return {
        "id": d["id"],
        "display_name": d["display_name"],
        "description": d["description"],
        "bounds": {
            "x": [d["bounds_x_min"], d["bounds_x_max"]],
            "y": [d["bounds_y_min"], d["bounds_y_max"]],
            "z": [d["bounds_z_min"], d["bounds_z_max"]],
        },
        "up_axis": d["up_axis"],
        "unit": d["unit"],
        "created_at": d["created_at"],
        "updated_at": d["updated_at"],
    }


def scenes_collection():
    """GET /api/v3/lite/scenes — 列表；POST — 新建。"""
    if request.method == "GET":
        conn = get_connection()
        rows = conn.execute("SELECT * FROM lite_scenes ORDER BY created_at").fetchall()
        conn.close()
        return jsonify({"items": [_scene_row_to_dict(r) for r in rows]})

    data = request.get_json(force=True)
    required = ("id", "display_name", "bounds")
    missing = [k for k in required if not data.get(k)]
    if missing:
        return jsonify({"error": {"code": "validation_error",
                                  "message": f"缺少必填字段: {missing}"}}), 400

    b = data["bounds"]
    conn = get_connection()
    try:
        with conn:
            conn.execute(
                """INSERT INTO lite_scenes
                   (id, display_name, description,
                    bounds_x_min, bounds_x_max,
                    bounds_y_min, bounds_y_max,
                    bounds_z_min, bounds_z_max)
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                (data["id"], data["display_name"], data.get("description"),
                 b["x"][0], b["x"][1],
                 b["y"][0], b["y"][1],
                 b["z"][0], b["z"][1]),
            )
    except Exception as e:
        conn.close()
        if "UNIQUE constraint" in str(e):
            return jsonify({"error": {"code": "conflict",
                                      "message": f"scene id 已存在: {data['id']}"}}), 409
        return jsonify({"error": {"code": "internal_error", "message": str(e)}}), 500

    row = conn.execute("SELECT * FROM lite_scenes WHERE id = ?", (data["id"],)).fetchone()
    conn.close()
    return jsonify(_scene_row_to_dict(row)), 201


def scene_detail(scene_id):
    """GET /api/v3/lite/scenes/<id> — 场景详情（含关联实例 id 列表）。"""
    conn = get_connection()
    row = conn.execute("SELECT * FROM lite_scenes WHERE id = ?", (scene_id,)).fetchone()
    if not row:
        conn.close()
        return jsonify({"error": {"code": "not_found",
                                  "message": f"场景不存在: {scene_id}"}}), 404

    instance_ids = [
        r["instance_id"]
        for r in conn.execute(
            "SELECT instance_id FROM lite_scene_instances WHERE scene_id = ?", (scene_id,)
        ).fetchall()
    ]
    conn.close()
    result = _scene_row_to_dict(row)
    result["instance_ids"] = instance_ids
    return jsonify(result)


def scene_ue_data(scene_id):
    """GET /api/v3/lite/scenes/<id>/ue_data — UE 侧拉取场景数据（米制坐标）。"""
    conn = get_connection()
    row = conn.execute("SELECT * FROM lite_scenes WHERE id = ?", (scene_id,)).fetchone()
    if not row:
        conn.close()
        return jsonify({"error": {"code": "not_found",
                                  "message": f"场景不存在: {scene_id}"}}), 404

    inst_rows = conn.execute(
        """SELECT i.*, a.usd_cached_path, a.display_name as asset_display_name
           FROM lite_instances i
           JOIN lite_scene_instances si ON si.instance_id = i.id
           LEFT JOIN lite_assets a ON a.file_number = i.file_number
           WHERE si.scene_id = ?
           ORDER BY i.created_at""",
        (scene_id,)
    ).fetchall()
    conn.close()

    instances = []
    for r in inst_rows:
        usd_path = r["usd_cached_path"] or f"assets/usd_cache/{r['file_number']}.usd"
        instances.append({
            "id": r["id"],
            "asset": {
                "file_number":  r["file_number"],
                "usd_path":     usd_path,
            },
            "transform": {
                "translation": [r["translation_x"], r["translation_y"], r["translation_z"]],
                "rotation":    [r["rotation_x"],    r["rotation_y"],    r["rotation_z"]],
                "scale":       [r["scale_x"],        r["scale_y"],        r["scale_z"]],
            },
            "ontology_metadata": {
                "instance_id":     r["id"],
                "object_type_rid": r["object_type_rid"],
                "collision_type":  r["collision_type"],
            },
        })

    return jsonify({
        "scene": {
            "id":      row["id"],
            "unit":    "meter",
            "up_axis": "Z",
        },
        "instances": instances,
    })


def scene_instances(scene_id):
    """POST /api/v3/lite/scenes/<id>/instances — 批量添加实例到场景。"""
    conn = get_connection()
    if not conn.execute("SELECT 1 FROM lite_scenes WHERE id = ?", (scene_id,)).fetchone():
        conn.close()
        return jsonify({"error": {"code": "not_found",
                                  "message": f"场景不存在: {scene_id}"}}), 404

    data = request.get_json(force=True)
    ids = data.get("instance_ids", [])
    if not ids:
        conn.close()
        return jsonify({"error": {"code": "validation_error",
                                  "message": "instance_ids 不能为空"}}), 400

    added, skipped = [], []
    with conn:
        for iid in ids:
            if not conn.execute("SELECT 1 FROM lite_instances WHERE id = ?", (iid,)).fetchone():
                skipped.append(iid)
                continue
            try:
                conn.execute(
                    "INSERT INTO lite_scene_instances (scene_id, instance_id) VALUES (?,?)",
                    (scene_id, iid)
                )
                added.append(iid)
            except Exception:
                skipped.append(iid)  # 已存在，忽略

    conn.close()
    return jsonify({"added": added, "skipped": skipped})


def scene_placements_update(scene_id):
    """POST /api/v3/lite/scenes/<id>/placements/update — UE 回写坐标。

    接收米制坐标（右手系），直接存入 DB。
    """
    conn = get_connection()
    if not conn.execute("SELECT 1 FROM lite_scenes WHERE id = ?", (scene_id,)).fetchone():
        conn.close()
        return jsonify({"error": {"code": "not_found",
                                  "message": f"场景不存在: {scene_id}"}}), 404

    data = request.get_json(force=True)
    updates = data.get("updates", [])
    if not updates:
        conn.close()
        return jsonify({"error": {"code": "validation_error",
                                  "message": "updates 不能为空"}}), 400

    updated, skipped = [], []
    with conn:
        for u in updates:
            iid = u.get("instance_id")
            if not iid:
                continue
            row = conn.execute(
                "SELECT 1 FROM lite_instances WHERE id = ?", (iid,)
            ).fetchone()
            if not row:
                skipped.append(iid)
                continue

            t = u.get("translation", None)
            r = u.get("rotation", None)
            s = u.get("scale", None)

            fields, vals = [], []
            if t is not None:
                fields += ["translation_x=?", "translation_y=?", "translation_z=?"]
                vals += [t[0], t[1], t[2]]
            if r is not None:
                fields += ["rotation_x=?", "rotation_y=?", "rotation_z=?"]
                vals += [r[0], r[1], r[2]]
            if s is not None:
                fields += ["scale_x=?", "scale_y=?", "scale_z=?"]
                vals += [s[0], s[1], s[2]]

            if fields:
                fields.append("updated_at=CURRENT_TIMESTAMP")
                vals.append(iid)
                conn.execute(
                    f"UPDATE lite_instances SET {', '.join(fields)} WHERE id=?", vals
                )
                updated.append(iid)

    conn.close()
    return jsonify({"updated": updated, "skipped": skipped})


def scene_instance_remove(scene_id, instance_id):
    """DELETE /api/v3/lite/scenes/<id>/instances/<instance_id>"""
    conn = get_connection()
    cur = conn.execute(
        "SELECT 1 FROM lite_scene_instances WHERE scene_id = ? AND instance_id = ?",
        (scene_id, instance_id)
    )
    if not cur.fetchone():
        conn.close()
        return jsonify({"error": {"code": "not_found",
                                  "message": f"场景 {scene_id} 中没有实例 {instance_id}"}}), 404
    with conn:
        conn.execute(
            "DELETE FROM lite_scene_instances WHERE scene_id = ? AND instance_id = ?",
            (scene_id, instance_id)
        )
    conn.close()
    return "", 204
