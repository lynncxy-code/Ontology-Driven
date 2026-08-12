import pytest
from project_store import ProjectMismatch


def test_spawn_expected_mismatch_raises(store):
    with pytest.raises(ProjectMismatch) as e:
        store.spawn("i-x", "PE16A", {"x": 0, "y": 0, "z": 0}, expected_project_id="p_other")
    assert e.value.expected == "p_other" and e.value.actual == "p_test"
    assert store.get_raw_state("i-x") is None  # 未写


def test_spawn_expected_match_ok(store):
    inst = store.spawn("i-ok", "PE16A", {"x": 1, "y": 2, "z": 0}, expected_project_id="p_test")
    assert inst is not None
    assert store.get_raw_state("i-ok") is not None


def test_spawn_expected_none_skips(store):
    inst = store.spawn("i-none", "PE16A")
    assert inst is not None


def test_remove_expected_mismatch_raises(store):
    store.spawn("i-del", "PE16A")
    with pytest.raises(ProjectMismatch):
        store.remove("i-del", expected_project_id="p_other")
    assert store.get_raw_state("i-del") is not None  # 未删


def test_remove_expected_match_ok(store):
    store.spawn("i-del2", "PE16A")
    store.remove("i-del2", expected_project_id="p_test")
    assert store.get_raw_state("i-del2") is None


def test_update_component_expected_mismatch_raises(store):
    with pytest.raises(ProjectMismatch):
        store.update_component("c1", {"rotation": 90}, expected_project_id="p_other")


def test_update_component_expected_match_ok(store):
    assert store.update_component("c1", {"rotation": 45}, expected_project_id="p_test") is True


# ── 端点 409 契约（client fixture）──────────────────────────────
def test_delete_endpoint_expected_mismatch_409(client, store):
    store.spawn("DW-DEL", "PE16A")
    r = client.delete("/api/v2/instances/DW-DEL", json={"expected_project_id": "p_other"})
    assert r.status_code == 409
    assert r.get_json().get("expected") == "p_other"


def test_writeback_endpoint_expected_mismatch_409(client, store):
    store.spawn("DW-WB", "PE16A")
    r = client.post(
        "/api/v2/state/writeback",
        headers={"X-OntoTwin-Client": "Web"},
        json={
            "instance_id": "DW-WB",
            "transform": {"tx": 0, "ty": 0, "tz": 0},
            "expected_project_id": "p_other",
        },
    )
    assert r.status_code == 409


def test_spawn_endpoint_expected_mismatch_409(client, store, monkeypatch):
    # spawn 端点在触达 store 守卫前先校验 object_type 已挂载 injected_interfaces，
    # 而 fixture 的 PE16A 无接口（会 400）。故先给 app._object_types 里的 PE16A
    # 挂一个非空 injected_interfaces，再用错的 expected_project_id 触发 409。
    import app as app_module
    monkeypatch.setitem(app_module._object_types, "PE16A", {
        "rid": "PE16A", "name": "溶铜槽", "injected_interfaces": ["I3D_Representable"]})
    r = client.post("/api/v2/instances", json={
        "instance_id": "DW-SP", "object_type_rid": "PE16A",
        "expected_project_id": "p_other"})
    assert r.status_code == 409
    assert r.get_json().get("expected") == "p_other"


def test_transform_endpoint_expected_mismatch_409(client, store):
    store.spawn("DW-TF", "PE16A")  # 自由实例（无绑定构件）
    r = client.put("/api/v2/instances/DW-TF/transform", json={
        "canonical_xy": [1, 2], "expected_project_id": "p_other"})
    assert r.status_code == 409
