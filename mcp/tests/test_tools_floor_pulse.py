"""floor_pulse 工具单测（fake client）。重点：camelCase 键映射。"""
from ontotwin_mcp.server import build_server


class C:
    def __init__(self):
        self.calls = []

    def get(self, op, path, params=None):
        self.calls.append(("get", path, params)); return {"ok": True}

    def post_json(self, op, path, json=None, timeout=None):
        self.calls.append(("post", path, json)); return {"status": "ok"}


def _t(mcp, name):
    return mcp._ot_tools[name]


def test_toggle_mock_body():
    c = C(); mcp = build_server(c)
    _t(mcp, "toggle_floor_pulse_mock")(True)
    method, path, body = c.calls[-1]
    assert method == "post" and path == "/api/v2/floor_pulse/mock/toggle"
    assert body == {"enabled": True}


def test_move_mock_camelcase_body():
    c = C(); mcp = build_server(c)
    _t(mcp, "move_floor_pulse_mock")("human-01", "WS-03", workstation_name="焊接")
    method, path, body = c.calls[-1]
    assert method == "post" and path == "/api/v2/floor_pulse/mock/move"
    assert body == {"instanceId": "human-01", "workstationId": "WS-03",
                    "workstationName": "焊接"}


def test_move_mock_omits_empty_name():
    c = C(); mcp = build_server(c)
    _t(mcp, "move_floor_pulse_mock")("human-01", "WS-03")
    body = c.calls[-1][2]
    assert body == {"instanceId": "human-01", "workstationId": "WS-03"}
    assert "workstationName" not in body


def test_snapshot_endpoint():
    c = C(); mcp = build_server(c)
    _t(mcp, "get_floor_pulse_snapshot")()
    assert c.calls[-1] == ("get", "/api/v2/floor_pulse/snapshot", None)


def test_events_camelcase_param():
    c = C(); mcp = build_server(c)
    _t(mcp, "get_floor_pulse_events")(after_event_id=42)
    method, path, params = c.calls[-1]
    assert method == "get" and path == "/api/v2/floor_pulse/events"
    assert params == {"afterEventId": 42}


def test_events_default_param():
    c = C(); mcp = build_server(c)
    _t(mcp, "get_floor_pulse_events")()
    assert c.calls[-1][2] == {"afterEventId": 0}


def test_health_endpoint():
    c = C(); mcp = build_server(c)
    _t(mcp, "get_floor_pulse_health")()
    assert c.calls[-1] == ("get", "/api/v2/floor_pulse/health", None)


def test_floor_pulse_tools_registered():
    c = C(); mcp = build_server(c)
    expected = {
        "toggle_floor_pulse_mock", "move_floor_pulse_mock",
        "get_floor_pulse_snapshot", "get_floor_pulse_events", "get_floor_pulse_health",
    }
    assert expected <= set(mcp._ot_tools)
