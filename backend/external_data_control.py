"""Runtime control and monitoring for the active database's WebSocket stream."""

import copy
import datetime
import threading

from flask import Blueprint, jsonify, request


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


def build_active_realtime_status(project_store, runtime_status_reader):
    project = project_store.get_active_copy()
    if not project:
        return None

    database_id = str(project.get("id") or "")
    runtime = runtime_status_reader(database_id) or {}
    channel = runtime.get("realtime_channel")
    if not isinstance(channel, dict):
        channel = {}

    command = REALTIME_STREAM_CONTROL.get_command(database_id)
    reported_enabled = channel.get("enabled")
    if not isinstance(reported_enabled, bool):
        reported_enabled = None
    desired_enabled = command.get("enabled") if command else reported_enabled
    ue_online = bool(runtime.get("online"))
    in_sync = (
        ue_online
        and isinstance(desired_enabled, bool)
        and isinstance(reported_enabled, bool)
        and desired_enabled == reported_enabled
    )

    connection_state = str(channel.get("connection_state") or "unknown")
    active_source = channel.get("active_source") or "none"
    last_frame_age_ms = channel.get("last_frame_age_ms")
    target_count = int(channel.get("target_count") or 0)
    applied_target_count = int(channel.get("applied_target_count") or 0)
    if not ue_online:
        connection_state = "unknown"
        active_source = "none"
        last_frame_age_ms = None
        target_count = 0
        applied_target_count = 0

    return {
        "database": {
            "id": database_id,
            "name": project.get("name") or database_id,
        },
        "ue": {
            "online": ue_online,
            "project_id": runtime.get("ue_project_id") or project.get("bound_ue_project_id") or "",
            "project_name": runtime.get("ue_project_name") or project.get("bound_ue_project_name") or "",
            "last_heartbeat_at": runtime.get("last_seen_at"),
        },
        "websocket": {
            "stream_id": channel.get("stream_id") or "",
            "owner": channel.get("owner") or "",
            "url": channel.get("url") or "",
            "desired_enabled": desired_enabled,
            "reported_enabled": reported_enabled,
            "command_configured": command is not None,
            "command_updated_at": command.get("updated_at") if command else None,
            "connection_state": connection_state,
            "in_sync": in_sync,
            "active_source": active_source,
            "last_frame_age_ms": last_frame_age_ms,
            "frame_count": int(channel.get("frame_count") or 0),
            "target_count": target_count,
            "applied_target_count": applied_target_count,
            "error": channel.get("error") or "",
        },
        "http_snapshot": {
            "enabled": True,
            "affected_by_switch": False,
        },
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

        command = REALTIME_STREAM_CONTROL.set_enabled(database_id, enabled)
        return jsonify({
            "status": "accepted",
            "message": "控制命令已保存，等待 UE 下一次心跳同步",
            "command": command,
            **current_status(),
        })

    app.register_blueprint(blueprint)
