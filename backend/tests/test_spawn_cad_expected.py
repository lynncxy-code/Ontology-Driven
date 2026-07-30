"""
M5a Task 1 — coord/spawn_instances 端点透传可选 expected_project_id。

真写阶段（commit=True）把 expected_project_id 透传到 spawn/update_raw_state，
下游在锁内校验激活项目；不符抛 ProjectMismatch → 端点返回 409。
dry-run（commit=False）不受影响：无论 expected 是否匹配都只返回预览。
"""


def test_spawn_cad_expected_mismatch_409(client, store, monkeypatch):
    # spawn 端点前置校验用 app 模块级 _object_types；塞一个可用类型让 item 过三态校验。
    import app
    monkeypatch.setitem(app._object_types, "TESTBLK",
                        {"rid": "TESTBLK", "name": "测试块", "injected_interfaces": ["I3D_Representable"]})
    body = {
        "items": [{"block_name": "TESTBLK", "cad_xy": [1.0, 2.0]}],
        "transform_matrix": [[1, 0, 0], [0, 1, 0]],
        "commit": True,
        "expected_project_id": "p_other",
    }
    r = client.post("/api/v2/coord/spawn_instances", json=body)
    assert r.status_code == 409
    assert r.get_json().get("expected") == "p_other"


def test_spawn_cad_dry_run_ignores_expected(client, store, monkeypatch):
    import app
    monkeypatch.setitem(app._object_types, "TESTBLK",
                        {"rid": "TESTBLK", "name": "测试块", "injected_interfaces": ["I3D_Representable"]})
    body = {
        "items": [{"block_name": "TESTBLK", "cad_xy": [1.0, 2.0]}],
        "transform_matrix": [[1, 0, 0], [0, 1, 0]],
        "commit": False,               # dry-run
        "expected_project_id": "p_other",
    }
    r = client.post("/api/v2/coord/spawn_instances", json=body)
    assert r.status_code == 200
    assert r.get_json().get("status") == "dry_run"


def test_spawn_cad_expected_match_writes(client, store, monkeypatch):
    import app
    monkeypatch.setitem(app._object_types, "TESTBLK",
                        {"rid": "TESTBLK", "name": "测试块", "injected_interfaces": ["I3D_Representable"]})
    body = {
        "items": [{"block_name": "TESTBLK", "cad_xy": [3.0, 4.0], "instance_id": "TB-1"}],
        "transform_matrix": [[1, 0, 0], [0, 1, 0]],
        "commit": True,
        "expected_project_id": "p_test",   # 与激活项目一致
    }
    r = client.post("/api/v2/coord/spawn_instances", json=body)
    assert r.status_code == 200
    assert r.get_json()["summary"]["written_create"] == 1
