import pytest
from project_store import ProjectMismatch


def test_set_spatial_profile_expected_mismatch(store):
    with pytest.raises(ProjectMismatch) as e:
        store.set_spatial_profile({"canonical_origin": [2, 2]}, expected_project_id="p_other")
    assert e.value.expected == "p_other" and e.value.actual == "p_test"


def test_set_spatial_profile_expected_match(store):
    store.set_spatial_profile({"canonical_origin": [3, 3]}, expected_project_id="p_test")
    assert store.get_spatial_profile().get("canonical_origin") == [3, 3]


def test_upsert_frame_expected_mismatch(store):
    with pytest.raises(ProjectMismatch):
        store.upsert_frame({"id": "f1", "kind": "custom"}, expected_project_id="p_other")


def test_upsert_frame_expected_match(store):
    store.upsert_frame({"id": "f-ok", "kind": "custom"}, expected_project_id="p_test")
    assert any(f.get("id") == "f-ok" for f in store.list_frames())


# ── 端点 409（client fixture）──────────────────────────────────
def test_profile_put_endpoint_409(client, store):
    r = client.put("/api/v2/spatial/profile",
                   json={"canonical_origin": [9, 9], "expected_project_id": "p_other"})
    assert r.status_code == 409
    assert r.get_json().get("expected") == "p_other"


def test_frames_post_endpoint_409(client, store):
    r = client.post("/api/v2/spatial/frames",
                    json={"id": "fx", "kind": "custom", "expected_project_id": "p_other"})
    assert r.status_code == 409


def test_frames_post_does_not_leak_expected_into_frame(client, store):
    # 正常 upsert（match）后，帧数据不应残留 expected_project_id 字段
    client.post("/api/v2/spatial/frames",
                json={"id": "fclean", "kind": "custom", "expected_project_id": "p_test"})
    fr = next((f for f in store.list_frames() if f.get("id") == "fclean"), None)
    assert fr is not None
    assert "expected_project_id" not in fr
