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
    r = client.post("/api/v2/state/writeback", json={
        "instance_id": "DW-WB", "transform": {"tx": 0, "ty": 0, "tz": 0},
        "expected_project_id": "p_other"})
    assert r.status_code == 409
