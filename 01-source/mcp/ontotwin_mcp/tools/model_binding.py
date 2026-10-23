"""model_binding 域：实例换模型 + 类型默认模型。

save/clear 透传 expected_project_id（后端已自带锁内校验）；
promote/clear_type 是类型级写，无 expected（与其它类型级配置写口径一致）。
"""
from urllib.parse import quote


def register(mcp, client, registry):

    @mcp.tool()
    def get_model_binding(instance_id: str) -> dict:
        """只读：实例的模型绑定现状（当前模型、可选迁移模型、能力状态）。"""
        return client.get(
            "get_model_binding",
            f"/api/v2/instances/{quote(instance_id, safe='/')}/model-binding")

    @mcp.tool()
    def set_model_binding(instance_id: str, selection: dict,
                          expected_project_id: str = "") -> dict:
        """本操作会修改当前激活项目：给实例换模型。

        selection 结构以 get_model_binding 返回为准；expected_project_id 非空时透传做并发校验。
        """
        body = dict(selection)
        if expected_project_id:
            body["expected_project_id"] = expected_project_id
        return client.put_json(
            "set_model_binding",
            f"/api/v2/instances/{quote(instance_id, safe='/')}/model-binding", json=body)

    @mcp.tool()
    def clear_model_binding(instance_id: str, expected_project_id: str = "") -> dict:
        """本操作会修改当前激活项目：清除实例模型覆盖，恢复类型默认模型。"""
        body = {}
        if expected_project_id:
            body["expected_project_id"] = expected_project_id
        return client.delete_json(
            "clear_model_binding",
            f"/api/v2/instances/{quote(instance_id, safe='/')}/model-binding", json=body)

    @mcp.tool()
    def clear_type_model_default(object_type_rid: str) -> dict:
        """本操作会修改当前激活项目：清除类型的默认模型（类型级）。"""
        return client.delete_json(
            "clear_type_model_default",
            f"/api/v2/object-types/{quote(object_type_rid, safe='/')}/model-binding")

    @mcp.tool()
    def promote_model_binding(object_type_rid: str, source_asset_path: str) -> dict:
        """本操作会修改当前激活项目：把某个迁移模型提升为类型默认模型（类型级）。"""
        return client.post_json(
            "promote_model_binding",
            f"/api/v2/object-types/{quote(object_type_rid, safe='/')}/model-binding/promote",
            json={"source_asset_path": source_asset_path})

    for f in (get_model_binding, set_model_binding, clear_model_binding,
              clear_type_model_default, promote_model_binding):
        registry[f.__name__] = f
