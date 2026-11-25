"""OPT-08：数据集管理（重命名／删除／复制权限、撤销授权）与回收站组织隔离。"""
from unittest.mock import MagicMock, patch

import pytest

import tenant_api as tenant
from dataset_admin import service
from dataset_admin.service import TrashScope


# ── 回收站范围 ─────────────────────────────────────────────────────

ITEMS = [
    {"id": "pg:prj:p_own_deleted", "kind": "project", "project_id": "p_own_deleted"},
    {"id": "pg:prj:p_other_org", "kind": "project", "project_id": "p_other_org"},
    {"id": "pg:inst:p_live:I1", "kind": "instance", "project_id": "p_live"},
    {"id": "pg:inst:p_readonly:I2", "kind": "instance", "project_id": "p_readonly"},
    {"id": "pg:inst:p_other_org_live:I3", "kind": "instance", "project_id": "p_other_org_live"},
]


def admin_scope():
    return TrashScope(is_admin=True, deleted_projects={"p_own_deleted"},
                      viewable={"p_live", "p_readonly"}, editable={"p_live", "p_readonly"})


def editor_scope():
    return TrashScope(is_admin=False, deleted_projects=set(),
                      viewable={"p_live", "p_readonly"}, editable={"p_live"})


def test_scope_hides_other_organizations():
    visible = [i["id"] for i in ITEMS if admin_scope().can_view(i)]
    assert visible == ["pg:prj:p_own_deleted", "pg:inst:p_live:I1", "pg:inst:p_readonly:I2"]


def test_non_admin_never_sees_deleted_datasets_and_needs_edit_to_change_instances():
    scope = editor_scope()
    assert not scope.can_view(ITEMS[0])
    assert scope.can_modify(ITEMS[2])
    assert scope.can_view(ITEMS[3]) and not scope.can_modify(ITEMS[3])


def test_trash_scope_without_factory_context_is_empty():
    assert service.trash_scope(MagicMock(), "u", None, None) == TrashScope()


def test_trash_scope_collects_factory_projects():
    cur = MagicMock()
    cur.fetchall.side_effect = [[("p_deleted",)], [("p_a",), ("p_b",)]]

    def allowed(_cur, _user, pid, minimum="view"):
        return {"role": "admin"} if (pid == "p_a" or minimum == "view") else None

    with patch.object(tenant, "_factory_allowed", return_value=(True, "admin")), \
         patch.object(tenant, "_project_allowed", side_effect=allowed):
        scope = service.trash_scope(cur, "u", "org", "fac")
    assert scope.is_admin
    assert scope.deleted_projects == {"p_deleted"}
    assert scope.viewable == {"p_a", "p_b"}
    assert scope.editable == {"p_a"}


@pytest.fixture
def scoped_client(client, monkeypatch):
    import app as app_module

    trash = [dict(i) for i in ITEMS]
    calls = {"restore": [], "delete": []}
    monkeypatch.setattr(app_module.project_store, "list_trash", lambda: [dict(i) for i in trash], raising=False)
    monkeypatch.setattr(app_module.project_store, "restore_trash",
                        lambda tid: calls["restore"].append(tid) or ("instance", tid), raising=False)
    monkeypatch.setattr(app_module.project_store, "delete_trash",
                        lambda tid: calls["delete"].append(tid) or True, raising=False)
    holder = {"scope": editor_scope()}
    monkeypatch.setattr(app_module, "current_trash_scope", lambda: holder["scope"])
    return client, holder, calls


def test_trash_list_route_filters_by_scope(scoped_client):
    client, holder, _ = scoped_client
    ids = [i["id"] for i in client.get("/api/v2/trash").get_json()["items"]]
    assert ids == ["pg:inst:p_live:I1", "pg:inst:p_readonly:I2"]


def test_trash_restore_other_org_item_is_not_found(scoped_client):
    client, _, calls = scoped_client
    r = client.post("/api/v2/trash/pg:inst:p_other_org_live:I3/restore")
    assert r.status_code == 404
    assert calls["restore"] == []


def test_trash_delete_without_edit_is_forbidden(scoped_client):
    client, _, calls = scoped_client
    r = client.delete("/api/v2/trash/pg:inst:p_readonly:I2")
    assert r.status_code == 403
    assert calls["delete"] == []


def test_trash_restore_editable_item_passes(scoped_client):
    client, _, calls = scoped_client
    r = client.post("/api/v2/trash/pg:inst:p_live:I1/restore")
    assert r.status_code == 200
    assert calls["restore"] == ["pg:inst:p_live:I1"]


def test_trash_purge_only_touches_permitted_items(scoped_client):
    client, holder, calls = scoped_client
    body = client.post("/api/v2/trash/purge").get_json()
    assert calls["delete"] == ["pg:inst:p_live:I1"]
    assert body["purged"] == 1 and body["skipped"] == 1


# ── 重命名 ────────────────────────────────────────────────────────

def rename_cursor(conflict=False):
    cur = MagicMock()
    cur.fetchone.side_effect = [("org", "fac", "旧名", True), (1,) if conflict else None]
    cur.rowcount = 1
    return cur


def test_rename_requires_edit_permission():
    cur = rename_cursor()
    with patch.object(tenant, "_project_allowed", side_effect=lambda c, u, p, minimum="view": None if minimum == "edit" else {"role": "viewer"}):
        with pytest.raises(tenant.ApiError) as err:
            service.rename(cur, "u", "p1", "新名")
    assert err.value.status == 403


def test_rename_rejects_same_factory_duplicate():
    cur = rename_cursor(conflict=True)
    with patch.object(tenant, "_project_allowed", return_value={"role": "editor"}):
        with pytest.raises(tenant.ApiError) as err:
            service.rename(cur, "u", "p1", "  新名 ")
    assert err.value.status == 409 and err.value.code == "dataset_name_conflict"


def test_rename_updates_project_and_dataset_name():
    cur = rename_cursor()
    with patch.object(tenant, "_project_allowed", return_value={"role": "editor"}), \
         patch.object(service, "_guard_migration"), \
         patch.object(tenant, "_audit") as audit:
        result = service.rename(cur, "u", "p1", "新名")
    assert result == {"project_id": "p1", "name": "新名", "changed": True}
    update_sql, params = cur.execute.call_args_list[-1][0]
    assert "jsonb_set(dataset,'{name}'" in update_sql
    assert params == ("新名", "新名", "p1")
    assert audit.call_args[0][5] == "project.rename"


@pytest.mark.parametrize("value,code", [("", "dataset_name_required"), ("x" * 129, "dataset_name_too_long")])
def test_rename_validates_name(value, code):
    with pytest.raises(tenant.ApiError) as err:
        service.normalize_name(value)
    assert err.value.code == code


# ── 删除／复制／回退的可用性 ────────────────────────────────────────

def actions_for(role, can_edit, can_create, rollback_ready, has_content=True):
    cur = MagicMock()
    cur.fetchone.return_value = ("org", "fac", "数据集A", has_content)
    with patch.object(tenant, "_project_allowed",
                      side_effect=lambda c, u, p, minimum="view": ({"role": role} if (minimum == "view" or can_edit) else None)), \
         patch.object(tenant, "_org_role", return_value=role), \
         patch.object(tenant, "_factory_allowed", return_value=(can_create, role)):
        return service.available_actions(cur, "u", "p1", rollback_ready)


def test_admin_gets_every_action_when_rollback_backup_exists():
    a = actions_for("admin", True, True, True)
    assert all(a[k]["allowed"] for k in ("rename", "copy", "rollback", "delete"))


def test_editor_cannot_delete_and_rollback_needs_backup():
    a = actions_for("editor", True, True, False)
    assert a["rename"]["allowed"] and a["copy"]["allowed"]
    assert not a["delete"]["allowed"] and "组织管理员" in a["delete"]["reason"]
    assert not a["rollback"]["allowed"] and "更新记录" in a["rollback"]["reason"]


def test_viewer_only_sees_disabled_actions():
    a = actions_for("viewer", False, False, True)
    assert not any(a[k]["allowed"] for k in ("rename", "copy", "rollback", "delete"))


def test_delete_requires_org_admin():
    cur = MagicMock()
    cur.fetchone.return_value = ("org", "fac", "数据集A", True)
    with patch.object(tenant, "_project_allowed", return_value={"role": "editor"}), \
         patch.object(tenant, "_org_role", return_value="editor"), \
         patch.object(tenant, "_factory_allowed", return_value=(True, "editor")):
        with pytest.raises(tenant.ApiError) as err:
            service.require_delete(cur, "u", "p1")
    assert err.value.status == 403


def test_deleted_dataset_is_not_found_for_actions():
    cur = MagicMock()
    cur.fetchone.return_value = None
    with pytest.raises(tenant.ApiError) as err:
        service.available_actions(cur, "u", "gone", False)
    assert err.value.status == 404


# ── 撤销项目授权 ──────────────────────────────────────────────────

def test_revoke_permission_requires_admin():
    cur = MagicMock()
    cur.fetchone.return_value = ("org", "fac")
    with patch.object(tenant, "_org_role", return_value="editor"):
        with pytest.raises(tenant.ApiError) as err:
            service.revoke_permission(cur, "u", "p1", "target")
    assert err.value.status == 403


def test_revoke_permission_marks_revoked_and_audits():
    cur = MagicMock()
    cur.fetchone.return_value = ("org", "fac")
    cur.rowcount = 1
    with patch.object(tenant, "_org_role", return_value="admin"), \
         patch.object(tenant, "_audit") as audit:
        result = service.revoke_permission(cur, "u", "p1", "target")
    assert result["revoked"] is True
    assert "revoked_at=now()" in cur.execute.call_args_list[-1][0][0]
    assert audit.call_args[0][5] == "project.permission.revoke"


def test_empty_dataset_cannot_be_copied():
    a = actions_for("admin", True, True, False, has_content=False)
    assert not a["copy"]["allowed"] and "新建空数据集" in a["copy"]["reason"]
    cur = MagicMock()
    cur.fetchone.return_value = ("org", "fac", "空数据集", False)
    with patch.object(tenant, "_project_allowed", return_value={"role": "admin"}),          patch.object(tenant, "_org_role", return_value="admin"),          patch.object(tenant, "_factory_allowed", return_value=(True, "admin")):
        with pytest.raises(tenant.ApiError) as err:
            service.require_copy(cur, "u", "p1")
    assert err.value.status == 422 and err.value.code == "dataset_empty"


class ForeignKeyViolation(Exception):
    pass


def test_blocked_permanent_delete_returns_409_and_purge_skips(scoped_client, monkeypatch):
    import app as app_module
    client, holder, _ = scoped_client
    holder["scope"] = admin_scope()

    def blocked(tid):
        raise ForeignKeyViolation("audit_event")

    monkeypatch.setattr(app_module.project_store, "delete_trash", blocked, raising=False)
    r = client.delete("/api/v2/trash/pg:prj:p_own_deleted")
    assert r.status_code == 409 and r.get_json()["error"] == "trash_delete_blocked"
    body = client.post("/api/v2/trash/purge").get_json()
    assert body["purged"] == 0 and body["skipped"] == 3


def test_delete_rejects_online_bound_ue_scene():
    cur = MagicMock()
    cur.fetchone.return_value = ("org", "fac", "数据集A", True)
    cur.fetchall.return_value = [("ue_plant", "/Game/Maps/Main")]
    with patch.object(tenant, "_project_allowed", return_value={"role": "admin"}), \
         patch.object(tenant, "_org_role", return_value="admin"), \
         patch.object(tenant, "_factory_allowed", return_value=(True, "admin")), \
         patch("ue_project_binding.ue_scene_online", return_value=True):
        with pytest.raises(tenant.ApiError) as err:
            service.require_delete(cur, "u", "p1")
    assert err.value.status == 409 and err.value.code == "ue_still_online"


def test_assign_copy_rejects_same_factory_duplicate_name():
    cur = MagicMock()
    cur.fetchone.return_value = (1,)
    with pytest.raises(tenant.ApiError) as err:
        service.assign_copy(cur, "u", {"organization_id": "org", "factory_id": "fac"}, "p_new", name="重名集")
    assert err.value.status == 409 and err.value.code == "dataset_name_conflict"


def test_trashed_binding_conflict_detection():
    cur = MagicMock()
    cur.fetchone.side_effect = [("ue1", "sc1"), (1,)]
    assert service.trashed_binding_has_conflict(cur, "p1") is True
    cur2 = MagicMock()
    cur2.fetchone.side_effect = [("ue1", "sc1"), None]
    assert service.trashed_binding_has_conflict(cur2, "p1") is False


def test_trash_routes_ignore_explicit_project_header(scoped_client, monkeypatch):
    import app as app_module
    client, _, calls = scoped_client
    monkeypatch.setenv("ONTOTWIN_STORE", "pg")
    monkeypatch.setattr(app_module, "validate_legacy_browser_session", lambda ignore_project=False: {"ok": ignore_project})
    r = client.post(
        "/api/v2/trash/pg:inst:p_live:I1/restore",
        headers={"X-OntoTwin-Session": "tok", "X-OntoTwin-Project-Id": "p_deleted_or_readonly"},
    )
    assert r.status_code == 200
    assert calls["restore"] == ["pg:inst:p_live:I1"]


def test_permanent_delete_cleans_project_assets_and_backups(tmp_path):
    from dataset_admin.api import cleanup_deleted_project_trash
    asset_root = tmp_path / "project_assets"
    backup_root = tmp_path / "delivery_backups" / "p_gone"
    (asset_root / "p_gone" / "web").mkdir(parents=True)
    (asset_root / "p_gone" / "web" / "index.html").write_text("x", encoding="utf-8")
    backup_root.mkdir(parents=True)
    (backup_root / "latest.json").write_text("{}", encoding="utf-8")
    fake_pkg = MagicMock()
    fake_pkg.asset_root = str(asset_root)
    fake_pkg._backup_dir.side_effect = lambda pid: tmp_path / "delivery_backups" / pid
    cleanup_deleted_project_trash("pg:prj:p_gone", fake_pkg)
    assert not (asset_root / "p_gone").exists()
    assert not backup_root.exists()
