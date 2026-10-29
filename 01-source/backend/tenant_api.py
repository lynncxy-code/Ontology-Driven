"""OntoTwin 4.8 组织、账号、项目上下文和场景绑定 API。

这个模块只负责 4.8 的身份与归属边界，不把租户状态塞进旧版
``app_singleton.active_project_id``。旧版业务路由仍可继续使用；新页面和
UE 连接使用本模块提供的显式上下文 API。生产模式要求 PostgreSQL，测试可
在请求层用测试数据库或 Flask test client 验证。
"""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import time
import uuid
from datetime import datetime, timedelta, timezone
from functools import wraps

from flask import jsonify, request
from psycopg.types.json import Jsonb
from werkzeug.security import check_password_hash, generate_password_hash

from db import pg
from project_store import (
    CURRENT_SCHEMA_VERSION,
    _default_media_policy,
    _default_scene_interactions,
    _default_spatial_profile,
    _default_web_interactions,
)


SESSION_COOKIE = "ontotwin_session"
SESSION_TTL_HOURS = max(1, int(os.environ.get("ONTOTWIN_SESSION_TTL_HOURS", "8")))
ROLE_ORDER = {"viewer": 0, "editor": 1, "admin": 2}


class ApiError(Exception):
    def __init__(self, status: int, message: str, code: str = "bad_request", **extra):
        super().__init__(message)
        self.status = status
        self.message = message
        self.code = code
        self.extra = extra


def _now():
    return datetime.now(timezone.utc)


def _id(prefix):
    return f"{prefix}_{uuid.uuid4().hex}"


def _token_hash(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _body():
    value = request.get_json(silent=True)
    if not isinstance(value, dict):
        raise ApiError(400, "请求体必须是 JSON 对象", "invalid_json")
    return value


def _required(body, key):
    value = body.get(key)
    if value is None or (isinstance(value, str) and not value.strip()):
        raise ApiError(400, f"缺少字段：{key}", "missing_field", field=key)
    return value.strip() if isinstance(value, str) else value


def _hashable(value):
    """Convert PostgreSQL values into deterministic JSON hash input."""
    if isinstance(value, dict):
        return {str(k): _hashable(v) for k, v in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, (list, tuple)):
        return [_hashable(v) for v in value]
    if isinstance(value, (datetime,)):
        return value.isoformat()
    if isinstance(value, bytes):
        return value.hex()
    return value


def _project_content_hash(cur, project_id):
    """Hash project content while excluding expected ownership changes.

    Migration is allowed to change environment/organization/factory ownership
    and ``updated_at``. Everything else must round-trip byte-for-byte at the
    semantic JSON level.
    """
    cur.execute(
        """SELECT id,name,created_at,schema_version,dataset,calibration,
                  spatial_profile,components,instance_roster,frames,
                  scene_interactions,media_policy,web_interactions,status,deleted_at
             FROM project WHERE id=%s""",
        (project_id,),
    )
    project = cur.fetchone()
    if not project:
        raise ApiError(404, "迁移项目不存在", "project_not_found", project_id=project_id)
    payload = {
        "project": _hashable(dict(zip(
            ("id", "name", "created_at", "schema_version", "dataset", "calibration",
             "spatial_profile", "components", "instance_roster", "frames",
             "scene_interactions", "media_policy", "web_interactions", "status", "deleted_at"),
            project,
        ))),
    }
    cur.execute(
        """SELECT rid,name,source,data,deleted_at FROM object_type
             WHERE project_id=%s ORDER BY rid""",
        (project_id,),
    )
    payload["object_types"] = [_hashable(dict(zip(("rid", "name", "source", "data", "deleted_at"), row))) for row in cur.fetchall()]
    cur.execute(
        """SELECT zone_id,name,ue_level,streaming,parent_zone_id,level,deleted_at
             FROM zone WHERE project_id=%s ORDER BY zone_id""",
        (project_id,),
    )
    payload["zones"] = [_hashable(dict(zip(("zone_id", "name", "ue_level", "streaming", "parent_zone_id", "level", "deleted_at"), row))) for row in cur.fetchall()]
    cur.execute(
        """SELECT id,object_type_rid,object_type_name,zone_id,component_id,source,
                  ext_guid,display_name,hierarchy_path,source_folder_path,source_asset_path,
                  classification_status,classification_key,status,created_at,last_seen,
                  render_config,raw_state,deleted_at
             FROM instance WHERE project_id=%s ORDER BY id""",
        (project_id,),
    )
    instance_keys = ("id", "object_type_rid", "object_type_name", "zone_id", "component_id", "source",
                     "ext_guid", "display_name", "hierarchy_path", "source_folder_path", "source_asset_path",
                     "classification_status", "classification_key", "status", "created_at", "last_seen",
                     "render_config", "raw_state", "deleted_at")
    payload["instances"] = [_hashable(dict(zip(instance_keys, row))) for row in cur.fetchall()]
    cur.execute(
        """SELECT user_id,permission,granted_by,granted_at,revoked_at
             FROM project_permission WHERE project_id=%s ORDER BY user_id""",
        (project_id,),
    )
    payload["permissions"] = [_hashable(dict(zip(("user_id", "permission", "granted_by", "granted_at", "revoked_at"), row))) for row in cur.fetchall()]
    cur.execute(
        """SELECT binding_id,organization_id,factory_id,ue_project_id,scene_id,status,
                  bound_by,revision,created_at,updated_at
             FROM project_scene_binding WHERE project_id=%s ORDER BY binding_id""",
        (project_id,),
    )
    payload["scene_bindings"] = [_hashable(dict(zip(("binding_id", "organization_id", "factory_id", "ue_project_id", "scene_id", "status", "bound_by", "revision", "created_at", "updated_at"), row))) for row in cur.fetchall()]
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _json(value):
    return jsonify(value)


def _request_context_headers():
    """Read the browser-tab context carried on explicit requests.

    The authentication cookie remains the browser identity.  Organization,
    factory and project selection is request-scoped so two same-origin tabs do
    not overwrite each other's current context row.
    """
    return {
        "organization_id": (request.headers.get("X-OntoTwin-Organization-Id") or "").strip(),
        "factory_id": (request.headers.get("X-OntoTwin-Factory-Id") or "").strip(),
        "project_id": (request.headers.get("X-OntoTwin-Project-Id") or "").strip(),
    }


def _api(fn):
    """将数据库错误和产品级错误转换为统一响应。"""

    @wraps(fn)
    def wrapped(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except ApiError as exc:
            payload = {"error": exc.code, "message": exc.message}
            payload.update(exc.extra)
            return jsonify(payload), exc.status
        except Exception as exc:  # pragma: no cover - 真实数据库故障路径
            print(f"[tenant_api] {request.method} {request.path} failed: {exc}")
            return jsonify({"error": "storage_unavailable", "message": "组织服务暂不可用"}), 503

    return wrapped


def _require_pg():
    if os.environ.get("ONTOTWIN_STORE", "pg").lower() != "pg":
        raise ApiError(503, "4.8 组织服务需要 PostgreSQL", "postgresql_required")


def _load_session(cur, required=True):
    token = request.cookies.get(SESSION_COOKIE) or request.headers.get("X-OntoTwin-Session")
    if not token:
        if required:
            raise ApiError(401, "请先登录", "auth_required")
        return None
    cur.execute(
        """SELECT s.session_id, s.user_id, s.password_revision,
                  s.current_organization_id, s.current_factory_id, s.current_project_id,
                  s.expires_at, s.invalidated_at,
                  u.login_name, u.display_name, u.enabled, u.password_revision
           FROM user_session s JOIN user_account u ON u.user_id = s.user_id
          WHERE s.session_hash = %s""",
        (_token_hash(token),),
    )
    row = cur.fetchone()
    if not row or row[7] is not None or row[6] <= _now() or not row[10] or row[2] != row[11]:
        if required:
            raise ApiError(401, "登录已失效，请重新登录", "session_expired")
        return None
    # The heartbeat is deliberately throttled.  Authenticated GETs should not
    # each become a write transaction just because they refresh the session.
    cur.execute(
        """UPDATE user_session SET last_seen_at = now()
             WHERE session_id = %s AND last_seen_at < now() - interval '60 seconds'""",
        (row[0],),
    )
    session = {
        "session_id": row[0],
        "user_id": row[1],
        "login_name": row[8],
        "display_name": row[9],
        "password_revision": row[2],
        "organization_id": row[3],
        "factory_id": row[4],
        "project_id": row[5],
        "expires_at": row[6].isoformat() if hasattr(row[6], "isoformat") else str(row[6]),
    }
    context = _request_context_headers()
    if any(context.values()):
        org_id = context["organization_id"] or session["organization_id"]
        factory_id = context["factory_id"] or session["factory_id"]
        project_id = context["project_id"] or session["project_id"]

        if org_id and not _org_role(cur, session["user_id"], org_id):
            raise ApiError(403, "无权进入该组织", "forbidden")
        if factory_id:
            allowed, _ = _factory_allowed(cur, session["user_id"], org_id, factory_id)
            if not allowed:
                raise ApiError(403, "无权进入该工厂", "forbidden")
        if project_id:
            info = _project_allowed(cur, session["user_id"], project_id)
            if not info:
                raise ApiError(403, "无权访问该项目", "forbidden")
            if org_id and info["organization_id"] != org_id:
                raise ApiError(403, "项目不属于当前组织", "forbidden")
            if factory_id and info["factory_id"] != factory_id:
                raise ApiError(403, "项目不属于当前工厂", "forbidden")
            org_id, factory_id = info["organization_id"], info["factory_id"]

        session.update({
            "organization_id": org_id,
            "factory_id": factory_id,
            "project_id": project_id,
        })
    return session


def _org_role(cur, user_id, org_id):
    cur.execute(
        """SELECT role FROM organization_member
           WHERE organization_id=%s AND user_id=%s AND status='active' AND removed_at IS NULL""",
        (org_id, user_id),
    )
    row = cur.fetchone()
    return row[0] if row else None


def _factory_allowed(cur, user_id, org_id, factory_id, minimum="viewer"):
    role = _org_role(cur, user_id, org_id)
    if not role or ROLE_ORDER.get(role, -1) < ROLE_ORDER.get(minimum, 0):
        return False, role
    if role == "admin":
        cur.execute(
            "SELECT 1 FROM factory WHERE factory_id=%s AND organization_id=%s AND status='active'",
            (factory_id, org_id),
        )
    else:
        cur.execute(
            """SELECT 1 FROM factory_member fm JOIN factory f ON f.factory_id=fm.factory_id
                WHERE fm.factory_id=%s AND fm.user_id=%s AND fm.status='active'
                  AND fm.removed_at IS NULL AND f.organization_id=%s AND f.status='active'""",
            (factory_id, user_id, org_id),
        )
    return bool(cur.fetchone()), role


def _project_allowed(cur, user_id, project_id, minimum="view"):
    cur.execute(
        """SELECT p.organization_id, p.factory_id, p.name, p.status
             FROM project p WHERE p.id=%s AND p.deleted_at IS NULL""",
        (project_id,),
    )
    row = cur.fetchone()
    if not row or row[3] != "active":
        return None
    org_id, factory_id, name, status = row
    role = _org_role(cur, user_id, org_id)
    if role == "admin":
        return {"organization_id": org_id, "factory_id": factory_id, "name": name, "role": role}
    if minimum == "edit" and role != "editor":
        # 查看者即使持有历史残留的 project_permission=edit，也不能
        # 越过组织角色边界取得写权限。
        return None
    cur.execute(
        """SELECT 1 FROM factory_member WHERE factory_id=%s AND user_id=%s
                  AND status='active' AND removed_at IS NULL""",
        (factory_id, user_id),
    )
    in_factory = bool(cur.fetchone())
    cur.execute(
        """SELECT permission FROM project_permission
             WHERE project_id=%s AND user_id=%s AND revoked_at IS NULL""",
        (project_id, user_id),
    )
    perm = cur.fetchone()
    # 项目授权必须建立在有效工厂成员关系之上；不能靠一条残留的
    # project_permission 把用户“隐式”带入另一个工厂。
    if not in_factory:
        return None
    # 工厂成员默认可查看本厂项目；编辑必须再有项目级 edit 授权。
    # 新建项目时由 create_project 为创建者写入这条授权，避免编辑者
    # 因为加入工厂而意外获得全厂写权限。
    if minimum == "edit" and (not perm or perm[0] != "edit"):
        return None
    return {"organization_id": org_id, "factory_id": factory_id, "name": name, "role": role or "viewer"}


def legacy_project_scope():
    """返回旧 `/api/v2` 列表在 4.8 会话下可见的项目集合。

    未登录时返回 ``None``，保留旧测试夹具和维护接口兼容；一旦带有 4.8
    会话，缺少组织／工厂上下文返回空集合，防止旧路由把全库当成列表。
    这是全量路由参数化完成前的最小后端隔离闸门。
    """
    if os.environ.get("ONTOTWIN_STORE", "pg").lower() != "pg":
        return None
    token = request.cookies.get(SESSION_COOKIE) or request.headers.get("X-OntoTwin-Session")
    if not token:
        return None
    try:
        with pg.get_conn() as conn:
            with conn.cursor() as cur:
                session = _load_session(cur, required=False)
                if not session or not session.get("organization_id") or not session.get("factory_id"):
                    return set()
                allowed, role = _factory_allowed(cur, session["user_id"], session["organization_id"], session["factory_id"])
                if not allowed:
                    return set()
                cur.execute("SELECT id FROM project WHERE organization_id=%s AND factory_id=%s AND deleted_at IS NULL", (session["organization_id"], session["factory_id"]))
                return {r[0] for r in cur.fetchall()}
    except Exception:
        return set()


def legacy_project_role(project_id, minimum="view"):
    """旧路由最小角色检查；未登录返回 ``None`` 以兼容测试夹具。

    ``minimum='edit'`` is used by the legacy write gate.  It intentionally
    resolves project permission, not only the organization role.
    """
    if os.environ.get("ONTOTWIN_STORE", "pg").lower() != "pg":
        return None
    token = request.cookies.get(SESSION_COOKIE) or request.headers.get("X-OntoTwin-Session")
    if not token:
        return None
    try:
        with pg.get_conn() as conn:
            with conn.cursor() as cur:
                session = _load_session(cur, required=False)
                if not session:
                    return "none"
                info = _project_allowed(cur, session["user_id"], project_id, minimum=minimum)
                if not info:
                    return "none"
                return info["role"]
    except Exception:
        return "none"


def legacy_project_ue_allowed(project_id, ue_project_id, scene_id=""):
    """Validate an explicit legacy-route project against a UE scene binding.

    UE runtime calls do not carry a browser session.  In 4.8 they may still use
    the old ``/api/v2`` transport, but the project id must agree with the
    scene-level binding (or the old project-level binding during migration).
    """
    if not project_id or not ue_project_id:
        return False
    if os.environ.get("ONTOTWIN_STORE", "pg").lower() != "pg":
        return True
    try:
        with pg.get_conn() as conn:
            with conn.cursor() as cur:
                if scene_id:
                    cur.execute(
                        """SELECT 1 FROM project_scene_binding b JOIN ue_scene s ON s.scene_id=b.scene_id
                            WHERE b.project_id=%s AND b.ue_project_id=%s
                              AND (b.scene_id=%s OR s.stable_key=%s)
                              AND b.status='active'""",
                        (project_id, ue_project_id, scene_id, scene_id),
                    )
                    if cur.fetchone():
                        return True
                cur.execute(
                    """SELECT 1 FROM project p
                        WHERE p.id=%s AND p.deleted_at IS NULL
                          AND COALESCE(p.dataset->>'bound_ue_project_id','')=%s""",
                    (project_id, ue_project_id),
                )
                return bool(cur.fetchone())
    except Exception:
        return False


def _audit(cur, actor, org_id, factory_id, project_id, action, target, result="success", detail=None):
    cur.execute(
        """INSERT INTO audit_event(event_id, actor_user_id, organization_id, factory_id,
                  project_id, action, target, result, detail)
             VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (_id("evt"), actor, org_id, factory_id, project_id, action, target, result, Jsonb(detail or {})),
    )


def _set_cookie(response, token):
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=SESSION_TTL_HOURS * 3600,
        httponly=True,
        samesite="Lax",
        secure=os.environ.get("ONTOTWIN_COOKIE_SECURE", "0").lower() in {"1", "true", "yes"},
    )
    return response


def _clear_cookie(response):
    response.delete_cookie(SESSION_COOKIE)
    return response


def register_tenant_routes(app, project_store=None):
    """注册 4.8 API。调用一次即可；不改变旧版 /api 路由。"""

    @app.get("/api/v4.8/health")
    @_api
    def tenant_health():
        _require_pg()
        if not pg.ping():
            raise ApiError(503, "PostgreSQL 不可用", "database_unavailable")
        return _json({
            "ok": True,
            "version": "4.8",
            "release_id": os.environ.get("ONTOTWIN_RELEASE_ID", "4.8-dev"),
            "storage": "postgresql",
        })

    @app.post("/api/v4.8/auth/bootstrap")
    @_api
    def bootstrap():
        _require_pg()
        body = _body()
        env_name = _required(body, "environment_name")
        group_file = body.get("group_file")
        if group_file is not None:
            if not isinstance(group_file, dict) or group_file.get("format") != "ontotwin-group" or group_file.get("version") != 1 or not group_file.get("group_id"):
                raise ApiError(400, "集团信息文件格式不兼容", "invalid_group_file")
            group_data = group_file.get("group") if isinstance(group_file.get("group"), dict) else {}
            org_name = group_data.get("name") or body.get("organization_name")
            stable_group_id = group_file.get("group_id")
            logo_ref = group_data.get("logo_ref")
        else:
            org_name = _required(body, "organization_name")
            stable_group_id = _id("grp")
            logo_ref = body.get("logo_ref")
        if not org_name or not str(org_name).strip():
            raise ApiError(400, "集团信息缺少名称", "missing_field", field="organization_name")
        factory_name = (body.get("factory_name") or "").strip()
        login_name = _required(body, "login_name").lower()
        password = _required(body, "password")
        display_name = body.get("display_name") or login_name
        if len(password) < 8:
            raise ApiError(400, "初始密码至少 8 位", "weak_password")
        with pg.get_conn() as conn:
            with conn.transaction():
                with conn.cursor() as cur:
                    # 环境一旦创建，不能靠删除账号重新打开匿名初始化入口。
                    cur.execute("SELECT count(*) FROM environment")
                    if cur.fetchone()[0]:
                        raise ApiError(409, "本环境已经初始化", "already_bootstrapped")
                    env_id, org_id, user_id = (_id("env"), _id("org"), _id("usr"))
                    factory_id = None
                    cur.execute("INSERT INTO environment(environment_id,display_name) VALUES(%s,%s)", (env_id, env_name))
                    cur.execute(
                        """INSERT INTO organization(organization_id,environment_id,stable_group_id,name,logo_ref)
                           VALUES(%s,%s,%s,%s,%s)""",
                        (org_id, env_id, stable_group_id, org_name, logo_ref),
                    )
                    if factory_name:
                        factory_id = _id("fac")
                        cur.execute("INSERT INTO factory(factory_id,organization_id,name) VALUES(%s,%s,%s)", (factory_id, org_id, factory_name))
                    cur.execute(
                        """INSERT INTO user_account(user_id,environment_id,login_name,display_name,password_hash)
                           VALUES(%s,%s,%s,%s,%s)""",
                        (user_id, env_id, login_name, display_name, generate_password_hash(password)),
                    )
                    cur.execute(
                        "INSERT INTO organization_member(organization_id,user_id,role) VALUES(%s,%s,'admin')",
                        (org_id, user_id),
                    )
                    if factory_id:
                        cur.execute("INSERT INTO factory_member(factory_id,user_id) VALUES(%s,%s)", (factory_id, user_id))
                    _audit(cur, user_id, org_id, factory_id, None, "bootstrap", org_id)
        return _json({"environment_id": env_id, "organization_id": org_id, "factory_id": factory_id, "user_id": user_id}), 201

    @app.post("/api/v4.8/auth/login")
    @_api
    def login():
        _require_pg()
        body = _body()
        login_name = _required(body, "login_name").lower()
        password = _required(body, "password")
        with pg.get_conn() as conn:
            with conn.transaction():
                with conn.cursor() as cur:
                    cur.execute(
                        """SELECT user_id,password_hash,enabled,failed_count,locked_until,password_revision,display_name,must_change_password
                           FROM user_account WHERE login_name=%s ORDER BY created_at LIMIT 1""",
                        (login_name,),
                    )
                    row = cur.fetchone()
                    if not row:
                        raise ApiError(401, "账号或密码错误", "invalid_credentials")
                    if row[4] and row[4] > _now():
                        raise ApiError(423, "账号暂时锁定，请稍后再试", "account_locked")
                    if not row[2] or not check_password_hash(row[1], password):
                        failed = int(row[3] or 0) + 1
                        locked = _now() + timedelta(minutes=5) if failed >= 5 else None
                        cur.execute("UPDATE user_account SET failed_count=%s,locked_until=%s WHERE user_id=%s", (failed, locked, row[0]))
                        raise ApiError(401, "账号或密码错误", "invalid_credentials")
                    cur.execute("UPDATE user_account SET failed_count=0,locked_until=NULL,last_login_at=now() WHERE user_id=%s", (row[0],))
                    token = secrets.token_urlsafe(32)
                    sid = _id("ses")
                    expires = _now() + timedelta(hours=SESSION_TTL_HOURS)
                    cur.execute(
                        """INSERT INTO user_session(session_id,user_id,session_hash,expires_at,password_revision)
                           VALUES(%s,%s,%s,%s,%s)""",
                        (sid, row[0], _token_hash(token), expires, row[5]),
                    )
                    cur.execute(
                        """SELECT o.organization_id,o.name,om.role
                           FROM organization_member om JOIN organization o ON o.organization_id=om.organization_id
                          WHERE om.user_id=%s AND om.status='active' AND om.removed_at IS NULL AND o.status='active'
                          ORDER BY o.name""",
                        (row[0],),
                    )
                    orgs = [{"organization_id": r[0], "name": r[1], "role": r[2]} for r in cur.fetchall()]
        response = _json({"user": {"user_id": row[0], "login_name": login_name, "display_name": row[6], "must_change_password": bool(row[7])}, "organizations": orgs, "must_change_password": bool(row[7])})
        return _set_cookie(response, token)

    @app.post("/api/v4.8/auth/logout")
    @_api
    def logout():
        _require_pg()
        token = request.cookies.get(SESSION_COOKIE) or request.headers.get("X-OntoTwin-Session")
        if token:
            with pg.get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("UPDATE user_session SET invalidated_at=now() WHERE session_hash=%s", (_token_hash(token),))
        return _clear_cookie(_json({"ok": True}))

    @app.post("/api/v4.8/auth/change-password")
    @_api
    def change_password():
        _require_pg()
        body = _body()
        old_password = _required(body, "old_password")
        new_password = _required(body, "new_password")
        if len(new_password) < 8:
            raise ApiError(400, "新密码至少 8 位", "weak_password")
        with pg.get_conn() as conn:
            with conn.transaction():
                with conn.cursor() as cur:
                    session = _load_session(cur)
                    cur.execute("SELECT password_hash,password_revision FROM user_account WHERE user_id=%s FOR UPDATE", (session["user_id"],))
                    row = cur.fetchone()
                    if not row or not check_password_hash(row[0], old_password):
                        raise ApiError(401, "当前密码错误", "invalid_credentials")
                    cur.execute("UPDATE user_account SET password_hash=%s,password_revision=password_revision+1,must_change_password=FALSE,failed_count=0,locked_until=NULL WHERE user_id=%s", (generate_password_hash(new_password), session["user_id"]))
                    cur.execute("UPDATE user_session SET invalidated_at=now() WHERE user_id=%s", (session["user_id"],))
        return _clear_cookie(_json({"ok": True, "reauth_required": True}))

    @app.post("/api/v4.8/auth/profile")
    @_api
    def update_profile():
        _require_pg()
        body = _body()
        display_name = _required(body, "display_name")
        with pg.get_conn() as conn:
            with conn.cursor() as cur:
                session = _load_session(cur)
                cur.execute("UPDATE user_account SET display_name=%s WHERE user_id=%s", (display_name, session["user_id"]))
        return _json({"user_id": session["user_id"], "display_name": display_name})

    @app.get("/api/v4.8/auth/me")
    @_api
    def me():
        _require_pg()
        with pg.get_conn() as conn:
            with conn.cursor() as cur:
                session = _load_session(cur)
                cur.execute("SELECT must_change_password FROM user_account WHERE user_id=%s", (session["user_id"],))
                must_change = bool((cur.fetchone() or [False])[0])
                cur.execute(
                    """SELECT o.organization_id,o.name,om.role
                       FROM organization_member om JOIN organization o ON o.organization_id=om.organization_id
                      WHERE om.user_id=%s AND om.status='active' AND om.removed_at IS NULL ORDER BY o.name""",
                    (session["user_id"],),
                )
                orgs = [{"organization_id": r[0], "name": r[1], "role": r[2]} for r in cur.fetchall()]
        return _json({"user": {k: session[k] for k in ("user_id", "login_name", "display_name")}, "must_change_password": must_change, "context": session, "organizations": orgs})

    @app.get("/api/v4.8/organizations")
    @_api
    def organizations():
        _require_pg()
        with pg.get_conn() as conn:
            with conn.cursor() as cur:
                session = _load_session(cur)
                cur.execute(
                    """SELECT o.organization_id,o.name,o.logo_ref,o.status,om.role,
                              (SELECT count(*) FROM factory f WHERE f.organization_id=o.organization_id AND f.status='active')
                         FROM organization_member om JOIN organization o ON o.organization_id=om.organization_id
                        WHERE om.user_id=%s AND om.status='active' AND om.removed_at IS NULL AND o.status='active'
                        ORDER BY o.name""",
                    (session["user_id"],),
                )
                rows = [{"organization_id": r[0], "name": r[1], "logo_ref": r[2], "status": r[3], "role": r[4], "factory_count": r[5]} for r in cur.fetchall()]
        return _json({"items": rows, "current_organization_id": session["organization_id"]})

    @app.get("/api/v4.8/organizations/<org_id>/factories")
    @_api
    def factories(org_id):
        _require_pg()
        with pg.get_conn() as conn:
            with conn.cursor() as cur:
                session = _load_session(cur)
                role = _org_role(cur, session["user_id"], org_id)
                if not role:
                    raise ApiError(403, "无权访问该组织", "forbidden")
                if role == "admin":
                    cur.execute("SELECT factory_id,name,status,created_at FROM factory WHERE organization_id=%s AND status='active' ORDER BY name", (org_id,))
                else:
                    cur.execute(
                        """SELECT f.factory_id,f.name,f.status,f.created_at FROM factory_member fm
                           JOIN factory f ON f.factory_id=fm.factory_id
                          WHERE fm.user_id=%s AND f.organization_id=%s AND fm.status='active' AND fm.removed_at IS NULL
                            AND f.status='active' ORDER BY f.name""",
                        (session["user_id"], org_id),
                    )
                rows = [{"factory_id": r[0], "name": r[1], "status": r[2], "created_at": r[3].isoformat() if hasattr(r[3], "isoformat") else r[3]} for r in cur.fetchall()]
        return _json({"items": rows, "current_factory_id": session["factory_id"] if session["organization_id"] == org_id else None})

    @app.post("/api/v4.8/context")
    @_api
    def set_context():
        _require_pg()
        body = _body()
        org_id = _required(body, "organization_id")
        factory_id = body.get("factory_id")
        project_id = body.get("project_id")
        with pg.get_conn() as conn:
            with conn.transaction():
                with conn.cursor() as cur:
                    session = _load_session(cur)
                    role = _org_role(cur, session["user_id"], org_id)
                    if not role:
                        raise ApiError(403, "无权进入该组织", "forbidden")
                    if factory_id:
                        allowed, _ = _factory_allowed(cur, session["user_id"], org_id, factory_id)
                        if not allowed:
                            raise ApiError(403, "无权进入该工厂", "forbidden")
                    if project_id:
                        info = _project_allowed(cur, session["user_id"], project_id)
                        if not info or info["organization_id"] != org_id or info["factory_id"] != factory_id:
                            raise ApiError(403, "无权进入该项目", "forbidden")
                    cur.execute(
                        """UPDATE user_session SET current_organization_id=%s,current_factory_id=%s,current_project_id=%s
                           WHERE session_id=%s""",
                        (org_id, factory_id, project_id, session["session_id"]),
                    )
        if project_id and project_store is not None:
            # 兼容旧版 UE 绑定：把「当前项目」同步到全局激活态，让不带
            # project_id 的旧绑定接口（/api/v2/ue/bind_active_project）也能
            # 绑到本项目，而不是报 no active project。
            try:
                project_store.activate(str(project_id))
            except Exception:
                pass
        return _json({"organization_id": org_id, "factory_id": factory_id, "project_id": project_id})

    @app.get("/api/v4.8/projects")
    @_api
    def projects():
        _require_pg()
        org_id = request.args.get("organization_id")
        factory_id = request.args.get("factory_id")
        with pg.get_conn() as conn:
            with conn.cursor() as cur:
                session = _load_session(cur)
                org_id = org_id or session["organization_id"]
                factory_id = factory_id or session["factory_id"]
                if not org_id or not factory_id:
                    raise ApiError(400, "请先选择组织和工厂", "context_required")
                allowed, role = _factory_allowed(cur, session["user_id"], org_id, factory_id)
                if not allowed:
                    raise ApiError(403, "无权访问该工厂", "forbidden")
                cur.execute(
                    """SELECT p.id,p.name,p.created_at,p.schema_version,p.status,
                              (SELECT count(*) FROM object_type o WHERE o.project_id=p.id AND o.deleted_at IS NULL),
                              (SELECT count(*) FROM instance i WHERE i.project_id=p.id AND i.deleted_at IS NULL)
                         FROM project p WHERE p.organization_id=%s AND p.factory_id=%s AND p.deleted_at IS NULL
                        ORDER BY p.name""",
                    (org_id, factory_id),
                )
                rows = [{"project_id": r[0], "name": r[1], "created_at": r[2], "schema_version": r[3], "status": r[4], "type_count": r[5], "instance_count": r[6]} for r in cur.fetchall()]
        return _json({"items": rows, "current_project_id": session["project_id"]})

    @app.post("/api/v4.8/organizations")
    @_api
    def create_organization():
        _require_pg()
        body = _body()
        name = _required(body, "name")
        with pg.get_conn() as conn:
            with conn.transaction():
                with conn.cursor() as cur:
                    session = _load_session(cur)
                    current_org = session["organization_id"]
                    role = _org_role(cur, session["user_id"], current_org)
                    if role != "admin":
                        raise ApiError(403, "只有组织管理员可以新建组织", "forbidden")
                    cur.execute("SELECT environment_id FROM organization WHERE organization_id=%s", (current_org,))
                    env_id = cur.fetchone()[0]
                    org_id = _id("org")
                    cur.execute("INSERT INTO organization(organization_id,environment_id,stable_group_id,name,logo_ref) VALUES(%s,%s,%s,%s,%s)", (org_id, env_id, org_id, name, body.get("logo_ref")))
                    cur.execute("INSERT INTO organization_member(organization_id,user_id,role) VALUES(%s,%s,'admin')", (org_id, session["user_id"]))
                    _audit(cur, session["user_id"], org_id, None, None, "organization.create", org_id)
        return _json({"organization_id": org_id, "name": name}), 201

    @app.get("/api/v4.8/organizations/<org_id>/group-package")
    @_api
    def export_group_package(org_id):
        _require_pg()
        with pg.get_conn() as conn:
            with conn.cursor() as cur:
                session = _load_session(cur)
                if _org_role(cur, session["user_id"], org_id) != "admin":
                    raise ApiError(403, "只有组织管理员可以导出集团信息", "forbidden")
                cur.execute("SELECT stable_group_id,name,logo_ref FROM organization WHERE organization_id=%s AND status='active'", (org_id,))
                row = cur.fetchone()
                if not row:
                    raise ApiError(404, "组织不存在", "not_found")
        return _json({"format": "ontotwin-group", "version": 1, "group_id": row[0], "group": {"name": row[1], "logo_ref": row[2]}})

    @app.post("/api/v4.8/organizations/import-group")
    @_api
    def import_group_package():
        _require_pg()
        body = _body()
        package = body.get("group_file") if isinstance(body.get("group_file"), dict) else body
        if package.get("format") != "ontotwin-group" or package.get("version") != 1 or not package.get("group_id"):
            raise ApiError(400, "集团信息文件格式不兼容", "invalid_group_file")
        group = package.get("group") if isinstance(package.get("group"), dict) else {}
        name = (group.get("name") or "").strip()
        if not name:
            raise ApiError(400, "集团信息缺少名称", "missing_field", field="group.name")
        with pg.get_conn() as conn:
            with conn.transaction():
                with conn.cursor() as cur:
                    session = _load_session(cur)
                    cur.execute("SELECT environment_id FROM organization WHERE organization_id=%s", (session["organization_id"],))
                    env_id = cur.fetchone()[0]
                    cur.execute("SELECT organization_id FROM organization WHERE environment_id=%s AND stable_group_id=%s AND status='active'", (env_id, package["group_id"]))
                    if cur.fetchone():
                        raise ApiError(409, "本环境已存在该集团", "organization_exists")
                    org_id = _id("org")
                    cur.execute("INSERT INTO organization(organization_id,environment_id,stable_group_id,name,logo_ref) VALUES(%s,%s,%s,%s,%s)", (org_id, env_id, package["group_id"], name, group.get("logo_ref")))
                    cur.execute("INSERT INTO organization_member(organization_id,user_id,role) VALUES(%s,%s,'admin')", (org_id, session["user_id"]))
                    _audit(cur, session["user_id"], org_id, None, None, "organization.import_group", org_id)
        return _json({"organization_id": org_id, "name": name, "group_id": package["group_id"]}), 201

    @app.post("/api/v4.8/organizations/<org_id>/factories")
    @_api
    def create_factory(org_id):
        _require_pg()
        body = _body()
        name = _required(body, "name")
        with pg.get_conn() as conn:
            with conn.transaction():
                with conn.cursor() as cur:
                    session = _load_session(cur)
                    role = _org_role(cur, session["user_id"], org_id)
                    if role not in {"admin", "editor"}:
                        raise ApiError(403, "只有组织管理员或编辑者可以新建工厂", "forbidden")
                    factory_id = _id("fac")
                    cur.execute("INSERT INTO factory(factory_id,organization_id,name) VALUES(%s,%s,%s)", (factory_id, org_id, name))
                    cur.execute("INSERT INTO factory_member(factory_id,user_id) VALUES(%s,%s)", (factory_id, session["user_id"]))
                    _audit(cur, session["user_id"], org_id, factory_id, None, "factory.create", factory_id)
        return _json({"factory_id": factory_id, "name": name}), 201

    @app.post("/api/v4.8/organizations/<org_id>/members")
    @_api
    def add_member(org_id):
        _require_pg()
        body = _body()
        login_name = _required(body, "login_name").lower()
        role = body.get("role", "editor")
        if role not in ROLE_ORDER:
            raise ApiError(400, "角色必须为 admin、editor 或 viewer", "invalid_role")
        with pg.get_conn() as conn:
            with conn.transaction():
                with conn.cursor() as cur:
                    session = _load_session(cur)
                    if _org_role(cur, session["user_id"], org_id) != "admin":
                        raise ApiError(403, "只有组织管理员可以管理成员", "forbidden")
                    cur.execute("SELECT environment_id FROM organization WHERE organization_id=%s", (org_id,))
                    row = cur.fetchone()
                    if not row:
                        raise ApiError(404, "组织不存在", "not_found")
                    env_id = row[0]
                    cur.execute("SELECT user_id FROM user_account WHERE environment_id=%s AND login_name=%s", (env_id, login_name))
                    existing = cur.fetchone()
                    if existing:
                        user_id = existing[0]
                    else:
                        password = _required(body, "password")
                        if len(password) < 8:
                            raise ApiError(400, "初始密码至少 8 位", "weak_password")
                        user_id = _id("usr")
                        cur.execute("INSERT INTO user_account(user_id,environment_id,login_name,display_name,password_hash,must_change_password) VALUES(%s,%s,%s,%s,%s,TRUE)", (user_id, env_id, login_name, body.get("display_name") or login_name, generate_password_hash(password)))
                    cur.execute("""INSERT INTO organization_member(organization_id,user_id,role) VALUES(%s,%s,%s)
                       ON CONFLICT(organization_id,user_id) DO UPDATE SET role=EXCLUDED.role,status='active',removed_at=NULL""", (org_id, user_id, role))
                    for factory_id in body.get("factory_ids") or []:
                        cur.execute("SELECT 1 FROM factory WHERE factory_id=%s AND organization_id=%s", (factory_id, org_id))
                        if not cur.fetchone():
                            raise ApiError(400, "工厂不属于该组织", "invalid_factory")
                        cur.execute("""INSERT INTO factory_member(factory_id,user_id) VALUES(%s,%s)
                           ON CONFLICT(factory_id,user_id) DO UPDATE SET status='active',removed_at=NULL""", (factory_id, user_id))
                    _audit(cur, session["user_id"], org_id, None, None, "member.upsert", user_id, detail={"role": role})
        return _json({"user_id": user_id, "organization_id": org_id, "role": role}), 201

    @app.get("/api/v4.8/organizations/<org_id>/members")
    @_api
    def list_members(org_id):
        """Return active organization members and their factory assignments."""
        _require_pg()
        with pg.get_conn() as conn:
            with conn.cursor() as cur:
                session = _load_session(cur)
                if not _org_role(cur, session["user_id"], org_id):
                    raise ApiError(403, "无权访问该组织", "forbidden")
                cur.execute(
                    """SELECT u.user_id,u.login_name,u.display_name,u.enabled,
                              u.created_at,om.role,
                              f.factory_id,f.name
                         FROM organization_member om
                         JOIN user_account u ON u.user_id=om.user_id
                         LEFT JOIN factory_member fm
                           ON fm.user_id=u.user_id AND fm.status='active' AND fm.removed_at IS NULL
                         LEFT JOIN factory f
                           ON f.factory_id=fm.factory_id AND f.organization_id=om.organization_id AND f.status='active'
                        WHERE om.organization_id=%s AND om.status='active' AND om.removed_at IS NULL
                        ORDER BY u.display_name,u.login_name,f.name""",
                    (org_id,),
                )
                members = {}
                for row in cur.fetchall():
                    member = members.setdefault(row[0], {
                        "user_id": row[0],
                        "login_name": row[1],
                        "display_name": row[2],
                        "enabled": bool(row[3]),
                        "created_at": row[4].isoformat() if hasattr(row[4], "isoformat") else row[4],
                        "role": row[5],
                        "factories": [],
                    })
                    if row[6]:
                        member["factories"].append({"factory_id": row[6], "name": row[7]})
        return _json({"items": list(members.values())})

    @app.patch("/api/v4.8/organizations/<org_id>/members/<user_id>")
    @_api
    def update_member(org_id, user_id):
        """Update a member role and its factory assignments."""
        _require_pg()
        body = _body()
        role = body.get("role")
        factory_ids = body.get("factory_ids")
        if role is not None and role not in ROLE_ORDER:
            raise ApiError(400, "角色必须为 admin、editor 或 viewer", "invalid_role")
        if factory_ids is not None and not isinstance(factory_ids, list):
            raise ApiError(400, "factory_ids 必须是数组", "invalid_factory_ids")
        with pg.get_conn() as conn:
            with conn.transaction():
                with conn.cursor() as cur:
                    session = _load_session(cur)
                    if _org_role(cur, session["user_id"], org_id) != "admin":
                        raise ApiError(403, "只有组织管理员可以管理成员", "forbidden")
                    cur.execute(
                        "SELECT role FROM organization_member WHERE organization_id=%s AND user_id=%s AND status='active' AND removed_at IS NULL FOR UPDATE",
                        (org_id, user_id),
                    )
                    current = cur.fetchone()
                    if not current:
                        raise ApiError(404, "成员不存在", "member_not_found")
                    if role is not None and current[0] == "admin" and role != "admin":
                        cur.execute("SELECT count(*) FROM organization_member WHERE organization_id=%s AND role='admin' AND status='active' AND removed_at IS NULL", (org_id,))
                        if int(cur.fetchone()[0] or 0) <= 1:
                            raise ApiError(400, "组织至少需要保留一名管理员", "last_admin")
                    if role is not None:
                        cur.execute("UPDATE organization_member SET role=%s WHERE organization_id=%s AND user_id=%s", (role, org_id, user_id))
                    if factory_ids is not None:
                        cur.execute(
                            """SELECT factory_id FROM factory WHERE organization_id=%s AND status='active'""",
                            (org_id,),
                        )
                        valid = {row[0] for row in cur.fetchall()}
                        invalid = [fid for fid in factory_ids if fid not in valid]
                        if invalid:
                            raise ApiError(400, "存在不属于该组织的工厂", "invalid_factory")
                        cur.execute(
                            """UPDATE factory_member SET status='removed',removed_at=now()
                                WHERE user_id=%s AND factory_id IN
                                  (SELECT factory_id FROM factory WHERE organization_id=%s)""",
                            (user_id, org_id),
                        )
                        for factory_id in factory_ids:
                            cur.execute(
                                """INSERT INTO factory_member(factory_id,user_id,status,removed_at)
                                   VALUES(%s,%s,'active',NULL)
                                   ON CONFLICT(factory_id,user_id) DO UPDATE
                                     SET status='active',removed_at=NULL""",
                                (factory_id, user_id),
                            )
                        if factory_ids is not None:
                            cur.execute("""UPDATE project_permission pp SET revoked_at=now()
                                FROM project p WHERE pp.project_id=p.id AND pp.user_id=%s AND p.organization_id=%s
                                  AND p.factory_id NOT IN (SELECT unnest(%s::text[])) AND pp.revoked_at IS NULL""", (user_id, org_id, factory_ids))
                    _audit(cur, session["user_id"], org_id, None, None, "member.update", user_id, detail={"role": role, "factory_ids": factory_ids})
        return _json({"user_id": user_id, "organization_id": org_id, "role": role})

    @app.delete("/api/v4.8/organizations/<org_id>/members/<user_id>")
    @_api
    def remove_member(org_id, user_id):
        _require_pg()
        with pg.get_conn() as conn:
            with conn.transaction():
                with conn.cursor() as cur:
                    session = _load_session(cur)
                    if _org_role(cur, session["user_id"], org_id) != "admin":
                        raise ApiError(403, "只有组织管理员可以管理成员", "forbidden")
                    if user_id == session["user_id"]:
                        raise ApiError(400, "不能移除当前登录账号", "self_remove_forbidden")
                    cur.execute("SELECT role FROM organization_member WHERE organization_id=%s AND user_id=%s AND status='active' AND removed_at IS NULL FOR UPDATE", (org_id, user_id))
                    member = cur.fetchone()
                    if not member:
                        raise ApiError(404, "成员不存在", "member_not_found")
                    if member[0] == "admin":
                        cur.execute("SELECT count(*) FROM organization_member WHERE organization_id=%s AND role='admin' AND status='active' AND removed_at IS NULL", (org_id,))
                        if int(cur.fetchone()[0] or 0) <= 1:
                            raise ApiError(400, "组织至少需要保留一名管理员", "last_admin")
                    cur.execute("UPDATE organization_member SET status='removed',removed_at=now() WHERE organization_id=%s AND user_id=%s", (org_id, user_id))
                    cur.execute("""UPDATE factory_member SET status='removed',removed_at=now()
                                   WHERE user_id=%s AND factory_id IN (SELECT factory_id FROM factory WHERE organization_id=%s)""", (user_id, org_id))
                    _audit(cur, session["user_id"], org_id, None, None, "member.remove", user_id)
        return _json({"ok": True, "user_id": user_id, "organization_id": org_id})

    @app.post("/api/v4.8/projects")
    @_api
    def create_project():
        _require_pg()
        body = _body()
        name = _required(body, "name")
        org_id = _required(body, "organization_id")
        factory_id = _required(body, "factory_id")
        with pg.get_conn() as conn:
            with conn.transaction():
                with conn.cursor() as cur:
                    session = _load_session(cur)
                    allowed, role = _factory_allowed(cur, session["user_id"], org_id, factory_id, minimum="editor")
                    if not allowed:
                        raise ApiError(403, "只有该工厂的编辑者或管理员可以新建项目", "forbidden")
                    cur.execute("SELECT environment_id FROM organization WHERE organization_id=%s", (org_id,))
                    env = cur.fetchone()
                    if not env:
                        raise ApiError(404, "组织不存在", "not_found")
                    pid = _id("p")
                    created = time.strftime("%Y-%m-%d %H:%M:%S")
                    cur.execute(
                        """INSERT INTO project(id,name,created_at,schema_version,dataset,calibration,spatial_profile,
                              components,instance_roster,frames,scene_interactions,media_policy,web_interactions,
                              environment_id,organization_id,factory_id,status,updated_at)
                           VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'active',now())""",
                        (pid, name, created, CURRENT_SCHEMA_VERSION, None, None, Jsonb(_default_spatial_profile()), Jsonb({}), Jsonb([]), Jsonb([]), Jsonb(_default_scene_interactions()), Jsonb(_default_media_policy()), Jsonb(_default_web_interactions()), env[0], org_id, factory_id),
                    )
                    cur.execute("INSERT INTO project_permission(project_id,user_id,permission,granted_by) VALUES(%s,%s,'edit',%s)", (pid, session["user_id"], session["user_id"]))
                    _audit(cur, session["user_id"], org_id, factory_id, pid, "project.create", pid)
        return _json({"project_id": pid, "name": name, "organization_id": org_id, "factory_id": factory_id}), 201

    @app.get("/api/v4.8/projects/<project_id>/permissions")
    @_api
    def project_permissions(project_id):
        _require_pg()
        with pg.get_conn() as conn:
            with conn.cursor() as cur:
                session = _load_session(cur)
                info = _project_allowed(cur, session["user_id"], project_id)
                if not info:
                    raise ApiError(403, "无权查看项目授权", "forbidden")
                cur.execute("""SELECT pp.user_id,u.login_name,u.display_name,pp.permission,pp.granted_at
                                FROM project_permission pp JOIN user_account u ON u.user_id=pp.user_id
                               WHERE pp.project_id=%s AND pp.revoked_at IS NULL ORDER BY u.display_name""", (project_id,))
                rows = [{"user_id": r[0], "login_name": r[1], "display_name": r[2], "permission": r[3], "granted_at": r[4]} for r in cur.fetchall()]
        return _json({"items": rows})

    @app.post("/api/v4.8/projects/<project_id>/permissions")
    @_api
    def set_project_permission(project_id):
        _require_pg()
        body = _body()
        user_id = _required(body, "user_id")
        permission = body.get("permission", "view")
        if permission not in {"view", "edit"}:
            raise ApiError(400, "permission 必须为 view 或 edit", "invalid_permission")
        with pg.get_conn() as conn:
            with conn.transaction():
                with conn.cursor() as cur:
                    session = _load_session(cur)
                    cur.execute("SELECT organization_id,factory_id FROM project WHERE id=%s AND deleted_at IS NULL", (project_id,))
                    project = cur.fetchone()
                    if not project:
                        raise ApiError(404, "项目不存在", "not_found")
                    org_id, factory_id = project
                    if _org_role(cur, session["user_id"], org_id) != "admin":
                        raise ApiError(403, "只有组织管理员可以分配项目权限", "forbidden")
                    cur.execute("""SELECT 1 FROM organization_member WHERE organization_id=%s AND user_id=%s AND status='active' AND removed_at IS NULL""", (org_id, user_id))
                    if not cur.fetchone():
                        raise ApiError(400, "用户必须先加入该组织", "organization_membership_required")
                    cur.execute("""SELECT 1 FROM factory_member WHERE factory_id=%s AND user_id=%s AND status='active' AND removed_at IS NULL""", (factory_id, user_id))
                    in_factory = bool(cur.fetchone())
                    if not in_factory:
                        raise ApiError(400, "用户必须先加入该工厂", "factory_membership_required")
                    cur.execute("""INSERT INTO project_permission(project_id,user_id,permission,granted_by,revoked_at)
                       VALUES(%s,%s,%s,%s,NULL)
                       ON CONFLICT(project_id,user_id) DO UPDATE SET permission=EXCLUDED.permission,granted_by=EXCLUDED.granted_by,granted_at=now(),revoked_at=NULL""", (project_id, user_id, permission, session["user_id"]))
                    _audit(cur, session["user_id"], org_id, factory_id, project_id, "project.permission", user_id, detail={"permission": permission})
        return _json({"project_id": project_id, "user_id": user_id, "permission": permission})

    @app.get("/api/v4.8/projects/<project_id>/snapshot")
    @_api
    def project_snapshot(project_id):
        _require_pg()
        with pg.get_conn() as conn:
            with conn.cursor() as cur:
                session = _load_session(cur)
                info = _project_allowed(cur, session["user_id"], project_id)
                if not info:
                    raise ApiError(403, "无权访问该项目", "forbidden")
                if project_store is None or not hasattr(project_store, "_read_project"):
                    raise ApiError(503, "项目存储尚未提供 PostgreSQL 快照读取", "storage_unavailable")
                snapshot = project_store._read_project(project_id)
                if snapshot is None:
                    raise ApiError(404, "项目不存在", "not_found")
        return _json({"project": snapshot, "organization_id": info["organization_id"], "factory_id": info["factory_id"]})

    @app.post("/api/v4.8/ue/projects")
    @_api
    def register_ue_project():
        _require_pg()
        body = _body()
        stable_key = _required(body, "stable_key")
        display_name = body.get("display_name") or stable_key
        with pg.get_conn() as conn:
            with conn.transaction():
                with conn.cursor() as cur:
                    session = _load_session(cur)
                    cur.execute("SELECT ue_project_id FROM ue_project WHERE stable_key=%s", (stable_key,))
                    row = cur.fetchone()
                    ue_id = row[0] if row else _id("ue")
                    if row:
                        cur.execute("UPDATE ue_project SET display_name=%s,last_seen_at=now() WHERE ue_project_id=%s", (display_name, ue_id))
                    else:
                        cur.execute("INSERT INTO ue_project(ue_project_id,stable_key,display_name,last_seen_at) VALUES(%s,%s,%s,now())", (ue_id, stable_key, display_name))
        return _json({"ue_project_id": ue_id, "stable_key": stable_key, "display_name": display_name})

    @app.post("/api/v4.8/ue/projects/<ue_project_id>/scenes")
    @_api
    def register_ue_scene(ue_project_id):
        _require_pg()
        body = _body()
        stable_key = _required(body, "stable_key")
        with pg.get_conn() as conn:
            with conn.cursor() as cur:
                _load_session(cur)
                cur.execute("SELECT 1 FROM ue_project WHERE ue_project_id=%s", (ue_project_id,))
                if not cur.fetchone():
                    raise ApiError(404, "UE 工程不存在", "not_found")
                cur.execute("SELECT scene_id FROM ue_scene WHERE ue_project_id=%s AND stable_key=%s", (ue_project_id, stable_key))
                row = cur.fetchone()
                scene_id = row[0] if row else _id("scene")
                if row:
                    cur.execute("UPDATE ue_scene SET display_name=%s,level_path=%s WHERE scene_id=%s", (body.get("display_name") or stable_key, body.get("level_path"), scene_id))
                else:
                    cur.execute("INSERT INTO ue_scene(scene_id,ue_project_id,stable_key,display_name,level_path) VALUES(%s,%s,%s,%s,%s)", (scene_id, ue_project_id, stable_key, body.get("display_name") or stable_key, body.get("level_path")))
        return _json({"scene_id": scene_id, "ue_project_id": ue_project_id, "stable_key": stable_key})

    @app.post("/api/v4.8/bindings")
    @_api
    def bind_scene():
        _require_pg()
        body = _body()
        project_id = _required(body, "project_id")
        ue_project_id = _required(body, "ue_project_id")
        scene_id = _required(body, "scene_id")
        with pg.get_conn() as conn:
            with conn.transaction():
                with conn.cursor() as cur:
                    session = _load_session(cur)
                    info = _project_allowed(cur, session["user_id"], project_id, minimum="edit")
                    if not info:
                        raise ApiError(403, "无权绑定该项目", "forbidden")
                    cur.execute("SELECT 1 FROM ue_scene WHERE scene_id=%s AND ue_project_id=%s", (scene_id, ue_project_id))
                    if not cur.fetchone():
                        raise ApiError(400, "UE 工程与场景不匹配", "invalid_scene")
                    cur.execute("SELECT binding_id,project_id FROM project_scene_binding WHERE ue_project_id=%s AND scene_id=%s AND status='active'", (ue_project_id, scene_id))
                    conflict = cur.fetchone()
                    if conflict and conflict[1] != project_id:
                        raise ApiError(409, "该 UE 场景已经绑定其他项目", "scene_binding_conflict", binding_id=conflict[0])
                    cur.execute("UPDATE project_scene_binding SET status='replaced',updated_at=now() WHERE project_id=%s AND status='active'", (project_id,))
                    binding_id = conflict[0] if conflict and conflict[1] == project_id else _id("bind")
                    if conflict and conflict[1] == project_id:
                        cur.execute("UPDATE project_scene_binding SET ue_project_id=%s,scene_id=%s,updated_at=now(),revision=revision+1 WHERE binding_id=%s", (ue_project_id, scene_id, binding_id))
                    else:
                        cur.execute("""INSERT INTO project_scene_binding(binding_id,project_id,organization_id,factory_id,ue_project_id,scene_id,bound_by)
                           VALUES(%s,%s,%s,%s,%s,%s,%s)""", (binding_id, project_id, info["organization_id"], info["factory_id"], ue_project_id, scene_id, session["user_id"]))
                    _audit(cur, session["user_id"], info["organization_id"], info["factory_id"], project_id, "scene.bind", binding_id)
        return _json({"binding_id": binding_id, "project_id": project_id, "ue_project_id": ue_project_id, "scene_id": scene_id})

    @app.get("/api/v4.8/bindings")
    @_api
    def bindings():
        _require_pg()
        with pg.get_conn() as conn:
            with conn.cursor() as cur:
                session = _load_session(cur)
                project_id = request.args.get("project_id") or session["project_id"]
                if project_id and not _project_allowed(cur, session["user_id"], project_id):
                    raise ApiError(403, "无权访问该项目绑定", "forbidden")
                if project_id:
                    cur.execute("""SELECT b.binding_id,b.project_id,b.ue_project_id,s.scene_id,u.display_name,s.level_path,b.status,b.revision
                       FROM project_scene_binding b JOIN ue_project u ON u.ue_project_id=b.ue_project_id
                       JOIN ue_scene s ON s.scene_id=b.scene_id WHERE b.project_id=%s AND b.status='active'""", (project_id,))
                else:
                    cur.execute("""SELECT b.binding_id,b.project_id,b.ue_project_id,s.scene_id,u.display_name,s.level_path,b.status,b.revision
                       FROM project_scene_binding b JOIN ue_project u ON u.ue_project_id=b.ue_project_id
                       JOIN ue_scene s ON s.scene_id=b.scene_id JOIN project p ON p.id=b.project_id
                      WHERE b.organization_id=%s AND b.status='active'""", (session["organization_id"],))
                rows = [{"binding_id": r[0], "project_id": r[1], "ue_project_id": r[2], "scene_id": r[3], "ue_project_name": r[4], "level_path": r[5], "status": r[6], "revision": r[7]} for r in cur.fetchall()]
        return _json({"items": rows})

    @app.post("/api/v4.8/ue/connections/claim")
    @_api
    def claim_ue_connection():
        _require_pg()
        body = _body()
        ue_project_id = _required(body, "ue_project_id")
        scene_id = _required(body, "scene_id")
        project_id = body.get("project_id")
        with pg.get_conn() as conn:
            with conn.transaction():
                with conn.cursor() as cur:
                    session = _load_session(cur)
                    cur.execute("UPDATE ue_connection SET released_at=now(),status='stale' WHERE ue_project_id=%s AND scene_id=%s AND released_at IS NULL AND last_heartbeat_at < now() - interval '60 seconds'", (ue_project_id, scene_id))
                    cur.execute("SELECT connection_id,project_id FROM ue_connection WHERE ue_project_id=%s AND scene_id=%s AND released_at IS NULL AND status='connected'", (ue_project_id, scene_id))
                    current = cur.fetchone()
                    if current:
                        raise ApiError(409, "该 UE 场景已有连接，请先释放或等待 60 秒", "ue_connection_conflict", connection_id=current[0])
                    if project_id and not _project_allowed(cur, session["user_id"], project_id, minimum="view"):
                        raise ApiError(403, "无权连接该项目", "forbidden")
                    connection_id = _id("conn")
                    cur.execute("INSERT INTO ue_connection(connection_id,ue_project_id,scene_id,project_id,session_id) VALUES(%s,%s,%s,%s,%s)", (connection_id, ue_project_id, scene_id, project_id, session["session_id"]))
        return _json({"connection_id": connection_id, "expires_after_seconds": 60})

    @app.post("/api/v4.8/ue/connections/<connection_id>/heartbeat")
    @_api
    def heartbeat(connection_id):
        _require_pg()
        with pg.get_conn() as conn:
            with conn.cursor() as cur:
                session = _load_session(cur)
                cur.execute("UPDATE ue_connection SET last_heartbeat_at=now() WHERE connection_id=%s AND session_id=%s AND released_at IS NULL", (connection_id, session["session_id"]))
                if cur.rowcount != 1:
                    raise ApiError(404, "连接不存在或已释放", "not_found")
        return _json({"ok": True, "connection_id": connection_id})

    @app.delete("/api/v4.8/ue/connections/<connection_id>")
    @_api
    def release_connection(connection_id):
        _require_pg()
        with pg.get_conn() as conn:
            with conn.cursor() as cur:
                session = _load_session(cur)
                cur.execute("UPDATE ue_connection SET released_at=now(),status='released' WHERE connection_id=%s AND session_id=%s AND released_at IS NULL", (connection_id, session["session_id"]))
                if cur.rowcount != 1:
                    raise ApiError(404, "连接不存在或已释放", "not_found")
        return _json({"ok": True})

    @app.post("/api/v4.8/backups/manifest")
    @_api
    def register_backup_manifest():
        """登记外部 pg_dump/恢复演练产物；API 不伪造备份文件。"""
        _require_pg()
        body = _body()
        storage_uri = _required(body, "storage_uri")
        checksum = _required(body, "checksum")
        with pg.get_conn() as conn:
            with conn.cursor() as cur:
                session = _load_session(cur)
                cur.execute("SELECT organization_id FROM organization_member WHERE user_id=%s AND role='admin' AND status='active' AND removed_at IS NULL LIMIT 1", (session["user_id"],))
                row = cur.fetchone()
                if not row:
                    raise ApiError(403, "只有组织管理员可以登记备份", "forbidden")
                cur.execute("SELECT environment_id FROM organization WHERE organization_id=%s", (row[0],))
                env_id = cur.fetchone()[0]
                backup_id = _id("backup")
                cur.execute("INSERT INTO backup_manifest(backup_id,environment_id,storage_uri,checksum) VALUES(%s,%s,%s,%s)", (backup_id, env_id, storage_uri, checksum))
        return _json({"backup_id": backup_id, "environment_id": env_id}), 201

    @app.post("/api/v4.8/migrations/preflight")
    @_api
    def migration_preflight():
        """建立迁移批次和预检报告，不改项目归属、不冻结写入。"""
        _require_pg()
        body = _body()
        org_id = _required(body, "organization_id")
        factory_id = _required(body, "factory_id")
        requested = body.get("project_ids")
        if requested is not None and not isinstance(requested, list):
            raise ApiError(400, "project_ids 必须是数组", "invalid_field")
        with pg.get_conn() as conn:
            with conn.transaction():
                with conn.cursor() as cur:
                    session = _load_session(cur)
                    if _org_role(cur, session["user_id"], org_id) != "admin":
                        raise ApiError(403, "只有组织管理员可以执行迁移预检", "forbidden")
                    allowed, _ = _factory_allowed(cur, session["user_id"], org_id, factory_id, minimum="viewer")
                    if not allowed:
                        raise ApiError(403, "目标工厂不存在或无权访问", "forbidden")
                    cur.execute("SELECT environment_id FROM organization WHERE organization_id=%s", (org_id,))
                    env_id = cur.fetchone()[0]
                    if requested:
                        cur.execute("""SELECT p.id,p.name,p.organization_id,p.factory_id,p.dataset
                           FROM project p WHERE p.id = ANY(%s) AND p.deleted_at IS NULL ORDER BY p.id""", (requested,))
                    else:
                        cur.execute("""SELECT p.id,p.name,p.organization_id,p.factory_id,p.dataset
                           FROM project p WHERE p.deleted_at IS NULL AND (p.organization_id IS NULL OR p.factory_id IS NULL)
                          ORDER BY p.id""")
                    rows = cur.fetchall()
                    found = {r[0] for r in rows}
                    missing = [x for x in (requested or []) if x not in found]
                    conflicts = [{"project_id": r[0], "name": r[1], "organization_id": r[2], "factory_id": r[3]} for r in rows if r[2] and (r[2] != org_id or r[3] != factory_id)]
                    if missing:
                        raise ApiError(404, "预检项目不存在", "project_not_found", project_ids=missing)
                    if conflicts:
                        raise ApiError(409, "项目已有其他组织归属，不能在本批次覆盖", "project_ownership_conflict", conflicts=conflicts)
                    legacy = []
                    for pid, name, _, _, dataset in rows:
                        dataset = dataset or {}
                        ue_id = dataset.get("bound_ue_project_id") if isinstance(dataset, dict) else None
                        if ue_id:
                            legacy.append({"project_id": pid, "name": name, "legacy_ue_project_id": ue_id, "scene_status": "pending_review"})
                    migration_id = _id("mig")
                    report = {
                        "migration_id": migration_id,
                        "environment_id": env_id,
                        "target_organization_id": org_id,
                        "target_factory_id": factory_id,
                        "project_count": len(rows),
                        "projects": [{"project_id": r[0], "name": r[1], "legacy_binding": bool((r[4] or {}).get("bound_ue_project_id") if isinstance(r[4] or {}, dict) else False)} for r in rows],
                        "legacy_binding_review_count": len(legacy),
                        "legacy_binding_reviews": legacy,
                        "warnings": ["旧工程级 UE 绑定不会按名称猜测场景，迁移后进入待核对。"] if legacy else [],
                    }
                    cur.execute("INSERT INTO migration_batch(migration_id,environment_id,status,preflight_report_json) VALUES(%s,%s,'preflight',%s)", (migration_id, env_id, Jsonb(report)))
                    for pid, *_ in rows:
                        cur.execute("INSERT INTO migration_scope(migration_id,project_id,status) VALUES(%s,%s,'pending')", (migration_id, pid))
                        cur.execute(
                            "UPDATE migration_scope SET old_hash=%s WHERE migration_id=%s AND project_id=%s",
                            (_project_content_hash(cur, pid), migration_id, pid),
                        )
        return _json(report), 201

    @app.get("/api/v4.8/migrations/<migration_id>")
    @_api
    def migration_status(migration_id):
        _require_pg()
        with pg.get_conn() as conn:
            with conn.cursor() as cur:
                session = _load_session(cur)
                cur.execute("""SELECT mb.migration_id,mb.status,mb.freeze_started_at,mb.backup_id,
                                     mb.preflight_report_json,mb.confirmed_at,mb.completed_at,mb.failure_code
                                FROM migration_batch mb WHERE mb.migration_id=%s""", (migration_id,))
                row = cur.fetchone()
                if not row:
                    raise ApiError(404, "迁移批次不存在", "not_found")
                report = row[4] or {}
                if _org_role(cur, session["user_id"], report.get("target_organization_id")) != "admin":
                    raise ApiError(403, "无权查看该迁移批次", "forbidden")
                cur.execute("SELECT project_id,status,old_hash,new_hash FROM migration_scope WHERE migration_id=%s ORDER BY project_id", (migration_id,))
                scopes = [{"project_id": r[0], "status": r[1], "old_hash": r[2], "new_hash": r[3]} for r in cur.fetchall()]
        return _json({"migration_id": row[0], "status": row[1], "freeze_started_at": row[2], "backup_id": row[3], "preflight_report": report, "confirmed_at": row[5], "completed_at": row[6], "failure_code": row[7], "scope": scopes})

    @app.post("/api/v4.8/migrations/<migration_id>/confirm")
    @_api
    def migration_confirm(migration_id):
        """确认并执行归属迁移；冻结与实际写入必须跨事务可见。"""
        _require_pg()
        body = _body()
        if body.get("confirm") is not True:
            raise ApiError(400, "必须明确 confirm=true 才能执行迁移", "confirmation_required")
        backup_id = _required(body, "backup_id")

        # Phase 1 commits the frozen marker before any project row is changed.
        # ProjectStorePG._save_current() can therefore observe it and reject
        # concurrent legacy writes instead of seeing preflight and overwriting
        # the migrated row with a stale in-memory snapshot.
        with pg.get_conn() as conn:
            with conn.transaction():
                with conn.cursor() as cur:
                    session = _load_session(cur)
                    cur.execute("SELECT status,environment_id,preflight_report_json FROM migration_batch WHERE migration_id=%s FOR UPDATE", (migration_id,))
                    batch = cur.fetchone()
                    if not batch:
                        raise ApiError(404, "迁移批次不存在", "not_found")
                    status, env_id, report = batch
                    if status != "preflight":
                        raise ApiError(409, "该迁移批次已执行或已失效", "migration_not_pending")
                    if _org_role(cur, session["user_id"], report.get("target_organization_id")) != "admin":
                        raise ApiError(403, "只有目标组织管理员可以确认迁移", "forbidden")
                    cur.execute("SELECT 1 FROM backup_manifest WHERE backup_id=%s AND environment_id=%s", (backup_id, env_id))
                    if not cur.fetchone():
                        raise ApiError(400, "备份清单不存在或不属于当前环境", "backup_required")
                    org_id, factory_id = report["target_organization_id"], report["target_factory_id"]
                    cur.execute("""UPDATE migration_batch
                                      SET status='frozen',freeze_started_at=now(),backup_id=%s,
                                          confirmed_by=%s,confirmed_at=now(),failure_code=NULL
                                    WHERE migration_id=%s""", (backup_id, session["user_id"], migration_id))
                    cur.execute("SELECT project_id FROM migration_scope WHERE migration_id=%s FOR UPDATE", (migration_id,))
                    project_ids = [r[0] for r in cur.fetchall()]

        try:
            # Phase 2 performs the change while the committed frozen marker is
            # visible. Row locks plus the preflight hash prevent a stale writer
            # from being silently accepted.
            with pg.get_conn() as conn:
                with conn.transaction():
                    with conn.cursor() as cur:
                        cur.execute("SELECT status,environment_id,preflight_report_json FROM migration_batch WHERE migration_id=%s FOR UPDATE", (migration_id,))
                        batch = cur.fetchone()
                        if not batch or batch[0] != "frozen":
                            raise ApiError(409, "迁移冻结状态已变化，请重新预检", "migration_not_frozen")
                        _, env_id, report = batch
                        org_id, factory_id = report["target_organization_id"], report["target_factory_id"]
                        cur.execute("SELECT project_id,old_hash FROM migration_scope WHERE migration_id=%s ORDER BY project_id FOR UPDATE", (migration_id,))
                        scopes = cur.fetchall()
                        if [r[0] for r in scopes] != project_ids:
                            raise ApiError(409, "迁移范围发生变化，请重新预检", "migration_scope_changed")
                        for pid, old_hash in scopes:
                            cur.execute("SELECT id FROM project WHERE id=%s AND deleted_at IS NULL FOR UPDATE", (pid,))
                            if not cur.fetchone():
                                raise ApiError(409, "迁移项目已不存在，请重新预检", "migration_scope_changed", project_id=pid)
                            if _project_content_hash(cur, pid) != old_hash:
                                raise ApiError(409, "项目内容在预检后发生变化，请重新预检", "migration_content_changed", project_id=pid)
                        if project_ids:
                            cur.execute("""UPDATE project SET environment_id=%s,organization_id=%s,factory_id=%s,updated_at=now()
                               WHERE id=ANY(%s) AND deleted_at IS NULL
                               AND (organization_id IS NULL OR organization_id=%s) AND (factory_id IS NULL OR factory_id=%s)""", (env_id, org_id, factory_id, project_ids, org_id, factory_id))
                            if cur.rowcount != len(project_ids):
                                raise ApiError(409, "迁移期间项目归属发生变化，请重新预检", "migration_scope_changed")
                        for item in report.get("legacy_binding_reviews") or []:
                            cur.execute("""INSERT INTO legacy_binding_review(review_id,legacy_project_id,legacy_ue_project_id,status,evidence_json)
                               VALUES(%s,%s,%s,'pending',%s)
                               ON CONFLICT(legacy_project_id,legacy_ue_project_id) DO UPDATE SET status='pending'""", (_id("review"), item["project_id"], item["legacy_ue_project_id"], Jsonb({"migration_id": migration_id, "reason": "legacy_project_binding_has_no_scene_identity"})))
                        for pid, old_hash in scopes:
                            new_hash = _project_content_hash(cur, pid)
                            if new_hash != old_hash:
                                raise ApiError(409, "迁移回读校验失败，项目内容发生变化", "migration_readback_failed", project_id=pid)
                            cur.execute("UPDATE migration_scope SET status='migrated',new_hash=%s WHERE migration_id=%s AND project_id=%s", (new_hash, migration_id, pid))
                        cur.execute("UPDATE migration_batch SET status='completed',completed_at=now() WHERE migration_id=%s", (migration_id,))
                        _audit(cur, session["user_id"], org_id, factory_id, None, "migration.confirm", migration_id, detail={"backup_id": backup_id, "project_count": len(project_ids), "readback": "verified"})
        except Exception as exc:
            failure_code = getattr(exc, "code", None) or "migration_failed"
            try:
                with pg.get_conn() as failure_conn:
                    with failure_conn.transaction():
                        with failure_conn.cursor() as failure_cur:
                            failure_cur.execute("""UPDATE migration_batch
                                                   SET status='failed',failure_code=%s,rollback_at=now()
                                                 WHERE migration_id=%s AND status='frozen'""", (failure_code, migration_id))
            finally:
                raise
        return _json({"migration_id": migration_id, "status": "completed", "project_count": len(project_ids), "legacy_binding_review": "pending", "readback": "verified"})

    @app.get("/api/v4.8/migrations/<migration_id>/legacy-bindings")
    @_api
    def legacy_binding_reviews(migration_id):
        _require_pg()
        with pg.get_conn() as conn:
            with conn.cursor() as cur:
                session = _load_session(cur)
                cur.execute("SELECT preflight_report_json FROM migration_batch WHERE migration_id=%s", (migration_id,))
                batch = cur.fetchone()
                if not batch:
                    raise ApiError(404, "迁移批次不存在", "not_found")
                report = batch[0] or {}
                if _org_role(cur, session["user_id"], report.get("target_organization_id")) != "admin":
                    raise ApiError(403, "无权查看旧绑定核对项", "forbidden")
                cur.execute("""SELECT r.review_id,r.legacy_project_id,p.name,r.legacy_ue_project_id,
                                      r.candidate_scene_id,r.status,r.evidence_json,r.decision_note,r.reviewed_at
                                 FROM legacy_binding_review r JOIN project p ON p.id=r.legacy_project_id
                                WHERE r.evidence_json->>'migration_id'=%s ORDER BY p.name""", (migration_id,))
                rows = [{"review_id": r[0], "project_id": r[1], "project_name": r[2], "legacy_ue_project_id": r[3], "candidate_scene_id": r[4], "status": r[5], "evidence": r[6], "decision_note": r[7], "reviewed_at": r[8]} for r in cur.fetchall()]
        return _json({"items": rows})

    @app.post("/api/v4.8/legacy-bindings/<review_id>/resolve")
    @_api
    def resolve_legacy_binding(review_id):
        _require_pg()
        body = _body()
        scene_id = _required(body, "scene_id")
        note = body.get("decision_note") or "管理员核对确认"
        with pg.get_conn() as conn:
            with conn.transaction():
                with conn.cursor() as cur:
                    session = _load_session(cur)
                    cur.execute("""SELECT r.legacy_project_id,r.status,p.organization_id,p.factory_id
                                      FROM legacy_binding_review r JOIN project p ON p.id=r.legacy_project_id
                                     WHERE r.review_id=%s FOR UPDATE""", (review_id,))
                    row = cur.fetchone()
                    if not row:
                        raise ApiError(404, "旧绑定核对项不存在", "not_found")
                    project_id, old_status, org_id, factory_id = row
                    if _org_role(cur, session["user_id"], org_id) != "admin":
                        raise ApiError(403, "只有项目所属组织管理员可以核对旧绑定", "forbidden")
                    cur.execute("SELECT ue_project_id FROM ue_scene WHERE scene_id=%s", (scene_id,))
                    scene = cur.fetchone()
                    if not scene:
                        raise ApiError(404, "场景不存在", "scene_not_found")
                    cur.execute("SELECT binding_id,project_id FROM project_scene_binding WHERE ue_project_id=%s AND scene_id=%s AND status='active'", (scene[0], scene_id))
                    conflict = cur.fetchone()
                    if conflict and conflict[1] != project_id:
                        raise ApiError(409, "该场景已经绑定其他项目", "scene_binding_conflict", binding_id=conflict[0])
                    cur.execute("UPDATE project_scene_binding SET status='replaced',updated_at=now() WHERE project_id=%s AND status='active'", (project_id,))
                    binding_id = conflict[0] if conflict and conflict[1] == project_id else _id("bind")
                    if conflict and conflict[1] == project_id:
                        cur.execute("UPDATE project_scene_binding SET ue_project_id=%s,scene_id=%s,status='active',updated_at=now(),revision=revision+1 WHERE binding_id=%s", (scene[0], scene_id, binding_id))
                    else:
                        cur.execute("""INSERT INTO project_scene_binding(binding_id,project_id,organization_id,factory_id,ue_project_id,scene_id,status,bound_by)
                           VALUES(%s,%s,%s,%s,%s,%s,'active',%s)""", (binding_id, project_id, org_id, factory_id, scene[0], scene_id, session["user_id"]))
                    cur.execute("UPDATE legacy_binding_review SET candidate_scene_id=%s,status='resolved',decision_note=%s,reviewed_by=%s,reviewed_at=now() WHERE review_id=%s", (scene_id, note, session["user_id"], review_id))
                    _audit(cur, session["user_id"], org_id, factory_id, project_id, "legacy_binding.resolve", review_id, detail={"scene_id": scene_id})
        return _json({"review_id": review_id, "status": "resolved", "binding_id": binding_id, "scene_id": scene_id})

    return app

