"""OPT-07: shared in-memory project reads for high-frequency UE polling.

Why this exists
---------------
Every explicit-project ``/api/v2`` request used to rebuild the whole project from
PostgreSQL in ``before_request`` (``project_view`` -> ``for_request``).  UE scenes
poll several endpoints every 0.5-2 s, so a large project (ZHHZ: 674 instances,
~19k render parts, ~0.18 s per load) was reloaded several times per second per
scene, and some handlers deep-copied it again.

What it does
------------
* Only the read-only polling routes in ``HOT_ROUTES`` get a *shared* project
  object from this cache.  Every other request keeps the old per-request load.
* Each cached object carries a ``generation``.  A new generation is assigned
  whenever the project is (re)loaded, which happens after any write (see below)
  or at the latest every ``ttl`` seconds (default 30 s) so that changes made
  directly in the database by maintenance scripts are still picked up.
* The cache is dropped after every ProjectStore write method (``WRITE_METHODS``)
  and after every non-read HTTP request except the known non-mutating UE
  heartbeats in ``NON_MUTATING_REQUESTS``.
* Positive UE scene binding checks are cached the same way.

Nothing is persisted: no table, column or file format changes.  Setting
``ONTOTWIN_PROJECT_READ_CACHE=off`` restores the previous behaviour exactly.

Shared objects must never be modified.  The view handed to hot routes refuses
ProjectStore writes; ``tests/test_project_read_cache.py`` checks that the hot
handlers leave the shared project unchanged.
"""

from __future__ import annotations

import functools
import os
import threading
import time
from dataclasses import dataclass

from scoped_project_store import ScopedProjectStore, project_view

# (method, path) pairs served from the shared cache.  They must only read the
# project.  Adding a route here requires a no-mutation test for its handler.
HOT_ROUTES = frozenset({
    ("GET", "/api/v2/state/snapshot_changes"),
    ("GET", "/api/v2/state/snapshots"),
    ("GET", "/api/v2/scene-interactions/runtime"),
    ("POST", "/api/v2/scene-interactions/runtime"),   # UE heartbeat, memory only
    ("GET", "/api/v2/web-interactions/runtime"),
    ("GET", "/api/v2/ue/assets/scan-requests/pending"),
})

# Non-read requests that are known not to change project data.  All other
# POST/PUT/PATCH/DELETE requests drop the cache when they finish.
NON_MUTATING_REQUESTS = frozenset({
    ("POST", "/api/v2/scene-interactions/runtime"),   # heartbeat (in-memory status)
    ("POST", "/api/v2/ue/assets/folders"),            # UE asset folder index file
})

_READ_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})

# ProjectStore methods that persist project data.  After any of them returns
# (or raises) the cache is dropped.  ``tests/test_project_read_cache.py`` fails
# when a ProjectStorePG method writes SQL but is missing from this list.
WRITE_METHODS = (
    "_save_current",
    "_soft_delete_absent_instances",
    "transact_project",
    "transact_active",
    "transact_expected_active",
    "write_project",
    "edit_runtime_objects",
    "remove",
    "clear_instances",
    "mint_instances",
    "restore_trash",
    "restore_project",
    "restore_scene",
    "restore_instance",
    "delete_trash",
    "purge_trash",
    "create_project",
    "delete_project",
    "save_component_bundle",
)

_OFF_VALUES = {"0", "off", "false", "no", "disabled"}
_ON_VALUES = {"1", "on", "true", "yes", "enabled"}

_LISTENERS = []
_LISTENERS_LOCK = threading.Lock()


def _notify_write():
    with _LISTENERS_LOCK:
        listeners = list(_LISTENERS)
    for listener in listeners:
        listener()


def _wrap_write_method(method):
    if getattr(method, "_ontotwin_invalidates_read_cache", False):
        return method

    @functools.wraps(method)
    def wrapper(*args, **kwargs):
        try:
            return method(*args, **kwargs)
        finally:
            _notify_write()

    wrapper._ontotwin_invalidates_read_cache = True
    return wrapper


def install_write_hooks(*classes):
    """Wrap every ProjectStore write method defined on *classes* (idempotent)."""
    for cls in classes:
        for name in WRITE_METHODS:
            method = cls.__dict__.get(name)
            if callable(method):
                setattr(cls, name, _wrap_write_method(method))


class SharedProjectViewWriteError(RuntimeError):
    """A hot read-only route tried to write through the shared project view."""


@dataclass
class _Entry:
    project: dict
    generation: int
    loaded_at: float
    last_used: float


class ProjectReadCache:
    """Thread-safe pid -> shared project cache with write invalidation."""

    def __init__(self, ttl=30.0, max_entries=8, clock=time.monotonic, idle_seconds=120.0):
        self.ttl = max(0.0, float(ttl))
        self.max_entries = max(1, int(max_entries))
        # A project nobody has polled for this long is dropped to free memory.
        self.idle_seconds = max(self.ttl, float(idle_seconds))
        self._clock = clock
        self._lock = threading.Lock()
        self._entries = {}
        self._load_locks = {}
        self._epoch = 0
        self._generation = 0
        self.hits = 0
        self.loads = 0
        self.invalidations = 0

    def get(self, project_id, loader):
        """Return ``(project, generation)``; ``(None, None)`` if missing."""
        pid = str(project_id)
        hit = self._fresh(pid)
        if hit is not None:
            return hit
        with self._lock:
            load_lock = self._load_locks.setdefault(pid, threading.Lock())
        with load_lock:
            hit = self._fresh(pid)
            if hit is not None:
                return hit
            with self._lock:
                epoch = self._epoch
            project = loader(pid)
            with self._lock:
                self.loads += 1
                if project is None:
                    self._entries.pop(pid, None)
                    return None, None
                self._generation += 1
                generation = self._generation
                # A write that committed while we were loading may not be in
                # ``project``; serve it to this request but do not keep it.
                now = self._clock()
                if self._epoch == epoch:
                    self._entries[pid] = _Entry(project, generation, now, now)
                self._evict_locked(now)
            return project, generation

    def _fresh(self, pid):
        with self._lock:
            entry = self._entries.get(pid)
            if entry is None:
                return None
            now = self._clock()
            if now - entry.loaded_at >= self.ttl:
                return None
            entry.last_used = now
            self.hits += 1
            return entry.project, entry.generation

    def _evict_locked(self, now):
        for key in [k for k, e in self._entries.items() if now - e.last_used > self.idle_seconds]:
            self._entries.pop(key, None)
        while len(self._entries) > self.max_entries:
            oldest = min(self._entries, key=lambda key: self._entries[key].last_used)
            self._entries.pop(oldest, None)

    def invalidate_all(self):
        with self._lock:
            self._epoch += 1
            self._entries.clear()
            self.invalidations += 1

    def cached_ids(self):
        with self._lock:
            return sorted(self._entries)


class UEBindingCheckCache:
    """Remember successful UE scene/project binding checks for a short time."""

    def __init__(self, ttl=30.0, clock=time.monotonic):
        self.ttl = max(0.0, float(ttl))
        self._clock = clock
        self._lock = threading.Lock()
        self._allowed = {}

    def allowed(self, check, project_id, ue_project_id, scene_id=""):
        key = (str(project_id or ""), str(ue_project_id or ""), str(scene_id or ""))
        now = self._clock()
        with self._lock:
            expires = self._allowed.get(key)
            if expires is not None and expires > now:
                return True
        ok = bool(check(project_id, ue_project_id, scene_id))
        if ok:
            with self._lock:
                self._allowed[key] = now + self.ttl
        return ok

    def invalidate_all(self):
        with self._lock:
            self._allowed.clear()


def shared_project_view(base, project_id, project, generation):
    """A request store whose project is the shared cached object (read only)."""
    pid = str(project_id)
    clone = object.__new__(type(base))
    clone.__dict__.update(base.__dict__)
    clone._lock = threading.RLock()
    clone._active_id = pid
    clone._current = project
    clone._dirty = False
    clone._request_scoped = True
    clone._shared_read_only = True
    clone._cache_generation = generation

    base_read = base.read_project
    base_active_copy = type(base).get_active_copy

    def read_project(requested_id):
        return project if str(requested_id) == pid else base_read(requested_id)

    def get_active_copy(with_render_parts=False):
        if with_render_parts:
            return project
        return base_active_copy(clone, with_render_parts=False)

    def refuse(*_args, **_kwargs):
        raise SharedProjectViewWriteError(
            "OPT-07 shared project view is read-only; add a no-mutation test "
            "or remove the route from project_read_cache.HOT_ROUTES"
        )

    clone.read_project = read_project
    clone.get_active_copy = get_active_copy
    for name in WRITE_METHODS:
        setattr(clone, name, refuse)
    return clone


def _base_store(project_store):
    return project_store.base if isinstance(project_store, ScopedProjectStore) else project_store


def cache_enabled_for(base, env=None):
    env = os.environ if env is None else env
    value = str(env.get("ONTOTWIN_PROJECT_READ_CACHE", "") or "").strip().lower()
    if value in _OFF_VALUES:
        return False
    if value in _ON_VALUES:
        return True
    # Default: on for the PostgreSQL runtime, where each load is a full rebuild.
    return callable(getattr(base, "for_request", None))


def _env_float(name, default):
    try:
        return float(os.environ.get(name, default))
    except (TypeError, ValueError):
        return float(default)


class ProjectReadCacheService:
    def __init__(self, project_store, enabled=None, ttl=None,
                 max_entries=8, clock=time.monotonic, log=print):
        base = _base_store(project_store)
        self.enabled = cache_enabled_for(base) if enabled is None else bool(enabled)
        ttl = _env_float("ONTOTWIN_PROJECT_READ_CACHE_TTL", 30.0) if ttl is None else ttl
        self.cache = ProjectReadCache(ttl=ttl, max_entries=max_entries, clock=clock)
        self.bindings = UEBindingCheckCache(ttl=ttl, clock=clock)
        self._clock = clock
        self._log = log
        self._stats_lock = threading.Lock()
        self._reset_stats(clock())

    # ── request integration ─────────────────────────────────────
    def is_hot(self, method, path):
        return self.enabled and (str(method).upper(), path) in HOT_ROUTES

    def request_view(self, project_store, project_id, method, path):
        """Store view for ``g.ontotwin_project_store``; raises KeyError if missing."""
        if not self.is_hot(method, path):
            return project_view(project_store, project_id)
        base = _base_store(project_store)
        project, generation = self.cache.get(project_id, base._read_project)
        if project is None:
            raise KeyError(str(project_id))
        return shared_project_view(base, project_id, project, generation)

    def ue_allowed(self, check, project_id, ue_project_id, scene_id=""):
        if not self.enabled:
            return check(project_id, ue_project_id, scene_id)
        return self.bindings.allowed(check, project_id, ue_project_id, scene_id)

    def invalidate_all(self):
        self.cache.invalidate_all()
        self.bindings.invalidate_all()

    def after_request_finished(self, method, path):
        method = str(method).upper()
        if method in _READ_METHODS or (method, path) in NON_MUTATING_REQUESTS:
            return
        self.invalidate_all()

    # ── measurement (one log line per minute, no new endpoint) ──
    def _reset_stats(self, now):
        self._window_started = now
        self._hot_count = 0
        self._hot_total = 0.0
        self._hot_max = 0.0
        self._hits_at_window = self.cache.hits
        self._loads_at_window = self.cache.loads
        self._invalidations_at_window = self.cache.invalidations

    def record_hot_request(self, seconds):
        now = self._clock()
        line = None
        with self._stats_lock:
            self._hot_count += 1
            self._hot_total += seconds
            self._hot_max = max(self._hot_max, seconds)
            if now - self._window_started >= 60.0:
                window = now - self._window_started
                line = (
                    "[project-read-cache] {enabled} {window:.0f}s: hot_requests={count} "
                    "avg_ms={avg:.1f} max_ms={max:.1f} cache_hits={hits} loads={loads} "
                    "invalidations={inv} cached_projects={cached}"
                ).format(
                    enabled="on" if self.enabled else "off",
                    window=window,
                    count=self._hot_count,
                    avg=1000.0 * self._hot_total / max(1, self._hot_count),
                    max=1000.0 * self._hot_max,
                    hits=self.cache.hits - self._hits_at_window,
                    loads=self.cache.loads - self._loads_at_window,
                    inv=self.cache.invalidations - self._invalidations_at_window,
                    cached=len(self.cache.cached_ids()),
                )
                self._reset_stats(now)
        if line and self._log:
            self._log(line)


def register_project_read_cache(app, project_store, enabled=None):
    """Attach the cache to *app*; returns the service used by ``app.py``."""
    from flask import g, request

    import project_store as project_store_module
    classes = [project_store_module.ProjectStoreJSON]
    try:
        from project_store_pg import ProjectStorePG
        classes.append(ProjectStorePG)
    except Exception:  # pragma: no cover - PG driver missing in a test env
        pass
    install_write_hooks(*classes)

    service = ProjectReadCacheService(project_store, enabled=enabled)
    with _LISTENERS_LOCK:
        _LISTENERS.append(service.invalidate_all)

    # Polling routes for any project are timed even when the cache is off, so
    # the before/after numbers come from the same log line.
    def _is_timed(method, path):
        return (str(method).upper(), path) in HOT_ROUTES

    @app.before_request
    def _project_read_cache_start():
        if _is_timed(request.method, request.path):
            g.ontotwin_read_cache_started = time.perf_counter()

    @app.teardown_request
    def _project_read_cache_finish(_exc):
        started = g.pop("ontotwin_read_cache_started", None)
        if started is not None:
            service.record_hot_request(time.perf_counter() - started)
        service.after_request_finished(request.method, request.path)

    print(f"[project-read-cache] {'on' if service.enabled else 'off'} "
          f"(ttl={service.cache.ttl:.0f}s)")
    return service
