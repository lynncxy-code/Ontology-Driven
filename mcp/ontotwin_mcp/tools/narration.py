"""narration 域：漫游路线的路点语音讲解（TTS 合成 + 字幕）。

路点讲解文案写在路线的 waypoints[].narration 里（走 scene 域的 update_route）；
本域负责三件与「声音」有关的事：

    get_narration_provider_status   看 TTS 供应商是否已配好、可选音色有哪些
    save_narration_defaults         设项目级默认音色 / 语速 / 音量
    generate_route_narration        为指定路线合成音频（真正调 TTS，耗时且计费）

供应商未配置时 provider_status 返回 configured=false，generate 会失败——
先让人在服务端填好凭据再合成。

并发：两个写工具都要 expected_revision，取自 get_roaming_config 的 revision
（narration 与漫游共用 scene_interactions.revision）；冲突后重读再写。
音频文件本身走 /narration-assets/<id> 二进制下载，不在此封装。
"""
from urllib.parse import quote

_BASE = "/api/v2/scene-interactions"


def register(mcp, client, registry):

    @mcp.tool()
    def get_narration_provider_status() -> dict:
        """只读：TTS 供应商状态与音色目录。

        返回 configured / ready 与 voices（voice_id、display_name、音色类型、适用场景）。
        configured=false 表示服务端还没填凭据，此时不要调 generate_route_narration。
        """
        return client.get(
            "get_narration_provider_status", f"{_BASE}/narration/provider-status")

    @mcp.tool()
    def save_narration_defaults(defaults: dict, expected_revision: int,
                                expected_project_id: str = "") -> dict:
        """本操作会修改当前激活项目：保存项目级讲解默认值（音色 / 语速 / 音量等）。

        改默认值会顺带规范化各路线已有路点的 narration 配置，可能抬升路线 revision。
        expected_revision 取自 get_roaming_config；expected_project_id 非空时绑定项目身份。
        """
        body = {"defaults": defaults, "expected_revision": expected_revision}
        if expected_project_id:
            body["expected_project_id"] = expected_project_id
        return client.put_json(
            "save_narration_defaults", f"{_BASE}/narration/defaults", json=body)

    @mcp.tool()
    def generate_route_narration(route_id: str, expected_revision: int,
                                 waypoint_ids: list = None,
                                 expected_project_id: str = "") -> dict:
        """本操作会修改当前激活项目：为指定路线合成路点讲解音频。

        真正调用 TTS 供应商，耗时且可能计费。waypoint_ids 省略时合成整条路线的
        全部待更新路点；只想重做其中几个就把它们的 id 传进来。
        expected_project_id 非空时绑定项目身份。
        """
        body = {"expected_revision": expected_revision}
        if waypoint_ids:
            body["waypoint_ids"] = waypoint_ids
        if expected_project_id:
            body["expected_project_id"] = expected_project_id
        return client.post_json(
            "generate_route_narration",
            f"{_BASE}/routes/{quote(route_id, safe='/')}/narration/generate",
            json=body, timeout=180.0)

    for f in (get_narration_provider_status, save_narration_defaults,
              generate_route_narration):
        registry[f.__name__] = f
