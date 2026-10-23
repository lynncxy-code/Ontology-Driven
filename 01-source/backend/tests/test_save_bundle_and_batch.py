"""Task 7：bind/unbind/update_raw_state 锁内 expected 校验 + bind_batch 单锁批事务。"""
import io

import pytest
from project_store import ProjectMismatch


def test_bind_expected_mismatch(store):
    # 激活项目是 p_test；传入不符的 expected 应在锁内直接抛 ProjectMismatch。
    store.create_project("厂B", project_id="p_b")  # 现在激活变为 p_b
    with pytest.raises(ProjectMismatch):
        store.bind("c1", "DW-009", expected_project_id="p_test")


def test_bind_batch_partial_success_single_save(store):
    # 一条有效（c1 重绑到未占用的 DW-100），一条构件不存在（nope）。
    pairs = [{"component_id": "c1", "instance_id": "DW-100"},
             {"component_id": "nope", "instance_id": "DW-101"}]
    res = store.bind_batch(pairs)
    assert res["bound"] == 1
    assert len(res["failed"]) == 1 and res["failed"][0]["component_id"] == "nope"
    # 成功项确实写入并落盘。
    assert store.get_components()["c1"]["bound_instance_id"] == "DW-100"


def test_bind_batch_expected_mismatch_whole_batch(store):
    store.create_project("厂B", project_id="p_b")
    with pytest.raises(ProjectMismatch):
        store.bind_batch([{"component_id": "c1", "instance_id": "DW-1"}],
                         expected_project_id="p_test")


# ── Task 8：save_component_bundle 组合事务（一次持锁、一次保存） ──

def test_save_bundle_single_transaction(store):
    res = store.save_component_bundle(
        expected_project_id="p_test",
        profile_patch={"unit": "mm"},
        frame_patch=None,
        component_plan={"mode": "publish",
                        "components": {"c3": {"id": "c3", "object_type_rid": "PE16A"}}},
        mode="publish",
    )
    assert res["ok"] is True
    comps = store.get_components()
    # publish = 整体替换：只剩 c3，旧的 c1/c2 被清空。
    assert "c3" in comps
    assert "c1" not in comps and "c2" not in comps
    # profile 已按 set_spatial_profile 语义整体替换。
    assert store.get_spatial_profile() == {"unit": "mm"}


def test_save_bundle_frame_upsert(store):
    # frame_patch 命中 id 整条替换、否则追加（与 upsert_frame 语义一致）。
    store.save_component_bundle(
        expected_project_id="p_test",
        profile_patch=None,
        frame_patch={"id": "frame_cad", "name": "CAD 图纸", "unit": "mm"},
        component_plan={"mode": "publish", "components": {}},
        mode="publish",
    )
    assert store.get_frame("frame_cad") == {"id": "frame_cad", "name": "CAD 图纸", "unit": "mm"}


def test_save_bundle_expected_mismatch(store):
    store.create_project("厂B", project_id="p_b")
    with pytest.raises(ProjectMismatch):
        store.save_component_bundle(
            expected_project_id="p_test", profile_patch={"unit": "mm"},
            frame_patch=None, component_plan={"mode": "publish", "components": {}},
            mode="publish")


# ── Task 9：roster/upload multipart form field expected 校验 ──

def test_roster_upload_expected_mismatch_409(client):
    # 新建并激活「厂C-roster」→ 激活项目已切走；带 expected=p_test（旧项目）应 409。
    # 名称须与其它测试互不相同：create_empty_dataset 的 _datasets 是进程级模块全局，
    # 跨测试累积；同名会触发 name_duplicated 409 而不激活，污染依赖激活切换的用例。
    client.post("/api/v2/ontology/datasets", json={"name": "厂C-roster", "activate": True})
    data = {"file": (io.BytesIO("实例编号\nDW-001\n".encode("utf-8-sig")), "roster.csv"),
            "expected_project_id": "p_test"}
    r = client.post("/api/v2/binding/roster/upload", data=data,
                    content_type="multipart/form-data")
    assert r.status_code == 409
    body = r.get_json()
    assert body["error"] == "project changed"
    assert body["expected"] == "p_test"


def test_roster_upload_no_expected_still_works(client):
    # 不带 expected → 旧行为不变，正常落库。
    data = {"file": (io.BytesIO("实例编号\nDW-777\n".encode("utf-8-sig")), "roster.csv")}
    r = client.post("/api/v2/binding/roster/upload", data=data,
                    content_type="multipart/form-data")
    assert r.status_code == 200
    assert r.get_json()["added"] == 1


# ── 终审 fix wave（必修 1）：add_roster_entries expected 校验下沉到锁内 ──

def test_roster_add_entries_expected_mismatch_store_level(store):
    """store 级：激活切到 p_b 后，带旧 expected 的 add_roster_entries 在锁内、
    写之前抛 ProjectMismatch（消除 handler 级 check-then-act 的 TOCTOU）。"""
    store.create_project("厂B-roster-store", project_id="p_b")   # create_project 自动激活 p_b
    assert store.get_active_id() == "p_b"
    before_pb = list(store.get_roster())
    with pytest.raises(ProjectMismatch) as e:
        store.add_roster_entries([{"instance_id": "DW-900"}], expected_project_id="p_test")
    assert e.value.expected == "p_test" and e.value.actual == "p_b"
    # 校验失败后当前激活项目 p_b 的清单未被写入（锁内挡在写之前）
    assert store.get_roster() == before_pb
    assert not any(r.get("instance_id") == "DW-900"
                   for r in store._read_project("p_test")["instance_roster"])


def test_roster_add_entries_none_expected_still_works(store):
    """缺省 expected=None → 跳过校验，旧行为不变。"""
    store.add_roster_entries([{"instance_id": "DW-901"}])
    assert any(r.get("instance_id") == "DW-901" for r in store.get_roster())


# ── 终审 fix wave（必修 2）：save_components 校验失败零副作用 ──

def test_save_components_mismatch_leaves_live_profile_intact(client, store):
    """save_components 事务校验失败（expected 不符 → 409）后，当前激活项目的
    live spatial_profile 未被就地改写——证明 handler 先 deepcopy 再改，回滚零副作用。"""
    # 切走激活项目：现在激活是新建的 p_?，其 spatial_profile 尚未标定（matrix=None）。
    client.post("/api/v2/ontology/datasets", json={"name": "厂D-savecomp", "activate": True})
    before_matrix = store.get_spatial_profile().get("ue_transform", {}).get("matrix")
    assert before_matrix is None                    # 默认未标定

    r = client.post("/api/v2/coord/save_components", json={
        "mode": "dxf",
        "transform_matrix": [[2, 0, 5], [0, 2, 7], [0, 0, 1]],
        "items": [{"block_name": "PE16A", "cad_xy": [1.0, 2.0]}],
        "expected_project_id": "p_test",            # 与当前激活不符 → 409
    })
    assert r.status_code == 409
    assert r.get_json()["error"] == "project changed"
    # 关键断言：live spatial_profile 的 ue_transform.matrix 仍为 None，未被原地改写。
    assert store.get_spatial_profile().get("ue_transform", {}).get("matrix") is None
