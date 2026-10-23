"""spatial_write 工具单测（fake client）。"""
from ontotwin_mcp.server import build_server


class C:
    def __init__(self):
        self.calls = []

    def get(self, op, path, params=None):
        self.calls.append(("get", path, params)); return {}

    def post_json(self, op, path, json=None, timeout=None):
        self.calls.append(("post", path, json)); return {"status": "ok"}

    def put_json(self, op, path, json=None, timeout=None):
        self.calls.append(("put", path, json)); return {"status": "ok"}


def _t(mcp, name):
    return mcp._ot_tools[name]


def test_set_spatial_profile_body_with_expected():
    c = C(); mcp = build_server(c)
    _t(mcp, "set_spatial_profile")({"canonical_origin": [1, 1]}, expected_project_id="p1")
    method, path, body = c.calls[-1]
    assert method == "put" and path == "/api/v2/spatial/profile"
    assert body == {"canonical_origin": [1, 1], "expected_project_id": "p1"}


def test_set_spatial_profile_omits_empty_expected():
    c = C(); mcp = build_server(c)
    _t(mcp, "set_spatial_profile")({"canonical_origin": [1, 1]})
    assert c.calls[-1][2] == {"canonical_origin": [1, 1]}


def test_upsert_spatial_frame_body():
    c = C(); mcp = build_server(c)
    _t(mcp, "upsert_spatial_frame")({"id": "f1", "kind": "custom"}, expected_project_id="p1")
    method, path, body = c.calls[-1]
    assert method == "post" and path == "/api/v2/spatial/frames"
    assert body == {"id": "f1", "kind": "custom", "expected_project_id": "p1"}


def test_calibrate_spatial_frame_encoded_path_body():
    c = C(); mcp = build_server(c)
    _t(mcp, "calibrate_spatial_frame")("f#1", [{"src": [0, 0], "dst": [1, 1]}],
                                       name="世界", expected_project_id="p1")
    method, path, body = c.calls[-1]
    assert method == "post"
    assert path == "/api/v2/spatial/frames/f%231/calibrate"
    assert body == {"anchors": [{"src": [0, 0], "dst": [1, 1]}],
                    "name": "世界", "expected_project_id": "p1"}


def test_preview_spatial_transform_body():
    c = C(); mcp = build_server(c)
    _t(mcp, "preview_spatial_transform")([[1, 2], [3, 4]], floor=2)
    method, path, body = c.calls[-1]
    assert method == "post" and path == "/api/v2/spatial/preview"
    assert body == {"points": [[1, 2], [3, 4]], "floor": 2}
    assert "profile" not in body


def test_export_cad_scene_body():
    c = C(); mcp = build_server(c)
    _t(mcp, "export_cad_scene")([[1, 0, 0], [0, 1, 0]], [{"id": "e1"}])
    method, path, body = c.calls[-1]
    assert path == "/api/v2/coord/export"
    assert body == {"transform_matrix": [[1, 0, 0], [0, 1, 0]], "entities": [{"id": "e1"}],
                    "wall_height": 4500, "wall_thickness": 240}
    assert "polylines" not in body


def test_get_block_asset_mapping_endpoint():
    c = C(); mcp = build_server(c)
    _t(mcp, "get_block_asset_mapping")()
    assert c.calls[-1] == ("get", "/api/v2/coord/mapping", None)


def test_save_block_asset_mapping_dict_body():
    c = C(); mcp = build_server(c)
    _t(mcp, "save_block_asset_mapping")({"BLK-1": "assets/a.glb"})
    method, path, body = c.calls[-1]
    assert method == "post" and path == "/api/v2/coord/mapping"
    assert body == {"BLK-1": "assets/a.glb"}


def test_spatial_write_tools_registered():
    c = C(); mcp = build_server(c)
    expected = {
        "set_spatial_profile", "upsert_spatial_frame", "calibrate_spatial_frame",
        "preview_spatial_transform", "export_cad_scene", "get_block_asset_mapping",
        "save_block_asset_mapping",
    }
    assert expected <= set(mcp._ot_tools)
