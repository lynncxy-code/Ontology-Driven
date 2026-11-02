"""Scene-only bindings must expose the UE identity used by the asset catalog."""
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def bridge(client, monkeypatch):
    import app
    from db import pg

    datasets = [{"id": "p_test", "name": "Bridge target"}]
    metadata = [{"id": "p_test", "name": "Bridge target"}]
    monkeypatch.setattr(app, "_datasets", datasets)
    monkeypatch.setattr(app.project_store, "list_projects", lambda: metadata)
    monkeypatch.setattr(app, "legacy_project_scope", lambda: {"p_test"})
    conn = MagicMock()
    conn.__enter__.return_value = conn
    cursor = conn.cursor.return_value.__enter__.return_value
    cursor.fetchall.return_value = [
        ("p_test", "ueproj-bridge", "Bridge UE", "/Game/Bridge")
    ]
    monkeypatch.setattr(pg, "get_conn", lambda: conn)
    return datasets, metadata, cursor


def listed(client):
    response = client.get("/api/v2/ontology/datasets")
    assert response.status_code == 200, response.json
    return next(row for row in response.json if row["id"] == "p_test")


def test_scene_binding_identity_reads_uploaded_catalog(client, bridge, tmp_path, monkeypatch):
    import app

    monkeypatch.setattr(app.ue_asset_catalog_service, "catalog_root", str(tmp_path))
    uploaded = client.post("/api/v2/ue/assets/catalog", headers={
        "X-OntoTwin-UE-Project-Id": "ueproj-bridge",
        "X-OntoTwin-UE-Project-Name": "Bridge UE",
        "X-OntoTwin-UE-Context": "pie",
    }, json={
        "ue_project_id": "ueproj-bridge", "ue_project_name": "Bridge UE",
        "roots": ["/Game/Bridge"],
        "assets": [{"object_path": "/Game/Bridge/SM_Test.SM_Test", "asset_kind": "StaticMesh"}],
    })
    assert uploaded.status_code == 201, uploaded.json
    row = listed(client)
    assert row["bound_ue_project_id"] == "ueproj-bridge"
    assert row["bound_ue_project_name"] == "Bridge UE"
    assert row["bound_ue_scene"] == "/Game/Bridge"
    catalog = client.get("/api/v2/ue/assets/catalog", query_string={
        "project_id": "p_test", "ue_project_id": row["bound_ue_project_id"],
    })
    assert catalog.status_code == 200, catalog.json
    assert catalog.json["assets"][0]["object_path"] == "/Game/Bridge/SM_Test.SM_Test"


@pytest.mark.parametrize("source", [0, 1])
def test_existing_legacy_identity_is_preserved(client, bridge, source):
    bridge[source][0].update(bound_ue_project_id="ue-legacy", bound_ue_project_name="Legacy UE")
    row = listed(client)
    assert row["bound_ue_project_id"] == "ue-legacy"
    assert row["bound_ue_project_name"] == "Legacy UE"
    assert row["bound_ue_scene"] == "/Game/Bridge"


def test_refresh_uses_current_binding_without_caching_bridge_in_dataset(client, bridge):
    assert listed(client)["bound_ue_project_id"] == "ueproj-bridge"
    bridge[2].fetchall.return_value = [("p_test", "ue-new", "New UE", "/Game/New")]
    row = listed(client)
    assert row["bound_ue_project_id"] == "ue-new"
    assert row["bound_ue_scene"] == "/Game/New"
    assert "bound_ue_project_id" not in bridge[0][0]


def test_other_project_binding_never_fills_unbound_project(client, bridge):
    bridge[0].append({"id": "p_hidden", "name": "Hidden"})
    bridge[2].fetchall.return_value = [("p_hidden", "ue-hidden", "Hidden UE", "/Game/Hidden")]
    response = client.get("/api/v2/ontology/datasets")
    assert response.status_code == 200
    assert [row["id"] for row in response.json] == ["p_test"]
    assert response.json[0]["bound_ue_project_id"] == ""
    assert response.json[0]["bound_ue_project_name"] == ""
    assert response.json[0]["bound_ue_scene"] == ""
