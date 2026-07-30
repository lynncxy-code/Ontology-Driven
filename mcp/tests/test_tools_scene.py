"""scene 工具单测（fake client，不起真 HTTP）。"""
from ontotwin_mcp.server import build_server


class C:
    def __init__(self):
        self.calls = []

    def get(self, op, path, params=None):
        self.calls.append(("get", path, params)); return {"ok": True}

    def post_json(self, op, path, json=None, timeout=None):
        self.calls.append(("post", path, json)); return {"ok": True}

    def put_json(self, op, path, json=None, timeout=None):
        self.calls.append(("put", path, json)); return {"ok": True}

    def delete_json(self, op, path, json=None, timeout=None):
        self.calls.append(("delete", path, json)); return {"ok": True}

    def post_multipart(self, *a, **k):
        return {}


def _t(mcp, name):
    return mcp._ot_tools[name]


def test_get_route_encoded_path():
    c = C(); mcp = build_server(c)
    _t(mcp, "get_route")("r#1")
    assert c.calls[-1] == ("get", "/api/v2/scene-interactions/routes/r%231", None)


def test_save_roaming_config_put_body():
    c = C(); mcp = build_server(c)
    _t(mcp, "save_roaming_config")({"spawn": {}}, 7)
    method, path, body = c.calls[-1]
    assert method == "put"
    assert path == "/api/v2/scene-interactions/roaming"
    assert body == {"config": {"spawn": {}}, "expected_revision": 7}


def test_create_route_post_body():
    c = C(); mcp = build_server(c)
    _t(mcp, "create_route")({"name": "巡检"}, 2)
    method, path, body = c.calls[-1]
    assert method == "post"
    assert path == "/api/v2/scene-interactions/routes"
    assert body == {"route": {"name": "巡检"}, "expected_revision": 2}


def test_update_route_put_encoded_path_body():
    c = C(); mcp = build_server(c)
    _t(mcp, "update_route")("r1", {"name": "x"}, 3)
    method, path, body = c.calls[-1]
    assert method == "put"
    assert path == "/api/v2/scene-interactions/routes/r1"
    assert body == {"route": {"name": "x"}, "expected_revision": 3}


def test_delete_route_delete_body():
    c = C(); mcp = build_server(c)
    _t(mcp, "delete_route")("r1", 5)
    method, path, body = c.calls[-1]
    assert method == "delete"
    assert path == "/api/v2/scene-interactions/routes/r1"
    assert body == {"expected_revision": 5}


def test_set_default_route_post_body():
    c = C(); mcp = build_server(c)
    _t(mcp, "set_default_route")("r1", 4)
    method, path, body = c.calls[-1]
    assert path == "/api/v2/scene-interactions/routes/r1/default"
    assert body == {"expected_revision": 4}


def test_scene_tools_registered():
    c = C(); mcp = build_server(c)
    expected = {
        "get_scene_catalog", "get_roaming_config", "list_routes", "get_route",
        "save_roaming_config", "create_route", "update_route", "delete_route",
        "review_route", "set_default_route",
    }
    assert expected <= set(mcp._ot_tools)
