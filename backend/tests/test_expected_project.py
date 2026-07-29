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
