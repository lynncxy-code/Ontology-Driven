"""overlay 工具单测（fake client，不起真 HTTP）。"""
from ontotwin_mcp.server import build_server


class C:
    def __init__(self):
        self.calls = []

    def get(self, op, path, params=None):
        self.calls.append(("get", path, params)); return {"ok": True}

    def post_json(self, op, path, json=None, timeout=None):
        self.calls.append(("post", path, json)); return {"ok": True}

    def put_json(self, op, path, json=None, timeout=None):
        self.calls.append(("put", path, json)); return {"status": "ok"}

    def delete_json(self, op, path, json=None, timeout=None):
        self.calls.append(("delete", path, json)); return {"status": "ok"}

    def post_multipart(self, *a, **k):
        return {}


def _t(mcp, name):
    return mcp._ot_tools[name]


def test_get_overlay_context_only_nonempty_params():
    c = C(); mcp = build_server(c)
    _t(mcp, "get_overlay_context")(object_type_rid="rid.a")
    assert c.calls[-1] == ("get", "/api/v2/overlays/context", {"object_type_rid": "rid.a"})


def test_enable_info_panel_injects_two_interfaces():
    c = C(); mcp = build_server(c)
    _t(mcp, "enable_info_panel")("rid.a")
    method, path, body = c.calls[-1]
    assert path == "/api/v2/ontology/inject"
    assert body == {"object_type_rid": "rid.a",
                    "interfaces": ["I3D_Representable", "I3D_Overlay"]}


def test_save_overlay_type_config_put_body_and_encoded_path():
    c = C(); mcp = build_server(c)
    _t(mcp, "save_overlay_type_config")("a#b", {"slots": {}}, 4)
    method, path, body = c.calls[-1]
    assert method == "put"
    assert path == "/api/v2/overlays/object-types/a%23b"
    assert body == {"config": {"slots": {}}, "expected_revision": 4}


def test_clear_overlay_instance_override_delete_body():
    c = C(); mcp = build_server(c)
    _t(mcp, "clear_overlay_instance_override")("i1", 2)
    method, path, body = c.calls[-1]
    assert method == "delete"
    assert path == "/api/v2/overlays/instances/i1"
    assert body == {"expected_revision": 2}


def test_batch_overlay_instance_override_body():
    c = C(); mcp = build_server(c)
    _t(mcp, "batch_overlay_instance_override")(
        "rid.a", ["i1", "i2"], {"slots": {}}, {"i1": 1, "i2": 3})
    method, path, body = c.calls[-1]
    assert path == "/api/v2/overlays/instances/batch"
    assert body == {"object_type_rid": "rid.a", "instance_ids": ["i1", "i2"],
                    "merge_patch": {"slots": {}}, "expected_revisions": {"i1": 1, "i2": 3}}


def test_save_overlay_type_config_threads_expected():
    c = C(); mcp = build_server(c)
    _t(mcp, "save_overlay_type_config")("rid.a", {"slots": {}}, 4, expected_project_id="p1")
    body = c.calls[-1][2]
    assert body == {"config": {"slots": {}}, "expected_revision": 4,
                    "expected_project_id": "p1"}


def test_save_overlay_type_config_omits_empty_expected():
    c = C(); mcp = build_server(c)
    _t(mcp, "save_overlay_type_config")("rid.a", {"slots": {}}, 4)
    assert "expected_project_id" not in c.calls[-1][2]


def test_clear_overlay_instance_override_threads_expected():
    c = C(); mcp = build_server(c)
    _t(mcp, "clear_overlay_instance_override")("i1", 2, expected_project_id="p1")
    body = c.calls[-1][2]
    assert body == {"expected_revision": 2, "expected_project_id": "p1"}


def test_overlay_tools_registered():
    c = C(); mcp = build_server(c)
    expected = {
        "list_overlay_templates", "get_overlay_context", "preview_overlay",
        "get_overlay_media_policy", "enable_info_panel", "save_overlay_type_config",
        "save_overlay_instance_override", "clear_overlay_instance_override",
        "batch_overlay_instance_override", "save_overlay_media_policy",
    }
    assert expected <= set(mcp._ot_tools)
