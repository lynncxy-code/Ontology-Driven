"""cad_calibration 域：CAD 一键成模的交互标定链（无状态，AI 持中间态）。

preview/scan 上传 DXF 出预览/候选类型；check 只读检查；commit 建/并类型数据集；
spawn 批量投产实例（commit=False dry-run，真写带 expected_project_id 护栏）。
"""
from typing import Optional

from .. import config
from ..files import resolve_upload


def register(mcp, client, registry):
    settings = getattr(client, "s", None) or config.load()

    @mcp.tool()
    def preview_cad(file_path: str) -> dict:
        """只读：上传 DXF 出预览数据（几何/图层）。"""
        base, content = resolve_upload(file_path, settings, allowed_ext=[".dxf"])
        return client.post_multipart(
            "preview_cad", "/api/v2/coord/preview",
            [("file", base, content)], timeout=settings.timeout_cadparse)

    @mcp.tool()
    def scan_cad_types(file_path: str) -> dict:
        """只读：扫描 DXF，返回候选 ObjectType 列表（含 preset asset_id）。"""
        base, content = resolve_upload(file_path, settings, allowed_ext=[".dxf"])
        return client.post_multipart(
            "scan_cad_types", "/api/v2/coord/types/scan",
            [("file", base, content)], timeout=settings.timeout_cadparse)

    @mcp.tool()
    def check_type_conflicts(rids: list, mode: str = "publish",
                             target_dataset_id: str = "") -> dict:
        """只读：给定待写入 rids，返回与目标/其它数据集的冲突。"""
        body = {"rids": rids, "mode": mode}
        if target_dataset_id:
            body["target_dataset_id"] = target_dataset_id
        return client.post_json(
            "check_type_conflicts", "/api/v2/coord/types/check_conflicts", json=body)

    @mcp.tool()
    def check_type_coverage(block_names: list) -> dict:
        """只读：给定 block_names，返回激活数据集覆盖/缺失情况。"""
        return client.post_json(
            "check_type_coverage", "/api/v2/coord/types/check_coverage",
            json={"block_names": block_names})

    @mcp.tool()
    def commit_cad_types(items: list, mode: str, source_file: str = "",
                         publish_options: Optional[dict] = None,
                         merge_options: Optional[dict] = None,
                         conflict_strategy: str = "", force: bool = False) -> dict:
        """本操作会修改当前激活项目：提交审核后的候选，发布新数据集或合并到现有。

        mode="publish" 用 publish_options={"name":...} 新建；mode="merge" 用
        merge_options={"target_dataset_id":...} 合并（目标显式，不需 expected_project_id）。
        """
        body = {"items": items, "mode": mode}
        if source_file:
            body["source_file"] = source_file
        if publish_options is not None:
            body["publish_options"] = publish_options
        if merge_options is not None:
            body["merge_options"] = merge_options
        if conflict_strategy:
            body["conflict_strategy"] = conflict_strategy
        if force:
            body["force"] = force
        return client.post_json(
            "commit_cad_types", "/api/v2/coord/types/commit", json=body)

    @mcp.tool()
    def spawn_cad_instances(items: list, transform_matrix: list,
                            source_label: str = "", mode: str = "dxf",
                            conflict_strategy: str = "update_coord",
                            commit: bool = False,
                            expected_project_id: str = "") -> dict:
        """本操作在 commit=True 时会修改当前激活项目：把 CAD 实体批量投产为实例。

        commit=False 为 dry-run（只返回 summary/to_create/conflicts，不写）；真写务必先 dry-run。
        expected_project_id 非空时作乐观并发校验（取自 get_active_project 的 project_id）。
        """
        body = {"items": items, "transform_matrix": transform_matrix,
                "mode": mode, "conflict_strategy": conflict_strategy, "commit": commit}
        if source_label:
            body["source_label"] = source_label
        if expected_project_id:
            body["expected_project_id"] = expected_project_id
        return client.post_json(
            "spawn_cad_instances", "/api/v2/coord/spawn_instances", json=body)

    for f in (preview_cad, scan_cad_types, check_type_conflicts, check_type_coverage,
              commit_cad_types, spawn_cad_instances):
        registry[f.__name__] = f
