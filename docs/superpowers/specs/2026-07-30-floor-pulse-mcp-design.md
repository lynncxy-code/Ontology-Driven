# OntoTwin Nexus M6 —— floor_pulse 外部数据监控 MCP 扩展设计

> 「MCP 覆盖整个系统操作面」路线图第五个交付的子项目（M6）。路线图 M1–M6，M5 待做。
> 前置：基础 30 + M1（20）+ M2（7）+ M3（9）+ M4（7）= 73 工具，均已交付 main。

## 修订记录

- **v1（2026-07-30）**：首版。沿用直通式 / 文档 A。范围与两处说明已与用户敲定。

---

## 1. 目标与非目标

### 目标

把「外部数据监控台」（floor_pulse）开放给 MCP：

- **本地模拟控制**：开关模拟数据、注入模拟移动事件（内存态，无外部依赖）。
- **中转站监控**（代理）：读快照、读增量事件、查健康（代理外部中间件 `MIDDLEWARE_BASE_URL` + 注入 mock 覆写）。

### 非目标

- **不管中间件部署**：`snapshot`/`events`/`health` 代理外部中转站（如 `host.docker.internal:5001`）。88.66 上该中间件**未部署** → 这三个工具返回 **503 `NEXUS_DEGRADED`**，属预期（部署记录已载）。真要联调需另起中间件，M6 只做转译。
- **后端 / client / errors 零改动**。
- **不做 M5**（CAD/坐标标定链）。

---

## 2. 架构

- 直通式；`register(mcp, client, registry)`；文档 A。
- **无并发键**：floor_pulse 是全局内存 mock 态 + 外部代理，非项目作用域，不透传 `expected_project_id`。
- **client / errors / 后端 全零改动**：get / post_json 已存在；503→`NEXUS_DEGRADED`（可重试）、400→`NEXUS_VALIDATION_ERROR` 已覆盖。
- **已知小瑕疵（接受，不修）**：errors 的 503 hint 文案为 Neo4j 专属（"语义图库暂不可达"），floor_pulse 的 503 会套用它——`code=NEXUS_DEGRADED` + 可重试语义正确，后端 error `middleware_unreachable` 也在消息里，仅 hint 偏 Neo4j。改它会破坏 M0 的 `test_503_neo4j_no_overpromise`，不值当。

---

## 3. 工具清单（5 个：3 读 + 2 写）→ MCP 73→78

| 工具 | 方法 + 端点 | 参数 | 请求 |
|---|---|---|---|
| `toggle_floor_pulse_mock` | POST `/api/v2/floor_pulse/mock/toggle` | `enabled: bool` | body `{enabled}` |
| `move_floor_pulse_mock` | POST `/api/v2/floor_pulse/mock/move` | `instance_id`, `workstation_id`, `workstation_name=""` | body `{instanceId, workstationId}` + 非空 `workstationName`。需先开 mock，否则后端 400 |
| `get_floor_pulse_snapshot` | GET `/api/v2/floor_pulse/snapshot` | — | 代理中转站快照（+ mock 覆写）；不可达 503 |
| `get_floor_pulse_events` | GET `/api/v2/floor_pulse/events` | `after_event_id: int = 0` | query `{afterEventId: after_event_id}`；代理增量事件；不可达 503 |
| `get_floor_pulse_health` | GET `/api/v2/floor_pulse/health` | — | 代理中转站健康；不可达返回 `{status:"unreachable"}` 503 |

### ⚠ 键名映射（后端是 camelCase，务必转换）

后端 floor_pulse 端点用 **camelCase** 键，与其它域（snake_case）不同，直通式**必须转换**：
- `move_floor_pulse_mock`：`instance_id → instanceId`，`workstation_id → workstationId`，`workstation_name → workstationName`（非空才放）。
- `get_floor_pulse_events`：`after_event_id → afterEventId`（query 参数）。
- `toggle_floor_pulse_mock`：`enabled` 本就同名，直接 `{enabled}`。

---

## 4. 错误映射 / client / 后端

**全零改动**。M6 状态码已被覆盖：
- 代理不可达 503（`middleware_unreachable` / 其它）→ `NEXUS_DEGRADED`（可重试；hint 偏 Neo4j 见 §2 已知瑕疵）。
- `move` 未开 mock 400 → `NEXUS_VALIDATION_ERROR`；缺参 400 同。
- client 用 get / post_json（已存在）。后端不动。

---

## 5. Skill 层（文档 A）

`mcp/skills/ontotwin-nexus/SKILL.md` 增「外部数据监控（floor_pulse）」段：

- **看外部数据**：`get_floor_pulse_health()` 先看中转站通不通（离线返回 `NEXUS_DEGRADED`/`unreachable`）→ `get_floor_pulse_snapshot()` 拉当前快照 → `get_floor_pulse_events(after_event_id=…)` 拉增量。
- **模拟演示**（无中转站时自造数据）：`toggle_floor_pulse_mock(True)` 开 → `move_floor_pulse_mock(instance_id, workstation_id, workstation_name)` 注入移动事件（会进快照/事件流）→ `toggle_floor_pulse_mock(False)` 关并清空。
- 提示：中转站中间件（5001）未部署时，snapshot/events/health 会 `NEXUS_DEGRADED`——这是数据源离线，非工具故障；mock 链路不依赖中间件、始终可用。
- 触发示例：「看看中转站健康吗」「开模拟，把 human-01 移到 WS-03」「拉一下最新的现场快照」。

---

## 6. Repo 布局

```
mcp/ontotwin_mcp/tools/
  floor_pulse.py       # 新增：5 个工具
  __init__.py          # register_all 追加 floor_pulse
```
client/errors/后端 不改。

---

## 7. 测试策略

- **协议**：stdio 列表新增 5 工具全可见；`call_tool` 挑 `get_floor_pulse_health` 走一遍（fake client 回放，不依赖真中间件）。
- **单元（fake client）**：每工具断言 URL/方法/请求体；**重点 camelCase 键映射**（`instanceId`/`workstationId`/`workstationName` 非空、`afterEventId` query）。
- **只读冒烟**：floor_pulse 读工具依赖外部中间件（88.66 上未部署，必 503），**不入 selfcheck**（同 `get_ontology_registry`）。
- **写路径**：mock toggle/move 是全局内存态，可对 88.66 直接验（开→move→snapshot 看到覆写→关），非项目数据、无污染；也可只在单测覆盖。

---

## 8. 交付里程碑（任务分组，供 writing-plans）

| 组 | 内容 | 独立可测 |
|---|---|---|
| A · floor_pulse | 5 个工具 + register + 单测 | ✅ |
| B · skill+协议 | SKILL.md 段 + stdio 协议测试（selfcheck 不改） | ✅ |

M6 最小：一个工具域 + 收口。无后端/errors/client 改动。

---

## 9. 依赖与兼容

- **无新依赖**、**后端零改动**、**client/errors 零改动**。纯加法，现有 73 工具与测试不回归。
- MCP 工具总数 **73 → 78**。
- 无 PG 平价。

---

## 10. 风险科普

- **camelCase vs snake_case**：Nexus 大部分 API 用 snake_case，但 floor_pulse 这套是对接 UE/中转站的实时协议，沿用了 camelCase（`instanceId` 等）。直通式转译层遇到这种「对端命名风格不一致」时，必须在工具里显式做键名映射，不能想当然按本域惯例传 snake_case——否则后端读不到必填字段直接 400。M6 的单测专门盯这个。
