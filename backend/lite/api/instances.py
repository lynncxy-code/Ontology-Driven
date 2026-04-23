"""实例管理 API：/api/v3/lite/instances/*"""
from flask import request, jsonify
from lite.models.db import get_connection


def _row_to_dict(row) -> dict:
    d = dict(row)
    return {
        "id": d["id"],
        "object_type_rid": d["object_type_rid"],
        "file_number": d["file_number"],
        "display_name": d["display_name"],
        "transform": {
            "translation": [d["translation_x"], d["translation_y"], d["translation_z"]],
            "rotation":    [d["rotation_x"],    d["rotation_y"],    d["rotation_z"]],
            "scale":       [d["scale_x"],        d["scale_y"],        d["scale_z"]],
        },
        "physics": {
            "collision_type": d["collision_type"],
            "mass":           d["mass"],
            "friction":       d["friction"],
        },
        "created_at": d["created_at"],
        "updated_at": d["updated_at"],
    }


def instances_collection():
    """GET /api/v3/lite/instances — 列表；POST — 新建。"""
    if request.method == "GET":
        conn = get_connection()
        rows = conn.execute("SELECT * FROM lite_instances ORDER BY created_at").fetchall()
        conn.close()
        return jsonify({"items": [_row_to_dict(r) for r in rows]})

    # POST — 新建实例
    data = request.get_json(force=True)
    required = ("id", "object_type_rid", "file_number")
    missing = [k for k in required if not data.get(k)]
    if missing:
        return jsonify({"error": {"code": "validation_error",
                                  "message": f"缺少必填字段: {missing}"}}), 400

    t = data.get("transform", {})
    tr = t.get("translation", [0, 0, 0])
    ro = t.get("rotation",    [0, 0, 0])
    sc = t.get("scale",       [1, 1, 1])
    ph = data.get("physics", {})

    conn = get_connection()
    try:
        with conn:
            conn.execute(
                """INSERT INTO lite_instances
                   (id, object_type_rid, file_number, display_name,
                    translation_x, translation_y, translation_z,
                    rotation_x, rotation_y, rotation_z,
                    scale_x, scale_y, scale_z,
                    collision_type, mass, friction)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (data["id"], data["object_type_rid"], data["file_number"],
                 data.get("display_name"),
                 tr[0], tr[1], tr[2],
                 ro[0], ro[1], ro[2],
                 sc[0], sc[1], sc[2],
                 ph.get("collision_type", "static"),
                 ph.get("mass"),
                 ph.get("friction", 0.5)),
            )
    except Exception as e:
        conn.close()
        if "UNIQUE constraint" in str(e):
            return jsonify({"error": {"code": "conflict",
                                      "message": f"instance id 已存在: {data['id']}"}}), 409
        if "FOREIGN KEY constraint" in str(e):
            return jsonify({"error": {"code": "validation_error",
                                      "message": f"file_number 不存在: {data['file_number']}"}}), 400
        return jsonify({"error": {"code": "internal_error", "message": str(e)}}), 500

    row = conn.execute("SELECT * FROM lite_instances WHERE id = ?", (data["id"],)).fetchone()
    conn.close()
    return jsonify(_row_to_dict(row)), 201


def instance_item(instance_id):
    """GET / PUT / DELETE /api/v3/lite/instances/<id>"""
    conn = get_connection()
    row = conn.execute("SELECT * FROM lite_instances WHERE id = ?", (instance_id,)).fetchone()
    if not row:
        conn.close()
        return jsonify({"error": {"code": "not_found",
                                  "message": f"实例不存在: {instance_id}"}}), 404

    if request.method == "GET":
        conn.close()
        return jsonify(_row_to_dict(row))

    if request.method == "DELETE":
        with conn:
            conn.execute("DELETE FROM lite_instances WHERE id = ?", (instance_id,))
        conn.close()
        return "", 204

    # PUT — 更新坐标 / 物理属性
    data = request.get_json(force=True)
    t = data.get("transform", {})
    tr = t.get("translation", [row["translation_x"], row["translation_y"], row["translation_z"]])
    ro = t.get("rotation",    [row["rotation_x"],    row["rotation_y"],    row["rotation_z"]])
    sc = t.get("scale",       [row["scale_x"],        row["scale_y"],        row["scale_z"]])
    ph = data.get("physics", {})

    with conn:
        conn.execute(
            """UPDATE lite_instances SET
               display_name   = ?,
               translation_x  = ?, translation_y = ?, translation_z = ?,
               rotation_x     = ?, rotation_y    = ?, rotation_z    = ?,
               scale_x        = ?, scale_y       = ?, scale_z       = ?,
               collision_type = ?, mass          = ?, friction      = ?,
               updated_at     = CURRENT_TIMESTAMP
               WHERE id = ?""",
            (data.get("display_name", row["display_name"]),
             tr[0], tr[1], tr[2],
             ro[0], ro[1], ro[2],
             sc[0], sc[1], sc[2],
             ph.get("collision_type", row["collision_type"]),
             ph.get("mass",     row["mass"]),
             ph.get("friction", row["friction"]),
             instance_id),
        )
    row = conn.execute("SELECT * FROM lite_instances WHERE id = ?", (instance_id,)).fetchone()
    conn.close()
    return jsonify(_row_to_dict(row))
