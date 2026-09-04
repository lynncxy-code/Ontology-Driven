"""lifecycle 域：实例生命周期写（建/删/改位置/回写）。

高危写：并发多写带 expected_project_id（M0 式，选填，非空才入 body）；
遇 NEXUS_PROJECT_CHANGED 说明项目被切走，重新确认后再写。
"""
from typing import Optional
from urllib.parse import quote


def register(mcp, client, registry):

    @mcp.tool()
    def create_instance(instance_id: str, object_type_rid: str,
                        initial_position: Optional[dict] = None,
                        display_name: str = "", expected_project_id: str = "") -> dict:
        """本操作会修改当前激活项目：投产一个新实例。

        前提：object_type_rid 必须已注入三维接口（否则后端 400）；实例 id 重复后端 409。
        """
        body = {"instance_id": instance_id, "object_type_rid": object_type_rid}
        if initial_position is not None:
            body["initial_position"] = initial_position
        if display_name:
            body["display_name"] = display_name
        if expected_project_id:
            body["expected_project_id"] = expected_project_id
        return client.post_json("create_instance", "/api/v2/instances", json=body)

    @mcp.tool()
    def delete_instance(instance_id: str, expected_project_id: str = "") -> dict:
        """本操作会修改当前激活项目：销毁一个实例（不可逆）。"""
        body = {}
        if expected_project_id:
            body["expected_project_id"] = expected_project_id
        return client.delete_json(
            "delete_instance",
            f"/api/v2/instances/{quote(instance_id, safe='/')}", json=body)

    @mcp.tool()
    def set_instance_transform(instance_id: str, transform: dict,
                               expected_project_id: str = "") -> dict:
        """本操作会修改当前激活项目：微调实例位置（规范坐标）。

        transform: {canonical_xy:[x,y], canonical_z, rotation, floor} 的任意子集。
        """
        body = dict(transform)
        if expected_project_id:
            body["expected_project_id"] = expected_project_id
        return client.put_json(
            "set_instance_transform",
            f"/api/v2/instances/{quote(instance_id, safe='/')}/transform", json=body)

    @mcp.tool()
    def writeback_instance_transform(instance_id: str, transform: dict,
                                     expected_project_id: str = "") -> dict:
        """本操作会修改当前激活项目：把 UE 端空间变换回写真源（UE cm）。

        transform: {tx,ty,tz,rx,ry,rz,sx,sy,sz}。
        """
        body = {"instance_id": instance_id, "transform": transform}
        if expected_project_id:
            body["expected_project_id"] = expected_project_id
        return client.post_json(
            "writeback_instance_transform", "/api/v2/state/writeback", json=body)

    @mcp.tool()
    def writeback_transforms_batch(changes: list) -> dict:
        """本操作会修改当前激活项目：原子回写一批实例的空间变换（UE cm）。

        changes 每项形如 {"instance_id": "...", "transform": {tx,ty,tz,rx,ry,rz,sx,sy,sz}}，
        单次最多 100 条。整批要么全成要么全不成——比逐条 writeback_instance_transform
        更适合保存一次 Runtime Editor 会话。

        ⚠️ 本端点**没有** expected_project_id 护栏（后端 apply_batch_writeback 不接受该参数），
        写期间若激活项目被切走不会被拦截。要这层保护就逐条用 writeback_instance_transform。
        """
        return client.post_json(
            "writeback_transforms_batch", "/api/v2/state/writeback/batch",
            json={"changes": changes})

    @mcp.tool()
    def writeback_material_overrides(changes: list,
                                     expected_project_id: str = "") -> dict:
        """本操作会修改当前激活项目：原子落库装配体各部件的材质覆盖。

        changes 每项描述一个实例上某部件的材质替换，来自编辑器预览。
        与空间回写分开，改材质不动位置。
        """
        body = {"changes": changes}
        if expected_project_id:
            body["expected_project_id"] = expected_project_id
        return client.post_json(
            "writeback_material_overrides", "/api/v2/state/material-writeback",
            json=body)

    for f in (create_instance, delete_instance, set_instance_transform,
              writeback_instance_transform, writeback_transforms_batch,
              writeback_material_overrides):
        registry[f.__name__] = f
