"""ue_assets（UE 资产目录与推荐）工具单测（fake client，不起真 HTTP）。"""
from ontotwin_mcp.server import build_server


class C:
    def __init__(self):
        self.calls = []

    def get(self, op, path, params=None):
        self.calls.append(("get", path, params)); return {"assets": []}

    def post_json(self, op, path, json=None, timeout=None):
        self.calls.append(("post", path, json)); return {"status": "ok"}


def _t(mcp, name):
    return mcp._ot_tools[name]


def test_get_catalog_without_project_sends_no_params():
    c = C(); mcp = build_server(c)
    _t(mcp, "get_ue_asset_catalog")()
    assert c.calls[-1] == ("get", "/api/v2/ue/assets/catalog", None)


def test_get_catalog_with_project_id():
    c = C(); mcp = build_server(c)
    _t(mcp, "get_ue_asset_catalog")("ueproj_SCC")
    assert c.calls[-1][2] == {"ue_project_id": "ueproj_SCC"}


def test_recommend_defaults_limit_three():
    c = C(); mcp = build_server(c)
    _t(mcp, "recommend_ue_assets")([{"block_name": "CNC"}])
    method, path, body = c.calls[-1]
    assert (method, path) == ("post", "/api/v2/ue/assets/recommend")
    assert body == {"items": [{"block_name": "CNC"}], "limit": 3}


def test_recommend_custom_limit_and_project():
    c = C(); mcp = build_server(c)
    _t(mcp, "recommend_ue_assets")([], ue_project_id="ueproj_A", limit=10)
    body = c.calls[-1][2]
    assert body["limit"] == 10
    assert body["ue_project_id"] == "ueproj_A"


def test_remember_selections_body():
    c = C(); mcp = build_server(c)
    sel = [{"block_name": "CNC", "object_path": "/Game/SM_CNC"}]
    _t(mcp, "remember_ue_asset_selections")(sel)
    method, path, body = c.calls[-1]
    assert (method, path) == ("post", "/api/v2/ue/assets/confirmations")
    assert body == {"selections": sel}


def test_replace_catalog_requires_project_id_in_body():
    """整表替换必须带 ue_project_id，否则后端拒绝。"""
    c = C(); mcp = build_server(c)
    _t(mcp, "replace_ue_asset_catalog")([{"object_path": "/Game/A"}], "ueproj_B")
    method, path, body = c.calls[-1]
    assert (method, path) == ("post", "/api/v2/ue/assets/catalog")
    assert body["ue_project_id"] == "ueproj_B"
    assert body["assets"] == [{"object_path": "/Game/A"}]


def test_tools_registered():
    c = C(); mcp = build_server(c)
    assert {"get_ue_asset_catalog", "recommend_ue_assets",
            "remember_ue_asset_selections",
            "replace_ue_asset_catalog"} <= set(mcp._ot_tools)
