"""ontology_edit 工具单测（fake client）。"""
from ontotwin_mcp.server import build_server


class C:
    def __init__(self):
        self.calls = []

    def get(self, op, path, params=None):
        self.calls.append(("get", path, params)); return {"ok": True}

    def post_json(self, op, path, json=None, timeout=None):
        self.calls.append(("post", path, json)); return {"status": "ok"}

    def delete_json(self, op, path, json=None, timeout=None):
        self.calls.append(("delete", path, json)); return {"status": "ok"}


def _t(mcp, name):
    return mcp._ot_tools[name]


def test_read_defs_endpoints():
    c = C(); mcp = build_server(c)
    _t(mcp, "list_interface_defs")()
    _t(mcp, "list_property_defs")()
    _t(mcp, "get_ontology_registry")()
    _t(mcp, "list_transform_types")()
    paths = [call[1] for call in c.calls]
    assert paths == [
        "/api/v2/ontology/interfaces", "/api/v2/ontology/properties",
        "/api/v2/ontology/registry", "/api/v2/transforms",
    ]


def test_inject_interfaces_body_minimal():
    c = C(); mcp = build_server(c)
    _t(mcp, "inject_interfaces")("rid.a", ["I3D_Representable", "I3D_Spatial"])
    method, path, body = c.calls[-1]
    assert method == "post" and path == "/api/v2/ontology/inject"
    assert body == {"object_type_rid": "rid.a",
                    "interfaces": ["I3D_Representable", "I3D_Spatial"]}
    assert "asset_id" not in body


def test_inject_interfaces_with_asset():
    c = C(); mcp = build_server(c)
    _t(mcp, "inject_interfaces")("rid.a", ["I3D_Representable"], asset_id="m1")
    body = c.calls[-1][2]
    assert body == {"object_type_rid": "rid.a",
                    "interfaces": ["I3D_Representable"], "asset_id": "m1"}


def test_remove_interface_delete_body():
    c = C(); mcp = build_server(c)
    _t(mcp, "remove_interface")("rid.a", "I3D_Spatial")
    method, path, body = c.calls[-1]
    assert method == "delete" and path == "/api/v2/ontology/inject"
    assert body == {"object_type_rid": "rid.a", "interface_rid": "I3D_Spatial"}


def test_build_staging_graph_from_registry_endpoint():
    c = C(); mcp = build_server(c)
    _t(mcp, "build_staging_graph_from_registry")()
    method, path, body = c.calls[-1]
    assert method == "post" and path == "/api/v2/ontology/graph_from_registry"


def test_ontology_edit_tools_registered():
    c = C(); mcp = build_server(c)
    expected = {
        "list_interface_defs", "list_property_defs", "get_ontology_registry",
        "list_transform_types", "inject_interfaces", "remove_interface",
        "build_staging_graph_from_registry",
    }
    assert expected <= set(mcp._ot_tools)
