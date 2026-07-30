"""spatial 域：空间标定底图参考帧读写（spatial_assets，/api/v2/spatial-frames）。

注意：与基础层 list_spatial_frames（/api/v2/spatial/frames，坐标规范系）不是一回事。
本域是底图参考帧（带 draft_revision 乐观锁），故一律用 reference_frame 命名划清界限。

并发：写用 expected_draft_revision（选填，放 payload；非 None 才透传，省略保持后端缺省）。
"""
from typing import Optional
from urllib.parse import quote

from .. import config
from ..files import resolve_upload

_FRAMES = "/api/v2/spatial-frames"


def register(mcp, client, registry):
    settings = getattr(client, "s", None) or config.load()

    @mcp.tool()
    def create_reference_frame(file_path: str, floor: int = 1, floor_id: str = "",
                               ue_level: str = "", name: str = "") -> dict:
        """本操作会修改当前激活项目：上传一张底图作空间标定参考帧（multipart）。

        file_path 指向本地图片（png/jpg/jpeg/webp）；floor/floor_id/ue_level/name 为可选元数据。
        """
        base, content = resolve_upload(
            file_path, settings, allowed_ext=[".png", ".jpg", ".jpeg", ".webp"])
        data = {"floor": str(floor)}
        if floor_id:
            data["floor_id"] = floor_id
        if ue_level:
            data["ue_level"] = ue_level
        if name:
            data["name"] = name
        return client.post_multipart(
            "create_reference_frame", f"{_FRAMES}/assets",
            [("file", base, content)], data=data)

    @mcp.tool()
    def list_reference_frames() -> dict:
        """只读：列出当前项目的空间标定底图参考帧。"""
        return client.get("list_reference_frames", _FRAMES)

    @mcp.tool()
    def get_reference_frame(frame_id: str) -> dict:
        """只读：单张底图参考帧（含 draft_revision / calibration_revision）。"""
        return client.get("get_reference_frame", f"{_FRAMES}/{quote(frame_id, safe='/')}")

    @mcp.tool()
    def save_reference_frame_draft(frame_id: str, draft: dict,
                                   expected_draft_revision: Optional[int] = None) -> dict:
        """本操作会修改当前激活项目：保存底图参考帧草稿（锚点/楼层参照等）。

        draft 结构以 get_reference_frame 返回为准。expected_draft_revision 非 None 时作
        乐观并发校验（取自 get_reference_frame 的 draft_revision）；省略保持后端缺省。
        """
        body = dict(draft)
        if expected_draft_revision is not None:
            body["expected_draft_revision"] = expected_draft_revision
        return client.put_json(
            "save_reference_frame_draft",
            f"{_FRAMES}/{quote(frame_id, safe='/')}/draft", json=body)

    @mcp.tool()
    def publish_reference_frame(frame_id: str, payload: Optional[dict] = None,
                                expected_draft_revision: Optional[int] = None) -> dict:
        """本操作会修改当前激活项目：发布底图参考帧（把草稿标定固化为生效标定）。

        expected_draft_revision 非 None 时作乐观并发校验；省略保持后端缺省。
        """
        body = dict(payload) if payload else {}
        if expected_draft_revision is not None:
            body["expected_draft_revision"] = expected_draft_revision
        return client.post_json(
            "publish_reference_frame",
            f"{_FRAMES}/{quote(frame_id, safe='/')}/publish", json=body)

    for f in (create_reference_frame, list_reference_frames, get_reference_frame,
              save_reference_frame_draft, publish_reference_frame):
        registry[f.__name__] = f
