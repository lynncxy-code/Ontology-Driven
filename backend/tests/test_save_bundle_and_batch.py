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
