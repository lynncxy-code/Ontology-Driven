"""NEW-13: one version number, worded for people; UE plugin versions per organization."""
import sqlite3
from unittest.mock import MagicMock

import pytest

import release_info


@pytest.fixture(autouse=True)
def clean_reports(monkeypatch):
    monkeypatch.setattr(release_info, "_reports", {})


def test_release_ids_are_worded_for_people():
    assert release_info.describe("rc.25") == {"kind": "candidate", "label": "候选 25", "display": "OntoTwin 候选 25 · 验收版"}
    assert release_info.describe("2026.12.1")["display"] == "OntoTwin 2026.12.1 · 正式版"
    assert release_info.describe("2026.11.1.1")["kind"] == "formal"
    assert release_info.describe("4.8-dev")["display"] == "OntoTwin 开发版"
    assert release_info.describe("4.8.0-rc.23")["display"] == "OntoTwin 4.8.0-rc.23"


def test_release_info_has_no_environment_or_backend_image_wording(client, monkeypatch):
    monkeypatch.setenv("ONTOTWIN_RELEASE_ID", "rc.25")
    monkeypatch.setenv("ONTOTWIN_RELEASE_BUILT_AT", "2026-11-24T02:39:11Z")
    data = client.get("/release-info.json").json
    assert data["display"] == "OntoTwin 候选 25 · 验收版"
    assert data["version"] == data["backend"] == "rc.25"
    assert data["updated_at"] == "2026-11-24T02:39:11Z"
    assert "environment" not in data and "note" not in data


def test_plugin_rows_compare_with_backend_and_skip_silent_projects():
    release_info.remember_plugin_report("ue_a", "/Game/A", "rc.25", now=1000)
    release_info.remember_plugin_report("ue_b", "/Game/B", "rc.24", now=1000)
    release_info.remember_plugin_report("ue_c", "/Game/C", None, now=1000)
    bindings = [
        {"ue_project_key": "ue_a", "scene_key": "/Game/A", "ue_project_name": "办公室", "scene_name": "A"},
        {"ue_project_key": "ue_b", "scene_key": "/Game/B", "ue_project_name": "展馆", "scene_name": "B"},
        {"ue_project_key": "ue_c", "scene_key": "/Game/C", "ue_project_name": "旧工程", "scene_name": "C"},
        {"ue_project_key": "ue_d", "scene_key": "/Game/D", "ue_project_name": "没连过", "scene_name": "D"},
    ]
    rows = release_info.plugin_rows(bindings, "rc.25", now=1100)
    assert [(r["ue_project_name"], r["status"]) for r in rows] == [("展馆", "different"), ("旧工程", "unknown"), ("办公室", "same")]
    assert rows[0]["plugin_label"] == "候选 24"
    assert release_info.plugin_rows(bindings, "rc.25", now=1000 + 8 * 24 * 3600) == []


def test_ue_requests_record_the_reported_plugin_version(client):
    client.get("/release-info.json", headers={"X-OntoTwin-UE-Project-Id": "ue_a", "X-OntoTwin-UE-Scene-Id": "/Game/A",
                                              "X-OntoTwin-Plugin-Release": "rc.25"})
    client.get("/release-info.json")  # browser request: nothing recorded
    assert release_info.plugin_report("ue_a", "/Game/A")["release"] == "rc.25"
    assert len(release_info._reports) == 1


def _fake_db(monkeypatch, project_id):
    import tenant_api
    from db import pg

    db = sqlite3.connect(":memory:")
    db.executescript("""
        CREATE TABLE project_scene_binding(project_id,organization_id,ue_project_id,scene_id,status);
        CREATE TABLE ue_project(ue_project_id,display_name,stable_key);
        CREATE TABLE ue_scene(scene_id,level_path,display_name,stable_key);
        INSERT INTO ue_project VALUES('u1','0bay 办公室','ue_office'),('u2','DigitalFactoryBase','ue_air');
        INSERT INTO ue_scene VALUES('s1','/Game/OfficeShell/Maps/Office','','/Game/OfficeShell/Maps/Office'),
                                   ('s2','/Game/Develop/Maps/Airbase/L_Airbase_J20','','/Game/Develop/Maps/Airbase/L_Airbase_J20');
        INSERT INTO project_scene_binding VALUES('p_office','org_0bay','u1','s1','active'),
                                                ('p_air','org_test','u2','s2','active'),
                                                ('p_show','org_test','u2','s2','replaced');
    """)
    cursor = db.cursor()
    cur = MagicMock()
    cur.execute.side_effect = lambda sql, args=(): cursor.execute(sql.replace("%s", "?"), args)
    cur.fetchall.side_effect = cursor.fetchall
    conn = MagicMock()
    conn.__enter__.return_value = conn
    conn.cursor.return_value.__enter__.return_value = cur
    monkeypatch.setattr(pg, "get_conn", lambda: conn)
    monkeypatch.setattr(tenant_api, "_require_pg", lambda: None)
    monkeypatch.setattr(tenant_api, "_load_session", lambda c: {"user_id": "user", "organization_id": "org_test", "project_id": project_id})
    monkeypatch.setattr(tenant_api, "_project_allowed", lambda c, u, p, m="view": None if p == "p_secret" else {"role": "viewer"})
    for ue, scene in (("ue_office", "/Game/OfficeShell/Maps/Office"), ("ue_air", "/Game/Develop/Maps/Airbase/L_Airbase_J20")):
        release_info.remember_plugin_report(ue, scene, None if ue == "ue_air" else "rc.29")
    return db


def test_ue_plugin_list_only_shows_the_current_projects_levels(client, monkeypatch):
    monkeypatch.setenv("ONTOTWIN_RELEASE_ID", "rc.29")
    db = _fake_db(monkeypatch, "p_air")
    try:
        data = client.get("/api/v4.8/release/ue-plugins").json
        assert data["project_id"] == "p_air" and data["bound"] == 1 and data["backend_label"] == "候选 29"
        assert [(r["ue_project_name"], r["scene_name"], r["status"]) for r in data["items"]] == [("DigitalFactoryBase", "L_Airbase_J20", "unknown")]
    finally:
        db.close()


def test_project_without_bindings_or_without_project_lists_nothing(client, monkeypatch):
    for project_id, bound in (("p_show", 0), (None, 0)):
        db = _fake_db(monkeypatch, project_id)
        try:
            data = client.get("/api/v4.8/release/ue-plugins").json
            assert data["bound"] == bound and data["items"] == [] and data["project_id"] == project_id
        finally:
            db.close()


def test_project_the_account_may_not_view_is_refused(client, monkeypatch):
    db = _fake_db(monkeypatch, "p_secret")
    try:
        assert client.get("/api/v4.8/release/ue-plugins").status_code == 403
    finally:
        db.close()


def test_level_paths_are_shortened_for_display():
    assert release_info.short_level_name("/Game/Develop/Maps/Airbase/L_Airbase_J20") == "L_Airbase_J20"
    assert release_info.short_level_name("standard.factory") == "standard.factory"
    assert release_info.short_level_name("主场馆") == "主场馆"

def test_ue_plugin_list_requires_sign_in(client, monkeypatch):
    import tenant_api

    monkeypatch.setattr(tenant_api, "_require_pg", lambda: None)

    def no_session(cur):
        raise tenant_api.ApiError(401, "请先登录", "auth_required")

    monkeypatch.setattr(tenant_api, "_load_session", no_session)
    conn = MagicMock()
    conn.__enter__.return_value = conn
    from db import pg
    monkeypatch.setattr(pg, "get_conn", lambda: conn)
    assert client.get("/api/v4.8/release/ue-plugins").status_code == 401
