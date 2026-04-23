"""导出 API：/api/v3/lite/scenes/<id>/export 及下载。"""
import json
from pathlib import Path
from flask import request, jsonify, send_file
from lite.models.db import get_connection
# usd_exporter 依赖 pxr，懒加载避免 Docker 环境缺包时阻断整个路由注册

# 导出文件存放位置（相对项目根）
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_EXPORTS_DIR  = _PROJECT_ROOT / "exports"


def scene_export(scene_id):
    """POST /api/v3/lite/scenes/<id>/export — 同步导出 USD。"""
    conn = get_connection()

    # 1. 查场景
    scene_row = conn.execute(
        "SELECT * FROM lite_scenes WHERE id = ?", (scene_id,)
    ).fetchone()
    if not scene_row:
        conn.close()
        return jsonify({"error": {"code": "not_found",
                                  "message": f"场景不存在: {scene_id}"}}), 404

    # 2. 查该场景的所有实例（JOIN assets 拿 USD 路径）
    inst_rows = conn.execute(
        """SELECT i.*, a.usd_cached_path
           FROM lite_instances i
           JOIN lite_scene_instances si ON si.instance_id = i.id
           LEFT JOIN lite_assets a ON a.file_number = i.file_number
           WHERE si.scene_id = ?
           ORDER BY i.created_at""",
        (scene_id,)
    ).fetchall()

    if not inst_rows:
        conn.close()
        return jsonify({"error": {"code": "validation_error",
                                  "message": "场景中没有实例，无法导出"}}), 400

    # 3. 确定导出版本号
    last = conn.execute(
        "SELECT MAX(version) as v FROM lite_exports WHERE scene_id = ?", (scene_id,)
    ).fetchone()
    version = (last["v"] or 0) + 1

    # 4. 组装 scene_data dict（usd_exporter 需要的格式）
    opts = request.get_json(force=True, silent=True) or {}
    include_physics = opts.get("include_physics", True)

    scene_data = {
        "id":           scene_row["id"],
        "display_name": scene_row["display_name"],
        "dataset_id":   "standard_practice",
        "bounds": {
            "x": [scene_row["bounds_x_min"], scene_row["bounds_x_max"]],
            "y": [scene_row["bounds_y_min"], scene_row["bounds_y_max"]],
            "z": [scene_row["bounds_z_min"], scene_row["bounds_z_max"]],
        },
        "instances": [
            {
                "id":              r["id"],
                "object_type_rid": r["object_type_rid"],
                "file_number":     r["file_number"],
                "display_name":    r["display_name"],
                "translation":     [r["translation_x"], r["translation_y"], r["translation_z"]],
                "rotation":        [r["rotation_x"],    r["rotation_y"],    r["rotation_z"]],
                "scale":           [r["scale_x"],        r["scale_y"],        r["scale_z"]],
                "collision_type":  r["collision_type"],
                "mass":            r["mass"],
                "friction":        r["friction"],
            }
            for r in inst_rows
        ],
    }

    # 5. 调用导出器
    _EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    fmt = opts.get("format", "usda")
    out_file = _EXPORTS_DIR / f"{scene_id}_v{version}.{fmt}"

    try:
        from lite.services.usd_exporter import export_scene_to_usd
    except ImportError as e:
        return jsonify({"error": {"code": "internal_error",
                                  "message": f"USD 导出依赖未安装: {e}"}}), 500

    result = export_scene_to_usd(
        scene_data, str(out_file),
        export_version=version,
        include_physics=include_physics,
    )

    # 6. 记录导出历史
    file_size = out_file.stat().st_size if out_file.exists() else 0
    with conn:
        conn.execute(
            """INSERT INTO lite_exports (scene_id, version, file_path, file_size_bytes, report_json)
               VALUES (?,?,?,?,?)""",
            (scene_id, version, str(out_file), file_size,
             json.dumps({"warnings": result["warnings"]})),
        )
    export_id = conn.execute(
        "SELECT id FROM lite_exports WHERE scene_id=? AND version=?", (scene_id, version)
    ).fetchone()["id"]
    conn.close()

    return jsonify({
        "success":        result["success"],
        "export_version": version,
        "file_path":      str(out_file.relative_to(_PROJECT_ROOT)),
        "download_url":   f"/api/v3/lite/exports/{export_id}/download",
        "stats": {
            "prim_count": result["prim_count"],
            "warnings":   result["warnings"],
        },
    })


def export_download(export_id):
    """GET /api/v3/lite/exports/<id>/download — 下载 USD 文件。"""
    conn = get_connection()
    row = conn.execute("SELECT * FROM lite_exports WHERE id = ?", (export_id,)).fetchone()
    conn.close()
    if not row:
        return jsonify({"error": {"code": "not_found",
                                  "message": f"导出记录不存在: {export_id}"}}), 404

    file_path = Path(row["file_path"])
    if not file_path.exists():
        return jsonify({"error": {"code": "not_found",
                                  "message": "导出文件已被删除"}}), 404

    return send_file(str(file_path), as_attachment=True,
                     download_name=file_path.name)
