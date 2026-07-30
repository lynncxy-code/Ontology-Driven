"""cad_calibration 工具单测（fake client）。"""
from ontotwin_mcp.server import build_server


class C:
    def __init__(self):
        self.calls = []

    def post_json(self, op, path, json=None, timeout=None):
        self.calls.append(("post", path, json)); return {"status": "ok"}

    def post_multipart(self, op, path, files, data=None, timeout=None):
        self.calls.append(("multipart", path, list(files), data, timeout)); return {"ok": True}

    def get(self, *a, **k):
        return {}


def _t(mcp, name):
    return mcp._ot_tools[name]


def test_preview_cad_multipart(monkeypatch):
    monkeypatch.setattr("ontotwin_mcp.tools.cad_calibration.resolve_upload",
                        lambda p, s, allowed_ext=None: ("plan.dxf", b"x"))
    monkeypatch.setenv("NEXUS_TIMEOUT_CADPARSE", "77")
    c = C(); mcp = build_server(c)
    _t(mcp, "preview_cad")("whatever.dxf")
    method, path, files, data, timeout = c.calls[-1]
    assert method == "multipart" and path == "/api/v2/coord/preview"
    assert files[0] == ("file", "plan.dxf", b"x")
    assert timeout == 77.0


def test_scan_cad_types_multipart(monkeypatch):
    monkeypatch.setattr("ontotwin_mcp.tools.cad_calibration.resolve_upload",
                        lambda p, s, allowed_ext=None: ("plan.dxf", b"x"))
    c = C(); mcp = build_server(c)
    _t(mcp, "scan_cad_types")("whatever.dxf")
    assert c.calls[-1][1] == "/api/v2/coord/types/scan"


def test_check_type_conflicts_body():
    c = C(); mcp = build_server(c)
    _t(mcp, "check_type_conflicts")(["A", "B"], mode="merge", target_dataset_id="ds1")
    method, path, body = c.calls[-1]
    assert path == "/api/v2/coord/types/check_conflicts"
    assert body == {"rids": ["A", "B"], "mode": "merge", "target_dataset_id": "ds1"}


def test_check_type_conflicts_omits_empty_target():
    c = C(); mcp = build_server(c)
    _t(mcp, "check_type_conflicts")(["A"])
    assert c.calls[-1][2] == {"rids": ["A"], "mode": "publish"}


def test_check_type_coverage_body():
    c = C(); mcp = build_server(c)
    _t(mcp, "check_type_coverage")(["A", "B"])
    method, path, body = c.calls[-1]
    assert path == "/api/v2/coord/types/check_coverage"
    assert body == {"block_names": ["A", "B"]}


def test_commit_cad_types_body():
    c = C(); mcp = build_server(c)
    _t(mcp, "commit_cad_types")([{"block_name": "X"}], "publish",
                                source_file="a.dxf",
                                publish_options={"name": "厂A"})
    method, path, body = c.calls[-1]
    assert path == "/api/v2/coord/types/commit"
    assert body == {"items": [{"block_name": "X"}], "mode": "publish",
                    "source_file": "a.dxf", "publish_options": {"name": "厂A"}}


def test_spawn_cad_instances_dry_run_body():
    c = C(); mcp = build_server(c)
    _t(mcp, "spawn_cad_instances")([{"block_name": "X", "cad_xy": [1, 2]}],
                                   [[1, 0, 0], [0, 1, 0]])
    method, path, body = c.calls[-1]
    assert path == "/api/v2/coord/spawn_instances"
    assert body == {"items": [{"block_name": "X", "cad_xy": [1, 2]}],
                    "transform_matrix": [[1, 0, 0], [0, 1, 0]],
                    "mode": "dxf", "conflict_strategy": "update_coord", "commit": False}
    assert "expected_project_id" not in body


def test_spawn_cad_instances_commit_with_expected():
    c = C(); mcp = build_server(c)
    _t(mcp, "spawn_cad_instances")([{"block_name": "X"}], [[1, 0, 0], [0, 1, 0]],
                                   source_label="a.dxf", commit=True,
                                   expected_project_id="p1")
    body = c.calls[-1][2]
    assert body["commit"] is True
    assert body["source_label"] == "a.dxf"
    assert body["expected_project_id"] == "p1"


def test_cad_calibration_tools_registered():
    c = C(); mcp = build_server(c)
    expected = {
        "preview_cad", "scan_cad_types", "check_type_conflicts",
        "check_type_coverage", "commit_cad_types", "spawn_cad_instances",
    }
    assert expected <= set(mcp._ot_tools)
