"""OntoTwin 4.1 in-memory incremental snapshot feed.

The feed deliberately stays outside ProjectStore persistence.  A process restart,
active-project switch, invalid cursor, or expired history produces a reset response
containing the current full baseline.
"""

from __future__ import annotations

import copy
import threading
import time
import uuid
from collections import deque
from contextlib import nullcontext
from dataclasses import dataclass, field

SCHEMA_VERSION = "snapshot_delta_v1"
_IGNORED_DIFF_FIELDS = {"timestamp", "raw_state"}
_EMPTY_DICT = {}
_EMPTY_LIST = []


@dataclass
class _ChangeBatch:
    revision: int
    upserts: dict
    deleted_ids: set


@dataclass
class _ScopeState:
    stream_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    revision: int = 1
    tokens: dict = field(default_factory=dict)
    snapshots: dict = field(default_factory=dict)
    history: deque = field(default_factory=deque)
    last_access: float = field(default_factory=time.monotonic)

    @property
    def cursor(self):
        return f"{self.stream_id}:{self.revision}"


def _merge_transport_upsert(current, incoming):
    """Merge two interface-level transport patches for a lagging client."""
    if current is None:
        return copy.deepcopy(incoming)
    merged = copy.deepcopy(current)
    for key, value in incoming.items():
        if key == "interfaces":
            target = merged.setdefault("interfaces", {})
            for interface_name, interface_value in (value or {}).items():
                target[interface_name] = copy.deepcopy(interface_value)
        else:
            merged[key] = copy.deepcopy(value)
    return merged


def _build_transport_patch(previous, current):
    """Return (patch, requires_reset) using whole-interface replacement semantics."""
    instance_id = current.get("instanceId")
    patch = {"instanceId": instance_id}

    previous_keys = set(previous) - _IGNORED_DIFF_FIELDS - {"instanceId", "interfaces"}
    current_keys = set(current) - _IGNORED_DIFF_FIELDS - {"instanceId", "interfaces"}
    if previous_keys - current_keys:
        return None, True

    for key in sorted(current_keys):
        if key not in previous or previous.get(key) != current.get(key):
            patch[key] = copy.deepcopy(current.get(key))

    previous_interfaces = previous.get("interfaces") or {}
    current_interfaces = current.get("interfaces") or {}
    if set(previous_interfaces) - set(current_interfaces):
        return None, True

    changed_interfaces = {}
    for name, value in current_interfaces.items():
        if name not in previous_interfaces or previous_interfaces.get(name) != value:
            changed_interfaces[name] = copy.deepcopy(value)
    if changed_interfaces:
        patch["interfaces"] = changed_interfaces

    if len(patch) == 1:
        return None, False
    return patch, False


class SnapshotDeltaService:
    def __init__(self, max_history=128, max_scopes=32):
        self.max_history = max(1, int(max_history))
        self.max_scopes = max(1, int(max_scopes))
        self._lock = threading.RLock()
        # 3.5：scope_id 已含 project_id，隔离天然靠 scope，多 UE 各绑不同项目互不冲流
        # （历史上有单值 _active_project_id 门控，会导致跨项目轮询清空全部流；已移除）
        self._states = {}

    @staticmethod
    def _parse_cursor(cursor):
        if not cursor or not isinstance(cursor, str) or ":" not in cursor:
            return None
        stream_id, revision_text = cursor.rsplit(":", 1)
        try:
            revision = int(revision_text)
        except (TypeError, ValueError):
            return None
        if not stream_id or revision < 0:
            return None
        return stream_id, revision

    def _build_full_baseline(self, tokens, build_snapshot):
        snapshots = {}
        for instance_id in sorted(tokens):
            snapshot = build_snapshot(instance_id)
            if snapshot:
                snapshots[instance_id] = snapshot
        return snapshots

    def _new_state(self, tokens, build_snapshot):
        state = _ScopeState()
        state.tokens = dict(tokens)
        state.snapshots = self._build_full_baseline(tokens, build_snapshot)
        state.history = deque(maxlen=self.max_history)
        return state

    def _rotate_state(self, state):
        state.stream_id = uuid.uuid4().hex[:16]
        state.revision = 1
        state.history.clear()

    def _refresh_state(self, state, tokens, build_snapshot):
        changed_ids = [
            instance_id
            for instance_id, token in tokens.items()
            if state.tokens.get(instance_id) != token
        ]
        removed_ids = set(state.tokens) - set(tokens)
        upserts = {}
        deleted_ids = {
            instance_id for instance_id in removed_ids if instance_id in state.snapshots
        }
        requires_reset = False

        for instance_id in changed_ids:
            previous = state.snapshots.get(instance_id)
            current = build_snapshot(instance_id)
            if not current:
                if previous is not None:
                    deleted_ids.add(instance_id)
                    state.snapshots.pop(instance_id, None)
                continue

            state.snapshots[instance_id] = current
            if previous is None:
                upserts[instance_id] = copy.deepcopy(current)
                continue

            patch, structural_change = _build_transport_patch(previous, current)
            if structural_change:
                requires_reset = True
            elif patch:
                upserts[instance_id] = patch

        for instance_id in removed_ids:
            state.snapshots.pop(instance_id, None)
        state.tokens = dict(tokens)

        if requires_reset:
            self._rotate_state(state)
            return "structural_change"

        if upserts or deleted_ids:
            state.revision += 1
            state.history.append(_ChangeBatch(
                revision=state.revision,
                upserts=upserts,
                deleted_ids=deleted_ids,
            ))
        return None

    def _reset_payload(self, state, reason):
        upserts = [state.snapshots[key] for key in sorted(state.snapshots)]
        return self._payload(state, "reset", upserts, [], reason)

    def _delta_payload(self, state, since_revision):
        combined_upserts = {}
        combined_deleted_ids = set()
        for batch in state.history:
            if batch.revision <= since_revision:
                continue
            for instance_id in batch.deleted_ids:
                combined_upserts.pop(instance_id, None)
                combined_deleted_ids.add(instance_id)
            for instance_id, upsert in batch.upserts.items():
                combined_deleted_ids.discard(instance_id)
                combined_upserts[instance_id] = _merge_transport_upsert(
                    combined_upserts.get(instance_id), upsert
                )

        upserts = [combined_upserts[key] for key in sorted(combined_upserts)]
        deleted_ids = sorted(combined_deleted_ids)
        return self._payload(state, "delta", upserts, deleted_ids, None)

    @staticmethod
    def _payload(state, mode, upserts, deleted_ids, reset_reason):
        return {
            "schemaVersion": SCHEMA_VERSION,
            "mode": mode,
            "streamId": state.stream_id,
            "revision": state.revision,
            "cursor": state.cursor,
            "upserts": upserts,
            "deletedIds": deleted_ids,
            "resetReason": reset_reason,
            "serverTime": time.time(),
            "stats": {
                "instanceCount": len(state.snapshots),
                "upsertCount": len(upserts),
                "deletedCount": len(deleted_ids),
            },
        }

    def _evict_old_scopes(self, keep_scope):
        while len(self._states) > self.max_scopes:
            candidates = [
                (state.last_access, scope_id)
                for scope_id, state in self._states.items()
                if scope_id != keep_scope
            ]
            if not candidates:
                return
            _, oldest_scope = min(candidates)
            self._states.pop(oldest_scope, None)

    def poll(self, project_id, scope_id, cursor, tokens, build_snapshot):
        with self._lock:
            state = self._states.get(scope_id)
            if state is None:
                state = self._new_state(tokens, build_snapshot)
                self._states[scope_id] = state
                self._evict_old_scopes(scope_id)
                reason = "missing_cursor" if not cursor else "stream_mismatch"
                return self._reset_payload(state, reason)

            state.last_access = time.monotonic()
            refresh_reset_reason = self._refresh_state(state, tokens, build_snapshot)
            if refresh_reset_reason:
                return self._reset_payload(state, refresh_reset_reason)

            parsed = self._parse_cursor(cursor)
            if parsed is None:
                reason = "missing_cursor" if not cursor else "invalid_cursor"
                return self._reset_payload(state, reason)

            stream_id, since_revision = parsed
            if stream_id != state.stream_id:
                return self._reset_payload(state, "stream_mismatch")
            if since_revision > state.revision:
                return self._reset_payload(state, "revision_ahead")

            earliest_supported = (
                state.history[0].revision - 1 if state.history else state.revision
            )
            if since_revision < earliest_supported:
                return self._reset_payload(state, "history_expired")
            return self._delta_payload(state, since_revision)


def _tokens_from_instances(instances, zone, object_types, project_id):
    """从一份 instances 字典生成 tokens。抽出以复用（激活/非激活两条路径）。"""
    now = time.time()
    tokens = {}
    for instance_id, instance in instances.items():
        if zone is not None and instance.get("zone_id") != zone:
            continue
        raw_state = instance.get("raw_state")
        if not isinstance(raw_state, dict):
            raw_state = _EMPTY_DICT
        render_config = instance.get("render_config")
        if not isinstance(render_config, dict):
            render_config = _EMPTY_DICT
        render_parts = render_config.get("render_parts")
        if not isinstance(render_parts, list):
            render_parts = _EMPTY_LIST
        model_override = render_config.get("model_override")
        if not isinstance(model_override, dict):
            model_override = _EMPTY_DICT
        interface_overrides = render_config.get("interface_overrides")
        if not isinstance(interface_overrides, dict):
            interface_overrides = _EMPTY_DICT
        override = interface_overrides.get("I3D_Overlay")
        if not isinstance(override, dict):
            override = _EMPTY_DICT
        object_type_rid = instance.get("object_type_rid", "")
        object_type = object_types.get(object_type_rid)
        if not isinstance(object_type, dict):
            object_type = _EMPTY_DICT
        interface_configs = object_type.get("interface_configs")
        if not isinstance(interface_configs, dict):
            interface_configs = _EMPTY_DICT
        type_overlay = interface_configs.get("I3D_Overlay")
        if not isinstance(type_overlay, dict):
            type_overlay = _EMPTY_DICT
        last_seen = float(instance.get("last_seen") or 0.0)
        tokens[instance_id] = (
            id(instance),
            id(raw_state),
            # Exact heartbeat timestamps are intentionally excluded. They used
            # to rebuild every snapshot on every simulator tick. The online
            # transition remains part of the token, while real raw-state
            # updates replace the mapping and change id(raw_state).
            (now - last_seen) < 3.0,
            object_type_rid,
            instance.get("display_name"),
            tuple(instance.get("hierarchy_path") or []),
            instance.get("source_folder_path"),
            instance.get("source_asset_path"),
            instance.get("classification_status"),
            instance.get("classification_key"),
            instance.get("zone_id"),
            id(render_config),
            render_config.get("asset_id"),
            render_config.get("ue_asset_path"),
            render_config.get("assembly_signature"),
            id(render_parts),
            len(render_parts),
            model_override.get("revision"),
            model_override.get("asset_id"),
            model_override.get("ue_asset_path"),
            override.get("revision"),
            id(object_type),
            object_type.get("asset_id"),
            object_type.get("ue_asset_path"),
            tuple(object_type.get("injected_interfaces") or []),
            type_overlay.get("revision"),
        )
    return project_id, tokens


def _collect_instance_tokens(project_store, zone, object_types, project=None, project_id=None):
    """3.5：project/project_id 显式传入时不走 _current（供 UE 按 UE-ID 路由到非激活项目用）。"""
    if project is not None:
        instances = (project or {}).get("instances") or {}
        return _tokens_from_instances(instances, zone, object_types, project_id or "")
    lock = getattr(project_store, "_lock", None)
    context = lock if lock is not None else nullcontext()
    with context:
        project = getattr(project_store, "_current", None)
        project_id = getattr(project_store, "_active_id", None) or ""
        instances = (project or {}).get("instances") or {}
        return _tokens_from_instances(instances, zone, object_types, project_id)


def register_snapshot_delta_routes(
    app,
    project_store,
    build_snapshot,
    request_guard,
    object_types_provider,
    service=None,
    build_snapshot_for_project=None,
    ue_resolver=None,
):
    """
    3.5：新增两个可选钩子以支持"UE 按 UE-ID 路由到它绑的项目"：
      - ue_resolver(project_store, request) -> (pid, ok, info)
      - build_snapshot_for_project(project_dict) -> callable(iid) -> snapshot_dict
    未传时保持旧行为（仅按激活项目提供 delta）。
    """
    from flask import Blueprint, jsonify, request

    blueprint = Blueprint("snapshot_delta_api", __name__)
    delta_service = service or SnapshotDeltaService()

    @blueprint.get("/api/v2/state/snapshot_changes")
    def snapshot_changes():
        # 优先走 UE 路由：解析请求→pid（web=None）
        pid = None
        if ue_resolver is not None:
            pid, ok, info = ue_resolver(project_store, request)
            if not ok:
                return jsonify(info), 403
        else:
            ok, info = request_guard(project_store, request)
            if not ok:
                return jsonify(info), 403

        zone = request.args.get("zone") or request.args.get("scene") or None
        cursor = request.args.get("cursor")

        if pid is None:
            # Web 请求 → 走激活项目（旧路径）
            object_types = object_types_provider() or {}
            project_id, tokens = _collect_instance_tokens(project_store, zone, object_types)
            build_snap = build_snapshot
        else:
            # UE 请求 → 按其绑的项目做 delta（scope_id 天然带 pid，切激活不影响）
            project = project_store.read_project(pid)
            if project is None:
                return jsonify({"error": "project_gone", "project_id": pid}), 410
            object_types = project.get("object_types") or {}
            project_id, tokens = _collect_instance_tokens(
                project_store, zone, object_types,
                project=project, project_id=pid,
            )
            if build_snapshot_for_project is not None:
                build_snap = build_snapshot_for_project(project)
            else:
                build_snap = build_snapshot   # 兜底：仍会用激活数据，效果不对但不崩

        scope_id = f"{project_id}\x1f{zone or ''}"
        payload = delta_service.poll(
            project_id=project_id,
            scope_id=scope_id,
            cursor=cursor,
            tokens=tokens,
            build_snapshot=build_snap,
        )
        return jsonify(payload)

    app.register_blueprint(blueprint)
    return delta_service
