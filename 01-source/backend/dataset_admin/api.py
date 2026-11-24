"""数据集管理路由：重命名、删除、复制、可用操作查询、撤销项目授权，
以及给旧回收站路由用的组织／工厂范围。"""

import os

from flask import request

import tenant_api as tenant
from tenant_api import ApiError, _api, _json
from db import pg
from dataset_package.service import DatasetPackageError

from . import service


def _package_error(exc):
    extra = {"details": exc.details} if exc.details is not None else {}
    return ApiError(exc.status, str(exc), exc.code, **extra)


def current_trash_scope():
    """返回当前请求的回收站范围；旧 JSON 部署或未登录时返回 ``None``（不限制）。"""
    if os.environ.get("ONTOTWIN_STORE", "pg").lower() != "pg":
        return None
    token = request.cookies.get(tenant.SESSION_COOKIE) or request.headers.get("X-OntoTwin-Session")
    if not token:
        return None
    with pg.get_conn() as conn:
        with conn.cursor() as cur:
            session = tenant._load_session(cur)
            return service.trash_scope(cur, session["user_id"],
                                       session.get("organization_id"), session.get("factory_id"))


def register_dataset_admin_routes(app, project_store, package_service,
                                  on_renamed=None, on_deleted=None):
    """``package_service`` 是数据集包服务（复制靠导出再导入实现，附件一并复制）。"""

    def rollback_ready(project_id):
        return (package_service._backup_dir(project_id) / "latest.json").exists()

    @app.get("/api/v4.8/projects/<project_id>/actions")
    @_api
    def dataset_admin_actions(project_id):
        tenant._require_pg()
        with pg.get_conn() as conn:
            with conn.cursor() as cur:
                session = tenant._load_session(cur)
                return _json(service.available_actions(
                    cur, session["user_id"], project_id, rollback_ready(project_id)))

    @app.patch("/api/v4.8/projects/<project_id>")
    @_api
    def dataset_admin_rename(project_id):
        tenant._require_pg()
        body = tenant._body()
        with pg.get_conn() as conn:
            with conn.transaction():
                with conn.cursor() as cur:
                    session = tenant._load_session(cur)
                    result = service.rename(cur, session["user_id"], project_id, body.get("name"))
        if result["changed"]:
            base = getattr(project_store, "_base", project_store)
            with base._lock:
                current = getattr(base, "_current", None)
                if current and current.get("id") == project_id:
                    current["name"] = result["name"]
                    if isinstance(current.get("dataset"), dict):
                        current["dataset"]["name"] = result["name"]
            if on_renamed:
                on_renamed(project_id, result["name"])
        return _json(result)

    @app.delete("/api/v4.8/projects/<project_id>")
    @_api
    def dataset_admin_delete(project_id):
        tenant._require_pg()
        with pg.get_conn() as conn:
            with conn.cursor() as cur:
                session = tenant._load_session(cur)
                project = service.require_delete(cur, session["user_id"], project_id)
        try:
            package_service._require_offline(project_id)
        except DatasetPackageError:
            raise ApiError(409, "该数据集的关卡正在 UE 中运行，请先停止 UE 再删除", "ue_still_online")
        from project_store_pg import ProjectMigrationFrozenError
        try:
            existed = project_store.delete_project(project_id)
        except ProjectMigrationFrozenError:
            raise ApiError(409, "该数据集正在迁移，暂时不能删除", "project_migration_frozen")
        if not existed:
            raise ApiError(404, "数据集不存在或已删除", "not_found")
        with pg.get_conn() as conn:
            with conn.transaction():
                with conn.cursor() as cur:
                    service.audit(cur, session["user_id"], project, project_id, "project.delete")
        if on_deleted:
            on_deleted(project_id)
        return _json({"project_id": project_id, "deleted": True, "in_trash": True})

    @app.post("/api/v4.8/projects/<project_id>/copy")
    @_api
    def dataset_admin_copy(project_id):
        tenant._require_pg()
        body = request.get_json(silent=True) or {}
        with pg.get_conn() as conn:
            with conn.cursor() as cur:
                session = tenant._load_session(cur)
                source = service.require_copy(cur, session["user_id"], project_id)
        requested = str(body.get("name") or "").strip()
        name = service.normalize_name(requested) if requested else package_service._suggest_name(
            source["name"], package_service._existing_names())
        missing = []
        try:
            try:
                data, _, _ = package_service.export_package(project_id)
            except DatasetPackageError as exc:
                if exc.code != "attachments_missing":
                    raise
                # 附件文件已丢失时仍复制数据本身，并告诉用户缺了哪些附件。
                missing = (exc.details or {}).get("missing") or []
                data, _, _ = package_service.export_package(project_id, data_only=True)
            # 归属由下面的 assign_copy 按源数据集明确写入；导入包自带的
            # 「按请求头归属」钩子在这里关掉（它要求工厂成员身份，组织管理员
            # 不一定是成员）。导入本身也持有这把可重入锁，所以替换是安全的。
            with package_service.store._lock:
                hook, package_service.on_project_imported = package_service.on_project_imported, None
                try:
                    result = package_service.import_delivery(
                        data, name, origin=request.host_url.rstrip("/"))
                finally:
                    package_service.on_project_imported = hook
        except DatasetPackageError as exc:
            raise _package_error(exc)
        new_id = result["project_id"]
        try:
            with pg.get_conn() as conn:
                with conn.transaction():
                    with conn.cursor() as cur:
                        service.assign_copy(cur, session["user_id"], source, new_id)
                        service.audit(cur, session["user_id"], source, new_id, "project.copy",
                                      detail={"source_project_id": project_id})
        except Exception:
            project_store.delete_project(new_id)
            if on_deleted:
                on_deleted(new_id)
            raise
        return _json({"project_id": new_id, "name": result.get("dataset_name") or name,
                      "source_project_id": project_id, "missing_attachments": missing}), 201

    @app.delete("/api/v4.8/projects/<project_id>/permissions/<user_id>")
    @_api
    def dataset_admin_revoke_permission(project_id, user_id):
        tenant._require_pg()
        with pg.get_conn() as conn:
            with conn.transaction():
                with conn.cursor() as cur:
                    session = tenant._load_session(cur)
                    return _json(service.revoke_permission(cur, session["user_id"], project_id, user_id))
