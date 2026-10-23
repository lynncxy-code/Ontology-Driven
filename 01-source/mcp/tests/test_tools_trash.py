"""trash（回收站）工具单测（fake client，不起真 HTTP）。"""
from ontotwin_mcp.server import build_server


class C:
    def __init__(self):
        self.calls = []

    def get(self, op, path, params=None):
        self.calls.append(("get", path, params)); return {"items": []}

    def post_json(self, op, path, json=None, timeout=None):
        self.calls.append(("post", path, json)); return {"status": "ok"}

    def delete_json(self, op, path, json=None, timeout=None):
        self.calls.append(("delete", path, json)); return {"status": "ok"}


def _t(mcp, name):
    return mcp._ot_tools[name]


def test_list_endpoint():
    c = C(); mcp = build_server(c)
    _t(mcp, "list_trash")()
    assert c.calls[-1] == ("get", "/api/v2/trash", None)


def test_restore_path():
    c = C(); mcp = build_server(c)
    _t(mcp, "restore_trash_item")("project_123_ab")
    method, path, _ = c.calls[-1]
    assert (method, path) == ("post", "/api/v2/trash/project_123_ab/restore")


def test_restore_quotes_pg_style_id():
    """PG 后端的条目 id 形如 pg:inst:<pid>:<iid>，冒号必须转义。"""
    c = C(); mcp = build_server(c)
    _t(mcp, "restore_trash_item")("pg:inst:ds_1:i9")
    path = c.calls[-1][1]
    assert ":" not in path.split("/api/v2/trash/")[1].split("/restore")[0]


def test_delete_uses_delete_verb():
    c = C(); mcp = build_server(c)
    _t(mcp, "delete_trash_item")("t1")
    method, path, _ = c.calls[-1]
    assert (method, path) == ("delete", "/api/v2/trash/t1")


def test_purge_endpoint():
    c = C(); mcp = build_server(c)
    _t(mcp, "purge_trash")()
    method, path, _ = c.calls[-1]
    assert (method, path) == ("post", "/api/v2/trash/purge")


def test_destructive_tools_flagged_in_docstring():
    """永久删除类工具必须在 docstring 里写明不可恢复，避免 agent 误用。"""
    c = C(); mcp = build_server(c)
    for name in ("delete_trash_item", "purge_trash"):
        assert "不可恢复" in (_t(mcp, name).__doc__ or "")


def test_tools_registered():
    c = C(); mcp = build_server(c)
    assert {"list_trash", "restore_trash_item", "delete_trash_item",
            "purge_trash"} <= set(mcp._ot_tools)
