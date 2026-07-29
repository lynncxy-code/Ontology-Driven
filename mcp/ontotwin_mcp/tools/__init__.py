"""工具注册：各域 register(mcp, client, registry) 依次挂载到 FastMCP。

registry（挂在 mcp._ot_tools）保存 {工具名: 裸函数}，供单测直调裸函数、
以及跨域工具（如 ontology 缺省数据集回退到 get_active_project）复用。
"""

from . import project, ontology, runtime, cad


def register_all(mcp, client):
    registry = {}
    for mod in (project, ontology, runtime, cad):
        mod.register(mcp, client, registry)
    mcp._ot_tools = registry
    return registry
