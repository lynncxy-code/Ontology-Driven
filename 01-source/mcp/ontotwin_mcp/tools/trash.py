"""trash 域：回收站——删除项目 / 清空场景 / 删实例后的可恢复缓冲。

删除动作不直接抹掉数据，而是先落进回收站：

    list_trash            看有什么可恢复
    restore_trash_item    恢复到原位置（同 id 已存在时覆盖）
    delete_trash_item     从回收站彻底删掉一条（不可恢复）
    purge_trash           清空整个回收站（不可恢复）

条目分三类 kind：project（整个项目）、scene（一批实例，通常来自清空场景）、
instance（单个实例）。条目 id 是不透明字符串，从 list_trash 取，别自己拼。

两种后端行为不同，但接口一致：
- 文件后端：快照存在 data/trash/ 下，默认 90 天后自动清理；
- PG 后端：走表上的 deleted_at 软删除，不自动清理。
"""
from urllib.parse import quote

_BASE = "/api/v2/trash"


def register(mcp, client, registry):

    @mcp.tool()
    def list_trash() -> dict:
        """只读：回收站条目列表（kind、名称、删除时间、来源项目、实例数）。

        恢复或删除前先调它拿条目 id。
        """
        return client.get("list_trash", _BASE)

    @mcp.tool()
    def restore_trash_item(trash_id: str) -> dict:
        """本操作会修改数据：把回收站条目恢复到原位置。

        冲突策略是覆盖——同 id 的项目/实例已存在时会被这条快照盖掉，
        恢复前先确认目标不是你正在用的那份。trash_id 取自 list_trash。
        """
        return client.post_json(
            "restore_trash_item", f"{_BASE}/{quote(trash_id, safe='')}/restore")

    @mcp.tool()
    def delete_trash_item(trash_id: str) -> dict:
        """本操作不可恢复：把一条回收站条目彻底删除。

        删完这份快照就没了，确认不再需要再调。
        """
        return client.delete_json(
            "delete_trash_item", f"{_BASE}/{quote(trash_id, safe='')}")

    @mcp.tool()
    def purge_trash() -> dict:
        """本操作不可恢复：清空整个回收站，返回清掉的条数。

        所有待恢复的项目 / 场景 / 实例快照一次性抹掉，调用前务必先 list_trash 确认。
        """
        return client.post_json("purge_trash", f"{_BASE}/purge")

    for f in (list_trash, restore_trash_item, delete_trash_item, purge_trash):
        registry[f.__name__] = f
