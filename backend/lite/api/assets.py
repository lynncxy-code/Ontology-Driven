"""资产管理 API：/api/v3/lite/assets/*

每个 URL 路径只用一条规则（GET+POST 合并），避免 Werkzeug 3.x 多规则匹配冲突。
"""
import json
import hashlib
import time
from pathlib import Path
from flask import request, jsonify
from lite.models.db import get_connection


def _row_to_dict(row) -> dict:
    d = dict(row)
    if d.get("bounding_box"):
        try:
            d["bounding_box"] = json.loads(d["bounding_box"])
        except (json.JSONDecodeError, TypeError):
            pass
    return d


def assets_collection():
    """GET /api/v3/lite/assets — 列表；POST — 新建。"""
    if request.method == "GET":
        conn = get_connection()
        rows = conn.execute("SELECT * FROM lite_assets ORDER BY created_at").fetchall()
        conn.close()
        return jsonify({"items": [_row_to_dict(r) for r in rows]})

    # POST
    data = request.get_json(force=True)
    required = ("file_number", "display_name", "fbx_source_path")
    missing = [k for k in required if not data.get(k)]
    if missing:
        return jsonify({"error": {"code": "validation_error",
                                  "message": f"缺少必填字段: {missing}"}}), 400

    bbox_json = json.dumps(data["bounding_box"]) if data.get("bounding_box") else None
    conn = get_connection()
    try:
        with conn:
            conn.execute(
                """INSERT INTO lite_assets
                   (file_number, display_name, fbx_source_path, bounding_box, mass_hint)
                   VALUES (?, ?, ?, ?, ?)""",
                (data["file_number"], data["display_name"],
                 data["fbx_source_path"], bbox_json, data.get("mass_hint")),
            )
    except Exception as e:
        conn.close()
        if "UNIQUE constraint" in str(e):
            return jsonify({"error": {"code": "conflict",
                                      "message": f"file_number 已存在: {data['file_number']}"}}), 409
        return jsonify({"error": {"code": "internal_error", "message": str(e)}}), 500

    row = conn.execute("SELECT * FROM lite_assets WHERE file_number = ?",
                       (data["file_number"],)).fetchone()
    conn.close()
    return jsonify(_row_to_dict(row)), 201


def asset_item(file_number):
    """DELETE /api/v3/lite/assets/<file_number>"""
    conn = get_connection()
    if not conn.execute("SELECT 1 FROM lite_assets WHERE file_number = ?",
                        (file_number,)).fetchone():
        conn.close()
        return jsonify({"error": {"code": "not_found",
                                  "message": f"资产不存在: {file_number}"}}), 404
    with conn:
        conn.execute("DELETE FROM lite_assets WHERE file_number = ?", (file_number,))
    conn.close()
    return "", 204


def rebuild_usd(file_number):
    """POST /api/v3/lite/assets/<file_number>/rebuild_usd"""
    conn = get_connection()
    if not conn.execute("SELECT 1 FROM lite_assets WHERE file_number = ?",
                        (file_number,)).fetchone():
        conn.close()
        return jsonify({"error": {"code": "not_found",
                                  "message": f"资产不存在: {file_number}"}}), 404

    project_root = Path(__file__).resolve().parent.parent.parent.parent
    usd_path = project_root / "assets" / "usd_cache" / f"{file_number}.usd"
    if not usd_path.exists():
        conn.close()
        return jsonify({"error": {"code": "not_found",
                                  "message": f"usd_cache 中未找到 {file_number}.usd"}}), 404

    t0 = time.monotonic()
    h = hashlib.sha256(usd_path.read_bytes()).hexdigest()
    duration_ms = int((time.monotonic() - t0) * 1000)
    with conn:
        conn.execute(
            """UPDATE lite_assets
               SET usd_cached_path = ?, usd_cache_hash = ?, usd_cached_at = CURRENT_TIMESTAMP
               WHERE file_number = ?""",
            (str(usd_path), h, file_number),
        )
    conn.close()
    return jsonify({"usd_cached_path": str(usd_path), "duration_ms": duration_ms})
