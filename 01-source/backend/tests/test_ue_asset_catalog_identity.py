"""BUG-20 回归：网页必须用「UE 上报身份」查资产目录。

RC21 及之前的 ``/api/v2/ontology/datasets`` 把数据库主键
``ue_project.ue_project_id``（形如 ``ue_<uuid>``）当作 ``bound_ue_project_id``
返回，而资产目录按 UE 上报的 ``ue_project.stable_key``（形如
``ueproj_scc_w18``）落盘。结果是 UE 日志显示同步成功（201），网页却一直
显示“已同步 0 个资产”；未知工程读目录也会被伪装成“同步成功但 0 个资产”。
"""
from unittest.mock import MagicMock

import pytest

from ue_asset_catalog.service import AssetCatalogError, UEAssetCatalogService


def _fake_conn(rows):
    conn = MagicMock()
    cur = conn.cursor.return_value.__enter__.return_value
    cur.fetchall.return_value = rows
    conn.__enter__.return_value = conn
    return conn


def test_scene_binding_reports_ue_reported_identity(monkeypatch):
    import app
    from db import pg

    conn = _fake_conn([
        (
            "p_70bd",
            "ue_9c94e525c3714ebc9d45deeb4e84ff11",
            "ueproj_scc_w18",
            "SCC4",
            "/Game/Maps/SCC4",
        ),
    ])
    monkeypatch.setattr(pg, "get_conn", lambda: conn)

    bindings = app._active_scene_bindings()

    assert bindings["p_70bd"]["ue_project_id"] == "ueproj_scc_w18"
    assert bindings["p_70bd"]["bound_id"] == "ue_9c94e525c3714ebc9d45deeb4e84ff11"
    assert bindings["p_70bd"]["ue_project_name"] == "SCC4"
    assert bindings["p_70bd"]["scene"] == "/Game/Maps/SCC4"


def test_scene_binding_falls_back_when_stable_key_missing(monkeypatch):
    import app
    from db import pg

    conn = _fake_conn([("p_legacy", "ueproj_legacy", None, "Legacy", "L1")])
    monkeypatch.setattr(pg, "get_conn", lambda: conn)

    bindings = app._active_scene_bindings()

    # 旧数据没有 stable_key 时退回主键，行为与修复前一致。
    assert bindings["p_legacy"]["ue_project_id"] == "ueproj_legacy"


def test_datasets_endpoint_returns_catalog_identity(client, monkeypatch):
    from db import pg

    conn = _fake_conn([
        ("p_test", "ue_internal_only", "ueproj_scc_w18", "SCC4", "/Game/Maps/SCC4"),
    ])
    monkeypatch.setattr(pg, "get_conn", lambda: conn)

    response = client.get("/api/v2/ontology/datasets")

    assert response.status_code == 200
    row = next(item for item in response.json if item["id"] == "p_test")
    assert row["bound_ue_project_id"] == "ueproj_scc_w18"
    assert row["bound_ue_project_name"] == "SCC4"
    assert row["bound_ue_scene"] == "/Game/Maps/SCC4"


def test_scene_binding_overrides_stale_legacy_dataset_field(client, monkeypatch):
    """4.8 场景绑定才是权威；旧 dataset 字段里的残留绑定不能抢先。"""
    import app as app_module
    from db import pg

    monkeypatch.setattr(app_module, "_datasets", [
        {"id": "p_test", "name": "测试厂", "bound_ue_project_id": "ueproj_stale"},
    ])
    conn = _fake_conn([
        ("p_test", "ue_internal", "ueproj_scc_w18", "SCC4", "L1"),
    ])
    monkeypatch.setattr(pg, "get_conn", lambda: conn)

    response = client.get("/api/v2/ontology/datasets")

    row = next(item for item in response.json if item["id"] == "p_test")
    assert row["bound_ue_project_id"] == "ueproj_scc_w18"
    assert row["bound_ue_project_name"] == "SCC4"


def test_catalog_read_for_unknown_project_is_404(tmp_path):
    service = UEAssetCatalogService(MagicMock(), str(tmp_path / "catalogs"))

    with pytest.raises(AssetCatalogError) as raised:
        service.get_catalog("ueproj_never_synced")

    assert raised.value.code == "asset_catalog_missing"
    assert raised.value.status == 404


def test_catalog_read_uses_ue_reported_identity(tmp_path):
    service = UEAssetCatalogService(MagicMock(), str(tmp_path / "catalogs"))
    service.replace_catalog({
        "ue_project_id": "ueproj_scc_w18",
        "roots": ["/Game"],
        "assets": [{"object_path": "/Game/A/SM_A.SM_A", "asset_kind": "StaticMesh"}],
    })

    result = service.get_catalog("ueproj_scc_w18")

    assert result["asset_count"] == 1
    assert result["available_folders"] == ["/Game"]
