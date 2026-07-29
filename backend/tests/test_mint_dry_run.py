"""Task 4：mint 抽纯 _plan_mint + mint_instances(dry_run, expected_project_id)。

覆盖：dry_run 只出规划不落库 / 真写落库 / will_update 排除 last_seen /
expected 不符抛 ProjectMismatch。fixture `store` 已激活 p_test，含
PE16A 类型 + 2 个已绑定构件（DW-001 / DW-002）。
"""

import pytest
from project_store import ProjectMismatch


def test_dry_run_no_write_but_plans(store):
    before = dict(store._instances)
    res = store.mint_instances(dry_run=True)
    assert set(res["to_create"]) == {"DW-001", "DW-002"}
    assert store._instances == before            # 未写
    assert res["minted"] == 0                     # dry_run 不计已铸


def test_real_mint_writes(store):
    res = store.mint_instances(dry_run=False)
    assert set(store._instances.keys()) == {"DW-001", "DW-002"}
    assert res["minted"] == 2


def test_will_update_excludes_last_seen(store):
    store.mint_instances(dry_run=False)          # 先铸一次
    res = store.mint_instances(dry_run=True)     # 无业务变化
    assert res["to_update"] == []                # last_seen 刷新不算 update


def test_mint_expected_mismatch(store):
    store.create_project("厂B", project_id="p_b")
    with pytest.raises(ProjectMismatch):
        store.mint_instances(dry_run=False, expected_project_id="p_test")
