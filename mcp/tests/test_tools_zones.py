"""zones（分区）工具单测（fake client，不起真 HTTP）。"""
from ontotwin_mcp.server import build_server


class C:
    def __init__(self):
        self.calls = []

    def get(self, op, path, params=None):
        self.calls.append(("get", path, params)); return {"zones": []}

    def put_json(self, op, path, json=None, timeout=None):
        self.calls.append(("put", path, json)); return {"ok": True}


def _t(mcp, name):
    return mcp._ot_tools[name]


def test_get_zones_endpoint():
    c = C(); mcp = build_server(c)
    _t(mcp, "get_zones")()
    assert c.calls[-1] == ("get", "/api/v2/zones", None)


def test_assign_zones_body_zone_and_expected():
    c = C(); mcp = build_server(c)
    _t(mcp, "assign_zones")(["i1", "i2"], zone_id="A区", expected_project_id="p1")
    method, path, body = c.calls[-1]
    assert method == "put"
    assert path == "/api/v2/zones/assignments"
    assert body == {"instance_ids": ["i1", "i2"], "zone_id": "A区", "expected_project_id": "p1"}


def test_assign_zones_empty_zone_becomes_none():
    c = C(); mcp = build_server(c)
    _t(mcp, "assign_zones")(["i1"])
    method, path, body = c.calls[-1]
    assert body == {"instance_ids": ["i1"], "zone_id": None}
    assert "expected_project_id" not in body


def test_zones_tools_registered():
    c = C(); mcp = build_server(c)
    assert {"get_zones", "assign_zones"} <= set(mcp._ot_tools)
