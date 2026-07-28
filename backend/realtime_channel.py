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


def enrich_instances_with_realtime_channel(instances, runtime_status):
    """Attach an ephemeral channel view without mutating ProjectStore values."""
    enriched = []
    for instance in instances:
        item = copy.copy(instance)
        channel = project_instance_realtime_channel(item.get("id"), runtime_status)
        if channel is not None:
            item["realtime_channel"] = channel
        enriched.append(item)
    return enriched
