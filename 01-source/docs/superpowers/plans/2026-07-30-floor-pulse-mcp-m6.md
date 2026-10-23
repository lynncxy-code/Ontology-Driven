# M6 floor_pulse 外部数据监控 MCP 扩展 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. Steps use checkbox (`- [ ]`) syntax.

**Goal:** 给 MCP 新增 5 工具（3 读 + 2 写）：floor_pulse 本地模拟控制（toggle/move）+ 中转站代理监控（snapshot/events/health）。

**Architecture:** 纯 `mcp/` 转译层，沿用直通式 + `register(mcp, client, registry)`。floor_pulse 全局内存 mock 态 + 外部代理，**非项目作用域，无 `expected_project_id`**。**后端/client/errors 全零改动**。关键：floor_pulse 后端用 **camelCase** 键，工具须显式映射。

**Tech Stack:** Python 3.10、`mcp`（FastMCP）、`httpx`；pytest（fake client + `create_connected_server_and_client_session`）。

## Global Constraints

- **后端零改动 + client 零改动 + errors 零改动**：只动 `mcp/`（tools/、tests/、SKILL.md）。selfcheck 不改（floor_pulse 读依赖外部中间件，88.66 上必 503）。
- **无新依赖**。**纯加法**：现有 73 工具及测试不回归。
- **无并发键**：不透传 `expected_project_id`。
- **camelCase 键映射（本计划核心）**：`move_floor_pulse_mock` 的 body 用 `instanceId`/`workstationId`/`workstationName`（非 snake_case）；`get_floor_pulse_events` 的 query 用 `afterEventId`。传错键名后端读不到必填字段直接 400。
- **docstring**：floor_pulse mock 是全局态、**不是项目写**，所以 toggle/move 的首句**不用**「本操作会修改当前激活项目」，改用「本操作切换全局模拟开关…」「注入一条模拟移动事件…」；读工具 `只读：...`。Passthrough。
- **无路径参数**：5 端点均固定路径，工具不需要 `quote`。

---

### Task 1: floor_pulse 域（5 工具）

**Files:**
- Create: `mcp/ontotwin_mcp/tools/floor_pulse.py`
- Modify: `mcp/ontotwin_mcp/tools/__init__.py`
- Test: `mcp/tests/test_tools_floor_pulse.py`

**Interfaces:**
- Consumes: `client.get/post_json`。
- Produces（工具名 → 端点）：
  - `toggle_floor_pulse_mock(enabled: bool)` → POST `/api/v2/floor_pulse/mock/toggle`，body `{enabled}`
  - `move_floor_pulse_mock(instance_id, workstation_id, workstation_name="")` → POST `/api/v2/floor_pulse/mock/move`，body `{instanceId, workstationId}` + 非空 `workstationName`
  - `get_floor_pulse_snapshot()` → GET `/api/v2/floor_pulse/snapshot`
  - `get_floor_pulse_events(after_event_id=0)` → GET `/api/v2/floor_pulse/events`，params `{afterEventId: after_event_id}`
  - `get_floor_pulse_health()` → GET `/api/v2/floor_pulse/health`

- [ ] **Step 1: 写失败测试** `mcp/tests/test_tools_floor_pulse.py`

```python
"""floor_pulse 工具单测（fake client）。重点：camelCase 键映射。"""
from ontotwin_mcp.server import build_server


class C:
    def __init__(self):
        self.calls = []

    def get(self, op, path, params=None):
        self.calls.append(("get", path, params)); return {"ok": True}

    def post_json(self, op, path, json=None, timeout=None):
        self.calls.append(("post", path, json)); return {"status": "ok"}


def _t(mcp, name):
    return mcp._ot_tools[name]


def test_toggle_mock_body():
    c = C(); mcp = build_server(c)
    _t(mcp, "toggle_floor_pulse_mock")(True)
    method, path, body = c.calls[-1]
    assert method == "post" and path == "/api/v2/floor_pulse/mock/toggle"
    assert body == {"enabled": True}


def test_move_mock_camelcase_body():
    c = C(); mcp = build_server(c)
    _t(mcp, "move_floor_pulse_mock")("human-01", "WS-03", workstation_name="焊接")
    method, path, body = c.calls[-1]
    assert method == "post" and path == "/api/v2/floor_pulse/mock/move"
    assert body == {"instanceId": "human-01", "workstationId": "WS-03",
                    "workstationName": "焊接"}


def test_move_mock_omits_empty_name():
    c = C(); mcp = build_server(c)
    _t(mcp, "move_floor_pulse_mock")("human-01", "WS-03")
    body = c.calls[-1][2]
    assert body == {"instanceId": "human-01", "workstationId": "WS-03"}
    assert "workstationName" not in body


def test_snapshot_endpoint():
    c = C(); mcp = build_server(c)
    _t(mcp, "get_floor_pulse_snapshot")()
    assert c.calls[-1] == ("get", "/api/v2/floor_pulse/snapshot", None)


def test_events_camelcase_param():
    c = C(); mcp = build_server(c)
    _t(mcp, "get_floor_pulse_events")(after_event_id=42)
    method, path, params = c.calls[-1]
    assert method == "get" and path == "/api/v2/floor_pulse/events"
    assert params == {"afterEventId": 42}


def test_events_default_param():
    c = C(); mcp = build_server(c)
    _t(mcp, "get_floor_pulse_events")()
    assert c.calls[-1][2] == {"afterEventId": 0}


def test_health_endpoint():
    c = C(); mcp = build_server(c)
    _t(mcp, "get_floor_pulse_health")()
    assert c.calls[-1] == ("get", "/api/v2/floor_pulse/health", None)


def test_floor_pulse_tools_registered():
    c = C(); mcp = build_server(c)
    expected = {
        "toggle_floor_pulse_mock", "move_floor_pulse_mock",
        "get_floor_pulse_snapshot", "get_floor_pulse_events", "get_floor_pulse_health",
    }
    assert expected <= set(mcp._ot_tools)
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd mcp && python -m pytest tests/test_tools_floor_pulse.py -v`
Expected: FAIL（未注册）

- [ ] **Step 3: 建 `mcp/ontotwin_mcp/tools/floor_pulse.py`**

```python
"""floor_pulse 域：外部数据监控台（本地模拟控制 + 中转站代理）。

注意：floor_pulse 后端用 camelCase 键（instanceId/workstationId/afterEventId），
与其它域 snake_case 不同 —— 工具里必须显式映射，不能传 snake_case。
snapshot/events/health 代理外部中间件，不可达返回 503 NEXUS_DEGRADED。
mock 态是全局内存、非项目作用域，故 toggle/move 无 expected_project_id。
"""


def register(mcp, client, registry):

    @mcp.tool()
    def toggle_floor_pulse_mock(enabled: bool) -> dict:
        """本操作切换全局模拟开关：开启后 move_floor_pulse_mock 才能注入事件；关闭会清空模拟状态。"""
        return client.post_json(
            "toggle_floor_pulse_mock", "/api/v2/floor_pulse/mock/toggle",
            json={"enabled": enabled})

    @mcp.tool()
    def move_floor_pulse_mock(instance_id: str, workstation_id: str,
                              workstation_name: str = "") -> dict:
        """注入一条模拟移动事件（需先 toggle_floor_pulse_mock(True)，否则后端 400）。

        WS-00（休息区）→ idle，其它工位 → working。
        """
        body = {"instanceId": instance_id, "workstationId": workstation_id}
        if workstation_name:
            body["workstationName"] = workstation_name
        return client.post_json(
            "move_floor_pulse_mock", "/api/v2/floor_pulse/mock/move", json=body)

    @mcp.tool()
    def get_floor_pulse_snapshot() -> dict:
        """只读：拉中转站当前快照（含 mock 覆写）。中间件不可达返回 NEXUS_DEGRADED。"""
        return client.get("get_floor_pulse_snapshot", "/api/v2/floor_pulse/snapshot")

    @mcp.tool()
    def get_floor_pulse_events(after_event_id: int = 0) -> dict:
        """只读：拉中转站增量事件（eventId > after_event_id）。中间件不可达返回 NEXUS_DEGRADED。"""
        return client.get(
            "get_floor_pulse_events", "/api/v2/floor_pulse/events",
            params={"afterEventId": after_event_id})

    @mcp.tool()
    def get_floor_pulse_health() -> dict:
        """只读：查中转站健康状态。不可达返回 NEXUS_DEGRADED / {status: unreachable}。"""
        return client.get("get_floor_pulse_health", "/api/v2/floor_pulse/health")

    for f in (toggle_floor_pulse_mock, move_floor_pulse_mock,
              get_floor_pulse_snapshot, get_floor_pulse_events, get_floor_pulse_health):
        registry[f.__name__] = f
```

- [ ] **Step 4: 挂进 `register_all`**（`tools/__init__.py`；追加 `floor_pulse`）

```python
from . import (project, ontology, runtime, cad, binding, phase2,
               overlay, scene, spatial, zones, lifecycle, model_binding,
               ontology_edit, floor_pulse)


def register_all(mcp, client):
    registry = {}
    for mod in (project, ontology, runtime, cad, binding, phase2,
                overlay, scene, spatial, zones, lifecycle, model_binding,
                ontology_edit, floor_pulse):
        mod.register(mcp, client, registry)
    mcp._ot_tools = registry
    return registry
```

- [ ] **Step 5: 跑测试确认通过 + 全量不回归**

Run: `cd mcp && python -m pytest tests/test_tools_floor_pulse.py tests/test_stdio.py -v`
Expected: PASS

- [ ] **Step 6: 提交**

```bash
git add mcp/ontotwin_mcp/tools/floor_pulse.py mcp/ontotwin_mcp/tools/__init__.py mcp/tests/test_tools_floor_pulse.py
git commit -m "feat(mcp): floor_pulse 域 5 工具（模拟控制 + 中转站代理监控，camelCase 键映射）"
```

---

### Task 2: 协议冒烟 + skill 文档

**Files:**
- Modify: `mcp/tests/test_stdio.py`
- Modify: `mcp/skills/ontotwin-nexus/SKILL.md`

（selfcheck 不改：floor_pulse 读依赖外部中间件，88.66 上必 503。）

**Interfaces:**
- Consumes: Task 1 注册的工具。
- Produces：协议层验证 5 新工具可 list/call；skill 增「外部数据监控」段。

- [ ] **Step 1: 写失败测试**（追加到 `test_stdio.py`）

```python
async def test_floor_pulse_tools_listed_and_callable():
    """M6 floor_pulse 5 工具全部注册；挑一个只读工具走真 call_tool。"""
    routes = {"/api/v2/floor_pulse/health": {"status": "ok"}}
    mcp = build_server(FakeClient(routes))
    async with create_connected_server_and_client_session(mcp._mcp_server) as session:
        names = {t.name for t in (await session.list_tools()).tools}
        res = await session.call_tool("get_floor_pulse_health", {})

    new_tools = {
        "toggle_floor_pulse_mock", "move_floor_pulse_mock",
        "get_floor_pulse_snapshot", "get_floor_pulse_events", "get_floor_pulse_health",
    }
    assert new_tools <= names, f"缺工具: {new_tools - names}"
    assert len(names) >= 78, f"工具总数应 ≥78（73+5），实际 {len(names)}"
    assert res.isError is False
```

- [ ] **Step 2: 跑测试确认（Task 1 已完成则直接 PASS，属预期）**

Run: `cd mcp && python -m pytest tests/test_stdio.py -k floor_pulse -v`
Expected: PASS（5 工具已注册；回归守卫）

- [ ] **Step 3: skill 增「外部数据监控（floor_pulse）」段**（`mcp/skills/ontotwin-nexus/SKILL.md`）

先 Read 现有 SKILL.md，在「本体深编辑」段之后追加（文档 A）：

````markdown
## 外部数据监控（floor_pulse）

**看外部现场数据**（代理中转站中间件）
- `get_floor_pulse_health()` 先看中转站通不通 → `get_floor_pulse_snapshot()` 拉当前快照 → `get_floor_pulse_events(after_event_id=…)` 拉增量事件。
- 中间件（如 5001）未部署时这三个返回 `NEXUS_DEGRADED`——是**数据源离线**，非工具故障。

**模拟演示**（无中转站时自造数据，mock 链路不依赖中间件）
- `toggle_floor_pulse_mock(True)` 开 → `move_floor_pulse_mock(instance_id, workstation_id, workstation_name)` 注入移动事件（WS-00=休息区→idle，其它→working；会进快照/事件流）→ `toggle_floor_pulse_mock(False)` 关并清空。
- 注：`move` 前必须先 `toggle(True)`，否则后端 400。

**触发示例**
- 「看看中转站健康吗」
- 「开模拟，把 human-01 移到 WS-03（焊接工位）」
- 「拉一下最新的现场快照 / 从事件 42 之后的增量」
````

- [ ] **Step 4: 跑全量测试确认通过**

Run: `cd mcp && python -m pytest tests/ -v`
Expected: PASS（全绿）

- [ ] **Step 5: 提交**

```bash
git add mcp/tests/test_stdio.py mcp/skills/ontotwin-nexus/SKILL.md
git commit -m "feat(mcp): floor_pulse 协议冒烟 + skill playbook"
```

---

## 交付后（人工，可选）

- 重打发行包：`mcp/build-dist.ps1`。
- 真机验证：mock 链路可对 88.66 直接验（`toggle(True)` → `move` → `snapshot` 看到覆写 → `toggle(False)`），全局内存态、无项目污染；snapshot/events/health 因中间件未部署会 `NEXUS_DEGRADED`（预期）。**M6 后端零改动，无需部署。**
- **至此路线图 M1–M6 全部交付，MCP 覆盖全系统可编程操作面（~78 工具）。**

---

## Self-Review 记录

- **Spec 覆盖**：spec §3 的 5 工具 ↔ Task 1；§5 skill ↔ Task 2 Step 3；§7 测试 ↔ Task 1/2。后端/client/errors/selfcheck 零改动（无对应任务，符合 spec §2/§4）。
- **camelCase 一致**：`move` body `instanceId/workstationId/workstationName`、`events` query `afterEventId` 贯穿 spec 与 plan、单测专测。
- **docstring**：toggle/move 不用「本操作会修改当前激活项目」（非项目写），用「切换全局模拟开关」「注入模拟移动事件」。
- **占位符扫描**：无 TBD；每 code step 含完整代码。
- **命名无冲突**：5 个新名与现有 73 工具无交集。
