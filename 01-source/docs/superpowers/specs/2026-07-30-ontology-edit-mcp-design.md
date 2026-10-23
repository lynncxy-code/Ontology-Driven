# OntoTwin Nexus M4 —— 本体深编辑 MCP 扩展设计

> 「MCP 覆盖整个系统操作面」路线图第四个子项目（M4）。路线图 M1–M6。
> 前置：基础 30 + M1（20）+ M2（7）+ M3（9）= 66 工具，均已交付 main（M3 后端已部署 88.66）。

## 修订记录

- **v1（2026-07-30）**：首版。用户定：纳入 graph_from_registry、排除 fetch_api。沿用直通式 / 文档 A。

---

## 1. 目标与非目标

### 目标

把本体类型的**能力接口编辑**与**定义查询**开放给 MCP：

- **接口编辑**：给类型挂载 / 移除三维能力接口（I3D_Representable 及子接口 I3D_Spatial/Visual/Behavioral/Overlay）。
- **定义查询**：接口定义、属性定义、Neo4j 注册表、变换类型。
- **暂存图生成**：从 Neo4j 本体图库出暂存图（与基础层 `get_import_staging_graph` 读侧配对）。

### 非目标

- **排除 `POST /ontology/fetch_api`**：它代理拉取**外部任意 URL** 的图数据——让 AI 驱动服务器 fetch 任意 URL 属 SSRF 风险，不暴露。
- **后端零改动**：`inject`/`remove` 是**类型级配置写**（`_persist_active_project`，无 `expected_project_id`），与 M1 `enable_info_panel`（就是调 `/inject`）、M3 promote/clear_type（Option B）同口径。不碰 `backend/`。
- **不做 M5–M6**。

---

## 2. 架构

- 直通式；`register(mcp, client, registry)`；文档 A。
- **无并发键**：M4 全是类型级配置写或暂存图生成，沿用系统「单激活项目」模型，不透传 `expected_project_id`（与 M1 的 `enable_info_panel`、M3 的 promote 一致）。
- **client / errors / 后端 全零改动**：get/post_json/delete_json 已存在；错误映射（400→VALIDATION_ERROR、404→NOT_FOUND、503→DEGRADED、5xx→BACKEND_ERROR）已覆盖 M4 全部状态码。

---

## 3. 工具清单（7 个：4 读 + 3 写）→ MCP 66→73

### 3.1 接口编辑（2 写，类型级、无 expected）

| 工具 | 方法 + 端点 | 参数 | 请求 / 返回 |
|---|---|---|---|
| `inject_interfaces` | POST `/api/v2/ontology/inject` | `object_type_rid`, `interfaces:list`, `asset_id=""` | body `{object_type_rid, interfaces}` + 非空 `asset_id`；返回 `{object_type_rid, injected_interfaces, asset_id}`。子接口需先有 `I3D_Representable`（后端 400 校验）；合并追加、不覆盖 |
| `remove_interface` | DELETE `/api/v2/ontology/inject` | `object_type_rid`, `interface_rid` | body `{object_type_rid, interface_rid}`（delete_json）；移 `I3D_Representable` 级联清空子接口 + 清 asset |

> `inject_interfaces` 是通用版；M1 的 `enable_info_panel` 是它「固定注入 I3D_Representable+I3D_Overlay」的便捷特例，两者并存。

### 3.2 定义查询（4 读）

| 工具 | 方法 + 端点 | 返回 |
|---|---|---|
| `list_interface_defs` | GET `/api/v2/ontology/interfaces` | 全部能力接口定义（两层结构，静态常量） |
| `list_property_defs` | GET `/api/v2/ontology/properties` | 属性定义（静态常量） |
| `get_ontology_registry` | GET `/api/v2/ontology/registry` | Neo4j 注册表（不可达 503→`NEXUS_DEGRADED`） |
| `list_transform_types` | GET `/api/v2/transforms` | 变换类型（静态常量） |

### 3.3 暂存图生成（1 写：暂存态 compute）

| 工具 | 方法 + 端点 | 返回 |
|---|---|---|
| `build_staging_graph_from_registry` | POST `/api/v2/ontology/graph_from_registry` | `{status, node_count, link_count, category_count, graph_data}`；从 Neo4j 出图并写入暂存 `_custom_graph_data`（不落项目，与 `get_import_staging_graph` 读侧配对）。Neo4j 不可达 503→`NEXUS_DEGRADED` |

- 无 body。级别：暂存态生成（非项目持久化），低风险。

---

## 4. 错误映射 / client / 后端

**全零改动**。M4 涉及的状态码已被现有映射覆盖：
- inject 校验失败 400 → `NEXUS_VALIDATION_ERROR`；`object_type_rid` 不存在 404 → `NEXUS_NOT_FOUND`。
- registry / graph_from_registry 的 Neo4j 不可达 503 → `NEXUS_DEGRADED`（可重试提示，已在 M0 映射）。
- graph_from_registry 读图失败 500 → `NEXUS_BACKEND_ERROR`。
- client 用 get / post_json / delete_json（均已存在）。后端不动。

---

## 5. Skill 层（文档 A）

`mcp/skills/ontotwin-nexus/SKILL.md` 增「本体深编辑」段：

- **配能力**：`list_interface_defs()` 看有哪些接口 → `inject_interfaces(rid, ["I3D_Representable", "I3D_Spatial", ...])` 挂载（子接口必须同时/已有 I3D_Representable，否则 400）→ `remove_interface(rid, "I3D_Spatial")` 移除；移 `I3D_Representable` 会级联清空。
- **查定义**：`list_property_defs` / `list_transform_types` / `get_ontology_registry`（registry 走 Neo4j，不可达返回 `NEXUS_DEGRADED`，不影响其它功能）。
- **暂存图**：`build_staging_graph_from_registry()` 从图库出暂存图 → 基础层 `get_import_staging_graph()` 可读回；再走 `publish_ontology_dataset` 发布。
- 速查（A）：接口两层结构（顶层 `I3D_Representable` + 子 `I3D_Spatial/Visual/Behavioral/Overlay`）；具体定义以 `list_interface_defs` 返回为准。
- 触发示例：「给货架类型挂上 I3D_Representable 和 I3D_Spatial」「看看有哪些能力接口可选」「从图库重建暂存图」。

---

## 6. Repo 布局

```
mcp/ontotwin_mcp/tools/
  ontology_edit.py     # 新增：7 个本体深编辑工具
  __init__.py          # register_all 追加 ontology_edit
```
沿用 `register(mcp, client, registry)` + registry 尾注册。client/errors/后端 不改。

---

## 7. 测试策略

- **协议**：stdio 列表新增 7 工具全可见；`call_tool` 挑 `list_interface_defs` 走一遍。
- **单元（fake client）**：每工具断言 URL/方法/请求体；重点 `inject_interfaces` 的 body（`interfaces` + 非空 `asset_id` 才放入）、`remove_interface` 的 delete_json body。
- **只读冒烟**（88.66）：`list_interface_defs`、`list_property_defs`、`list_transform_types` 纳入 `selfcheck.py`（可无参、静态常量，稳定）；`get_ontology_registry` 依赖 Neo4j，不入冒烟（可能 503）。
- **写路径**：inject/remove 只对一次性抛弃类型验证，不碰生产库。

---

## 8. 交付里程碑（任务分组，供 writing-plans）

| 组 | 内容 | 独立可测 |
|---|---|---|
| A · ontology_edit | 7 个工具 + register + 单测 | ✅ |
| B · skill+冒烟 | SKILL.md 段 + selfcheck 3 读工具 + stdio 协议测试 | ✅ |

M4 最小：一个工具域 + 收口。无后端/errors/client 改动，故无独立"基座"任务。

---

## 9. 依赖与兼容

- **无新依赖**、**后端零改动**、**client/errors 零改动**。纯加法，现有 66 工具与测试不回归。
- MCP 工具总数 **66 → 73**。
- 无 PG 平价（不动后端）。

---

## 10. 风险科普

- **SSRF 为什么排除 fetch_api**：`fetch_api` 让后端去 GET 一个**调用方给的任意 URL**。若把它变成 AI 工具，AI（或注入 AI 的提示）就能驱动服务器访问内网任意地址（如 `http://169.254.169.254/` 云元数据、内网管理口），这是典型 SSRF。同类"出图"需求用 `build_staging_graph_from_registry`（只读本机 Neo4j）满足，不给外部 URL 入口。
- **接口的两层约束**：子接口（Spatial/Visual/Behavioral/Overlay）依赖顶层 `I3D_Representable`；这是后端强约束（缺则 400），直通式如实透传，skill 里点明先挂顶层。
