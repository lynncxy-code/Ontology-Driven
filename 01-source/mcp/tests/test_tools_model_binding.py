"""model_binding 工具单测（fake client）。"""
from ontotwin_mcp.server import build_server


class C:
    def __init__(self):
        self.calls = []

    def get(self, op, path, params=None):
        self.calls.append(("get", path, params)); return {"ok": True}

    def post_json(self, op, path, json=None, timeout=None):
        self.calls.append(("post", path, json)); return {"status": "ok"}

    def put_json(self, op, path, json=None, timeout=None):
        self.calls.append(("put", path, json)); return {"status": "ok"}

    def delete_json(self, op, path, json=None, timeout=None):
        self.calls.append(("delete", path, json)); return {"status": "ok"}


def _t(mcp, name):
    return mcp._ot_tools[name]


def test_get_model_binding_endpoint():
    c = C(); mcp = build_server(c)
    _t(mcp, "get_model_binding")("i1")
    assert c.calls[-1] == ("get", "/api/v2/instances/i1/model-binding", None)


def test_set_model_binding_body_with_expected():
    c = C(); mcp = build_server(c)
    _t(mcp, "set_model_binding")("i1", {"asset_id": "m2"}, expected_project_id="p1")
    method, path, body = c.calls[-1]
    assert method == "put"
    assert path == "/api/v2/instances/i1/model-binding"
    assert body == {"asset_id": "m2", "expected_project_id": "p1"}


def test_clear_model_binding_delete_body():
    c = C(); mcp = build_server(c)
    _t(mcp, "clear_model_binding")("i1", expected_project_id="p1")
    method, path, body = c.calls[-1]
    assert method == "delete"
    assert path == "/api/v2/instances/i1/model-binding"
    assert body == {"expected_project_id": "p1"}


def test_clear_type_model_default_endpoint():
    c = C(); mcp = build_server(c)
    _t(mcp, "clear_type_model_default")("rid.a")
    method, path, body = c.calls[-1]
    assert method == "delete"
    assert path == "/api/v2/object-types/rid.a/model-binding"


def test_promote_model_binding_body():
    c = C(); mcp = build_server(c)
    _t(mcp, "promote_model_binding")("rid.a", "assets/high.glb")
    method, path, body = c.calls[-1]
    assert method == "post"
    assert path == "/api/v2/object-types/rid.a/model-binding/promote"
    assert body == {"source_asset_path": "assets/high.glb"}


def test_model_binding_tools_registered():
    c = C(); mcp = build_server(c)
    assert {"get_model_binding", "set_model_binding", "clear_model_binding",
            "clear_type_model_default", "promote_model_binding"} <= set(mcp._ot_tools)
