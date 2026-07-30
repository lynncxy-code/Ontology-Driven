"""MCP 协议端到端测试（真走 initialize → list_tools → call_tool）。

用 mcp 1.29.0 官方 in-memory 传输 `create_connected_server_and_client_session`，
不起子进程：把 FastMCP 的低层 Server（`mcp._mcp_server`）接一对内存流给
`ClientSession`，客户端与服务端在同进程内跑真 JSON-RPC 握手与工具调用。

后端用注入的 FakeClient 回放假数据，不打真 HTTP。
"""
import json

import pytest
from mcp.shared.memory import create_connected_server_and_client_session

from ontotwin_mcp.server import build_server


class FakeClient:
    """回放路由响应；不起真 HTTP，仅用于协议层 call_tool 冒烟。"""

    def __init__(self, routes=None):
        self.routes = routes or {}

    def get(self, op, path, params=None):
        return self.routes.get(path, [])

    def post_json(self, op, path, json=None, timeout=None):
        return self.routes.get(path, {})

    def post_multipart(self, op, path, files, data=None, timeout=None):
        return self.routes.get(path, {})


# 核心工具必须全部注册（≥22：15 读 + 7 写；实际 30，含 3 个二期只读工具）
CORE_TOOLS = {
    "get_active_project",
    "mint_instances",
    "save_components",
    "list_instances",
    "upload_roster",
    "import_ontology_csv",
}


async def test_initialize_and_list_tools_has_core():
    """协议握手后 list_tools 断言核心工具都在，总数 ≥ 22。"""
    mcp = build_server(FakeClient())
    async with create_connected_server_and_client_session(mcp._mcp_server) as session:
        # initialize 握手在进入上下文时已发生；显式再跑一次确保协议就绪
        result = await session.list_tools()
        names = {t.name for t in result.tools}

    assert CORE_TOOLS <= names, f"缺工具: {CORE_TOOLS - names}"
    assert len(names) >= 22, f"工具总数应 ≥22，实际 {len(names)}"


async def test_explicit_initialize_returns_server_info():
    """显式 initialize 返回服务器信息（server name = ontotwin）。"""
    mcp = build_server(FakeClient())
    async with create_connected_server_and_client_session(mcp._mcp_server) as session:
        init = await session.initialize()
    assert init.serverInfo.name == "ontotwin"


async def test_call_tool_readonly_list_instances():
    """挑一个只读工具走真 call_tool，后端注入假数据，断言无错且透传。"""
    mcp = build_server(FakeClient({"/api/v2/instances": [{"id": "i1"}]}))
    async with create_connected_server_and_client_session(mcp._mcp_server) as session:
        res = await session.call_tool("list_instances", {})

    assert res.isError is False
    # FastMCP 把 list 结果按元素拆成多个 content 块，这里 1 个实例 → 1 块
    assert len(res.content) == 1
    payload = json.loads(res.content[0].text)
    assert payload == {"id": "i1"}


async def test_call_tool_readonly_get_active_project():
    """再挑一个只读工具（返回 dict）走 call_tool，断言归一化结果。"""
    mcp = build_server(
        FakeClient(
            {"/api/v2/ontology/datasets": [{"id": "p1", "name": "厂", "is_active": True}]}
        )
    )
    async with create_connected_server_and_client_session(mcp._mcp_server) as session:
        res = await session.call_tool("get_active_project", {})

    assert res.isError is False
    payload = json.loads(res.content[0].text)
    assert payload["writable"] is True
    assert payload["project_id"] == "p1"


async def test_scene_config_tools_listed_and_callable():
    """场景配置 20 工具全部注册；挑一个只读工具走真 call_tool。"""
    routes = {"/api/v2/overlays/templates": {"templates": []}}
    mcp = build_server(FakeClient(routes))
    async with create_connected_server_and_client_session(mcp._mcp_server) as session:
        names = {t.name for t in (await session.list_tools()).tools}
        res = await session.call_tool("list_overlay_templates", {})

    new_tools = {
        "list_overlay_templates", "get_overlay_context", "preview_overlay",
        "get_overlay_media_policy", "enable_info_panel", "save_overlay_type_config",
        "save_overlay_instance_override", "clear_overlay_instance_override",
        "batch_overlay_instance_override", "save_overlay_media_policy",
        "get_scene_catalog", "get_roaming_config", "list_routes", "get_route",
        "save_roaming_config", "create_route", "update_route", "delete_route",
        "review_route", "set_default_route",
    }
    assert new_tools <= names, f"缺工具: {new_tools - names}"
    assert len(names) >= 50, f"工具总数应 ≥50（30+20），实际 {len(names)}"
    assert res.isError is False


async def test_spatial_zones_tools_listed_and_callable():
    """M2 空间/分区 7 工具全部注册；挑一个只读工具走真 call_tool。"""
    routes = {"/api/v2/spatial-frames": {"project_id": "p1", "frames": []}}
    mcp = build_server(FakeClient(routes))
    async with create_connected_server_and_client_session(mcp._mcp_server) as session:
        names = {t.name for t in (await session.list_tools()).tools}
        res = await session.call_tool("list_reference_frames", {})

    new_tools = {
        "create_reference_frame", "list_reference_frames", "get_reference_frame",
        "save_reference_frame_draft", "publish_reference_frame",
        "get_zones", "assign_zones",
    }
    assert new_tools <= names, f"缺工具: {new_tools - names}"
    assert len(names) >= 57, f"工具总数应 ≥57（50+7），实际 {len(names)}"
    assert res.isError is False


async def test_lifecycle_model_binding_tools_listed_and_callable():
    """M3 生命周期/换模型 9 工具全部注册；挑一个只读工具走真 call_tool。"""
    routes = {"/api/v2/instances/i1/model-binding": {"instance_id": "i1"}}
    mcp = build_server(FakeClient(routes))
    async with create_connected_server_and_client_session(mcp._mcp_server) as session:
        names = {t.name for t in (await session.list_tools()).tools}
        res = await session.call_tool("get_model_binding", {"instance_id": "i1"})

    new_tools = {
        "create_instance", "delete_instance", "set_instance_transform",
        "writeback_instance_transform", "get_model_binding", "set_model_binding",
        "clear_model_binding", "clear_type_model_default", "promote_model_binding",
    }
    assert new_tools <= names, f"缺工具: {new_tools - names}"
    assert len(names) >= 66, f"工具总数应 ≥66（57+9），实际 {len(names)}"
    assert res.isError is False


async def test_ontology_edit_tools_listed_and_callable():
    """M4 本体深编辑 7 工具全部注册；挑一个只读工具走真 call_tool。"""
    routes = {"/api/v2/ontology/interfaces": {"interfaces": []}}
    mcp = build_server(FakeClient(routes))
    async with create_connected_server_and_client_session(mcp._mcp_server) as session:
        names = {t.name for t in (await session.list_tools()).tools}
        res = await session.call_tool("list_interface_defs", {})

    new_tools = {
        "list_interface_defs", "list_property_defs", "get_ontology_registry",
        "list_transform_types", "inject_interfaces", "remove_interface",
        "build_staging_graph_from_registry",
    }
    assert new_tools <= names, f"缺工具: {new_tools - names}"
    assert len(names) >= 73, f"工具总数应 ≥73（66+7），实际 {len(names)}"
    assert res.isError is False
