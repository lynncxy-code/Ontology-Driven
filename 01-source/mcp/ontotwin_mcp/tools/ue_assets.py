"""ue_assets 域：UE 工程的资产目录与「类型 → 资产」推荐记忆。

目录由 UE 侧插件盘点后同步上来（一个 UE 工程一份，按 ue_project_id 隔离），
用途是给本体类型选模型时提供候选：

    get_ue_asset_catalog          看某个 UE 工程已同步的资产清单
    recommend_ue_assets           给一批类型/块名要推荐资产，带打分与理由
    remember_ue_asset_selections  记住人工确认的对应关系，下次推荐置顶
    replace_ue_asset_catalog      整表替换目录（通常由 UE 插件调，人工少用）

推荐分数的来源：曾人工确认（1.0）> 命中旧版对应记录（0.9）> 名称相似度。
所以 remember 用得越多，recommend 越准。

注意 ue_project_id 是 UE 工程身份（形如 ueproj_XXX），不是 Nexus 的项目 id。
省略它时后端回落到「当前激活项目所绑的 UE 工程」；若该项目还没绑过 UE，
会返回 409 ue_project_not_bound——这不是故障，是提示你要么显式传 ue_project_id，
要么先让 UE 侧完成一次工程绑定（get_ue_binding_status 可查当前绑定态）。
"""

_BASE = "/api/v2/ue/assets"


def register(mcp, client, registry):

    @mcp.tool()
    def get_ue_asset_catalog(ue_project_id: str = "") -> dict:
        """只读：某 UE 工程已同步的资产目录（含 supported 标记与统计）。

        ue_project_id 省略时用服务端缺省工程。
        """
        params = {"ue_project_id": ue_project_id} if ue_project_id else None
        return client.get("get_ue_asset_catalog", f"{_BASE}/catalog", params=params)

    @mcp.tool()
    def recommend_ue_assets(items: list, ue_project_id: str = "",
                            limit: int = 3) -> dict:
        """只读：为一批类型/块名推荐 UE 资产，返回候选与打分理由。

        items 每项形如 {"block_name": "CNC", "preset_asset_id": "..."}（后者可选）。
        单次最多 200 项，limit 取 1~10（默认 3）。不写任何东西，选中后要
        remember_ue_asset_selections 才会被记住。
        """
        body = {"items": items, "limit": limit}
        if ue_project_id:
            body["ue_project_id"] = ue_project_id
        return client.post_json("recommend_ue_assets", f"{_BASE}/recommend", json=body)

    @mcp.tool()
    def remember_ue_asset_selections(selections: list,
                                     ue_project_id: str = "") -> dict:
        """本操作会修改 UE 资产目录：记住人工确认的「类型 → 资产」对应。

        selections 每项形如 {"block_name": "CNC", "object_path": "/Game/..."}。
        只有目录里 supported=true 的资产才会被记住；下次 recommend 时置顶。
        """
        body = {"selections": selections}
        if ue_project_id:
            body["ue_project_id"] = ue_project_id
        return client.post_json(
            "remember_ue_asset_selections", f"{_BASE}/confirmations", json=body)

    @mcp.tool()
    def replace_ue_asset_catalog(assets: list, ue_project_id: str) -> dict:
        """本操作会整表替换 UE 资产目录：用给定清单覆盖该工程的全部资产。

        通常由 UE 插件盘点后自动调用；人工调用前先 get_ue_asset_catalog 确认要覆盖的
        是哪一份。ue_project_id 必填且要与目录归属一致，否则后端返 409。
        单次最多同步 5000 个资产。
        """
        return client.post_json(
            "replace_ue_asset_catalog", f"{_BASE}/catalog",
            json={"ue_project_id": ue_project_id, "assets": assets})

    for f in (get_ue_asset_catalog, recommend_ue_assets,
              remember_ue_asset_selections, replace_ue_asset_catalog):
        registry[f.__name__] = f
