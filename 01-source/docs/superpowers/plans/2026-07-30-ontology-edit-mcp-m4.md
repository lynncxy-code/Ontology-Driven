# M4 本体深编辑 MCP 扩展 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. Steps use checkbox (`- [ ]`) syntax.

**Goal:** 给 MCP 新增 7 工具（4 读 + 3 写）：类型能力接口挂载/移除、接口/属性/注册表/变换定义查询、从 Neo4j 生成暂存图。

**Architecture:** 纯 `mcp/` 转译层，沿用直通式 + `register(mcp, client, registry)`。`inject`/`remove` 是类型级配置写（后端 `_persist_active_project`，无 `expected_project_id`，与 M1 `enable_info_panel`、M3 promote 同口径）。**后端/client/errors 全零改动**（400/404/503 映射已覆盖）。排除 `fetch_api`（SSRF）。

**Tech Stack:** Python 3.10、`mcp`（FastMCP）、`httpx`；pytest（fake client + `create_connected_server_and_client_session`）。

## Global Constraints

- **后端零改动 + client 零改动 + errors 零改动**：只动 `mcp/`（tools/、tests/、selfcheck.py、SKILL.md）。
- **无新依赖**。**纯加法**：现有 66 工具及测试不回归。
- **无并发键**：M4 全是类型级配置写 / 暂存图生成，不透传 `expected_project_id`。
- **直通式**：不重塑后端响应。docstring 中文；写工具首句 `本操作会修改当前激活项目：...`（`build_staging_graph_from_registry` 例外——它不落项目，首句用「从 Neo4j 本体图库生成暂存图…」）；读工具 `只读：...`。
- **无路径参数**：M4 所有端点是固定路径 + body/无 body，工具里**不需要** `quote`。
- **注册惯例**：`for f in (...): registry[f.__name__] = f`。

---

### Task 1: ontology_edit 域（7 工具）

**Files:**
- Create: `mcp/ontotwin_mcp/tools/ontology_edit.py`
- Modify: `mcp/ontotwin_mcp/tools/__init__.py`
- Test: `mcp/tests/test_tools_ontology_edit.py`

**Interfaces:**
- Consumes: `client.get/post_json/delete_json`。
- Produces（工具名 → 端点）：
  - `list_interface_defs()` → GET `/api/v2/ontology/interfaces`
  - `list_property_defs()` → GET `/api/v2/ontology/properties`
  - `get_ontology_registry()` → GET `/api/v2/ontology/registry`
  - `list_transform_types()` → GET `/api/v2/transforms`
  - `inject_interfaces(object_type_rid, interfaces, asset_id="")` → POST `/api/v2/ontology/inject`，body `{object_type_rid, interfaces}`（+ 非空 `asset_id`）
  - `remove_interface(object_type_rid, interface_rid)` → DELETE `/api/v2/ontology/inject`（delete_json），body `{object_type_rid, interface_rid}`
  - `build_staging_graph_from_registry()` → POST `/api/v2/ontology/graph_from_registry`（无 body）

- [ ] **Step 1: 写失败测试** `mcp/tests/test_tools_ontology_edit.py`

```python
"""ontology_edit 工具单测（fake client）。"""
from ontotwin_mcp.server import build_server


class C:
    def __init__(self):
        self.calls = []

    def get(self, op, path, params=None):
        self.calls.append(("get", path, params)); return {"ok": True}

    def post_json(self, op, path, json=None, timeout=None):
        self.calls.append(("post", path, json)); return {"status": "ok"}

    def delete_json(self, op, path, json=None, timeout=None):
        self.calls.append(("delete", path, json)); return {"status": "ok"}


def _t(mcp, name):
    return mcp._ot_tools[name]


def test_read_defs_endpoints():
    c = C(); mcp = build_server(c)
    _t(mcp, "list_interface_defs")()
    _t(mcp, "list_property_defs")()
    _t(mcp, "get_ontology_registry")()
    _t(mcp, "list_transform_types")()
    paths = [call[1] for call in c.calls]
    assert paths == [
        "/api/v2/ontology/interfaces", "/api/v2/ontology/properties",
        "/api/v2/ontology/registry", "/api/v2/transforms",
    ]


def test_inject_interfaces_body_minimal():
    c = C(); mcp = build_server(c)
    _t(mcp, "inject_interfaces")("rid.a", ["I3D_Representable", "I3D_Spatial"])
    method, path, body = c.calls[-1]
    assert method == "post" and path == "/api/v2/ontology/inject"
    assert body == {"object_type_rid": "rid.a",
                    "interfaces": ["I3D_Representable", "I3D_Spatial"]}
    assert "asset_id" not in body


def test_inject_interfaces_with_asset():
    c = C(); mcp = build_server(c)
    _t(mcp, "inject_interfaces")("rid.a", ["I3D_Representable"], asset_id="m1")
    body = c.calls[-1][2]
    assert body == {"object_type_rid": "rid.a",
                    "interfaces": ["I3D_Representable"], "asset_id": "m1"}


def test_remove_interface_delete_body():
    c = C(); mcp = build_server(c)
    _t(mcp, "remove_interface")("rid.a", "I3D_Spatial")
    method, path, body = c.calls[-1]
    assert method == "delete" and path == "/api/v2/ontology/inject"
    assert body == {"object_type_rid": "rid.a", "interface_rid": "I3D_Spatial"}


def test_build_staging_graph_from_registry_endpoint():
    c = C(); mcp = build_server(c)
    _t(mcp, "build_staging_graph_from_registry")()
    method, path, body = c.calls[-1]
    assert method == "post" and path == "/api/v2/ontology/graph_from_registry"


def test_ontology_edit_tools_registered():
    c = C(); mcp = build_server(c)
    expected = {
        "list_interface_defs", "list_property_defs", "get_ontology_registry",
        "list_transform_types", "inject_interfaces", "remove_interface",
        "build_staging_graph_from_registry",
    }
    assert expected <= set(mcp._ot_tools)
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd mcp && python -m pytest tests/test_tools_ontology_edit.py -v`
Expected: FAIL（未注册）

- [ ] **Step 3: 建 `mcp/ontotwin_mcp/tools/ontology_edit.py`**

```python
"""ontology_edit 域：本体类型能力接口编辑 + 定义查询 + 暂存图生成。

inject/remove 是类型级配置写（无 expected，与 enable_info_panel/promote 同口径）；
定义查询只读；build_staging_graph_from_registry 从 Neo4j 出暂存图（不落项目）。
排除 fetch_api（SSRF：外部任意 URL 拉取）。
"""


def register(mcp, client, registry):

    @mcp.tool()
    def list_interface_defs() -> dict:
        """只读：全部三维能力接口定义（两层结构：I3D_Representable + 子接口）。"""
        return client.get("list_interface_defs", "/api/v2/ontology/interfaces")

    @mcp.tool()
    def list_property_defs() -> dict:
        """只读：本体属性定义。"""
        return client.get("list_property_defs", "/api/v2/ontology/properties")

    @mcp.tool()
    def get_ontology_registry() -> dict:
        """只读：从 Neo4j 本体图库读取注册表（不可达返回 NEXUS_DEGRADED）。"""
        return client.get("get_ontology_registry", "/api/v2/ontology/registry")

    @mcp.tool()
    def list_transform_types() -> dict:
        """只读：可用的变换类型定义。"""
        return client.get("list_transform_types", "/api/v2/transforms")

    @mcp.tool()
    def inject_interfaces(object_type_rid: str, interfaces: list,
                          asset_id: str = "") -> dict:
        """本操作会修改当前激活项目：给类型挂载三维能力接口（合并追加，不覆盖）。

        子接口（I3D_Spatial/Visual/Behavioral/Overlay）需先有或同时挂 I3D_Representable，
        否则后端 400。可选 asset_id 一并保存为该类型资产。
        """
        body = {"object_type_rid": object_type_rid, "interfaces": interfaces}
        if asset_id:
            body["asset_id"] = asset_id
        return client.post_json("inject_interfaces", "/api/v2/ontology/inject", json=body)

    @mcp.tool()
    def remove_interface(object_type_rid: str, interface_rid: str) -> dict:
        """本操作会修改当前激活项目：从类型移除一个能力接口。

        移除 I3D_Representable 会级联清空所有子接口并清空该类型资产。
        """
        return client.delete_json(
            "remove_interface", "/api/v2/ontology/inject",
            json={"object_type_rid": object_type_rid, "interface_rid": interface_rid})

    @mcp.tool()
    def build_staging_graph_from_registry() -> dict:
        """从 Neo4j 本体图库生成暂存图（写入暂存区，不落项目）。

        产出 {nodes, links, categories}，可用 get_import_staging_graph 读回，再
        publish_ontology_dataset 发布。Neo4j 不可达返回 NEXUS_DEGRADED。
        """
        return client.post_json(
            "build_staging_graph_from_registry",
            "/api/v2/ontology/graph_from_registry")

    for f in (list_interface_defs, list_property_defs, get_ontology_registry,
              list_transform_types, inject_interfaces, remove_interface,
              build_staging_graph_from_registry):
        registry[f.__name__] = f
```

- [ ] **Step 4: 挂进 `register_all`**（`tools/__init__.py`；追加 `ontology_edit`）

```python
from . import (project, ontology, runtime, cad, binding, phase2,
               overlay, scene, spatial, zones, lifecycle, model_binding,
               ontology_edit)


def register_all(mcp, client):
    registry = {}
    for mod in (project, ontology, runtime, cad, binding, phase2,
                overlay, scene, spatial, zones, lifecycle, model_binding,
                ontology_edit):
        mod.register(mcp, client, registry)
    mcp._ot_tools = registry
    return registry
```

- [ ] **Step 5: 跑测试确认通过 + 全量不回归**

Run: `cd mcp && python -m pytest tests/test_tools_ontology_edit.py tests/test_stdio.py -v`
Expected: PASS

- [ ] **Step 6: 提交**

```bash
git add mcp/ontotwin_mcp/tools/ontology_edit.py mcp/ontotwin_mcp/tools/__init__.py mcp/tests/test_tools_ontology_edit.py
git commit -m "feat(mcp): ontology_edit 域 7 工具（接口注入/移除、定义查询、暂存图生成）"
```

---

### Task 2: 协议冒烟 + selfcheck + skill 文档

**Files:**
- Modify: `mcp/tests/test_stdio.py`
- Modify: `mcp/selfcheck.py`
- Modify: `mcp/skills/ontotwin-nexus/SKILL.md`

**Interfaces:**
- Consumes: Task 1 注册的工具。
- Produces：协议层验证 7 新工具可 list/call；selfcheck 读工具补 3 个；skill 增「本体深编辑」段。

- [ ] **Step 1: 写失败测试**（追加到 `test_stdio.py`）

```python
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
```

- [ ] **Step 2: 跑测试确认（Task 1 已完成则直接 PASS，属预期）**

Run: `cd mcp && python -m pytest tests/test_stdio.py -k ontology_edit -v`
Expected: PASS（7 工具已注册；回归守卫）

- [ ] **Step 3: selfcheck 补 3 个只读冒烟工具**（`mcp/selfcheck.py`）

工具列表尾部追加 `list_interface_defs`, `list_property_defs`, `list_transform_types`（现共 20 个；`get_ontology_registry` 依赖 Neo4j 可能 503，不入），并把 print 的「17 个」改为「20 个」：

```python
for t in [
    "get_active_project", "list_projects", "list_object_types",
    "get_import_staging_graph", "list_instances", "get_state_snapshots",
    "list_components", "list_roster", "get_spatial_profile", "get_ue_binding_status",
    "list_overlay_templates", "get_overlay_media_policy", "get_scene_catalog",
    "get_roaming_config", "list_routes", "list_reference_frames", "get_zones",
    "list_interface_defs", "list_property_defs", "list_transform_types",
]:
    run(t)
```
```python
print(f"=== OntoTwin MCP 基础只读链路冒烟检查 · 20 个代表性只读工具（后端 {BASE}）===")
```
（顶部 docstring 的「17 个」措辞可一并改为「20 个」，非必须。）

- [ ] **Step 4: skill 增「本体深编辑」段**（`mcp/skills/ontotwin-nexus/SKILL.md`）

先 Read 现有 SKILL.md，在「实例生命周期 / 换模型」段之后追加（文档 A）：

````markdown
## 本体深编辑（能力接口 / 定义 / 暂存图）

**配能力接口**
- `list_interface_defs()` 看有哪些接口 → `inject_interfaces(rid, ["I3D_Representable", "I3D_Spatial", ...])` 挂载（合并追加）。子接口（Spatial/Visual/Behavioral/Overlay）必须已有或同时挂 `I3D_Representable`，否则 400。
- `remove_interface(rid, "I3D_Spatial")` 移除；移 `I3D_Representable` 会级联清空所有子接口 + 清资产。
- 注：`enable_info_panel(rid)` 是「注入 I3D_Representable + I3D_Overlay」的便捷特例；要挂别的接口用 `inject_interfaces`。

**查定义**
- `list_property_defs()` / `list_transform_types()`（静态定义）；`get_ontology_registry()`（Neo4j 注册表，不可达返回 `NEXUS_DEGRADED`，不影响其它功能）。

**暂存图**
- `build_staging_graph_from_registry()` 从图库出暂存图 → `get_import_staging_graph()` 读回 → `publish_ontology_dataset(name)` 发布。

**触发示例**
- 「给货架类型挂上 I3D_Representable 和 I3D_Spatial」
- 「看看有哪些能力接口可以挂」
- 「从本体图库重建暂存图并发布成新数据集」
````

- [ ] **Step 5: 跑全量测试确认通过**

Run: `cd mcp && python -m pytest tests/ -v`
Expected: PASS（全绿）

- [ ] **Step 6: 提交**

```bash
git add mcp/tests/test_stdio.py mcp/selfcheck.py mcp/skills/ontotwin-nexus/SKILL.md
git commit -m "feat(mcp): 本体深编辑协议冒烟 + selfcheck 补读工具 + skill playbook"
```

---

## 交付后（人工，可选）

- 重打发行包：`mcp/build-dist.ps1`。
- 真机只读冒烟：`python selfcheck.py`，确认新增 3 个读工具对 88.66 `[OK]`。
- 写路径（inject/remove）只对一次性抛弃类型验证，不碰生产库。**M4 后端零改动，无需部署。**

---

## Self-Review 记录

- **Spec 覆盖**：spec §3 的 7 工具 ↔ Task 1；§5 skill ↔ Task 2 Step 4；§7 测试三层 ↔ Task 1/2。后端/client/errors 零改动（无对应任务，符合 spec §4）。
- **类型一致**：`asset_id: str=""`（非空入 body）；`interfaces: list`；无 expected_project_id（M4 无并发键）。
- **占位符扫描**：无 TBD；每 code step 含完整代码。
- **无路径参数**：确认 M4 所有端点固定路径，工具无 `quote`（与含路径参数的 M1–M3 不同）。
- **命名无冲突**：7 个新名与现有 66 工具无交集（`enable_info_panel` 是 M1 的，`inject_interfaces` 是新的通用版）。
