"""scene 域：人物漫游 + 漫游路线读写。

读（read-only）：catalog / roaming / routes / route。
写（config-write，项目级持久化，expected_revision 必填）：save_roaming、
路线增删改 / 评审 / 设默认。

并发：写前先 get_roaming_config / list_routes / get_route 拿 revision，带
expected_revision 写回；遇 NEXUS_REVISION_CONFLICT 重读后重写。各写工具另有可选
expected_project_id，非空时把写操作绑定到指定项目身份，后端据此校验当前激活项目。
"""
from urllib.parse import quote

_ROUTES = "/api/v2/scene-interactions/routes"


def register(mcp, client, registry):

    @mcp.tool()
    def get_scene_catalog() -> dict:
        """只读：场景交互资源目录（可用帧 / 路线等）。"""
        return client.get("get_scene_catalog", "/api/v2/scene-interactions/catalog")

    @mcp.tool()
    def get_roaming_config() -> dict:
        """只读：人物漫游配置（含 revision、runtime_status、calibration_state、catalog_version）。"""
        return client.get("get_roaming_config", "/api/v2/scene-interactions/roaming")

    @mcp.tool()
    def list_routes() -> dict:
        """只读：漫游路线列表（含 default_route_id）。"""
        return client.get("list_routes", _ROUTES)

    @mcp.tool()
    def get_route(route_id: str) -> dict:
        """只读：单条漫游路线（含 revision）。"""
        return client.get("get_route", f"{_ROUTES}/{quote(route_id, safe='/')}")

    @mcp.tool()
    def save_roaming_config(config: dict, expected_revision: int,
                            expected_project_id: str = "") -> dict:
        """本操作会修改当前激活项目：保存人物漫游配置。

        expected_revision 取自 get_roaming_config 的 revision。
        expected_project_id 非空时把本次写绑定到指定项目身份。
        """
        body = {"config": config, "expected_revision": expected_revision}
        if expected_project_id:
            body["expected_project_id"] = expected_project_id
        return client.put_json(
            "save_roaming_config", "/api/v2/scene-interactions/roaming",
            json=body)

    @mcp.tool()
    def create_route(route: dict, expected_revision: int,
                     expected_project_id: str = "") -> dict:
        """本操作会修改当前激活项目：新建一条漫游路线。

        expected_revision 为路线集合版本，取自 list_routes / get_roaming_config。
        expected_project_id 非空时把本次写绑定到指定项目身份。
        """
        body = {"route": route, "expected_revision": expected_revision}
        if expected_project_id:
            body["expected_project_id"] = expected_project_id
        return client.post_json(
            "create_route", _ROUTES,
            json=body)

    @mcp.tool()
    def update_route(route_id: str, route: dict, expected_revision: int,
                     expected_project_id: str = "") -> dict:
        """本操作会修改当前激活项目：更新指定漫游路线。

        expected_project_id 非空时把本次写绑定到指定项目身份。
        """
        body = {"route": route, "expected_revision": expected_revision}
        if expected_project_id:
            body["expected_project_id"] = expected_project_id
        return client.put_json(
            "update_route", f"{_ROUTES}/{quote(route_id, safe='/')}",
            json=body)

    @mcp.tool()
    def delete_route(route_id: str, expected_revision: int,
                     expected_project_id: str = "") -> dict:
        """本操作会修改当前激活项目：删除指定漫游路线。

        expected_project_id 非空时把本次写绑定到指定项目身份。
        """
        body = {"expected_revision": expected_revision}
        if expected_project_id:
            body["expected_project_id"] = expected_project_id
        return client.delete_json(
            "delete_route", f"{_ROUTES}/{quote(route_id, safe='/')}",
            json=body)

    @mcp.tool()
    def review_route(route_id: str, expected_revision: int,
                     expected_project_id: str = "") -> dict:
        """本操作会修改当前激活项目：标记路线为已评审。

        expected_project_id 非空时把本次写绑定到指定项目身份。
        """
        body = {"expected_revision": expected_revision}
        if expected_project_id:
            body["expected_project_id"] = expected_project_id
        return client.post_json(
            "review_route", f"{_ROUTES}/{quote(route_id, safe='/')}/review",
            json=body)

    @mcp.tool()
    def set_default_route(route_id: str, expected_revision: int,
                          expected_project_id: str = "") -> dict:
        """本操作会修改当前激活项目：设为人物漫游默认路线。

        expected_project_id 非空时把本次写绑定到指定项目身份。
        """
        body = {"expected_revision": expected_revision}
        if expected_project_id:
            body["expected_project_id"] = expected_project_id
        return client.post_json(
            "set_default_route", f"{_ROUTES}/{quote(route_id, safe='/')}/default",
            json=body)

    for f in (get_scene_catalog, get_roaming_config, list_routes, get_route,
              save_roaming_config, create_route, update_route, delete_route,
              review_route, set_default_route):
        registry[f.__name__] = f
