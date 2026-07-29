"""ontology 域读工具：导入暂存图 / 项目本体图 / 类型库列举与详情。"""


def register(mcp, client, registry):
    @mcp.tool()
    def get_import_staging_graph() -> dict:
        """返回本体导入暂存区的自定义图（{nodes,links,categories}）。只读。"""
        return client.get("get_import_staging_graph", "/api/v2/ontology/custom_graph")

    @mcp.tool()
    def get_project_ontology_graph(dataset_id: str = "") -> dict:
        """返回指定数据集的本体图（{nodes,links,categories}）。只读。

        dataset_id 缺省时回退到当前激活项目的 dataset_id。
        """
        did = dataset_id
        if not did:
            active = registry["get_active_project"]()
            did = active.get("dataset_id")
        return client.get(
            "get_project_ontology_graph", f"/api/v2/ontology/datasets/{did}/graph")

    @mcp.tool()
    def list_object_types() -> list:
        """列出当前激活项目的对象类型（ObjectType）注册表。只读。"""
        return client.get("list_object_types", "/api/v2/ontology/types")

    @mcp.tool()
    def get_object_type(rid: str) -> dict:
        """返回指定 rid 的对象类型详情（含属性与能力接口）。只读。"""
        return client.get("get_object_type", f"/api/v2/ontology/types/{rid}")

    for f in (get_import_staging_graph, get_project_ontology_graph,
              list_object_types, get_object_type):
        registry[f.__name__] = f
