"""Project the UE runtime heartbeat into a per-instance realtime-channel state.

This module deliberately does not persist anything.  The existing ProjectStore
status remains the OntoTwin/HTTP lifecycle status; realtime-channel state is an
ephemeral view derived from the latest UE heartbeat.
"""

import copy

from runtime_source_policy import is_websocket_spatial_instance


REALTIME_CHANNEL_UNKNOWN = "unknown"
REALTIME_CHANNEL_WEBSOCKET = "realtime"
REALTIME_CHANNEL_HTTP_FALLBACK = "http_fallback"
REALTIME_CHANNEL_TARGET_LOST = "target_lost"

INSTANCE_LIVENESS_STATIC = "static"
INSTANCE_LIVENESS_ONLINE = "online"
INSTANCE_LIVENESS_DEGRADED = "degraded"
INSTANCE_LIVENESS_OFFLINE = "offline"
INSTANCE_LIVENESS_UNKNOWN = "unknown"


def project_instance_realtime_channel(instance_id, runtime_status):
    """Return a browser-facing channel view, or ``None`` for non-WS instances."""
    if not is_websocket_spatial_instance(instance_id):
        return None

    result = {
        "state": REALTIME_CHANNEL_UNKNOWN,
        "enabled": None,
        "connection_state": "unknown",
        "active_source": "none",
        "last_frame_age_ms": None,
        "frame_count": 0,
        "target_state": "unknown",
        "applied": False,
        "last_reported_at": None,
        "error": "",
    }
    if not isinstance(runtime_status, dict) or not runtime_status.get("online"):
        return result

    channel = runtime_status.get("realtime_channel")
    if not isinstance(channel, dict):
        return result

    result.update({
        "enabled": channel.get("enabled"),
        "connection_state": channel.get("connection_state") or "unknown",
        "active_source": channel.get("active_source") or "none",
        "last_frame_age_ms": channel.get("last_frame_age_ms"),
        "frame_count": channel.get("frame_count") or 0,
        "last_reported_at": runtime_status.get("last_seen_at"),
        "error": channel.get("error") or "",
    })

    target = next(
        (
            item for item in channel.get("targets") or []
            if isinstance(item, dict) and item.get("instance_id") == instance_id
        ),
        None,
    )
    if target:
        result["target_state"] = target.get("state") or "unknown"
        result["applied"] = bool(target.get("applied"))

    if result["active_source"] == "websocket":
        if result["applied"] and result["target_state"].lower() != "lost":
            result["state"] = REALTIME_CHANNEL_WEBSOCKET
        else:
            result["state"] = REALTIME_CHANNEL_TARGET_LOST
    else:
        result["state"] = REALTIME_CHANNEL_HTTP_FALLBACK
    return result


def project_instance_liveness(instance_id, runtime_status):
    """Project the status that the instance centre should show.

    ProjectStore ``status`` is a legacy three-second data-freshness flag.  It is
    not a valid connectivity signal for CAD/static instances, which have no
    recurring telemetry by design.  Realtime-owned instances use the explicit
    UE channel health; every other instance is reported as static instead of
    being falsely labelled offline.
    """
    channel = project_instance_realtime_channel(instance_id, runtime_status)
    if channel is None:
        return {
            "mode": "static",
            "state": INSTANCE_LIVENESS_STATIC,
            "label": "静态实例",
            "detail": "未配置实时数据源，不参与失联判定",
        }

    state = channel["state"]
    if state == REALTIME_CHANNEL_WEBSOCKET:
        projected = (INSTANCE_LIVENESS_ONLINE, "实时在线", "WebSocket 目标正在驱动该实例")
    elif state == REALTIME_CHANNEL_HTTP_FALLBACK:
        projected = (INSTANCE_LIVENESS_DEGRADED, "HTTP 接管", "实时通道未生效，当前使用 HTTP 快照")
    elif state == REALTIME_CHANNEL_TARGET_LOST:
        projected = (INSTANCE_LIVENESS_OFFLINE, "目标失联", "实时通道没有可应用到该实例的目标")
    else:
        projected = (INSTANCE_LIVENESS_UNKNOWN, "等待通道", "尚未收到有效的 UE 实时通道健康回报")

    return {
        "mode": "realtime",
        "state": projected[0],
        "label": projected[1],
        "detail": projected[2],
    }


def enrich_instances_with_realtime_channel(instances, runtime_status):
    """Attach an ephemeral channel view without mutating ProjectStore values."""
    enriched = []
    for instance in instances:
        item = copy.copy(instance)
        instance_id = item.get("id")
        channel = project_instance_realtime_channel(instance_id, runtime_status)
        if channel is not None:
            item["realtime_channel"] = channel
        item["liveness"] = project_instance_liveness(instance_id, runtime_status)
        enriched.append(item)
    return enriched
