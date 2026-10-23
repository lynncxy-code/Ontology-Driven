"""Runtime control and monitoring for the active database's realtime streams.

The first version of this endpoint exposed a single ``websocket`` object.  The
runtime, however, is already capable of reporting more than one provider and a
single frame can contain more than one target category.  This module therefore
builds a small, additive projection:

* ``streams`` is the forward-compatible list used by new clients;
* ``websocket`` remains a legacy projection of the first/current stream; and
* ``summary`` contains totals without changing the project-store format.

The projection deliberately does not infer an applied target from a received
target.  Missing execution counters are represented as unknown in ``streams``
and are kept as the old numeric zero in the compatibility projection.
"""

import copy
import datetime
import math
import threading

from flask import Blueprint, jsonify, request


REALTIME_STATUS_SCHEMA_VERSION = "external_realtime_v2"
DEFAULT_FRAME_FRESHNESS_THRESHOLD_MS = 5_000

_EXECUTION_STATES = {
    "not_registered",
    "waiting",
    "ready",
    "partial",
    "none_applied",
    "failed",
    # ``unknown`` is useful for old heartbeats which do not report execution
    # counters.  It is not treated as a healthy state by the projection.
    "unknown",
}
_CONTROL_STATES = {"not_configured", "syncing", "in_sync", "stale_database"}
_FRAME_STATES = {"no_frame", "fresh", "stale", "unknown"}


def _non_negative_int(value, default=None):
    """Return a safe non-negative integer, or *default* for unknown input.

    Runtime heartbeat validation normally guarantees integer values.  Keeping
    this guard in the projection is important for old/external readers and for
    tests that feed a partially populated heartbeat directly.
    """

    if value is None or isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value if value >= 0 else default
    if isinstance(value, float) and math.isfinite(value) and value >= 0 and value.is_integer():
        return int(value)
    return default


def _copy_json_value(value, depth=0):
    """Copy diagnostic values while keeping the response JSON serializable.

    UE plugins may add diagnostic fields before the backend schema is updated.
    Unknown fields are retained where possible, but exotic values are reduced
    to strings instead of making the whole status response fail to serialize.
    """

    if depth > 8:
        return "<max-depth>"
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, list):
        return [_copy_json_value(item, depth + 1) for item in value]
    if isinstance(value, dict):
        return {
            str(key): _copy_json_value(item, depth + 1)
            for key, item in value.items()
        }
    return str(value)


def _normalise_reason(reason):
    """Normalise one UE-provided unapplied reason without inventing one."""

    if isinstance(reason, str):
        text = reason.strip()
        return {"code": "unknown", "count": None, "message": text}
    if not isinstance(reason, dict):
        return None
    code = reason.get("code")
    message = reason.get("message")
    result = {
        "code": str(code).strip()[:128] if code is not None else "unknown",
        "count": _non_negative_int(reason.get("count")),
        "message": str(message).strip()[:500] if message is not None else "",
    }
    # Preserve optional provider metadata (handler/category/key, etc.) while
    # keeping the canonical fields above predictable for the frontend.
    for key, value in reason.items():
        if key not in result:
            result[str(key)] = _copy_json_value(value)
    return result


def _normalise_reasons(value):
    if value is None:
        return []
    if isinstance(value, dict):
        # Some providers report ``{"instance_missing": 5}``; retain the code
        # and count but do not turn a category/key into a guessed business type.
        result = []
        for code, count in value.items():
            result.append({
                "code": str(code)[:128],
                "count": _non_negative_int(count),
                "message": "",
            })
        return result
    if not isinstance(value, list):
        return []
    return [item for item in (_normalise_reason(item) for item in value) if item is not None]


def _normalise_category(category):
    if isinstance(category, str):
        category_id = category.strip()[:128]
        if not category_id:
            return None
        return {
            "category_id": category_id,
            "label": category_id,
            "lifecycle": "unknown",
            "handler_id": "",
            "target_count": None,
            "applied_count": None,
            "unapplied_count": None,
            "reasons": [],
        }
    if not isinstance(category, dict):
        return None
    category_id = category.get("category_id")
    if category_id is None:
        category_id = category.get("id")
    if category_id is None:
        category_id = category.get("clazz")
    category_id = str(category_id or "").strip()[:128]
    if not category_id:
        return None
    target_count = _non_negative_int(
        category.get("target_count", category.get("count"))
    )
    applied_count = _non_negative_int(
        category.get("applied_count", category.get("applied_target_count"))
    )
    unapplied_count = _non_negative_int(category.get("unapplied_count"))
    if unapplied_count is None and target_count is not None and applied_count is not None:
        unapplied_count = max(target_count - applied_count, 0)
    result = {
        "category_id": category_id,
        "label": str(category.get("label") or category_id)[:256],
        "lifecycle": str(category.get("lifecycle") or "unknown")[:64],
        "handler_id": str(category.get("handler_id") or "")[:256],
        "target_count": target_count,
        "applied_count": applied_count,
        "unapplied_count": unapplied_count,
        "reasons": _normalise_reasons(category.get("reasons")),
    }
    for key, value in category.items():
        if key not in result:
            result[str(key)] = _copy_json_value(value)
    return result


def _normalise_categories(value):
    if value is None:
        return []
    if isinstance(value, dict):
        # Accept a map keyed by category id as a convenience for older plugin
        # builds; values still need to contain real counts from the provider.
        items = []
        for category_id, category in value.items():
            if isinstance(category, dict):
                item = dict(category)
                item.setdefault("category_id", category_id)
            else:
                item = {"category_id": category_id, "target_count": category}
            items.append(item)
        value = items
    if not isinstance(value, list):
        return []
    return [item for item in (_normalise_category(item) for item in value) if item is not None]


def _channel_list(runtime):
    """Return reported channels, deduplicating the legacy singular field."""

    if not isinstance(runtime, dict):
        return []
    channels = []
    raw_channels = runtime.get("realtime_channels")
    if isinstance(raw_channels, list):
        channels.extend(
            item for item in raw_channels
            if isinstance(item, dict) and item
        )
    legacy = runtime.get("realtime_channel")
    if isinstance(legacy, dict) and legacy:
        legacy_stream_id = str(legacy.get("stream_id") or "")
        duplicate = any(
            legacy_stream_id
            and str(item.get("stream_id") or "") == legacy_stream_id
            for item in channels
        )
        if not duplicate:
            channels.append(legacy)
    return channels


def _frame_projection(channel, ue_online):
    age = channel.get("last_frame_age_ms")
    age = age if isinstance(age, (int, float)) and not isinstance(age, bool) and age >= 0 else None
    frame_count = _non_negative_int(channel.get("frame_count"), 0)
    if not ue_online:
        return "unknown", None, age
    if age is None:
        if frame_count > 0:
            return "unknown", None, None
        return "no_frame", None, None
    fresh = age <= DEFAULT_FRAME_FRESHNESS_THRESHOLD_MS
    return ("fresh" if fresh else "stale"), fresh, age


def _control_projection(command, reported_enabled, ue_online):
    desired_enabled = command.get("enabled") if command else reported_enabled
    if command is None:
        state = "not_configured"
    elif not ue_online or not isinstance(reported_enabled, bool):
        state = "syncing"
    elif desired_enabled == reported_enabled:
        state = "in_sync"
    else:
        state = "syncing"
    # ``in_sync`` is retained as a bool for old clients.  With no command the
    # old endpoint considered an identical heartbeat value in sync, so keep
    # that behaviour while exposing the more precise control_state above.
    in_sync = (
        ue_online
        and isinstance(desired_enabled, bool)
        and isinstance(reported_enabled, bool)
        and desired_enabled == reported_enabled
    )
    return desired_enabled, state, in_sync


def _execution_projection(channel, ue_online, connection_state, frame_state, target_count, applied_count):
    explicit = str(channel.get("execution_state") or "").strip().lower()
    if explicit not in _EXECUTION_STATES:
        explicit = ""

    if not ue_online or connection_state in {"disabled", "disconnected", "error", "unknown"}:
        derived = "waiting"
    elif frame_state in {"no_frame", "unknown", "stale"}:
        derived = "waiting"
    elif target_count is None or applied_count is None:
        derived = "unknown"
    elif target_count < 0 or applied_count < 0 or applied_count > target_count:
        derived = "failed"
    elif target_count > 0 and applied_count == 0:
        # Safety invariant: a received frame with no applied target is never
        # allowed to become a healthy/green state.
        derived = "none_applied"
    elif target_count > 0 and applied_count < target_count:
        derived = "partial"
    else:
        derived = "ready"

    # Explicit provider state is useful when counters are unavailable, but a
    # stale/no-frame transport state must not be masked by an old "ready"
    # value.  The hard 25/0 rule always wins over an erroneous provider state.
    if target_count is not None and applied_count == 0 and target_count > 0:
        return "none_applied"
    if frame_state in {"no_frame", "stale", "unknown"}:
        return "waiting" if derived != "failed" else derived
    if explicit and derived not in {"none_applied", "failed", "waiting"}:
        return explicit
    return derived


def _health_projection(control_state, connection_state, frame_state, execution_state, target_count, applied_count):
    if connection_state == "disabled":
        return "disabled", False
    healthy = (
        control_state == "in_sync"
        and connection_state == "connected"
        and frame_state == "fresh"
        and execution_state == "ready"
        and target_count is not None
        and applied_count is not None
        and applied_count == target_count
    )
    if healthy:
        return "healthy", True
    if connection_state == "unknown" or frame_state in {"no_frame", "unknown"}:
        return "waiting", False
    return "attention", False


def _utc_now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")


class RealtimeStreamControlRegistry:
    """Keep explicit operator commands isolated and persisted by database id."""

    def __init__(self):
        self._lock = threading.RLock()
        self._by_database = {}
        self._project_store = None

    def configure_project_store(self, project_store):
        """Attach the store used for lazy loading and low-frequency persistence."""
        with self._lock:
            self._project_store = project_store

    @staticmethod
    def _setting_key(database_id):
        return f"external_data.realtime_stream.{database_id}"

    @staticmethod
    def _command_from_value(stream, database_id):
        if not isinstance(stream, dict) or not isinstance(stream.get("enabled"), bool):
            return None
        return {
            "database_id": str(database_id),
            "enabled": stream["enabled"],
            "updated_at": str(stream.get("updated_at") or ""),
        }

    def _persist_command(self, command):
        with self._lock:
            project_store = self._project_store
        if project_store is None:
            return

        project_store.set_runtime_setting(
            self._setting_key(command["database_id"]),
            {
                "enabled": command["enabled"],
                "updated_at": command["updated_at"],
            },
        )

    def set_enabled(self, database_id, enabled):
        command = {
            "database_id": str(database_id),
            "enabled": bool(enabled),
            "updated_at": _utc_now(),
        }
        self._persist_command(command)
        with self._lock:
            self._by_database[str(database_id)] = command
        return copy.deepcopy(command)

    def get_command(self, database_id):
        if not database_id:
            return None
        with self._lock:
            value = self._by_database.get(str(database_id))
            project_store = self._project_store
        if value:
            return copy.deepcopy(value)
        if project_store is None:
            return None

        persisted = project_store.get_runtime_setting(self._setting_key(database_id))
        value = self._command_from_value(persisted, database_id)
        if value:
            with self._lock:
                value = self._by_database.setdefault(str(database_id), value)
            return copy.deepcopy(value)
        return None


REALTIME_STREAM_CONTROL = RealtimeStreamControlRegistry()


def realtime_control_for_heartbeat(database_id):
    """Return the explicit command to include in a UE heartbeat response."""
    return REALTIME_STREAM_CONTROL.get_command(database_id)


def _project_stream(channel, database_id, command, ue_online, control_supported=True):
    """Project one reported channel into the additive ``streams`` contract."""

    channel = channel if isinstance(channel, dict) else {}
    reported_enabled = channel.get("enabled")
    if not isinstance(reported_enabled, bool):
        reported_enabled = None
    desired_enabled, control_state, in_sync = _control_projection(
        command, reported_enabled, ue_online
    )

    raw_connection = str(channel.get("connection_state") or "").strip().lower()
    connection_state = raw_connection if raw_connection in {
        "disabled",
        "connecting",
        "connected",
        "reconnecting",
        "disconnected",
        "error",
        "unknown",
    } else "unknown"
    # ``unknown`` is intentionally accepted in the public projection for a
    # heartbeat that has not reported a socket state yet.
    if not ue_online:
        connection_state = "unknown"
    raw_source = str(channel.get("active_source") or "none").strip().lower() or "none"
    active_source = raw_source if raw_source in {"none", "http_snapshot", "websocket"} else "none"
    if not ue_online:
        active_source = "none"

    raw_target_present = "target_count" in channel
    raw_applied_present = "applied_target_count" in channel
    target_count = _non_negative_int(channel.get("target_count"))
    applied_count = _non_negative_int(channel.get("applied_target_count"))
    frame_count = _non_negative_int(channel.get("frame_count"), 0)
    source_timestamp_ms = _non_negative_int(channel.get("source_timestamp_ms"))
    if not ue_online:
        # Do not expose the last online frame as current data while UE is
        # offline.  The legacy projection historically returned zeroes here.
        target_count = 0
        applied_count = 0
        raw_target_present = raw_applied_present = True

    frame_state, frame_fresh, last_frame_age_ms = _frame_projection(channel, ue_online)
    if not ue_online:
        last_frame_age_ms = None
    execution_state = _execution_projection(
        channel,
        ue_online,
        connection_state,
        frame_state,
        target_count if raw_target_present else None,
        applied_count if raw_applied_present else None,
    )
    # A stale/no-frame status must not report an old successful execution as
    # current.  This also keeps an old heartbeat with counters but no age from
    # becoming a false-green stream.
    if frame_state in {"no_frame", "stale", "unknown"} and not channel.get("execution_state"):
        execution_state = "waiting" if ue_online else "waiting"

    if target_count is not None and applied_count is not None:
        unapplied_count = max(target_count - applied_count, 0)
    else:
        unapplied_count = None

    categories = _normalise_categories(channel.get("categories"))
    reasons_value = channel.get("unapplied_reasons")
    if reasons_value is None:
        reasons_value = channel.get("reasons")
    unapplied_reasons = _normalise_reasons(reasons_value)
    diagnostics = _copy_json_value(channel.get("diagnostics")) if "diagnostics" in channel else None
    if diagnostics is None and "diagnostic" in channel:
        diagnostics = _copy_json_value(channel.get("diagnostic"))

    # ``None`` is the intentional representation for an execution counter
    # missing from a new/old heartbeat.  It lets clients say "not reported"
    # instead of silently treating received targets as applied.
    stream = {
        "stream_id": str(channel.get("stream_id") or "")[:256],
        "display_name": str(channel.get("display_name") or "实时数据流")[:256],
        "owner": str(channel.get("owner") or "")[:128],
        "owner_state": str(
            channel.get("owner_state")
            or ("registered" if channel.get("owner") else "unknown")
        )[:64],
        "url": str(channel.get("url") or "")[:2048],
        "desired_enabled": desired_enabled,
        "reported_enabled": reported_enabled,
        "command_configured": command is not None,
        "command_updated_at": command.get("updated_at") if command else None,
        # The MVP keeps the existing per-database command key.  Only the first
        # reported stream is therefore controllable; future streams remain
        # observable until a per-stream command registry is approved.
        "control_supported": bool(control_supported),
        "control_scope": "database_primary" if control_supported else "observe_only",
        "control_state": control_state,
        "connection_state": connection_state,
        "in_sync": in_sync,
        "active_source": active_source,
        "last_frame_at": channel.get("last_frame_at") if isinstance(channel.get("last_frame_at"), str) else None,
        "source_timestamp_ms": source_timestamp_ms,
        "last_frame_age_ms": last_frame_age_ms,
        "freshness_threshold_ms": DEFAULT_FRAME_FRESHNESS_THRESHOLD_MS,
        "frame_state": frame_state,
        "frame_fresh": frame_fresh,
        "frame_count": frame_count,
        "target_count": target_count,
        "applied_target_count": applied_count,
        "applied_target_count_known": raw_applied_present and applied_count is not None,
        "unapplied_target_count": unapplied_count,
        "execution_state": execution_state,
        "execution_known": execution_state in {"ready", "partial", "none_applied", "failed"},
        "categories": categories,
        "categories_known": bool(categories),
        "unapplied_reasons": unapplied_reasons,
        "error": str(channel.get("error") or "")[:500],
    }
    if diagnostics is not None:
        stream["diagnostics"] = diagnostics

    health_state, healthy = _health_projection(
        control_state,
        connection_state,
        frame_state,
        execution_state,
        target_count,
        applied_count,
    )
    stream["health_state"] = health_state
    stream["healthy"] = healthy
    # Preserve provider-supplied fields that are not part of the canonical
    # contract, excluding potentially duplicate raw counters.
    known = set(stream)
    for key, value in channel.items():
        if key not in known and key not in {"targets", "position", "world_position", "location", "x", "y", "z"}:
            stream[str(key)] = _copy_json_value(value)
    return stream


def _legacy_websocket_projection(stream):
    """Return the original singular shape plus additive status fields."""

    def legacy_count(value):
        return value if isinstance(value, int) and value >= 0 else 0

    return {
        "stream_id": stream.get("stream_id") or "",
        "owner": stream.get("owner") or "",
        "url": stream.get("url") or "",
        "desired_enabled": stream.get("desired_enabled"),
        "reported_enabled": stream.get("reported_enabled"),
        "command_configured": bool(stream.get("command_configured")),
        "command_updated_at": stream.get("command_updated_at"),
        "control_supported": stream.get("control_supported", True) is not False,
        "control_scope": stream.get("control_scope") or "database_primary",
        "connection_state": stream.get("connection_state") or "unknown",
        "in_sync": bool(stream.get("in_sync")),
        "active_source": stream.get("active_source") or "none",
        "source_timestamp_ms": stream.get("source_timestamp_ms"),
        "last_frame_age_ms": stream.get("last_frame_age_ms"),
        "frame_count": legacy_count(stream.get("frame_count")),
        "target_count": legacy_count(stream.get("target_count")),
        "applied_target_count": legacy_count(stream.get("applied_target_count")),
        "error": stream.get("error") or "",
        # Additive fields are harmless to old consumers and useful to scripts
        # that have not migrated to ``streams`` yet.
        "control_state": stream.get("control_state"),
        "frame_state": stream.get("frame_state"),
        "frame_fresh": stream.get("frame_fresh"),
        "execution_state": stream.get("execution_state"),
        "unapplied_target_count": stream.get("unapplied_target_count"),
        "categories": copy.deepcopy(stream.get("categories") or []),
        "unapplied_reasons": copy.deepcopy(stream.get("unapplied_reasons") or []),
    }


def _sum_stream_field(streams, field):
    values = [stream.get(field) for stream in streams]
    if any(value is None for value in values):
        return None
    return sum(value for value in values if isinstance(value, int) and value >= 0)


def _summary_for_streams(streams):
    connected = sum(1 for stream in streams if stream.get("connection_state") == "connected")
    healthy = sum(1 for stream in streams if stream.get("healthy") is True)
    attention = len(streams) - healthy
    return {
        "stream_count": len(streams),
        "connected_stream_count": connected,
        "healthy_stream_count": healthy,
        "attention_stream_count": attention,
        "total_target_count": _sum_stream_field(streams, "target_count"),
        "total_applied_target_count": _sum_stream_field(streams, "applied_target_count"),
        "total_unapplied_target_count": _sum_stream_field(streams, "unapplied_target_count"),
    }


def build_active_realtime_status(project_store, runtime_status_reader):
    """Build the additive v2 status projection for the active Database.

    ``runtime_status_reader`` is intentionally injected so this function stays
    a pure projection and remains straightforward to test without a UE process.
    """

    project = project_store.get_active_copy()
    if not project:
        return None

    database_id = str(project.get("id") or "")
    runtime = runtime_status_reader(database_id) or {}
    ue_online = bool(runtime.get("online")) if isinstance(runtime, dict) else False
    channels = _channel_list(runtime)
    command = REALTIME_STREAM_CONTROL.get_command(database_id)
    streams = []
    for index, channel in enumerate(channels):
        # The current command registry stores the primary stream command by
        # database id.  Until per-stream persistence is approved, apply it to
        # the first/current channel only and leave future channels observable.
        channel_command = command if index == 0 else None
        streams.append(_project_stream(
            channel,
            database_id,
            channel_command,
            ue_online,
            control_supported=index == 0,
        ))

    summary = _summary_for_streams(streams)
    if streams:
        legacy = _legacy_websocket_projection(streams[0])
    else:
        # Keep the old empty-object shape when UE has not registered a channel.
        legacy = {
            "stream_id": "",
            "owner": "",
            "url": "",
            "desired_enabled": command.get("enabled") if command else None,
            "reported_enabled": None,
            "command_configured": command is not None,
            "command_updated_at": command.get("updated_at") if command else None,
            "connection_state": "unknown",
            "in_sync": False,
            "active_source": "none",
            "source_timestamp_ms": None,
            "last_frame_age_ms": None,
            "frame_count": 0,
            "target_count": 0,
            "applied_target_count": 0,
            "error": "",
            "control_state": "syncing" if command else "not_configured",
            "frame_state": "unknown",
            "frame_fresh": None,
            "execution_state": "waiting",
            "unapplied_target_count": 0,
            "categories": [],
            "unapplied_reasons": [],
        }

    # If a provider supplies an HTTP snapshot health object, preserve its
    # fields while retaining the explicit decoupling defaults.
    http_snapshot = {
        "enabled": True,
        "affected_by_switch": False,
    }
    if isinstance(runtime, dict) and isinstance(runtime.get("http_snapshot"), dict):
        http_snapshot.update(_copy_json_value(runtime["http_snapshot"]))
        http_snapshot.setdefault("enabled", True)
        http_snapshot["affected_by_switch"] = False

    return {
        "schema_version": REALTIME_STATUS_SCHEMA_VERSION,
        "database": {
            "id": database_id,
            "name": project.get("name") or database_id,
        },
        "ue": {
            "online": ue_online,
            "project_id": (runtime.get("ue_project_id") if isinstance(runtime, dict) else None)
            or project.get("bound_ue_project_id")
            or "",
            "project_name": (runtime.get("ue_project_name") if isinstance(runtime, dict) else None)
            or project.get("bound_ue_project_name")
            or "",
            "last_heartbeat_at": (
                runtime.get("last_heartbeat_at") if isinstance(runtime, dict) else None
            )
            or (runtime.get("last_seen_at") if isinstance(runtime, dict) else None),
        },
        "summary": summary,
        "streams": streams,
        "websocket": legacy,
        "http_snapshot": http_snapshot,
    }


def register_external_data_control_routes(app, project_store, runtime_status_reader):
    REALTIME_STREAM_CONTROL.configure_project_store(project_store)
    blueprint = Blueprint("external_data_control_api", __name__)

    def current_status():
        return build_active_realtime_status(project_store, runtime_status_reader)

    @blueprint.get("/api/v2/external-data/realtime")
    def get_realtime_status():
        status = current_status()
        if status is None:
            return jsonify({
                "error": "active_database_not_found",
                "message": "当前没有激活的 Database",
            }), 404
        return jsonify(status)

    @blueprint.put("/api/v2/external-data/realtime")
    def set_realtime_enabled():
        data = request.get_json(silent=True) or {}
        enabled = data.get("enabled")
        if not isinstance(enabled, bool):
            return jsonify({
                "error": "invalid_enabled",
                "message": "enabled 必须是布尔值",
            }), 400

        project = project_store.get_active_copy()
        if not project:
            return jsonify({
                "error": "active_database_not_found",
                "message": "当前没有激活的 Database",
            }), 404

        database_id = str(project.get("id") or "")
        expected = str(data.get("expected_database_id") or "").strip()
        if expected and expected != database_id:
            return jsonify({
                "error": "active_database_changed",
                "message": "当前激活 Database 已切换，请刷新页面后重试",
                "expected_database_id": expected,
                "active_database_id": database_id,
            }), 409

        requested_stream_id = data.get("stream_id")
        if requested_stream_id is not None:
            if not isinstance(requested_stream_id, str) or not requested_stream_id.strip():
                return jsonify({
                    "error": "invalid_stream_id",
                    "message": "stream_id 必须是非空字符串",
                }), 400
            # The MVP registry intentionally keeps the existing per-database
            # setting key.  Accept the optional stream_id only when it names
            # the currently reported primary stream; this avoids silently
            # toggling a different/future stream with the legacy command.
            current = current_status() or {}
            stream_ids = {
                str(item.get("stream_id") or "")
                for item in current.get("streams", [])
                if isinstance(item, dict)
            }
            if requested_stream_id.strip() not in stream_ids:
                return jsonify({
                    "error": "unknown_stream",
                    "message": "当前激活项目没有该数据流",
                    "stream_id": requested_stream_id.strip(),
                }), 409
            # The current persisted command is scoped to the active Database,
            # not to an individual stream.  Never report success for a
            # secondary stream and silently toggle the primary one instead.
            current_streams = current.get("streams", [])
            if current_streams and requested_stream_id.strip() != str(
                current_streams[0].get("stream_id") or ""
            ):
                return jsonify({
                    "error": "stream_not_controllable",
                    "message": "当前版本仅支持控制主数据流，其他数据流暂为只读观察",
                    "stream_id": requested_stream_id.strip(),
                }), 409

        command = REALTIME_STREAM_CONTROL.set_enabled(database_id, enabled)
        return jsonify({
            "status": "accepted",
            "message": "控制命令已保存，等待 UE 下一次心跳同步",
            "command": command,
            **current_status(),
        })

    app.register_blueprint(blueprint)
