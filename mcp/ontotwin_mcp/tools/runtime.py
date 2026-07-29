"""runtime 域读工具：实例 / 状态快照 / 空间画像 / 绑定台。"""


def register(mcp, client, registry):
    @mcp.tool()
    def list_instances() -> list:
        """列出当前激活项目的所有实例。只读。"""
        return client.get("list_instances", "/api/v2/instances")

    @mcp.tool()
    def get_instance_state(instance_id: str) -> dict:
        """返回指定实例的当前状态。只读。"""
        return client.get("get_instance_state", f"/api/v2/instances/{instance_id}")

    @mcp.tool()
    def get_instance_snapshot(instance_id: str) -> dict:
        """返回指定实例的状态快照。只读。"""
        return client.get(
            "get_instance_snapshot", "/api/v2/state/snapshot",
            params={"id": instance_id})

    @mcp.tool()
    def get_state_snapshots(zone: str = "") -> dict:
        """返回状态快照集合，可按 zone 过滤。只读。"""
        params = {"zone": zone} if zone else None
        return client.get("get_state_snapshots", "/api/v2/state/snapshots", params=params)

    @mcp.tool()
    def get_spatial_profile() -> dict:
        """返回当前激活项目的空间画像（坐标/包围盒等）。只读。"""
        return client.get("get_spatial_profile", "/api/v2/spatial/profile")

    @mcp.tool()
    def list_components() -> list:
        """列出绑定台可用组件。只读。"""
        return client.get("list_components", "/api/v2/binding/components")

    @mcp.tool()
    def list_roster() -> list:
        """列出绑定台花名册（实例绑定关系）。只读。"""
        return client.get("list_roster", "/api/v2/binding/roster")

    for f in (list_instances, get_instance_state, get_instance_snapshot,
              get_state_snapshots, get_spatial_profile, list_components, list_roster):
        registry[f.__name__] = f
