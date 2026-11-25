"""数据集管理路由：重命名、删除、复制、可用操作查询、撤销项目授权，
以及给旧回收站路由用的组织／工厂范围。"""

import os
import shutil

from flask import request

import tenant_api as tenant
from tenant_api import ApiError, _api, _json
from db import pg
from dataset_package import attachments
from dataset_package.service import DatasetPackageError

from . import service


def _package_error(exc):
    extra = {"details": exc.details} if exc.details is not None else {}
    return ApiError(exc.status, str(exc), exc.code, **extra)


def current_trash_scope():
    """返回当前请求的回收站范围。

    仅显式 JSON 测试模式（ONTOTWIN_STORE != 'pg'）返回 ``None``；
    PG 运行时强制核验登录会话及当前组织／工厂权限，缺失或越权直接抛 ``ApiError``，
    绝不退回全局范围。
    """
    if os.environ.get("ONTOTWIN_STORE", "pg").strip().lower() != "pg":
        return None
    with pg.get_conn() as conn:
        with conn.cursor() as cur:
            session = tenant._load_session(cur, required=True, ignore_project=True)
            return service.require_trash_scope(
                cur,
                session["user_id"],
                session.get("organization_id"),
                session.get("factory_id"),
            )


def current_factory_dataset_names():
    """返回当前会话所属工厂下的数据集名称列表；非 PG 或无工厂上下文时返回 ``None``。"""
    if os.environ.get("ONTOTWIN_STORE", "pg").strip().lower() != "pg":
        return None
    try:
        token = request.cookies.get(tenant.SESSION_COOKIE) or request.headers.get("X-OntoTwin-Session")
    except RuntimeError:
        return None
    if not token:
        return None
    try:
        with pg.get_conn() as conn:
            with conn.cursor() as cur:
                session = tenant._load_session(cur, required=False, ignore_project=True)
                org_id = (session or {}).get("organization_id")
                factory_id = (session or {}).get("factory_id")
                if not org_id or not factory_id:
                    return []
                allowed, _ = tenant._factory_allowed(cur, session["user_id"], org_id, factory_id)
                if not allowed:
                    return []
                return sorted(service.factory_dataset_names(cur, org_id, factory_id))
    except Exception:
        return None


def check_trashed_binding_conflict(trash_id):
    """恢复已删数据集前检查其原关卡是否已被其他数据集占用。"""
    if os.environ.get("ONTOTWIN_STORE", "pg").strip().lower() != "pg":
        return False
    text = str(trash_id or "")
    if not text.startswith("pg:prj:"):
        return False
    pid = text[len("pg:prj:"):]
    if not pid or ":" in pid:
        return False
    with pg.get_conn() as conn:
        with conn.cursor() as cur:
            return service.trashed_binding_has_conflict(cur, pid)


def cleanup_deleted_project_trash(trash_id, package_service, scope=None, item_name=""):
    """数据集永久删除成功后清理磁盘附件与回退备份，并补记审计记录。"""
    text = str(trash_id or "")
    if not text.startswith("pg:prj:"):
        return
    pid = text[len("pg:prj:"):]
    if not pid or ":" in pid:
        return
    if package_service is not None:
        try:
            shutil.rmtree(attachments.project_dir(package_service.asset_root, pid), ignore_errors=True)
            shutil.rmtree(package_service._backup_dir(pid), ignore_errors=True)
        except Exception:
            pass
    if os.environ.get("ONTOTWIN_STORE", "pg").strip().lower() == "pg" and scope and scope.user_id and scope.organization_id:
        try:
            with pg.get_conn() as conn:
                with conn.transaction():
                    with conn.cursor() as cur:
                        tenant._audit(cur, scope.user_id, scope.organization_id, scope.factory_id,
                                      None, "project.permanent_delete", pid,
                                      detail={"deleted_project_id": pid, "name": item_name or pid})
        except Exception:
            pass


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
        requested = str(body.get("name") or "").strip()
        with pg.get_conn() as conn:
            with conn.cursor() as cur:
                session = tenant._load_session(cur)
                source = service.require_copy(cur, session["user_id"], project_id)
                existing = service.factory_dataset_names(
                    cur, source["organization_id"], source["factory_id"]
                )
        if requested:
            name = service.normalize_name(requested)
            if name in existing:
                raise ApiError(409, f"当前工厂已有同名数据集：{name}", "dataset_name_conflict")
        else:
            name = package_service._suggest_name(source["name"], existing)
        missing = []
        try:
            # 某张底图或附件缺失时，保留其余完好附件一并复制，并把缺失项如实告知用户。
            data, _, manifest = package_service.export_package(
                project_id, allow_missing_attachments=True
            )
            missing = list(manifest.get("missing_attachments") or [])
            # 归属由下面的 assign_copy 按源数据集明确写入；导入包自带的
            # 「按请求头归属」钩子在这里关掉（它要求工厂成员身份，组织管理员
            # 不一定是成员），重名检查也切到本工厂数据库名单。
            with package_service.store._lock:
                hook, package_service.on_project_imported = package_service.on_project_imported, None
                names_fn, package_service.dataset_names = package_service.dataset_names, (lambda: list(existing))
                try:
                    result = package_service.import_delivery(
                        data, name, origin=request.host_url.rstrip("/"))
                finally:
                    package_service.on_project_imported = hook
                    package_service.dataset_names = names_fn
        except DatasetPackageError as exc:
            raise _package_error(exc)
        new_id = result["project_id"]
        try:
            with pg.get_conn() as conn:
                with conn.transaction():
                    with conn.cursor() as cur:
                        service.assign_copy(cur, session["user_id"], source, new_id, name=name)
                        service.audit(cur, session["user_id"], source, new_id, "project.copy",
                                      detail={"source_project_id": project_id})
        except Exception:
            project_store.delete_project(new_id)
            try:
                project_store.delete_trash(f"pg:prj:{new_id}")
                cleanup_deleted_project_trash(f"pg:prj:{new_id}", package_service)
            except Exception:
                pass
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
