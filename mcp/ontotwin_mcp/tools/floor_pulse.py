"""floor_pulse 域：外部数据监控台（本地模拟控制 + 中转站代理）。

注意：floor_pulse 后端用 camelCase 键（instanceId/workstationId/afterEventId），
与其它域 snake_case 不同 —— 工具里必须显式映射，不能传 snake_case。
snapshot/events/health 代理外部中间件，不可达返回 503 NEXUS_DEGRADED。
mock 态是全局内存、非项目作用域，故 toggle/move 无 expected_project_id。
"""


def register(mcp, client, registry):

    @mcp.tool()
    def toggle_floor_pulse_mock(enabled: bool) -> dict:
        """本操作切换全局模拟开关：开启后 move_floor_pulse_mock 才能注入事件；关闭会清空模拟状态。"""
        return client.post_json(
            "toggle_floor_pulse_mock", "/api/v2/floor_pulse/mock/toggle",
            json={"enabled": enabled})

    @mcp.tool()
    def move_floor_pulse_mock(instance_id: str, workstation_id: str,
                              workstation_name: str = "") -> dict:
        """注入一条模拟移动事件（需先 toggle_floor_pulse_mock(True)，否则后端 400）。

        WS-00（休息区）→ idle，其它工位 → working。
        """
        body = {"instanceId": instance_id, "workstationId": workstation_id}
        if workstation_name:
            body["workstationName"] = workstation_name
        return client.post_json(
            "move_floor_pulse_mock", "/api/v2/floor_pulse/mock/move", json=body)

    @mcp.tool()
    def get_floor_pulse_snapshot() -> dict:
        """只读：拉中转站当前快照（含 mock 覆写）。中间件不可达返回 NEXUS_DEGRADED。"""
        return client.get("get_floor_pulse_snapshot", "/api/v2/floor_pulse/snapshot")

    @mcp.tool()
    def get_floor_pulse_events(after_event_id: int = 0) -> dict:
        """只读：拉中转站增量事件（eventId > after_event_id）。中间件不可达返回 NEXUS_DEGRADED。"""
        return client.get(
            "get_floor_pulse_events", "/api/v2/floor_pulse/events",
            params={"afterEventId": after_event_id})

    @mcp.tool()
    def get_floor_pulse_health() -> dict:
        """只读：查中转站健康状态。不可达返回 NEXUS_DEGRADED / {status: unreachable}。"""
        return client.get("get_floor_pulse_health", "/api/v2/floor_pulse/health")

    for f in (toggle_floor_pulse_mock, move_floor_pulse_mock,
              get_floor_pulse_snapshot, get_floor_pulse_events, get_floor_pulse_health):
        registry[f.__name__] = f
