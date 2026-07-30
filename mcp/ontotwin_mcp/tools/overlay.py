"""overlay 域：信息面板配置读写。

读（read-only）：模板 / 上下文 / 预览 / 媒体策略。
写（config-write，项目级持久化，expected_revision 必填）：启用面板能力、存类型配置、
存/清实例覆盖、批量覆盖、存媒体策略。

并发：写前先用 get_overlay_context 拿 revision，改结构后带 expected_revision 写回；
遇 NEXUS_REVISION_CONFLICT 重新读后重写。revision 绑定当前激活项目的这份配置，
项目切走则旧 revision 必对不上 → 409，故本域无需再透传 expected_project_id。
"""
from typing import Optional
from urllib.parse import quote

INFO_PANEL_INTERFACES = ["I3D_Representable", "I3D_Overlay"]


def register(mcp, client, registry):

    @mcp.tool()
    def list_overlay_templates() -> dict:
        """只读：列出可用的信息面板模板。"""
        return client.get("list_overlay_templates", "/api/v2/overlays/templates")

    @mcp.tool()
    def get_overlay_context(object_type_rid: str = "", instance_id: str = "") -> dict:
        """只读：读取信息面板配置上下文。

        返回含 type_config.revision / instance_override.revision /
        instances[].override_revision / media_policy.revision。写面板前先调它拿
        revision 与当前活配置，照结构改后再 save_*。
        """
        params = {}
        if object_type_rid:
            params["object_type_rid"] = object_type_rid
        if instance_id:
            params["instance_id"] = instance_id
        return client.get("get_overlay_context", "/api/v2/overlays/context", params=params)

    @mcp.tool()
    def preview_overlay(object_type_rid: str = "", instance_id: str = "",
                        config: Optional[dict] = None) -> dict:
        """只读（纯计算）：按给定 config 预览面板解析结果，不落库。config 省略时用已存配置。"""
        body = {"object_type_rid": object_type_rid or None,
                "instance_id": instance_id or None, "config": config}
        return client.post_json("preview_overlay", "/api/v2/overlays/preview", json=body)

    @mcp.tool()
    def get_overlay_media_policy() -> dict:
        """只读：读取媒体域名策略（含 revision）。"""
        return client.get("get_overlay_media_policy", "/api/v2/overlays/media/policy")

    @mcp.tool()
    def enable_info_panel(object_type_rid: str) -> dict:
        """本操作会修改当前激活项目：给类型注入信息面板能力（I3D_Representable+I3D_Overlay）。

        类型首次配置面板前调用；幂等（重复注入同一组接口无副作用）。
        """
        return client.post_json(
            "enable_info_panel", "/api/v2/ontology/inject",
            json={"object_type_rid": object_type_rid, "interfaces": INFO_PANEL_INTERFACES})

    @mcp.tool()
    def save_overlay_type_config(object_type_rid: str, config: dict,
                                 expected_revision: int) -> dict:
        """本操作会修改当前激活项目：保存类型级信息面板配置。

        expected_revision 取自 get_overlay_context 的 type_config.revision；
        冲突返回 NEXUS_REVISION_CONFLICT，重读后再写。
        """
        return client.put_json(
            "save_overlay_type_config",
            f"/api/v2/overlays/object-types/{quote(object_type_rid, safe='/')}",
            json={"config": config, "expected_revision": expected_revision})

    @mcp.tool()
    def save_overlay_instance_override(instance_id: str, override: dict,
                                       expected_revision: int) -> dict:
        """本操作会修改当前激活项目：保存实例级面板覆盖。

        expected_revision 取自 get_overlay_context 的 instance_override.revision。
        """
        return client.put_json(
            "save_overlay_instance_override",
            f"/api/v2/overlays/instances/{quote(instance_id, safe='/')}",
            json={"override": override, "expected_revision": expected_revision})

    @mcp.tool()
    def clear_overlay_instance_override(instance_id: str, expected_revision: int) -> dict:
        """本操作会修改当前激活项目：清除实例覆盖，恢复继承类型配置。"""
        return client.delete_json(
            "clear_overlay_instance_override",
            f"/api/v2/overlays/instances/{quote(instance_id, safe='/')}",
            json={"expected_revision": expected_revision})

    @mcp.tool()
    def batch_overlay_instance_override(object_type_rid: str, instance_ids: list,
                                        merge_patch: dict, expected_revisions: dict) -> dict:
        """本操作会修改当前激活项目：给一批实例合并同一份覆盖补丁。

        expected_revisions 为 {instance_id: revision} 映射，逐实例乐观并发校验。
        """
        return client.post_json(
            "batch_overlay_instance_override", "/api/v2/overlays/instances/batch",
            json={"object_type_rid": object_type_rid, "instance_ids": instance_ids,
                  "merge_patch": merge_patch, "expected_revisions": expected_revisions})

    @mcp.tool()
    def save_overlay_media_policy(policy: dict, expected_revision: int) -> dict:
        """本操作会修改当前激活项目：保存媒体域名策略。"""
        return client.put_json(
            "save_overlay_media_policy", "/api/v2/overlays/media/policy",
            json={"policy": policy, "expected_revision": expected_revision})

    for f in (list_overlay_templates, get_overlay_context, preview_overlay,
              get_overlay_media_policy, enable_info_panel, save_overlay_type_config,
              save_overlay_instance_override, clear_overlay_instance_override,
              batch_overlay_instance_override, save_overlay_media_policy):
        registry[f.__name__] = f
