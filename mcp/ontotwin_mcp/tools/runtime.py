"""runtime 域读工具：实例 / 状态快照 / 空间画像 / 绑定台。"""

from urllib.parse import quote


def register(mcp, client, registry):
    @mcp.tool()
    def list_instances() -> list:
        """列出当前激活项目的所有实例。只读。"""
        return client.get("list_instances", "/api/v2/instances")

    @mcp.tool()
    def get_instance_state(instance_id: str) -> dict:
        """返回指定实例的当前状态。只读。"""
        return client.get("get_instance_state",
                          f"/api/v2/instances/{quote(instance_id, safe='/')}")

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
    def list_components() -> dict:
        """列出绑定台可用组件。只读。返回后端包裹结构 {components, count}。"""
        return client.get("list_components", "/api/v2/binding/components")

    @mcp.tool()
    def list_roster() -> dict:
        """列出绑定台花名册（实例绑定关系）。只读。返回后端包裹结构 {roster}。"""
        return client.get("list_roster", "/api/v2/binding/roster")

    @mcp.tool()
    def set_instance_state(instance_id: str, patch: dict,
                           expected_project_id: str = "") -> dict:
        """本操作会修改当前激活项目（persist-write）：覆写指定实例的状态字段。

        patch 为要覆盖的状态键值；expected_project_id 非空时作乐观并发校验，
        为空则保持后端缺省（旧）行为。
        """
        body = {"instance_id": instance_id, "patch": patch}
        if expected_project_id:
            body["expected_project_id"] = expected_project_id
        return client.post_json("set_instance_state", "/api/v2/state/override", json=body)

    for f in (list_instances, get_instance_state, get_instance_snapshot,
              get_state_snapshots, get_spatial_profile, list_components, list_roster,
              set_instance_state):
        registry[f.__name__] = f
