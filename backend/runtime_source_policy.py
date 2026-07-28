"""Runtime data-source policy for spatial values owned by realtime feeds."""


WEBSOCKET_SPATIAL_INSTANCE_IDS = frozenset({
    "agv:agvfac000000001n01",
    "agv:agvfac000000001n02",
    "agv:agvfac000000001n03",
    "agv:agvfac000000001n04",
    "agv:agvfac000000001n05",
})


def is_websocket_spatial_instance(instance_id):
    """Return True when mock spatial simulation must yield to WebSocket."""
    return str(instance_id or "") in WEBSOCKET_SPATIAL_INSTANCE_IDS
