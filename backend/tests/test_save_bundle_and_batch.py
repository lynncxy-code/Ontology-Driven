"""Task 7：bind/unbind/update_raw_state 锁内 expected 校验 + bind_batch 单锁批事务。"""
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
