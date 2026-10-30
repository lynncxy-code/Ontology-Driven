"""4.8 显式项目闸门与 UE 资产目录的边界（BUG-16 回归）。

UE 资产目录按「UE 工程 ID」独立落盘（backend/data/ue_asset_catalogs/），
且同步发生在项目绑定之前：TwinSceneManager 的资产目录组件在 BeginPlay
就上报目录，此时还没有 BoundProjectId 可发。带 UE 身份的请求必须放行，
否则 UE 侧固定 400 project_id_required（屏幕上显示「资产目录同步失败：HTTP 400」），
Web 端也就永远读不到目录。浏览器请求仍必须显式携带 project_id。
"""
import os

UE_HEADERS = {
    "X-OntoTwin-UE-Project-Id": "ueproj-guard",
    "X-OntoTwin-UE-Project-Name": "GuardProject",
    "X-OntoTwin-UE-Context": "pie",
}

CATALOG_PAYLOAD = {
    "ue_project_id": "ueproj-guard",
    "ue_project_name": "GuardProject",
    "roots": ["/Game/Guard"],
    "assets": [
        {"object_path": "/Game/Guard/SM_A.SM_A", "asset_kind": "StaticMesh"},
    ],
}


def test_ue_identity_can_sync_and_read_catalog(client, tmp_path, monkeypatch):
    import app as app_module

    # 目录必须落在测试临时目录，不能写进 backend/data/ue_asset_catalogs。
    monkeypatch.setattr(app_module.ue_asset_catalog_service, "catalog_root", str(tmp_path))

    synced = client.post("/api/v2/ue/assets/catalog", headers=UE_HEADERS, json=CATALOG_PAYLOAD)
    assert synced.status_code == 201, synced.get_json()
    assert synced.get_json()["ue_project_id"] == "ueproj-guard"
    assert os.listdir(tmp_path), "资产目录应写入隔离目录"

    read = client.get("/api/v2/ue/assets/catalog?ue_project_id=ueproj-guard", headers=UE_HEADERS)
    assert read.status_code == 200, read.get_json()
    body = read.get_json()
    assert body["asset_count"] == 1
    assert body["assets"][0]["object_path"] == "/Game/Guard/SM_A.SM_A"


def test_ue_identity_can_publish_folder_index(client, tmp_path, monkeypatch):
    import app as app_module

    monkeypatch.setattr(app_module.ue_asset_catalog_service, "catalog_root", str(tmp_path))

    published = client.post(
        "/api/v2/ue/assets/folders",
        headers=UE_HEADERS,
        json={"ue_project_id": "ueproj-guard", "folders": ["/Game"]},
    )
    assert published.status_code == 201, published.get_json()
    assert published.get_json()["folder_count"] >= 1


def test_browser_session_without_project_is_still_rejected(client):
    """浏览器请求不能借 UE 目录绕过显式项目闸门。"""
    response = client.get(
        "/api/v2/ue/assets/catalog?ue_project_id=ueproj-guard",
        headers={"X-OntoTwin-Session": "fake-session-token"},
    )
    assert response.status_code == 400
    assert response.get_json()["error"] == "project_id_required"


def test_browser_with_explicit_project_reads_catalog(client, store):
    """coord_workbench 在没有 4.8 会话上下文时用 ?project_id= 显式补上下文。"""
    response = client.get(
        "/api/v2/ue/assets/catalog?ue_project_id=ueproj-browser&project_id=p_test",
    )
    assert response.status_code == 200, response.get_json()
    assert response.get_json()["ue_project_id"] == "ueproj-browser"
