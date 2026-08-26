"""web_interaction 域：Web 页面 / 业务视图与三维场景的联动配置（PRD 3.8）。

一份项目级配置走「草稿 → 校验 → 发布」三段：

    save_web_interaction_draft   写草稿（不影响运行时）
    validate_web_interaction     校验草稿或指定配置，返回 errors / warnings
    publish_web_interaction      把草稿发布为运行时生效版本

apply_web_interaction 是「一步到位」：把给定配置校验后直接发布，跳过草稿。
rollback_web_interaction 回到上一个已发布版本。

并发：所有写工具都要 expected_revision，取自 get_web_interaction 的 revision；
版本不符后端返 web_interaction_revision_conflict（HTTP 409），重读后重写即可。

publish / apply 默认拒绝带 warnings 的配置；确认无碍时传 confirm_warnings=True 放行。

运行时通道（/web-interactions/runtime、runtime-events）属 UE 侧心跳，不在此封装。
"""

_BASE = "/api/v2/web-interactions"


def register(mcp, client, registry):

    @mcp.tool()
    def get_web_interaction() -> dict:
        """只读：当前项目的 Web 交互配置（含 revision、draft、published）。

        写任何配置前先调它拿 revision。
        """
        return client.get("get_web_interaction", _BASE)

    @mcp.tool()
    def validate_web_interaction(config: dict = None) -> dict:
        """只读：校验 Web 交互配置，返回 errors 与 warnings。

        config 省略时校验当前草稿。发布前先跑一遍：errors 非空则 publish 必失败。
        """
        body = {}
        if config is not None:
            body["config"] = config
        return client.post_json(
            "validate_web_interaction", f"{_BASE}/validate", json=body)

    @mcp.tool()
    def preview_web_interaction(source: str = "draft", config: dict = None) -> dict:
        """只读：解析配置里的数据绑定并返回预览结果，不写任何东西。

        source 取 draft（默认）或 published；显式给 config 时以 config 为准。
        """
        body = {"source": source}
        if config is not None:
            body["config"] = config
        return client.post_json(
            "preview_web_interaction", f"{_BASE}/resolve-preview", json=body)

    @mcp.tool()
    def save_web_interaction_draft(draft: dict, expected_revision: int) -> dict:
        """本操作会修改当前激活项目：保存 Web 交互草稿。

        只动草稿，运行时仍用已发布版本。expected_revision 取自 get_web_interaction。
        """
        return client.put_json(
            "save_web_interaction_draft", f"{_BASE}/draft",
            json={"draft": draft, "expected_revision": expected_revision})

    @mcp.tool()
    def publish_web_interaction(expected_revision: int,
                                confirm_warnings: bool = False) -> dict:
        """本操作会修改当前激活项目：把当前草稿发布为运行时生效版本。

        草稿有 errors 时拒绝发布；只有 warnings 时需 confirm_warnings=True 才放行。
        """
        body = {"expected_revision": expected_revision}
        if confirm_warnings:
            body["confirm_warnings"] = True
        return client.post_json(
            "publish_web_interaction", f"{_BASE}/publish", json=body)

    @mcp.tool()
    def apply_web_interaction(config: dict, expected_revision: int,
                              confirm_warnings: bool = False) -> dict:
        """本操作会修改当前激活项目：校验并直接发布给定配置（跳过草稿）。

        适合一次成型的整份配置；需要人工复核时改用 save_web_interaction_draft。
        """
        body = {"config": config, "expected_revision": expected_revision}
        if confirm_warnings:
            body["confirm_warnings"] = True
        return client.post_json(
            "apply_web_interaction", f"{_BASE}/apply", json=body)

    @mcp.tool()
    def rollback_web_interaction(expected_revision: int) -> dict:
        """本操作会修改当前激活项目：回滚到上一个已发布的 Web 交互配置。"""
        return client.post_json(
            "rollback_web_interaction", f"{_BASE}/rollback",
            json={"expected_revision": expected_revision})

    for f in (get_web_interaction, validate_web_interaction,
              preview_web_interaction, save_web_interaction_draft,
              publish_web_interaction, apply_web_interaction,
              rollback_web_interaction):
        registry[f.__name__] = f
