"""UE 连接诊断（只读）。

GET /api/v2/ue/diagnostics —— 现场一条 curl 定位"UE 连不上 / 绑不上"：
存储后端、PG 连通性、激活项目、UE-ID 索引与持久层是否一致、重复绑定，
以及（携带 X-OntoTwin-UE-Project-Id 时）该 UE 工程的绑定判定与建议操作。

本模块不写任何数据；唯一副作用是索引未命中时的节流自愈重建（与 UE 请求路径一致）。
"""

import os

from flask import jsonify, request

import ue_project_binding as ub


def _store_backend(project_store):
    name = type(project_store).__name__
    return "pg" if name == "ProjectStorePG" else "json"


def _pg_status():
    try:
        from db import pg
    except Exception as exc:  # psycopg 缺失等
        return {"reachable": False, "error": f"import failed: {exc}"}
    url = getattr(pg, "DATABASE_URL", "") or ""
    # 不回显口令
    safe_url = url
    if "@" in url and "://" in url:
        scheme, rest = url.split("://", 1)
        safe_url = f"{scheme}://***@{rest.split('@', 1)[1]}"
    return {"reachable": bool(pg.ping()), "url": safe_url}


def build_diagnostics(project_store, req):
    requested = (os.environ.get("ONTOTWIN_STORE") or "json").strip().lower()
    backend = _store_backend(project_store)
    report = {
        "store": {
            "requested": requested,
            "backend": backend,
            "fallback": requested == "pg" and backend != "pg",
        },
        "active_project_id": project_store.get_active_id() if hasattr(project_store, "get_active_id") else None,
        "index": ub.index_state(),
        "problems": [],
    }
    if backend == "pg" or requested == "pg":
        report["pg"] = _pg_status()
        if not report["pg"]["reachable"]:
            report["problems"].append("PostgreSQL 不可达：UE 绑定与项目数据都无法读取")
    if report["store"]["fallback"]:
        report["problems"].append("ONTOTWIN_STORE=pg 但实际运行在 JSON 存储上，数据与绑定来自本地 JSON 文件")
    if not report["active_project_id"]:
        report["problems"].append("没有激活项目：UE 首次绑定需要先在 Web UI 激活目标项目")

    # 持久层与内存索引一致性
    try:
        persisted = {}
        for meta in project_store.list_projects() or []:
            ue_id = str(meta.get("bound_ue_project_id") or "").strip()
            if ue_id:
                persisted.setdefault(ue_id, []).append(meta.get("id"))
        index = ub.index_snapshot()
        drift = sorted(k for k in persisted if k not in index) + sorted(k for k in index if k not in persisted)
        report["persisted_bindings"] = persisted
        report["index_drift"] = drift
        if drift:
            report["problems"].append(f"内存索引与持久层不一致：{drift}（下一次 UE 请求会自愈重建）")
        dup = {k: v for k, v in persisted.items() if len(v) > 1}
        if dup:
            report["problems"].append(f"同一 UE 工程绑定在多个项目上：{dup}")
    except Exception as exc:
        report["problems"].append(f"读取项目列表失败：{exc}")

    incoming = ub.request_ue_project(req)
    if incoming.get("id"):
        pid, ok, info = ub.resolve_project_for_ue(project_store, req)
        ue = {"request": incoming, "ok": ok, **info}
        if ok and pid is not None:
            ue["is_active"] = pid == report["active_project_id"]
            if not ue["is_active"]:
                ue["advice"] = "读取正常；如需在 UE 中保存修改，请先在 Web UI 激活该项目"
        elif info.get("binding_state") == "unbound":
            ue["advice"] = "该 UE 工程尚未绑定：在 Web UI 激活目标项目，再在 UE 中执行绑定"
        report["ue"] = ue
    report["ok"] = not report["problems"]
    return report


def register_ue_diagnostics_routes(app, project_store_getter):
    @app.route("/api/v2/ue/diagnostics", methods=["GET"])
    def ue_diagnostics():
        return jsonify(build_diagnostics(project_store_getter(), request))
