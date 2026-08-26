"""既有域新增工具的单测：zones 目录、批量回写、材质回写、媒体解析、场景清空。"""
from ontotwin_mcp.server import build_server


class C:
    def __init__(self):
        self.calls = []

    def get(self, op, path, params=None):
        self.calls.append(("get", path, params)); return {}

    def put_json(self, op, path, json=None, timeout=None):
        self.calls.append(("put", path, json)); return {"status": "ok"}

    def post_json(self, op, path, json=None, timeout=None):
        self.calls.append(("post", path, json)); return {"status": "ok"}


def _t(mcp, name):
    return mcp._ot_tools[name]


# ── zones 目录 ────────────────────────────────────────────
def test_save_zone_catalog_body():
    c = C(); mcp = build_server(c)
    zones = [{"zone_id": "floor3", "name": "三楼", "level": "floor"}]
    _t(mcp, "save_zone_catalog")(zones)
    method, path, body = c.calls[-1]
    assert (method, path) == ("put", "/api/v2/zones/catalog")
    assert body == {"zones": zones}


def test_save_zone_catalog_project_guard():
    c = C(); mcp = build_server(c)
    _t(mcp, "save_zone_catalog")([], expected_project_id="p1")
    assert c.calls[-1][2]["expected_project_id"] == "p1"


# ── 批量 / 材质回写 ───────────────────────────────────────
def test_writeback_batch_endpoint():
    c = C(); mcp = build_server(c)
    changes = [{"instance_id": "i1", "transform": {"tx": 1}}]
    _t(mcp, "writeback_transforms_batch")(changes)
    method, path, body = c.calls[-1]
    assert (method, path) == ("post", "/api/v2/state/writeback/batch")
    assert body == {"changes": changes}


def test_writeback_batch_is_separate_from_single():
    """批量与单条走不同端点，别混。"""
    c = C(); mcp = build_server(c)
    _t(mcp, "writeback_instance_transform")("i1", {"tx": 1})
    single = c.calls[-1][1]
    _t(mcp, "writeback_transforms_batch")([])
    batch = c.calls[-1][1]
    assert single == "/api/v2/state/writeback"
    assert batch == "/api/v2/state/writeback/batch"


def test_material_writeback_endpoint():
    c = C(); mcp = build_server(c)
    _t(mcp, "writeback_material_overrides")([{"instance_id": "i1"}],
                                            expected_project_id="p2")
    method, path, body = c.calls[-1]
    assert (method, path) == ("post", "/api/v2/state/material-writeback")
    assert body["expected_project_id"] == "p2"


# ── overlay 媒体解析 ──────────────────────────────────────
def test_resolve_overlay_media_body():
    c = C(); mcp = build_server(c)
    _t(mcp, "resolve_overlay_media")("i7")
    method, path, body = c.calls[-1]
    assert (method, path) == ("post", "/api/v2/overlays/media/resolve")
    assert body == {"instance_id": "i7"}


# ── 场景概况 / 清空 ───────────────────────────────────────
def test_list_scenes_endpoint():
    c = C(); mcp = build_server(c)
    _t(mcp, "list_scenes")()
    assert c.calls[-1] == ("get", "/api/v2/scenes", None)


def test_clear_scene_endpoint():
    c = C(); mcp = build_server(c)
    _t(mcp, "clear_scene")()
    method, path, _ = c.calls[-1]
    assert (method, path) == ("post", "/api/v2/scene/clear")


def test_clear_scene_marked_high_risk():
    """清空场景是高危操作，docstring 要写明并指向回收站。"""
    c = C(); mcp = build_server(c)
    doc = _t(mcp, "clear_scene").__doc__ or ""
    assert "高危" in doc
    assert "回收站" in doc


def test_total_tool_count_grew():
    """新增 24 个工具后总数应到 115；掉了说明有模块没注册上。"""
    c = C(); mcp = build_server(c)
    assert len(mcp._ot_tools) == 115
