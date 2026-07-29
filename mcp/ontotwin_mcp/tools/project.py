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
    def activate_project(dataset_id: str, expected_current: str = "") -> dict:
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

    for f in (list_projects, get_active_project, activate_project, create_empty_project):
        registry[f.__name__] = f
