"""web_interaction（Web 交互配置）工具单测（fake client，不起真 HTTP）。"""
from ontotwin_mcp.server import build_server


class C:
    def __init__(self):
        self.calls = []

    def get(self, op, path, params=None):
        self.calls.append(("get", path, params)); return {"revision": 3}

    def put_json(self, op, path, json=None, timeout=None):
        self.calls.append(("put", path, json)); return {"status": "ok"}

    def post_json(self, op, path, json=None, timeout=None):
        self.calls.append(("post", path, json)); return {"status": "ok"}


def _t(mcp, name):
    return mcp._ot_tools[name]


def test_get_endpoint():
    c = C(); mcp = build_server(c)
    _t(mcp, "get_web_interaction")()
    assert c.calls[-1] == ("get", "/api/v2/web-interactions", None)


def test_validate_without_config_sends_empty_body():
    c = C(); mcp = build_server(c)
    _t(mcp, "validate_web_interaction")()
    method, path, body = c.calls[-1]
    assert (method, path) == ("post", "/api/v2/web-interactions/validate")
    assert body == {}


def test_validate_with_config_passes_through():
    c = C(); mcp = build_server(c)
    _t(mcp, "validate_web_interaction")({"pages": []})
    assert c.calls[-1][2] == {"config": {"pages": []}}


def test_preview_defaults_to_draft_source():
    c = C(); mcp = build_server(c)
    _t(mcp, "preview_web_interaction")()
    method, path, body = c.calls[-1]
    assert path == "/api/v2/web-interactions/resolve-preview"
    assert body == {"source": "draft"}


def test_preview_published_source():
    c = C(); mcp = build_server(c)
    _t(mcp, "preview_web_interaction")(source="published")
    assert c.calls[-1][2] == {"source": "published"}


def test_save_draft_body():
    c = C(); mcp = build_server(c)
    _t(mcp, "save_web_interaction_draft")({"pages": [1]}, 7)
    method, path, body = c.calls[-1]
    assert (method, path) == ("put", "/api/v2/web-interactions/draft")
    assert body == {"draft": {"pages": [1]}, "expected_revision": 7}


def test_publish_omits_confirm_when_false():
    c = C(); mcp = build_server(c)
    _t(mcp, "publish_web_interaction")(2)
    body = c.calls[-1][2]
    assert body == {"expected_revision": 2}
    assert "confirm_warnings" not in body


def test_publish_includes_confirm_when_true():
    c = C(); mcp = build_server(c)
    _t(mcp, "publish_web_interaction")(2, confirm_warnings=True)
    assert c.calls[-1][2] == {"expected_revision": 2, "confirm_warnings": True}


def test_apply_carries_config_and_revision():
    c = C(); mcp = build_server(c)
    _t(mcp, "apply_web_interaction")({"pages": []}, 5)
    method, path, body = c.calls[-1]
    assert (method, path) == ("post", "/api/v2/web-interactions/apply")
    assert body == {"config": {"pages": []}, "expected_revision": 5}


def test_rollback_body():
    c = C(); mcp = build_server(c)
    _t(mcp, "rollback_web_interaction")(9)
    method, path, body = c.calls[-1]
    assert (method, path) == ("post", "/api/v2/web-interactions/rollback")
    assert body == {"expected_revision": 9}


def test_runtime_channels_not_exposed():
    """UE 心跳通道不该出现在工具清单里。"""
    c = C(); mcp = build_server(c)
    names = set(mcp._ot_tools)
    assert not any("runtime_event" in n for n in names)


def test_tools_registered():
    c = C(); mcp = build_server(c)
    assert {
        "get_web_interaction", "validate_web_interaction",
        "preview_web_interaction", "save_web_interaction_draft",
        "publish_web_interaction", "apply_web_interaction",
        "rollback_web_interaction",
    } <= set(mcp._ot_tools)
