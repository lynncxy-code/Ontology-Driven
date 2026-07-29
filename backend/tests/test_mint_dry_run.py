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


# ── Task 6：binding_mint handler 级用例（严格 JSON 边界 + 409 映射）──────────

def test_mint_handler_empty_body_still_real_mints(client):
    r = client.post("/api/v2/binding/mint")          # 无 body，旧行为
    assert r.status_code == 200 and r.get_json()["minted"] == 2


def test_mint_handler_dry_run_no_write(client):
    r = client.post("/api/v2/binding/mint", json={"dry_run": True})
    assert r.status_code == 200
    body = r.get_json()
    assert body["minted"] == 0 and set(body["to_create"]) == {"DW-001", "DW-002"}


def test_mint_handler_malformed_json_400(client):
    r = client.post("/api/v2/binding/mint", data="{bad", content_type="application/json")
    assert r.status_code == 400


def test_mint_handler_string_true_rejected(client):
    r = client.post("/api/v2/binding/mint", json={"dry_run": "true"})
    assert r.status_code == 400


def test_mint_handler_expected_mismatch_409(client):
    # 切走激活项目后带旧 expected
    client.post("/api/v2/ontology/datasets", json={"name": "厂B", "activate": True})
    r = client.post("/api/v2/binding/mint", json={"expected_project_id": "p_test"})
    assert r.status_code == 409
