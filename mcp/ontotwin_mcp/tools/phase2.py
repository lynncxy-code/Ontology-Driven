"""phase2 域：二期只读工具（spec §3.3）。

只收敛只读端点（位置诊断 / UE 绑定状态 / 空间坐标系）；二期写工具
（promote_model_binding、transform PUT、spatial 写）按 spec 收敛策略暂不开。
"""


def register(mcp, client, registry):
    @mcp.tool()
    def get_instance_transform(instance_id: str) -> dict:
        """返回指定实例的位置/变换信息（位置诊断）。只读。"""
        return client.get(
            "get_instance_transform",
            f"/api/v2/instances/{instance_id}/transform")

    @mcp.tool()
    def get_ue_binding_status() -> dict:
        """返回 UE 工程与当前激活项目的绑定状态。只读。"""
        return client.get("get_ue_binding_status", "/api/v2/ue/binding_status")

    @mcp.tool()
    def list_spatial_frames() -> list:
        """列出当前激活项目的空间坐标系（frames）。只读。"""
        return client.get("list_spatial_frames", "/api/v2/spatial/frames")

    for f in (get_instance_transform, get_ue_binding_status, list_spatial_frames):
        registry[f.__name__] = f
