"""project 域工具：数据集（项目）列举 / 激活态归一化 / 激活 / 新建。"""


def register(mcp, client, registry):
    @mcp.tool()
    def list_projects() -> list:
        """列出所有项目（数据集），含 is_active 标记。只读。"""
        return client.get("list_projects", "/api/v2/ontology/datasets")

    @mcp.tool()
    def get_active_project() -> dict:
        """返回当前激活项目的归一化视图 {dataset_id,dataset_name,project_id,writable,kind}。只读。

        writable=true 仅当激活的是真实项目（非内置 demo）；写工具前应先调它确认 writable。
        kind 取值：project（真实项目）/ demo（内置只读）/ none（无激活）。
        """
        rows = client.get("get_active_project", "/api/v2/ontology/datasets")
        active = next((r for r in rows if r.get("is_active")), None)
        if not active:
            return {"dataset_id": None, "dataset_name": None, "project_id": None,
                    "writable": False, "kind": "none"}
        is_demo = active.get("id") == "demo"
        return {
            "dataset_id": active.get("id"),
            "dataset_name": active.get("name"),
            "project_id": None if is_demo else active.get("id"),
            "writable": not is_demo,
            "kind": "demo" if is_demo else "project",
        }

    @mcp.tool()
    def activate_project(dataset_id: str) -> dict:
        """会改全局激活态（persist）：把指定数据集设为当前激活项目。高危，一切工具只认当前激活项目。

        激活已有项目为只读操作，不覆盖其类型能力配置。
        """
        return client.post_json(
            "activate_project", "/api/v2/ontology/datasets/activate",
            json={"dataset_id": dataset_id},
        )

    @mcp.tool()
    def create_empty_project(name: str) -> dict:
        """会新增一条数据集记录（persist）：新建空数据集，固定不切换激活态（activate=false）。

        类型库需另经 import→publish→activate 流程填充。
        """
        return client.post_json(
            "create_empty_project", "/api/v2/ontology/datasets",
            json={"name": name, "activate": False},
        )

    @mcp.tool()
    def list_scenes() -> dict:
        """只读：所有项目的实例侧概况（各项目实例数、分区数、未分区数、UE 绑定）。

        与 list_projects 的区别：那个从数据集角度看类型库，这个从实例角度看场景规模，
        清理前拿它判断哪个项目是空的。
        """
        return client.get("list_scenes", "/api/v2/scenes")

    @mcp.tool()
    def clear_scene() -> dict:
        """本操作会修改当前激活项目：清空其全部实例（保留项目与类型库）。

        高危：一次抹掉当前项目所有实例，UE 轮询到后会销毁对应孪生体。
        实例会进回收站（list_trash 可见、restore_trash_item 可整批恢复），
        但类型能力配置与坐标标定不受影响。执行前先 get_active_project 确认切对了项目。
        """
        return client.post_json("clear_scene", "/api/v2/scene/clear")

    for f in (list_projects, get_active_project, activate_project,
              create_empty_project, list_scenes, clear_scene):
        registry[f.__name__] = f
