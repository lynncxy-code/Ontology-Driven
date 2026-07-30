"""硬化测试：F3 calibrate 别名污染 + F2 assign_zone 锁内 expected 护栏。

- F3：被 expected 护栏拒绝（409）的 calibrate 不得污染已存在的内存帧。
      get_frame 返回活引用，故 handler 必须深拷贝后再改。
- F2：assign_zone 增加锁内 expected_project_id 校验，激活项目不符抛 ProjectMismatch；
      zones/assignments 端点在项目切换时返回 409。
"""

import copy

import pytest
from flask import Flask

from project_store import ProjectMismatch
from zone_management import register_zone_management_routes


# ── F3: calibrate 别名 ──────────────────────────────────────────
def test_calibrate_409_does_not_mutate_existing_frame(client, store):
    # 先建一个帧，记下它的 from_canonical（None）
    store.upsert_frame({"id": "fcal", "kind": "custom", "unit": "mm"},
                       expected_project_id="p_test")
    before = copy.deepcopy(next(f for f in store.list_frames() if f["id"] == "fcal"))
    r = client.post("/api/v2/spatial/frames/fcal/calibrate", json={
        "anchors": [{"src": [0, 0], "dst": [1, 1]}, {"src": [1, 0], "dst": [2, 1]}],
        "name": "改名", "expected_project_id": "p_other"})
    assert r.status_code == 409
    after = next(f for f in store.list_frames() if f["id"] == "fcal")
    assert after == before, f"被拒的 calibrate 污染了内存帧: {after}"


# ── F2: zones 锁内护栏 ──────────────────────────────────────────
def test_assign_zone_expected_mismatch_raises(store):
    with pytest.raises(ProjectMismatch):
        store.assign_zone(["i1"], "A区", expected_project_id="p_other")


def test_assign_zone_expected_match_ok(store):
    # p_test 下应正常（可能 missing，但不抛 ProjectMismatch）
    store.assign_zone([], "A区", expected_project_id="p_test")


def test_zones_assignments_endpoint_409(store):
    # zone 蓝图的 service 在注册时绑定 store（闭包），故针对隔离 store 另建一个
    # Flask app 注册路由，确保端点走激活的 p_test 项目（与既有 zone 测试同一手法）。
    app = Flask(__name__)
    register_zone_management_routes(app, store)
    endpoint_client = app.test_client()
    r = endpoint_client.put("/api/v2/zones/assignments",
                            json={"instance_ids": ["i1"], "zone_id": "A区",
                                  "expected_project_id": "p_other"})
    assert r.status_code == 409
