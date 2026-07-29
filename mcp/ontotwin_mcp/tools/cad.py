"""cad/coord 域工具：DXF 解析（stage-write）、坐标标定（compute）、
组件持久化保存（persist-write，会修改当前激活项目）。"""

from .. import config
from ..files import resolve_upload


def register(mcp, client, registry):
    settings = getattr(client, "s", None) or config.load()

    @mcp.tool()
    def parse_cad_dxf(file_path: str, wall_height: float = 0, wall_thickness: float = 0) -> dict:
        """上传并解析 DXF，扫描 INSERT 块得候选（stage-write，不改激活项目）。

        wall_height/wall_thickness 为可选墙体拉伸参数（0 表示不生成墙体）。
        解析耗时，使用 cadparse 超时。
        """
        base, content = resolve_upload(file_path, settings, allowed_ext=[".dxf"])
        return client.post_multipart(
            "parse_cad_dxf", "/api/v2/cad/parse",
            [("file", base, content)],
            data={"wall_height": wall_height, "wall_thickness": wall_thickness},
            timeout=settings.timeout_cadparse)

    @mcp.tool()
    def calibrate_coordinates(anchors: list) -> dict:
        """根据锚点对求 2D 仿射矩阵（compute，无副作用，不改任何存储）。"""
        return client.post_json(
            "calibrate_coordinates", "/api/v2/coord/calibrate",
            json={"anchors": anchors})

    @mcp.tool()
    def save_components(payload: dict, expected_project_id: str = "") -> dict:
        """本操作会修改当前激活项目（persist-write）：保存标定后的组件到当前项目。

        expected_project_id 非空时作乐观并发校验；为空则保持后端缺省（旧）行为。
        """
        body = dict(payload)
        if expected_project_id:
            body["expected_project_id"] = expected_project_id
        return client.post_json(
            "save_components", "/api/v2/coord/save_components", json=body)

    for f in (parse_cad_dxf, calibrate_coordinates, save_components):
        registry[f.__name__] = f
