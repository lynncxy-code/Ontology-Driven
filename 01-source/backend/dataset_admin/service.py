"""数据集（4.8 项目）的日常管理：重命名、删除、复制前的权限判断，
项目授权撤销，以及回收站按组织／工厂隔离。

这里只放业务规则和 SQL，不读 flask ``request``；调用方负责打开数据库
连接、核验登录会话，再把 ``cur`` 和 ``user_id`` 传进来。
"""

from dataclasses import dataclass, field

import tenant_api as tenant
from tenant_api import ApiError

NAME_MAX = 128
EMPTY_COPY_REASON = "还没有导入本体内容，没有可复制的东西；需要的话直接新建空数据集"


def normalize_name(value):
    name = str(value or "").strip()
    if not name:
        raise ApiError(400, "请输入数据集名称", "dataset_name_required")
    if len(name) > NAME_MAX:
        raise ApiError(400, f"数据集名称不能超过 {NAME_MAX} 个字符", "dataset_name_too_long")
    return name


def _live_project(cur, project_id):
    cur.execute(
        """SELECT organization_id, factory_id, name,
                  jsonb_typeof(dataset->'graph_data')='object'
             FROM project WHERE id=%s AND deleted_at IS NULL""",
        (project_id,),
    )
    row = cur.fetchone()
    if not row:
        raise ApiError(404, "数据集不存在或已删除", "not_found")
    return {"organization_id": row[0], "factory_id": row[1], "name": row[2],
            "has_content": bool(row[3])}


def _require_view(cur, user_id, project_id):
    project = _live_project(cur, project_id)
    if not tenant._project_allowed(cur, user_id, project_id):
        raise ApiError(403, "无权访问该数据集", "forbidden")
    return project


# ── 每个操作的权限（同时供「…」菜单显示可用／不可用及原因） ─────────────

def _permission_flags(cur, user_id, project_id):
    project = _require_view(cur, user_id, project_id)
    role = tenant._org_role(cur, user_id, project["organization_id"])
    can_edit = bool(tenant._project_allowed(cur, user_id, project_id, minimum="edit"))
    can_create, _ = tenant._factory_allowed(
        cur, user_id, project["organization_id"], project["factory_id"], minimum="editor")
    return project, role, can_edit, can_create


def available_actions(cur, user_id, project_id, rollback_ready):
    project, role, can_edit, can_create = _permission_flags(cur, user_id, project_id)

    def item(allowed, reason):
        return {"allowed": bool(allowed), "reason": "" if allowed else reason}

    return {
        "project_id": project_id,
        "name": project["name"],
        "rename": item(can_edit, "需要该数据集的编辑权限"),
        "copy": item(
            can_create and project["has_content"],
            "需要该工厂的编辑者或管理员角色" if not can_create else EMPTY_COPY_REASON,
        ),
        "rollback": item(
            can_edit and rollback_ready,
            "需要该数据集的编辑权限" if not can_edit else "没有可回退的数据集包更新记录",
        ),
        "delete": item(role == "admin", "只有组织管理员可以删除数据集"),
    }


def require_delete(cur, user_id, project_id):
    project, role, _, _ = _permission_flags(cur, user_id, project_id)
    if role != "admin":
        raise ApiError(403, "只有组织管理员可以删除数据集", "forbidden")
    require_scene_offline(cur, project_id)
    return project


def require_scene_offline(cur, project_id):
    cur.execute(
        """SELECT u.stable_key, s.stable_key
             FROM project_scene_binding b
             JOIN ue_project u ON u.ue_project_id = b.ue_project_id
             JOIN ue_scene s ON s.scene_id = b.scene_id
            WHERE b.project_id = %s AND b.status = 'active'""",
        (project_id,),
    )
    from ue_project_binding import ue_scene_online
    for bound_ue_id, scene_key in cur.fetchall():
        if ue_scene_online(bound_ue_id, scene_key):
            raise ApiError(409, "该数据集的关卡正在 UE 中运行，请先停止 UE 再删除", "ue_still_online")


def factory_dataset_names(cur, org_id, factory_id):
    cur.execute(
        """SELECT btrim(name) FROM project
            WHERE organization_id=%s AND factory_id=%s AND deleted_at IS NULL AND name IS NOT NULL""",
        (org_id, factory_id),
    )
    return {r[0] for r in cur.fetchall() if r[0]}


def require_copy(cur, user_id, project_id):
    project, _, _, can_create = _permission_flags(cur, user_id, project_id)
    if not can_create:
        raise ApiError(403, "只有该工厂的编辑者或管理员可以复制数据集", "forbidden")
    if not project["has_content"]:
        raise ApiError(422, EMPTY_COPY_REASON, "dataset_empty")
    return project


def _guard_migration(cur, project_id):
    from project_store_pg import _guard_project_mutation, ProjectMigrationFrozenError
    try:
        _guard_project_mutation(cur, project_id)
    except ProjectMigrationFrozenError:
        raise ApiError(409, "该数据集正在迁移，暂时不能修改", "project_migration_frozen")


def rename(cur, user_id, project_id, new_name):
    name = normalize_name(new_name)
    project = _require_view(cur, user_id, project_id)
    if not tenant._project_allowed(cur, user_id, project_id, minimum="edit"):
        raise ApiError(403, "需要该数据集的编辑权限才能重命名", "forbidden")
    if (project["name"] or "").strip() == name:
        return {"project_id": project_id, "name": name, "changed": False}
    cur.execute(
        """SELECT 1 FROM project
            WHERE organization_id=%s AND factory_id=%s AND deleted_at IS NULL
              AND id<>%s AND btrim(name)=%s LIMIT 1""",
        (project["organization_id"], project["factory_id"], project_id, name),
    )
    if cur.fetchone():
        raise ApiError(409, f"当前工厂已有同名数据集：{name}", "dataset_name_conflict")
    _guard_migration(cur, project_id)
    # 名称同时存在于项目行和语义图数据集里，两处一起改，避免旧页面显示旧名。
    cur.execute(
        """UPDATE project
              SET name=%s,
                  dataset=CASE WHEN jsonb_typeof(dataset)='object'
                               THEN jsonb_set(dataset,'{name}',to_jsonb(%s::text))
                               ELSE dataset END,
                  updated_at=now()
            WHERE id=%s AND deleted_at IS NULL""",
        (name, name, project_id),
    )
    tenant._audit(cur, user_id, project["organization_id"], project["factory_id"], project_id,
                  "project.rename", project_id, detail={"from": project["name"], "to": name})
    return {"project_id": project_id, "name": name, "changed": True}


def assign_copy(cur, user_id, source, new_project_id, name=None):
    """复制出的数据集归到源数据集所在的组织／工厂，复制人获得编辑授权。"""
    if name:
        cur.execute(
            """SELECT 1 FROM project
                WHERE organization_id=%s AND factory_id=%s AND deleted_at IS NULL
                  AND id<>%s AND btrim(name)=%s LIMIT 1""",
            (source["organization_id"], source["factory_id"], new_project_id, name),
        )
        if cur.fetchone():
            raise ApiError(409, f"当前工厂已有同名数据集：{name}", "dataset_name_conflict")
    cur.execute("SELECT environment_id FROM organization WHERE organization_id=%s",
                (source["organization_id"],))
    env = cur.fetchone()
    cur.execute(
        """UPDATE project SET environment_id=%s, organization_id=%s, factory_id=%s,
                  status='active', updated_at=now()
            WHERE id=%s AND deleted_at IS NULL""",
        (env[0] if env else None, source["organization_id"], source["factory_id"], new_project_id),
    )
    if cur.rowcount != 1:
        raise ApiError(500, "复制后的数据集未找到，无法建立归属", "copy_assign_failed")
    cur.execute(
        """INSERT INTO project_permission(project_id,user_id,permission,granted_by)
           VALUES(%s,%s,'edit',%s)
           ON CONFLICT(project_id,user_id) DO UPDATE SET permission='edit',revoked_at=NULL""",
        (new_project_id, user_id, user_id),
    )


def audit(cur, user_id, project, project_id, action, detail=None):
    tenant._audit(cur, user_id, project["organization_id"], project["factory_id"], project_id,
                  action, project_id, detail=detail)


def revoke_permission(cur, user_id, project_id, target_user_id):
    cur.execute("SELECT organization_id,factory_id FROM project WHERE id=%s AND deleted_at IS NULL",
                (project_id,))
    row = cur.fetchone()
    if not row:
        raise ApiError(404, "项目不存在", "not_found")
    org_id, factory_id = row
    if tenant._org_role(cur, user_id, org_id) != "admin":
        raise ApiError(403, "只有组织管理员可以调整项目权限", "forbidden")
    cur.execute(
        """UPDATE project_permission SET revoked_at=now()
            WHERE project_id=%s AND user_id=%s AND revoked_at IS NULL""",
        (project_id, target_user_id),
    )
    revoked = cur.rowcount > 0
    if revoked:
        tenant._audit(cur, user_id, org_id, factory_id, project_id, "project.permission.revoke",
                      target_user_id)
    return {"project_id": project_id, "user_id": target_user_id, "revoked": revoked}


def trashed_binding_has_conflict(cur, project_id):
    cur.execute(
        """SELECT ue_project_id, scene_id
             FROM project_scene_binding
            WHERE project_id=%s AND status='trashed'
            ORDER BY updated_at DESC LIMIT 1""",
        (project_id,),
    )
    row = cur.fetchone()
    if not row:
        return False
    cur.execute(
        """SELECT 1 FROM project_scene_binding
            WHERE ue_project_id=%s AND scene_id=%s AND status='active' LIMIT 1""",
        row,
    )
    return cur.fetchone() is not None


# ── 回收站隔离 ───────────────────────────────────────────────────────

@dataclass
class TrashScope:
    """当前账号在当前工厂里能看到、能操作的回收站范围。"""

    is_admin: bool = False
    deleted_projects: set = field(default_factory=set)   # 本工厂已删除的数据集（仅管理员可见）
    viewable: set = field(default_factory=set)           # 可查看的数据集（看其中被删的实例）
    editable: set = field(default_factory=set)           # 可编辑的数据集（恢复／彻底删除实例）
    user_id: str = ""
    organization_id: str | None = None
    factory_id: str | None = None

    def can_view(self, item):
        pid = item.get("project_id")
        if item.get("kind") == "project":
            return self.is_admin and pid in self.deleted_projects
        return pid in self.viewable

    def can_modify(self, item):
        if item.get("kind") == "project":
            return self.can_view(item)
        return item.get("project_id") in self.editable


def _build_trash_scope(cur, user_id, org_id, factory_id, role):
    scope = TrashScope(
        is_admin=(role == "admin"),
        user_id=user_id,
        organization_id=org_id,
        factory_id=factory_id,
    )
    if scope.is_admin:
        cur.execute(
            """SELECT id FROM project
                WHERE organization_id=%s AND factory_id=%s AND deleted_at IS NOT NULL""",
            (org_id, factory_id),
        )
        scope.deleted_projects = {r[0] for r in cur.fetchall()}
    cur.execute(
        "SELECT id FROM project WHERE organization_id=%s AND factory_id=%s AND deleted_at IS NULL",
        (org_id, factory_id),
    )
    for (pid,) in cur.fetchall():
        if tenant._project_allowed(cur, user_id, pid):
            scope.viewable.add(pid)
            if tenant._project_allowed(cur, user_id, pid, minimum="edit"):
                scope.editable.add(pid)
    return scope


def trash_scope(cur, user_id, org_id, factory_id):
    if not org_id or not factory_id:
        return TrashScope()
    allowed, role = tenant._factory_allowed(cur, user_id, org_id, factory_id)
    if not allowed:
        return TrashScope()
    return _build_trash_scope(cur, user_id, org_id, factory_id, role)


def require_trash_scope(cur, user_id, org_id, factory_id):
    """严格核验当前组织与工厂权限；无法确认权限时直接拒绝。"""
    if not org_id or not factory_id:
        raise ApiError(400, "请先选择组织和工厂", "context_required")
    allowed, role = tenant._factory_allowed(cur, user_id, org_id, factory_id)
    if not allowed:
        raise ApiError(403, "无权访问该组织或工厂的回收站", "forbidden")
    return _build_trash_scope(cur, user_id, org_id, factory_id, role)
