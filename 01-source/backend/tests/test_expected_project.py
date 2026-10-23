import threading

import pytest
from project_store import ProjectMismatch


def test_expected_match_runs_and_persists(store):
    out = store.transact_expected_active("p_test", lambda w: w["object_types"].__setitem__("X", {"rid": "X"}) or "ok")
    assert out == "ok"
    assert "X" in store.get_object_types()


def test_expected_mismatch_raises_and_no_write(store):
    before = dict(store.get_object_types())
    with pytest.raises(ProjectMismatch) as e:
        store.transact_expected_active("p_other", lambda w: w["object_types"].__setitem__("Y", {"rid": "Y"}))
    assert e.value.expected == "p_other" and e.value.actual == "p_test"
    assert store.get_object_types() == before   # 未写


def test_expected_none_skips_check(store):
    store.transact_expected_active(None, lambda w: w["object_types"].__setitem__("Z", {"rid": "Z"}))
    assert "Z" in store.get_object_types()


# ── 并发用例：证明 expected 校验的锁语义真的挡住「中途切项目」 ──────────


def test_activate_first_then_write_rejected(store):
    """并发用例 A：activate 先切走激活项目 → 后到的带 expected 的写被拒。

    create_project 已核实会自动把激活态切到新项目（project_store.py:382-385），
    故无需显式 activate。先断言切换确已生效，再验证过期写被 ProjectMismatch 拒、
    且当前激活项目 p_b 与原项目 p_test 都未被写入。
    """
    store.create_project("厂B", project_id="p_b")   # create_project 自动激活 p_b
    assert store.get_active_id() == "p_b"            # 激活确已切走

    before_pb = dict(store.get_object_types())       # p_b 初始类型表（空）
    with pytest.raises(ProjectMismatch) as e:
        store.transact_expected_active(
            "p_test", lambda w: w["object_types"].__setitem__("K", {"rid": "K"})
        )
    assert e.value.expected == "p_test" and e.value.actual == "p_b"
    # 过期写被拒后，当前激活项目 p_b 未被写入，原项目 p_test 也未被误写
    assert store.get_object_types() == before_pb
    assert "K" not in store._read_project("p_test")["object_types"]


def test_write_holds_lock_activate_waits_lands_in_A(store):
    """并发用例 B（核心）：写线程持锁并通过 expected 校验后卡在栅栏，
    另一线程尝试切项目会阻塞在同一把锁上；放行后写完整落在 p_test，绝不到 p_b。

    正确性来自 transact_expected_active 全程持 self._lock（RLock）：
    expected 校验在 updater 之前、active 仍是 p_test 时通过；切项目的
    create_project 也要抢同一把锁，只能等写事务整体结束后才发生。因此不存在
    任何交错能让写落到 p_b —— 关键断言是确定性的，不依赖线程调度时序。
    """
    entered = threading.Event()
    release = threading.Event()
    write_outcome = {}

    def slow_update(w):
        entered.set()
        release.wait(2)
        w["object_types"]["SLOW"] = {"rid": "SLOW"}
        return "done"

    def run_write():
        try:
            write_outcome["result"] = store.transact_expected_active("p_test", slow_update)
        except Exception as exc:          # 线程内异常不静默，便于诊断
            write_outcome["error"] = exc

    t = threading.Thread(target=run_write, daemon=True)
    t.start()
    assert entered.wait(2)                # 写线程已进锁并停在栅栏

    switched = {}

    def do_switch():
        store.create_project("厂B", project_id="p_b")   # 抢同一把锁 → 阻塞至写事务结束
        switched["active"] = store.get_active_id()

    t2 = threading.Thread(target=do_switch, daemon=True)
    t2.start()
    release.set()                         # 放行写线程 → 写事务完成并释放锁 → 切换才可能发生
    t.join(3)
    t2.join(3)

    assert not t.is_alive() and not t2.is_alive()   # 未挂死
    assert write_outcome.get("error") is None       # 写线程未抛异常
    assert write_outcome.get("result") == "done"    # 写事务成功返回

    # 核心断言：写完整落在 p_test（重新激活后经公共读路径校验）
    assert store.activate("p_test")
    assert "SLOW" in store.get_object_types()
    # 关键断言：写绝不落到 p_b
    assert "SLOW" not in store._read_project("p_b")["object_types"]
    # activate 最终生效，但发生在写之后
    assert switched.get("active") == "p_b"
