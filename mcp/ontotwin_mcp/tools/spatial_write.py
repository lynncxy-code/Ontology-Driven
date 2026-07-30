"""spatial_write 域：系统一坐标规范系写 + coord 杂项。

注意：系统一 /api/v2/spatial/*（坐标规范系），与 M2 的系统二
/api/v2/spatial-frames（底图参考帧，reference_frame 命名）不是一回事。
set_spatial_profile/upsert_spatial_frame/calibrate_spatial_frame 写隐式激活项目 → 带 expected_project_id；
save_block_asset_mapping 写全局文件、export/preview 纯计算 → 无 expected。
"""
from typing import Optional
from urllib.parse import quote


def register(mcp, client, registry):

    @mcp.tool()
    def set_spatial_profile(profile: dict, expected_project_id: str = "") -> dict:
        """本操作会修改当前激活项目：设置坐标规范剖面（会触发全场景重算）。

        profile 含 ue_transform/floor_table/canonical_origin 任意子集。高危写，带 expected_project_id。
        """
        body = dict(profile)
        if expected_project_id:
            body["expected_project_id"] = expected_project_id
        return client.put_json("set_spatial_profile", "/api/v2/spatial/profile", json=body)

    @mcp.tool()
    def upsert_spatial_frame(frame: dict, expected_project_id: str = "") -> dict:
        """本操作会修改当前激活项目：建/改一个坐标帧（frame 需含 id）。"""
        body = dict(frame)
        if expected_project_id:
            body["expected_project_id"] = expected_project_id
        return client.post_json("upsert_spatial_frame", "/api/v2/spatial/frames", json=body)

    @mcp.tool()
    def calibrate_spatial_frame(frame_id: str, anchors: list, name: str = "",
                                unit: str = "", expected_project_id: str = "") -> dict:
        """本操作会修改当前激活项目：用锚点拟合标定指定坐标帧。"""
        body = {"anchors": anchors}
        if name:
            body["name"] = name
        if unit:
            body["unit"] = unit
        if expected_project_id:
            body["expected_project_id"] = expected_project_id
        return client.post_json(
            "calibrate_spatial_frame",
            f"/api/v2/spatial/frames/{quote(frame_id, safe='/')}/calibrate", json=body)

    @mcp.tool()
    def preview_spatial_transform(points: list, floor: int = 1,
                                  profile: Optional[dict] = None) -> dict:
        """计算：给一批规范坐标，返回派生 UE 坐标（可传 profile 覆盖，不落库）。"""
        body = {"points": points, "floor": floor}
        if profile is not None:
            body["profile"] = profile
        return client.post_json(
            "preview_spatial_transform", "/api/v2/spatial/preview", json=body)

    @mcp.tool()
    def export_cad_scene(transform_matrix: list, entities: list,
                         polylines: Optional[list] = None,
                         wall_height: int = 4500, wall_thickness: int = 240) -> dict:
        """计算：把 CAD 实体经变换矩阵导出为 UE 场景 JSON（不落库）。"""
        body = {"transform_matrix": transform_matrix, "entities": entities,
                "wall_height": wall_height, "wall_thickness": wall_thickness}
        if polylines is not None:
            body["polylines"] = polylines
        return client.post_json("export_cad_scene", "/api/v2/coord/export", json=body)

    @mcp.tool()
    def get_block_asset_mapping() -> dict:
        """只读：全局块名→资产路径映射。"""
        return client.get("get_block_asset_mapping", "/api/v2/coord/mapping")

    @mcp.tool()
    def save_block_asset_mapping(mapping: dict) -> dict:
        """本操作会修改全局块→资产映射文件（非项目数据、无 expected）：合并保存传入的 dict。"""
        return client.post_json(
            "save_block_asset_mapping", "/api/v2/coord/mapping", json=mapping)

    for f in (set_spatial_profile, upsert_spatial_frame, calibrate_spatial_frame,
              preview_spatial_transform, export_cad_scene, get_block_asset_mapping,
              save_block_asset_mapping):
        registry[f.__name__] = f
