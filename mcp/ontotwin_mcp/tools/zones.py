"""zones 域：实例分区读写（zone_management）。

并发：assign 用 expected_project_id（M0 式，选填，非空才透传）。
"""


def register(mcp, client, registry):

    @mcp.tool()
    def get_zones() -> dict:
        """只读：当前项目的分区汇总（各 zone 及实例数）。"""
        return client.get("get_zones", "/api/v2/zones")

    @mcp.tool()
    def assign_zones(instance_ids: list, zone_id: str = "",
                     expected_project_id: str = "") -> dict:
        """本操作会修改当前激活项目：批量给实例指派分区。

        zone_id 传空串表示解除分区。expected_project_id 非空时作乐观并发校验；
        为空则不放进 body，保持后端缺省行为。
        """
        body = {"instance_ids": instance_ids, "zone_id": (zone_id or None)}
        if expected_project_id:
            body["expected_project_id"] = expected_project_id
        return client.put_json("assign_zones", "/api/v2/zones/assignments", json=body)

    for f in (get_zones, assign_zones):
        registry[f.__name__] = f
