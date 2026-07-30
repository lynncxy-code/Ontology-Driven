"""OntoTwin MCP 基础只读链路冒烟检查（17 个代表性只读工具）——
不需要 AI 客户端、不需要 UE，一条命令验证「工具→后端」链路通。

注意：这是冒烟检查，只覆盖 17 个有代表性的只读工具，**不是全量工具覆盖**。
其余工具请按「测试指南.md」的提示词手册在 AI 客户端里逐一验证。

用法（在装好包的机器上）：
    python selfcheck.py
    # 后端不在默认 88.66：set NEXUS_BASE_URL=http://你的IP:5000  再跑
"""
import os, logging
logging.getLogger("httpx").setLevel(logging.WARNING)  # 静默 httpx 的逐条请求日志
from ontotwin_mcp.server import build_server

BASE = os.environ.get("NEXUS_BASE_URL", "http://192.168.88.66:5000")
mcp = build_server()          # 用真实 client 连后端
tools = mcp._ot_tools

def run(name, *args, **kwargs):
    try:
        r = tools[name](*args, **kwargs)
        print(f"[OK]   {name:26s} -> {str(r)[:110]}")
    except Exception as e:
        print(f"[ERR]  {name:26s} -> {type(e).__name__}: {str(e)[:100]}")

print(f"=== OntoTwin MCP 基础只读链路冒烟检查 · 17 个代表性只读工具（后端 {BASE}）===")
for t in [
    "get_active_project", "list_projects", "list_object_types",
    "get_import_staging_graph", "list_instances", "get_state_snapshots",
    "list_components", "list_roster", "get_spatial_profile", "get_ue_binding_status",
    "list_overlay_templates", "get_overlay_media_policy", "get_scene_catalog",
    "get_roaming_config", "list_routes", "list_reference_frames", "get_zones",
]:
    run(t)
print("=== 完成。[OK] = 工具经真实 HTTP 打到后端并拿到响应（内容随后端数据而异）===")
