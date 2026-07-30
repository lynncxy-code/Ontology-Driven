"""ontology_edit 域：本体类型能力接口编辑 + 定义查询 + 暂存图生成。

inject/remove 是类型级配置写（无 expected，与 enable_info_panel/promote 同口径）；
定义查询只读；build_staging_graph_from_registry 从 Neo4j 出暂存图（不落项目）。
排除 fetch_api（SSRF：外部任意 URL 拉取）。
"""


def register(mcp, client, registry):

    @mcp.tool()
    def list_interface_defs() -> dict:
        """只读：全部三维能力接口定义（两层结构：I3D_Representable + 子接口）。"""
        return client.get("list_interface_defs", "/api/v2/ontology/interfaces")

    @mcp.tool()
    def list_property_defs() -> dict:
        """只读：本体属性定义。"""
        return client.get("list_property_defs", "/api/v2/ontology/properties")

    @mcp.tool()
    def get_ontology_registry() -> dict:
        """只读：从 Neo4j 本体图库读取注册表（不可达返回 NEXUS_DEGRADED）。"""
        return client.get("get_ontology_registry", "/api/v2/ontology/registry")

    @mcp.tool()
    def list_transform_types() -> dict:
        """只读：可用的变换类型定义。"""
        return client.get("list_transform_types", "/api/v2/transforms")

    @mcp.tool()
    def inject_interfaces(object_type_rid: str, interfaces: list,
                          asset_id: str = "") -> dict:
        """本操作会修改当前激活项目：给类型挂载三维能力接口（合并追加，不覆盖）。

        子接口（I3D_Spatial/Visual/Behavioral/Overlay）需先有或同时挂 I3D_Representable，
        否则后端 400。可选 asset_id 一并保存为该类型资产。
        """
        body = {"object_type_rid": object_type_rid, "interfaces": interfaces}
        if asset_id:
            body["asset_id"] = asset_id
        return client.post_json("inject_interfaces", "/api/v2/ontology/inject", json=body)

    @mcp.tool()
    def remove_interface(object_type_rid: str, interface_rid: str) -> dict:
        """本操作会修改当前激活项目：从类型移除一个能力接口。

        移除 I3D_Representable 会级联清空所有子接口并清空该类型资产。
        """
        return client.delete_json(
            "remove_interface", "/api/v2/ontology/inject",
            json={"object_type_rid": object_type_rid, "interface_rid": interface_rid})

    @mcp.tool()
    def build_staging_graph_from_registry() -> dict:
        """从 Neo4j 本体图库生成暂存图（写入暂存区，不落项目）。

        产出 {nodes, links, categories}，可用 get_import_staging_graph 读回，再
        publish_ontology_dataset 发布。Neo4j 不可达返回 NEXUS_DEGRADED。
        """
        return client.post_json(
            "build_staging_graph_from_registry",
            "/api/v2/ontology/graph_from_registry")

    for f in (list_interface_defs, list_property_defs, get_ontology_registry,
              list_transform_types, inject_interfaces, remove_interface,
              build_staging_graph_from_registry):
        registry[f.__name__] = f
