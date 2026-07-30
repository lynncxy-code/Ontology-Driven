# OntoTwin Nexus M1 —— 场景配置 MCP 扩展设计（信息面板 / 人物漫游 / 漫游路线）

> 本设计是「MCP 覆盖整个系统操作面」路线图的第一个子项目（M1）。路线图共 M1–M6，本 spec 只覆盖 M1。
> 前置：`docs/superpowers/specs/2026-07-29-ontotwin-mcp-design.md`（基础 MCP 层，30 工具，已交付到 main）。

## 修订记录

- **v1（2026-07-30）**：首版。设计三决定已在 brainstorm 阶段与用户敲定 —— 直通式写工具 / 显式 `expected_revision` / 文档粒度 A（速查 + 活样例，后端为唯一真源）。

---

## 1. 目标与非目标

### 目标

把 Nexus 三块场景配置菜单开放给 MCP，使 AI 可读可写：

- **信息面板**（overlay）：类型级 / 实例级面板配置、批量覆盖、清除覆盖、预览、媒体域名策略、启用面板能力。
- **人物漫游**（roaming）：读取 / 保存漫游配置。
- **漫游路线**（routes）：路线增删改查、评审、设默认。

### 非目标（本轮不做）

- **后端零改动**：三块背后的 `backend/overlay/` 与 `backend/scene_interaction/` 蓝图**已具备完整 `revision` 乐观锁 + validator**，本轮纯 MCP 转译层，不碰 `backend/`（区别于 M0 的方案 B 后端扩展）。
- **UE 专用端点不做**：`POST /scene-interactions/runtime`（强制 UE 工程身份的运行心跳）、`GET /scene-interactions/runtime`（UE 运行投影）、`POST /overlays/media/resolve`（UE 侧媒体解析）——均属 UE 运行时，非 AI 配置面。
- **不做 M2–M6**：空间/分区、实例生命周期、本体深编辑、CAD 交互标定、floor_pulse，各自独立 spec。

---

## 2. 架构

- **同构于基础层**：沿用 `NexusClient` + `tools/*.py`（`register(mcp, client, registry)`）+ `_ot_tools` registry + stdio 入口，不新建运行时机制。
- **直通式（passthrough）写工具**：写工具读出当前 config → 调用方（AI）改整份结构 → 带 `expected_revision` 写回。后端 validator 是唯一结构真源，非法结构由后端 422 拦截。
- **显式并发**：所有写工具的 `expected_revision` 为**必填**参数（无静默默认 0），强制「先读后写」。读工具把治理用的 revision 一并返回。
- **revision 兼作跨项目护栏**：overlay / scene 的 revision 绑定在「当前激活项目的这份配置」上；项目一旦被切走，旧 revision 必然对不上 → 409。故本批工具**无需**再单独透传 `expected_project_id`（与 M0 写工具不同）。

---

## 3. 工具清单（20 个：8 读 + 12 写）

### 3.1 操作分级

| 级别 | 工具 | 审批建议 |
|---|---|---|
| **read-only** | 8 个读工具 | 可默认自动执行 |
| **config-write（项目级持久化）** | 12 个写工具 | 高危；默认需人工审批，不进默认自动编排 |

### 3.2 信息面板（overlay）——10 个

| 工具 | 方法 + 端点 | 级别 | 参数 | 返回要点 |
|---|---|---|---|---|
| `list_overlay_templates` | GET `/overlays/templates` | read | — | `{templates:[...]}` |
| `get_overlay_context` | GET `/overlays/context` | read | `object_type_rid=""`, `instance_id=""` | `{object_type, type_config{revision,config}, instance_override{revision}, instances[{id,override_revision}], media_policy{revision}}` |
| `preview_overlay` | POST `/overlays/preview` | read（纯计算） | `object_type_rid=""`, `instance_id=""`, `config=None` | `{preview}` |
| `get_overlay_media_policy` | GET `/overlays/media/policy` | read | — | `{...revision}` |
| `enable_info_panel` | POST `/ontology/inject` | write | `object_type_rid` | 注入 `I3D_Representable`+`I3D_Overlay`；幂等 |
| `save_overlay_type_config` | PUT `/overlays/object-types/<rid>` | write | `object_type_rid`, `config`, `expected_revision` | `{status, config{revision}}` |
| `save_overlay_instance_override` | PUT `/overlays/instances/<id>` | write | `instance_id`, `override`, `expected_revision` | `{status, override{revision}}` |
| `clear_overlay_instance_override` | DELETE `/overlays/instances/<id>` | write | `instance_id`, `expected_revision` | `{status, override}` |
| `batch_overlay_instance_override` | POST `/overlays/instances/batch` | write | `object_type_rid`, `instance_ids:list`, `merge_patch:dict`, `expected_revisions:dict` | `{status, instances:[...]}` |
| `save_overlay_media_policy` | PUT `/overlays/media/policy` | write | `policy`, `expected_revision` | `{...revision}` |

**请求体映射**（后端 key，取自 `overlay/api.py`）：
- `save_overlay_type_config` → `{config, expected_revision}`
- `save_overlay_instance_override` → `{override, expected_revision}`
- `clear_overlay_instance_override` → body `{expected_revision}`（后端 body/query 皆可，MCP 走 body）
- `batch_overlay_instance_override` → `{object_type_rid, instance_ids, merge_patch, expected_revisions}`
- `save_overlay_media_policy` → `{policy, expected_revision}`
- `preview_overlay` → `{object_type_rid, instance_id, config}`
- `enable_info_panel` → `{object_type_rid, interfaces:["I3D_Representable","I3D_Overlay"]}`

### 3.3 人物漫游 + 漫游路线（scene-interactions）——10 个

| 工具 | 方法 + 端点 | 级别 | 参数 | 返回要点 |
|---|---|---|---|---|
| `get_scene_catalog` | GET `/scene-interactions/catalog` | read | — | 可用资源目录（帧/路线等） |
| `get_roaming_config` | GET `/scene-interactions/roaming` | read | — | `{config, revision, runtime_status, calibration_state, catalog_version}` |
| `list_routes` | GET `/scene-interactions/routes` | read | — | `{routes:[...], default_route_id}` |
| `get_route` | GET `/scene-interactions/routes/<id>` | read | `route_id` | `{...route, revision}` |
| `save_roaming_config` | PUT `/scene-interactions/roaming` | write | `config`, `expected_revision` | `{...revision}` |
| `create_route` | POST `/scene-interactions/routes` | write | `route`, `expected_revision` | 201 `{...revision}` |
| `update_route` | PUT `/scene-interactions/routes/<id>` | write | `route_id`, `route`, `expected_revision` | `{...revision}` |
| `delete_route` | DELETE `/scene-interactions/routes/<id>` | write | `route_id`, `expected_revision` | `{...revision}` |
| `review_route` | POST `/scene-interactions/routes/<id>/review` | write | `route_id`, `expected_revision` | `{...revision}` |
| `set_default_route` | POST `/scene-interactions/routes/<id>/default` | write | `route_id`, `expected_revision` | `{...revision}` |

**请求体映射**（取自 `scene_interaction/api.py`）：
- `save_roaming_config` → `{config, expected_revision}`
- `create_route` / `update_route` → `{route, expected_revision}`
- `delete_route` / `review_route` / `set_default_route` → `{expected_revision}`

> URL 路径参数（`object_type_rid` / `instance_id` / `route_id`）一律 `quote(..., safe='/')` 编码，与基础层一致。

---

## 4. MCP 客户端扩展（`client.py`）

现有 `NexusClient` 只有 `get` / `post_json` / `post_multipart`，M1 需新增两个方法。**要点：`httpx.Client.delete()` 不接受请求体参数**，DELETE 必须走 `request("DELETE", json=...)`。

```python
def put_json(self, operation, path, json=None, timeout=None):
    to = timeout if timeout is not None else self.s.timeout_read
    try:
        r = self._c.put(path, json=json or {}, timeout=to)
    except httpx.HTTPError as e:
        raise map_transport_error(operation, e)
    return self._handle(operation, r)

def delete_json(self, operation, path, json=None, timeout=None):
    to = timeout if timeout is not None else self.s.timeout_read
    try:
        # httpx 的 delete() 不支持 body，用 request 显式带 json
        r = self._c.request("DELETE", path, json=json or {}, timeout=to)
    except httpx.HTTPError as e:
        raise map_transport_error(operation, e)
    return self._handle(operation, r)
```

`_handle` 复用现有分支（含 2xx 畸形 JSON → `map_bad_response`），无需改动。

---

## 5. 错误映射扩展（`errors.py`）

现有 `map_response_error` 有两个缺口，M1 补齐（加法式，不动既有分支语义）：

1. **422（validator 失败）**：现在会掉到兜底 `NEXUS_HTTP_ERROR`。新增 422 分支 → `NEXUS_VALIDATION`，把后端 `fields`（`[{path,message}]`）汇进 hint，方便直通式按报错纠正。
   - 触发后端 error：`overlay_validation_failed` / `roaming_validation_failed` / 媒体策略 `MediaPolicyError.code`。
2. **409 revision 冲突**：现在 `overlay_revision_conflict` / `scene_interaction_revision_conflict` 会掉进泛化 `NEXUS_CONFLICT`。在既有「项目漂移」分支**之后**新增判定：`berr` 以 `revision_conflict` 结尾 → `NEXUS_REVISION_CONFLICT`（`retryable=False`，但 hint 指引「重新 GET 拿最新 revision 后重试」）。保持「项目漂移」分支优先。
3. **404 无激活项目**：`active_project_not_found` → 复用 `NEXUS_NO_ACTIVE_PROJECT`（提示先 `activate_project`）；其余 404 仍 `NEXUS_NOT_FOUND`。

```python
# 追加/调整（示意，位置见注释）
if status == 404:
    if berr == "active_project_not_found":
        return NexusError("NEXUS_NO_ACTIVE_PROJECT", 404, operation, berr, False,
                          "请先用 activate_project 激活一个项目")
    return NexusError("NEXUS_NOT_FOUND", 404, operation, berr, False)
if status == 409:
    if "expected" in pj or "actual" in pj or berr == "project changed":
        ...  # 既有：NEXUS_PROJECT_CHANGED
    if isinstance(berr, str) and berr.endswith("revision_conflict"):
        return NexusError("NEXUS_REVISION_CONFLICT", 409, operation, berr, False,
                          "配置已被他处修改，请重新 GET 拿最新 revision 后重写")
    return NexusError("NEXUS_CONFLICT", 409, operation, berr, False, ...)
if status == 422:
    fields = pj.get("fields") if isinstance(pj.get("fields"), list) else []
    hint = "；".join(f"{f.get('path')}: {f.get('message')}" for f in fields)[:300] or "配置结构校验失败"
    return NexusError("NEXUS_VALIDATION", 422, operation, berr, False, hint)
```

---

## 6. 并发模型（显式 revision · 读→改→写）

- 写工具 `expected_revision` 必填。标准用法：先 `get_*` 拿 revision → 改结构 → `save_*(..., expected_revision=<读到的>)`。
- 遇 `NEXUS_REVISION_CONFLICT`：重新 `get_*` → 合并意图 → 重写。**MCP 不自动 fetch-then-write**（会静默覆盖他人改动，违背 M0 一贯的显式安全哲学）。
- `batch_overlay_instance_override` 用 `expected_revisions`（`{instance_id: revision}` 映射），逐实例治理。
- **残余风险**：读与写之间他方 bump revision，写侧必得 409——这正是 revision 要拦的，非缺陷。skill 明确此循环。

---

## 7. Skill 层（文档粒度 A）

扩展 `mcp/skills/ontotwin-nexus/SKILL.md`，新增「场景配置」段落：

- **playbook**：`enable_info_panel`（类型首次启用面板）→ `get_overlay_context` 读活配置 → 照结构改 → `save_overlay_type_config(expected_revision)`；实例级用 `save_overlay_instance_override`。漫游/路线同构。
- **金规**：① 写前必先读 revision；② 遇 `NEXUS_REVISION_CONFLICT` 重读重试；③ config 结构以 `get_overlay_context` 返回的**活配置为准**，不臆造字段；④ 面板类型未启用能力先 `enable_info_panel`。
- **config 速查（A）**：一段导航性说明——槽位（body/status/media/metrics）、绑定源四种（`literal`/`instance`/`object_type`/`raw_state`）、状态分级配色——**不复述全字段**。附一份从真实 `get_overlay_context` 抓下来的可改样例；后端加字段时活样例自动跟上，speedsheet 仅在 422 消息含糊的字段上补注解。
- 写进 3 个使用范例：改某类型面板状态配色 / 批量给一批实例覆盖标签 / 新建一条漫游路线并设默认。

---

## 8. Repo 布局

```
mcp/ontotwin_mcp/
  client.py          # + put_json / delete_json
  errors.py          # + 422 / 409-revision / 404-active
  tools/
    overlay.py       # 新增：10 个 overlay 工具
    scene.py         # 新增：10 个 roaming+routes 工具
    __init__.py      # register_all 追加 overlay.register / scene.register
```

沿用 `register(mcp, client, registry)` 签名与 `_ot_tools` 注册惯例，不碰 `backend/`。

---

## 9. 测试策略

- **协议测试**：stdio 列表新增 20 工具全部可见（扩展现有 stdio 协议测试）。
- **单元（in-memory `MockTransport`）**：每工具断言 URL / 方法 / 请求体 key；重点覆盖新 `put_json` / `delete_json`（DELETE 带 body）与新错误映射（422→`NEXUS_VALIDATION` 带 fields、409-revision→`NEXUS_REVISION_CONFLICT`、404-active→`NEXUS_NO_ACTIVE_PROJECT`）。
- **只读冒烟**（真部署 88.66）：`list_overlay_templates` / `get_overlay_context` / `get_scene_catalog` / `get_roaming_config` / `list_routes` 打通即可；纳入 `selfcheck.py` 读工具集。
- **写路径**：只对隔离临时 ProjectStore 或一次性抛弃数据集验证，**不碰生产库**（与基础层一致）。

---

## 10. 交付里程碑（任务分组，供 writing-plans）

| 组 | 内容 | 独立可测 |
|---|---|---|
| **A · 基座** | `client.put_json/delete_json` + `errors` 三处扩展 + 单元测试 | ✅ |
| **B · overlay** | 10 个信息面板工具 + register + 单元测试 | ✅ |
| **C · scene** | 10 个漫游/路线工具 + register + 单元测试 | ✅ |
| **D · skill+冒烟** | SKILL.md 场景配置段 + 速查/活样例 + `selfcheck` 读工具 + stdio 协议测试更新 | ✅ |

A 是 B/C 的前置；B、C 互不依赖；D 收口。

---

## 11. 依赖与兼容

- **无新依赖**：仅用现有 `httpx`（`put` / `request`）。不碰 `mcp/pyproject.toml` 依赖，不碰 `backend/requirements.txt`。
- **向后兼容**：纯加法，现有 30 工具与其测试不受影响。
- **无 PG 平价问题**：后端零改动，不涉及 `project_store_pg.py` 签名平价（区别于 M0 §14.0）。

---

## 12. 风险科普

- **乐观锁 vs 悲观锁**：revision 是「乐观锁」——不上锁、写时比对版本号，冲突了让调用方重来。适合「冲突少、读多写少」的配置编辑；代价是并发写会有一方吃 409。对单人维护、AI 偶发写的场景刚好。
- **直通式的赌注**：把「构造合法 config」的责任交给 AI + 后端 validator，省了在 MCP 侧维护一份会漂移的 schema 副本。赌的是后端 422 消息够清楚 + AI 照活样例改。这是文档粒度选 A 的直接结果，若某字段反复被 AI 写错，成本最低的补救是在 skill 速查加一行注解，而非搬来整份 schema。
