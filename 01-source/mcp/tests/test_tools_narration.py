"""narration（路点语音讲解）工具单测（fake client，不起真 HTTP）。"""
from ontotwin_mcp.server import build_server


class C:
    def __init__(self):
        self.calls = []

    def get(self, op, path, params=None):
        self.calls.append(("get", path, params)); return {"configured": False}

    def put_json(self, op, path, json=None, timeout=None):
        self.calls.append(("put", path, json)); return {"status": "ok"}

    def post_json(self, op, path, json=None, timeout=None):
        self.calls.append(("post", path, json, timeout)); return {"status": "ok"}


def _t(mcp, name):
    return mcp._ot_tools[name]


def test_provider_status_endpoint():
    c = C(); mcp = build_server(c)
    _t(mcp, "get_narration_provider_status")()
    assert c.calls[-1] == (
        "get", "/api/v2/scene-interactions/narration/provider-status", None)


def test_save_defaults_body():
    c = C(); mcp = build_server(c)
    _t(mcp, "save_narration_defaults")({"voice_id": "xiaoyun"}, 4)
    method, path, body = c.calls[-1]
    assert (method, path) == ("put", "/api/v2/scene-interactions/narration/defaults")
    assert body == {"defaults": {"voice_id": "xiaoyun"}, "expected_revision": 4}
    assert "expected_project_id" not in body


def test_save_defaults_with_project_guard():
    c = C(); mcp = build_server(c)
    _t(mcp, "save_narration_defaults")({}, 1, expected_project_id="p9")
    assert c.calls[-1][2]["expected_project_id"] == "p9"


def test_generate_path_quotes_route_id():
    c = C(); mcp = build_server(c)
    _t(mcp, "generate_route_narration")("route a/1", 2)
    path = c.calls[-1][1]
    assert path.startswith("/api/v2/scene-interactions/routes/")
    assert path.endswith("/narration/generate")
    assert " " not in path


def test_generate_omits_empty_waypoint_ids():
    c = C(); mcp = build_server(c)
    _t(mcp, "generate_route_narration")("r1", 3)
    body = c.calls[-1][2]
    assert body == {"expected_revision": 3}
    assert "waypoint_ids" not in body


def test_generate_passes_waypoint_subset():
    c = C(); mcp = build_server(c)
    _t(mcp, "generate_route_narration")("r1", 3, waypoint_ids=["w1", "w2"])
    assert c.calls[-1][2]["waypoint_ids"] == ["w1", "w2"]


def test_generate_uses_long_timeout():
    """TTS 合成慢，必须放宽超时，否则默认 30s 会误判失败。"""
    c = C(); mcp = build_server(c)
    _t(mcp, "generate_route_narration")("r1", 1)
    timeout = c.calls[-1][3]
    assert timeout and timeout >= 120


def test_audio_download_not_exposed():
    """音频二进制下载不该做成工具。"""
    c = C(); mcp = build_server(c)
    assert not any("asset_file" in n or "narration_asset" in n
                   for n in mcp._ot_tools)


def test_tools_registered():
    c = C(); mcp = build_server(c)
    assert {"get_narration_provider_status", "save_narration_defaults",
            "generate_route_narration"} <= set(mcp._ot_tools)
