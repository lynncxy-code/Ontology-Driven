"""spatial（空间参考帧）工具单测（fake client，不起真 HTTP）。"""
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

    def post_multipart(self, op, path, files, data=None, timeout=None):
        self.calls.append(("multipart", path, list(files), data)); return {"status": "ok"}


def _t(mcp, name):
    return mcp._ot_tools[name]


def test_create_reference_frame_multipart(monkeypatch):
    monkeypatch.setattr(
        "ontotwin_mcp.tools.spatial.resolve_upload",
        lambda p, s, allowed_ext=None: ("plan.png", b"img"))
    c = C(); mcp = build_server(c)
    _t(mcp, "create_reference_frame")("whatever.png", floor=2, floor_id="F2", name="一楼底图")
    method, path, files, data = c.calls[-1]
    assert method == "multipart"
    assert path == "/api/v2/spatial-frames/assets"
    assert files[0] == ("file", "plan.png", b"img")
    assert data == {"floor": "2", "floor_id": "F2", "name": "一楼底图"}
    assert "ue_level" not in data  # 空项不放入


def test_list_reference_frames_endpoint():
    c = C(); mcp = build_server(c)
    _t(mcp, "list_reference_frames")()
    assert c.calls[-1] == ("get", "/api/v2/spatial-frames", None)


def test_get_reference_frame_encoded_path():
    c = C(); mcp = build_server(c)
    _t(mcp, "get_reference_frame")("frame#1")
    assert c.calls[-1] == ("get", "/api/v2/spatial-frames/frame%231", None)


def test_save_reference_frame_draft_with_expected():
    c = C(); mcp = build_server(c)
    _t(mcp, "save_reference_frame_draft")("f1", {"anchors": [1]}, expected_draft_revision=3)
    method, path, body = c.calls[-1]
    assert method == "put"
    assert path == "/api/v2/spatial-frames/f1/draft"
    assert body == {"anchors": [1], "expected_draft_revision": 3}


def test_save_reference_frame_draft_omits_none_expected():
    c = C(); mcp = build_server(c)
    _t(mcp, "save_reference_frame_draft")("f1", {"anchors": []})
    method, path, body = c.calls[-1]
    assert body == {"anchors": []}
    assert "expected_draft_revision" not in body


def test_publish_reference_frame_body():
    c = C(); mcp = build_server(c)
    _t(mcp, "publish_reference_frame")("f1", expected_draft_revision=5)
    method, path, body = c.calls[-1]
    assert method == "post"
    assert path == "/api/v2/spatial-frames/f1/publish"
    assert body == {"expected_draft_revision": 5}


def test_publish_reference_frame_empty_body():
    c = C(); mcp = build_server(c)
    _t(mcp, "publish_reference_frame")("f1")
    assert c.calls[-1][2] == {}


def test_create_reference_frame_threads_expected_project(monkeypatch):
    monkeypatch.setattr(
        "ontotwin_mcp.tools.spatial.resolve_upload",
        lambda p, s, allowed_ext=None: ("plan.png", b"img"))
    c = C(); mcp = build_server(c)
    _t(mcp, "create_reference_frame")("whatever.png", expected_project_id="p1")
    data = c.calls[-1][3]
    assert data.get("expected_project_id") == "p1"


def test_create_reference_frame_omits_empty_expected_project(monkeypatch):
    monkeypatch.setattr(
        "ontotwin_mcp.tools.spatial.resolve_upload",
        lambda p, s, allowed_ext=None: ("plan.png", b"img"))
    c = C(); mcp = build_server(c)
    _t(mcp, "create_reference_frame")("whatever.png")
    data = c.calls[-1][3]
    assert "expected_project_id" not in data


def test_save_reference_frame_draft_threads_expected_project():
    c = C(); mcp = build_server(c)
    _t(mcp, "save_reference_frame_draft")("f1", {"anchors": []}, expected_project_id="p1")
    body = c.calls[-1][2]
    assert body.get("expected_project_id") == "p1"


def test_save_reference_frame_draft_omits_empty_expected_project():
    c = C(); mcp = build_server(c)
    _t(mcp, "save_reference_frame_draft")("f1", {"anchors": []})
    assert "expected_project_id" not in c.calls[-1][2]


def test_publish_reference_frame_threads_expected_project():
    c = C(); mcp = build_server(c)
    _t(mcp, "publish_reference_frame")("f1", expected_project_id="p1")
    assert c.calls[-1][2].get("expected_project_id") == "p1"


def test_publish_reference_frame_omits_empty_expected_project():
    c = C(); mcp = build_server(c)
    _t(mcp, "publish_reference_frame")("f1")
    assert "expected_project_id" not in c.calls[-1][2]


def test_spatial_tools_registered():
    c = C(); mcp = build_server(c)
    expected = {
        "create_reference_frame", "list_reference_frames", "get_reference_frame",
        "save_reference_frame_draft", "publish_reference_frame",
    }
    assert expected <= set(mcp._ot_tools)
