from ontotwin_mcp.server import build_server


class FakeClient:
    """记录调用并回放路由响应；不起真 HTTP，用于单测直调裸函数。"""

    def __init__(self, routes):
        self.routes = routes
        self.calls = []

    def get(self, op, path, params=None):
        self.calls.append((op, path, params))
        return self.routes[path]

    def post_json(self, op, path, json=None, timeout=None):
        self.calls.append((op, path, json))
        return self.routes[path]


def _tool(mcp, name):
    """按名取已注册工具的裸函数（绕过 MCP 协议层）。见 task-5 报告的注册表决策。"""
    return mcp._ot_tools[name]


def test_get_active_project_normalizes_demo():
    c = FakeClient({"/api/v2/ontology/datasets": [{"id": "demo", "name": "D", "is_active": True}]})
    mcp = build_server(c)
    res = _tool(mcp, "get_active_project")()
    assert res["kind"] == "demo"
    assert res["writable"] is False
    assert res["project_id"] is None
    assert res["dataset_id"] == "demo"


def test_get_active_project_writable():
    c = FakeClient({"/api/v2/ontology/datasets": [{"id": "p1", "name": "厂", "is_active": True}]})
    mcp = build_server(c)
    res = _tool(mcp, "get_active_project")()
    assert res["writable"] is True
    assert res["project_id"] == "p1"
    assert res["kind"] == "project"
    assert res["dataset_name"] == "厂"


def test_get_active_project_none():
    c = FakeClient({"/api/v2/ontology/datasets": [{"id": "p1", "name": "厂", "is_active": False}]})
    mcp = build_server(c)
    res = _tool(mcp, "get_active_project")()
    assert res["kind"] == "none"
    assert res["writable"] is False
    assert res["dataset_id"] is None


def test_list_instances_calls_endpoint():
    c = FakeClient({"/api/v2/instances": [{"id": "i1"}]})
    mcp = build_server(c)
    assert _tool(mcp, "list_instances")() == [{"id": "i1"}]
    assert c.calls[0][1] == "/api/v2/instances"


def test_list_projects_calls_endpoint():
    c = FakeClient({"/api/v2/ontology/datasets": [{"id": "p1", "is_active": True}]})
    mcp = build_server(c)
    assert _tool(mcp, "list_projects")() == [{"id": "p1", "is_active": True}]
    assert c.calls[-1][1] == "/api/v2/ontology/datasets"


def test_create_empty_project_forces_no_activate():
    c = FakeClient({"/api/v2/ontology/datasets": {"id": "new"}})
    mcp = build_server(c)
    _tool(mcp, "create_empty_project")("新厂")
    op, path, payload = c.calls[-1]
    assert path == "/api/v2/ontology/datasets"
    assert payload == {"name": "新厂", "activate": False}


def test_activate_project_posts_dataset_id():
    c = FakeClient({"/api/v2/ontology/datasets/activate": {"ok": True}})
    mcp = build_server(c)
    _tool(mcp, "activate_project")("p1")
    op, path, payload = c.calls[-1]
    assert path == "/api/v2/ontology/datasets/activate"
    assert payload == {"dataset_id": "p1"}


def test_get_object_type_uses_rid_in_path():
    c = FakeClient({"/api/v2/ontology/types/rid.abc": {"rid": "rid.abc"}})
    mcp = build_server(c)
    res = _tool(mcp, "get_object_type")("rid.abc")
    assert res == {"rid": "rid.abc"}
    assert c.calls[-1][1] == "/api/v2/ontology/types/rid.abc"


def test_get_project_ontology_graph_defaults_to_active_dataset():
    c = FakeClient({
        "/api/v2/ontology/datasets": [{"id": "p1", "name": "厂", "is_active": True}],
        "/api/v2/ontology/datasets/p1/graph": {"nodes": [], "links": []},
    })
    mcp = build_server(c)
    res = _tool(mcp, "get_project_ontology_graph")()
    assert res == {"nodes": [], "links": []}
    assert c.calls[-1][1] == "/api/v2/ontology/datasets/p1/graph"


def test_get_instance_snapshot_passes_id_param():
    c = FakeClient({"/api/v2/state/snapshot": {"id": "i1", "state": "ok"}})
    mcp = build_server(c)
    res = _tool(mcp, "get_instance_snapshot")("i1")
    assert res == {"id": "i1", "state": "ok"}
    op, path, params = c.calls[-1]
    assert path == "/api/v2/state/snapshot"
    assert params == {"id": "i1"}


def test_all_read_tools_registered():
    c = FakeClient({})
    mcp = build_server(c)
    expected = {
        "list_projects", "get_active_project", "activate_project", "create_empty_project",
        "get_import_staging_graph", "get_project_ontology_graph", "list_object_types", "get_object_type",
        "list_instances", "get_instance_state", "get_instance_snapshot", "get_state_snapshots",
        "get_spatial_profile", "list_components", "list_roster",
    }
    assert expected <= set(mcp._ot_tools)
