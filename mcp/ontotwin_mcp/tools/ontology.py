"""ontology 域工具：导入暂存图 / 项目本体图 / 类型库列举与详情（读），
以及本体写链的 import→publish 两步（stage-write）。"""

from .. import config
from ..files import resolve_upload


def register(mcp, client, registry):
    settings = getattr(client, "s", None) or config.load()

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

    @mcp.tool()
    def import_ontology_csv(file_paths: list) -> dict:
        """把若干本体 CSV 上传到导入暂存区（stage-write，不改激活项目）。

        后端按 filename 识别 6 张表（objectdef/linkdef/linksourcetype/linktargettype
        必须 + propertydef/hasproperty 可选），故 field 名与 filename 都用原 basename。
        """
        files = []
        for p in file_paths:
            base, content = resolve_upload(p, settings, allowed_ext=[".csv"])
            files.append((base, base, content))
        return client.post_multipart(
            "import_ontology_csv", "/api/v2/ontology/import_csv", files)

    @mcp.tool()
    def publish_ontology_dataset(name: str) -> dict:
        """把导入暂存区固化为一个命名数据集（stage-write，不改激活项目）。

        返回含 dataset_id；随后需 activate_project 才生效。
        """
        return client.post_json(
            "publish_ontology_dataset", "/api/v2/ontology/publish",
            json={"name": name})

    for f in (get_import_staging_graph, get_project_ontology_graph,
              list_object_types, get_object_type,
              import_ontology_csv, publish_ontology_dataset):
        registry[f.__name__] = f
