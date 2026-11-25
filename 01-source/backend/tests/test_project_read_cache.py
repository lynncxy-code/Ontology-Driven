"""OPT-07: shared project reads for high-frequency UE polling."""

import ast
import copy
import inspect
import re
import textwrap

import pytest

import project_read_cache as prc


class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


# ── ProjectReadCache ───────────────────────────────────────────────


def test_cache_reuses_one_object_until_invalidated():
    loads = []

    def loader(pid):
        loads.append(pid)
        return {"id": pid, "n": len(loads)}

    cache = prc.ProjectReadCache(ttl=30)
    first, gen1 = cache.get("p1", loader)
    second, gen2 = cache.get("p1", loader)
    assert first is second and gen1 == gen2
    assert loads == ["p1"]

    cache.invalidate_all()
    third, gen3 = cache.get("p1", loader)
    assert third is not first and gen3 != gen1
    assert loads == ["p1", "p1"]


def test_cache_reloads_after_ttl_to_pick_up_direct_database_edits():
    clock = FakeClock()
    cache = prc.ProjectReadCache(ttl=30, clock=clock)
    loader = lambda pid: {"id": pid}
    _, gen1 = cache.get("p1", loader)
    clock.now += 29.9
    assert cache.get("p1", loader)[1] == gen1
    clock.now += 0.2
    assert cache.get("p1", loader)[1] != gen1


def test_write_during_load_is_not_cached():
    cache = prc.ProjectReadCache(ttl=30)

    def loader_with_concurrent_write(pid):
        cache.invalidate_all()          # a write commits while we are loading
        return {"id": pid}

    project, generation = cache.get("p1", loader_with_concurrent_write)
    assert project == {"id": "p1"} and generation is not None
    assert cache.cached_ids() == []


def test_missing_project_returns_none_and_lru_eviction():
    cache = prc.ProjectReadCache(ttl=30, max_entries=2)
    assert cache.get("gone", lambda pid: None) == (None, None)
    for pid in ("a", "b", "c"):
        cache.get(pid, lambda value: {"id": value})
    assert cache.cached_ids() == ["b", "c"]


def test_projects_nobody_polls_are_released():
    clock = FakeClock()
    cache = prc.ProjectReadCache(ttl=30, clock=clock, idle_seconds=120)
    cache.get("old", lambda pid: {"id": pid})
    clock.now += 121
    cache.get("new", lambda pid: {"id": pid})
    assert cache.cached_ids() == ["new"]


# ── binding check cache ────────────────────────────────────────────


def test_binding_cache_keeps_only_successful_checks():
    calls = []

    def check(pid, ue, scene):
        calls.append((pid, ue, scene))
        return pid == "p1"

    cache = prc.UEBindingCheckCache(ttl=30)
    assert cache.allowed(check, "p1", "ue", "/Game/A")
    assert cache.allowed(check, "p1", "ue", "/Game/A")
    assert len(calls) == 1
    assert not cache.allowed(check, "p2", "ue", "/Game/A")
    assert not cache.allowed(check, "p2", "ue", "/Game/A")
    assert len(calls) == 3              # refusals are re-checked every time
    cache.invalidate_all()              # e.g. a scene was unbound
    assert cache.allowed(check, "p1", "ue", "/Game/A")
    assert len(calls) == 4


# ── write hooks ────────────────────────────────────────────────────


def test_write_hooks_notify_even_when_the_write_fails(monkeypatch):
    events = []
    monkeypatch.setattr(prc, "_LISTENERS", [lambda: events.append("x")])

    class Store:
        def _save_current(self):
            return "saved"

        def remove(self, _iid):
            raise ValueError("boom")

        def read_project(self, pid):
            return pid

    prc.install_write_hooks(Store)
    prc.install_write_hooks(Store)      # idempotent
    store = Store()
    assert store._save_current() == "saved"
    with pytest.raises(ValueError):
        store.remove("i1")
    assert store.read_project("p") == "p"
    assert events == ["x", "x"]


def test_write_hooks_keep_static_and_class_methods_working(monkeypatch):
    events = []
    monkeypatch.setattr(prc, "_LISTENERS", [lambda: events.append("x")])

    class Store:
        @staticmethod
        def persist_snapshot(project, connection=None):
            return ("static", project, connection)

        @classmethod
        def delete_project(cls, pid):
            return (cls.__name__, pid)

    prc.install_write_hooks(Store)
    prc.install_write_hooks(Store)
    store = Store()
    assert store.persist_snapshot("p", "c") == ("static", "p", "c")
    assert Store.persist_snapshot("p") == ("static", "p", None)
    assert store.delete_project("p") == ("Store", "p")
    assert events == ["x", "x", "x"]


_SQL_WRITE = re.compile(r"\b(INSERT\s+INTO|UPDATE\s+\w+\s+SET|DELETE\s+FROM)\b", re.I)
# Methods writing only non-project tables (process settings).
_NON_PROJECT_WRITERS = {"_save_active", "set_runtime_setting"}


def test_every_pg_store_method_that_writes_sql_invalidates_the_cache():
    import project_store_pg

    source = textwrap.dedent(inspect.getsource(project_store_pg.ProjectStorePG))
    tree = ast.parse(source)
    writers = set()
    for node in tree.body[0].body:
        if isinstance(node, ast.FunctionDef) and _SQL_WRITE.search(ast.get_source_segment(source, node) or ""):
            writers.add(node.name)
    missing = writers - set(prc.WRITE_METHODS) - _NON_PROJECT_WRITERS
    assert not missing, f"add these ProjectStorePG write methods to WRITE_METHODS: {sorted(missing)}"


# ── shared view ────────────────────────────────────────────────────


def test_shared_view_returns_the_cached_object_and_refuses_writes(store):
    project = store.read_project("p_test")
    view = prc.shared_project_view(store, "p_test", project, 7)
    assert view.read_project("p_test") is project
    assert view.get_active_copy(with_render_parts=True) is project
    assert view._cache_generation == 7
    with pytest.raises(prc.SharedProjectViewWriteError):
        view._save_current()
    with pytest.raises(prc.SharedProjectViewWriteError):
        view.transact_active(lambda working: None)


def test_service_only_shares_hot_routes_and_respects_switch(store):
    service = prc.ProjectReadCacheService(store, enabled=True, log=None)
    hot1 = service.request_view(store, "p_test", "GET", "/api/v2/state/snapshot_changes")
    hot2 = service.request_view(store, "p_test", "GET", "/api/v2/web-interactions/runtime")
    assert hot1._current is hot2._current
    cold = service.request_view(store, "p_test", "GET", "/api/v2/instances")
    assert cold._current is not hot1._current
    with pytest.raises(KeyError):
        service.request_view(store, "missing", "GET", "/api/v2/state/snapshot_changes")

    off = prc.ProjectReadCacheService(store, enabled=False, log=None)
    a = off.request_view(store, "p_test", "GET", "/api/v2/state/snapshot_changes")
    b = off.request_view(store, "p_test", "GET", "/api/v2/state/snapshot_changes")
    assert a._current is not b._current


def test_requests_that_may_write_drop_the_cache_but_heartbeats_do_not(store):
    service = prc.ProjectReadCacheService(store, enabled=True, log=None)
    service.request_view(store, "p_test", "GET", "/api/v2/state/snapshot_changes")
    service.after_request_finished("POST", "/api/v2/scene-interactions/runtime")
    service.after_request_finished("GET", "/api/v2/instances")
    assert service.cache.cached_ids() == ["p_test"]
    service.after_request_finished("POST", "/api/v2/state/writeback")
    assert service.cache.cached_ids() == []


def test_switch_reads_environment():
    class PG:
        def for_request(self, pid):
            return pid

    assert prc.cache_enabled_for(PG(), {}) is True
    assert prc.cache_enabled_for(object(), {}) is False
    assert prc.cache_enabled_for(PG(), {"ONTOTWIN_PROJECT_READ_CACHE": "off"}) is False
    assert prc.cache_enabled_for(object(), {"ONTOTWIN_PROJECT_READ_CACHE": "on"}) is True


def test_one_summary_line_per_minute():
    clock = FakeClock()
    lines = []
    service = prc.ProjectReadCacheService(object(), enabled=True, clock=clock, log=lines.append)
    service.record_hot_request(0.010)
    clock.now += 61
    service.record_hot_request(0.030)
    assert len(lines) == 1
    assert "hot_requests=2" in lines[0] and "avg_ms=20.0" in lines[0] and "max_ms=30.0" in lines[0]


# ── through the real Flask routes ──────────────────────────────────

UE_HEADERS = {
    "X-OntoTwin-UE-Project-Id": "ue-opt07",
    "X-OntoTwin-UE-Project-Name": "OPT07",
    "X-OntoTwin-UE-Context": "pie",
    "X-OntoTwin-Project-Id": "p_test",
}


@pytest.fixture
def cached_client(client, store, monkeypatch):
    import app as app_module

    def enrich(working):
        working["object_types"]["PE16A"]["injected_interfaces"] = [
            "I3D_Representable", "I3D_Spatial", "I3D_Visual", "I3D_Behavioral", "I3D_Overlay",
        ]

    store.transact_active(enrich)
    store.mint_instances()
    service = app_module.project_read_cache
    monkeypatch.setattr(service, "enabled", True)
    service.invalidate_all()
    yield client, service
    service.invalidate_all()


def _poll_all(client, cursor=None):
    url = "/api/v2/state/snapshot_changes" + (f"?cursor={cursor}" if cursor else "")
    changes = client.get(url, headers=UE_HEADERS)
    assert changes.status_code == 200, changes.get_json()
    for method, path in (
        ("get", "/api/v2/state/snapshots"),
        ("get", "/api/v2/scene-interactions/runtime"),
        ("get", "/api/v2/web-interactions/runtime"),
        ("get", "/api/v2/ue/assets/scan-requests/pending"),
    ):
        response = getattr(client, method)(path, headers=UE_HEADERS)
        assert response.status_code < 500, (path, response.get_json())
    heartbeat = client.post("/api/v2/scene-interactions/runtime", headers=UE_HEADERS, json={
        "runtime_state": "idle", "roaming_active": False,
    })
    assert heartbeat.status_code < 500, heartbeat.get_json()
    return changes.get_json()


def test_hot_routes_share_one_project_and_never_modify_it(cached_client, store):
    client, service = cached_client
    first = _poll_all(client)
    assert first["mode"] == "reset" and first["stats"]["instanceCount"] == 2
    assert service.cache.cached_ids() == ["p_test"]

    shared, _ = service.cache.get("p_test", lambda pid: pytest.fail("should be cached"))
    before = copy.deepcopy(shared)
    second = _poll_all(client, first["cursor"])
    third = _poll_all(client, second["cursor"])
    assert shared == before, "a hot route modified the shared cached project"
    assert service.cache.get("p_test", lambda pid: pytest.fail("reloaded"))[0] is shared
    assert second["mode"] == third["mode"] == "delta"
    assert second["upserts"] == third["upserts"] == []


def test_store_write_is_visible_on_the_next_poll(cached_client, store):
    client, service = cached_client
    first = _poll_all(client)

    def rename(working):
        working["instances"]["DW-001"]["display_name"] = "改名后的设备"

    store.transact_active(rename)
    assert service.cache.cached_ids() == []
    delta = client.get(f"/api/v2/state/snapshot_changes?cursor={first['cursor']}", headers=UE_HEADERS).get_json()
    assert delta["mode"] == "delta"
    assert [item["instanceId"] for item in delta["upserts"]] == ["DW-001"]
    assert delta["upserts"][0]["displayName"] == "改名后的设备"


def test_cached_and_uncached_responses_are_identical(cached_client, monkeypatch):
    client, service = cached_client
    cached = client.get("/api/v2/state/snapshots", headers=UE_HEADERS).get_json()
    monkeypatch.setattr(service, "enabled", False)
    uncached = client.get("/api/v2/state/snapshots", headers=UE_HEADERS).get_json()

    def strip(items):
        return sorted(
            ({k: v for k, v in item.items() if k != "timestamp"} for item in items),
            key=lambda item: item["instanceId"],
        )

    assert strip(cached) == strip(uncached)
