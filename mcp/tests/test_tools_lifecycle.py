"""lifecycle 工具单测（fake client）。"""
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

    def delete_json(self, op, path, json=None, timeout=None):
        self.calls.append(("delete", path, json)); return {"status": "removed"}


def _t(mcp, name):
    return mcp._ot_tools[name]


def test_create_instance_body_minimal():
    c = C(); mcp = build_server(c)
    _t(mcp, "create_instance")("i1", "rid.a")
    method, path, body = c.calls[-1]
    assert method == "post" and path == "/api/v2/instances"
    assert body == {"instance_id": "i1", "object_type_rid": "rid.a"}


def test_create_instance_body_full():
    c = C(); mcp = build_server(c)
    _t(mcp, "create_instance")("i1", "rid.a", initial_position={"x": 1, "y": 2, "z": 0},
                               display_name="货架A", expected_project_id="p1")
    body = c.calls[-1][2]
    assert body == {"instance_id": "i1", "object_type_rid": "rid.a",
                    "initial_position": {"x": 1, "y": 2, "z": 0},
                    "display_name": "货架A", "expected_project_id": "p1"}


def test_delete_instance_delete_json_with_expected():
    c = C(); mcp = build_server(c)
    _t(mcp, "delete_instance")("a#1", expected_project_id="p1")
    method, path, body = c.calls[-1]
    assert method == "delete"
    assert path == "/api/v2/instances/a%231"
    assert body == {"expected_project_id": "p1"}


def test_delete_instance_no_expected_empty_body():
    c = C(); mcp = build_server(c)
    _t(mcp, "delete_instance")("i1")
    assert c.calls[-1][2] == {}


def test_set_instance_transform_body():
    c = C(); mcp = build_server(c)
    _t(mcp, "set_instance_transform")("i1", {"canonical_xy": [1, 2], "rotation": 90},
                                      expected_project_id="p1")
    method, path, body = c.calls[-1]
    assert method == "put"
    assert path == "/api/v2/instances/i1/transform"
    assert body == {"canonical_xy": [1, 2], "rotation": 90, "expected_project_id": "p1"}


def test_writeback_transform_body():
    c = C(); mcp = build_server(c)
    _t(mcp, "writeback_instance_transform")("i1", {"tx": 1, "ty": 2, "tz": 3})
    method, path, body = c.calls[-1]
    assert method == "post"
    assert path == "/api/v2/state/writeback"
    assert body == {"instance_id": "i1", "transform": {"tx": 1, "ty": 2, "tz": 3}}


def test_lifecycle_tools_registered():
    c = C(); mcp = build_server(c)
    assert {"create_instance", "delete_instance", "set_instance_transform",
            "writeback_instance_transform"} <= set(mcp._ot_tools)
