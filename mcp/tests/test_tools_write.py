"""写链 + CAD 工具单测（FakeClient，不起真 HTTP）。

覆盖：import_csv multipart 保留 basename 作 field/filename、publish、
parse_cad_dxf 用 cadparse 超时、calibrate、save_components 透传/缺省 expected。
"""
import os

from ontotwin_mcp.server import build_server


def _tool(mcp, name):
    return mcp._ot_tools[name]


def test_import_csv_multipart_basenames(monkeypatch, tmp_path):
    files = []

    class C:
        def post_multipart(self, op, path, files_, data=None):
            files.extend(files_)
            return {"status": "ok"}

        def get(self, *a, **k):
            return []

        def post_json(self, *a, **k):
            return {}

    for n in ("objectdef.csv", "linkdef.csv"):
        (tmp_path / n).write_bytes(b"x")
    monkeypatch.setenv("NEXUS_ALLOWED_ROOTS", str(tmp_path))
    mcp = build_server(C())
    _tool(mcp, "import_ontology_csv")(
        [str(tmp_path / "objectdef.csv"), str(tmp_path / "linkdef.csv")])
    # 保留 basename 作 field/filename
    assert {f[0] for f in files} == {"objectdef.csv", "linkdef.csv"}
    assert {f[1] for f in files} == {"objectdef.csv", "linkdef.csv"}


def test_import_csv_hits_endpoint(monkeypatch, tmp_path):
    captured = {}

    class C:
        def post_multipart(self, op, path, files_, data=None):
            captured["op"] = op
            captured["path"] = path
            return {"status": "ok"}

        def get(self, *a, **k):
            return []

        def post_json(self, *a, **k):
            return {}

    (tmp_path / "objectdef.csv").write_bytes(b"x")
    monkeypatch.setenv("NEXUS_ALLOWED_ROOTS", str(tmp_path))
    mcp = build_server(C())
    _tool(mcp, "import_ontology_csv")([str(tmp_path / "objectdef.csv")])
    assert captured["path"] == "/api/v2/ontology/import_csv"
    assert captured["op"] == "import_ontology_csv"


def test_publish_ontology_dataset_posts_name():
    sent = {}

    class C:
        def post_json(self, op, path, json=None, timeout=None):
            sent["path"] = path
            sent["json"] = json
            return {"dataset_id": "d1"}

        def get(self, *a, **k):
            return []

    mcp = build_server(C())
    res = _tool(mcp, "publish_ontology_dataset")("我的库")
    assert sent["path"] == "/api/v2/ontology/publish"
    assert sent["json"] == {"name": "我的库"}
    assert res["dataset_id"] == "d1"


def test_parse_cad_dxf_uses_cadparse_timeout(monkeypatch, tmp_path):
    captured = {}

    class C:
        def post_multipart(self, op, path, files_, data=None, timeout=None):
            captured["path"] = path
            captured["files"] = list(files_)
            captured["data"] = data
            captured["timeout"] = timeout
            return {"status": "ok"}

        def get(self, *a, **k):
            return []

        def post_json(self, *a, **k):
            return {}

    (tmp_path / "plan.dxf").write_bytes(b"x")
    monkeypatch.setenv("NEXUS_ALLOWED_ROOTS", str(tmp_path))
    monkeypatch.setenv("NEXUS_TIMEOUT_CADPARSE", "99")
    mcp = build_server(C())
    _tool(mcp, "parse_cad_dxf")(str(tmp_path / "plan.dxf"), wall_height=3.0, wall_thickness=0.2)
    assert captured["path"] == "/api/v2/cad/parse"
    # field 名必须 file，filename 保留原 basename
    assert captured["files"][0][0] == "file"
    assert captured["files"][0][1] == "plan.dxf"
    assert captured["data"] == {"wall_height": 3.0, "wall_thickness": 0.2}
    assert captured["timeout"] == 99.0


def test_calibrate_coordinates_posts_anchors():
    sent = {}

    class C:
        def post_json(self, op, path, json=None, timeout=None):
            sent["path"] = path
            sent["json"] = json
            return {"matrix": []}

        def get(self, *a, **k):
            return []

    mcp = build_server(C())
    anchors = [{"src": [0, 0], "dst": [1, 1]}]
    _tool(mcp, "calibrate_coordinates")(anchors)
    assert sent["path"] == "/api/v2/coord/calibrate"
    assert sent["json"] == {"anchors": anchors}


def test_save_components_passes_expected():
    sent = {}

    class C:
        def post_json(self, op, path, json=None, timeout=None):
            sent.update(json or {})
            return {"status": "ok"}

        def get(self, *a, **k):
            return []

    mcp = build_server(C())
    _tool(mcp, "save_components")({"components": []}, expected_project_id="p1")
    assert sent.get("expected_project_id") == "p1"


def test_save_components_empty_expected_not_in_body():
    sent = {}
    path_seen = {}

    class C:
        def post_json(self, op, path, json=None, timeout=None):
            path_seen["path"] = path
            sent.update(json or {})
            return {"status": "ok"}

        def get(self, *a, **k):
            return []

    mcp = build_server(C())
    _tool(mcp, "save_components")({"components": [1]})
    assert path_seen["path"] == "/api/v2/coord/save_components"
    assert "expected_project_id" not in sent
    assert sent.get("components") == [1]


def test_write_tools_registered():
    class C:
        def get(self, *a, **k):
            return []

        def post_json(self, *a, **k):
            return {}

        def post_multipart(self, *a, **k):
            return {}

    mcp = build_server(C())
    expected = {
        "import_ontology_csv", "publish_ontology_dataset",
        "parse_cad_dxf", "calibrate_coordinates", "save_components",
    }
    assert expected <= set(mcp._ot_tools)
