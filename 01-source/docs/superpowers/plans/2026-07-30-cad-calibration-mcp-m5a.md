# M5a CAD 交互标定链 MCP 扩展 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. Steps use checkbox (`- [ ]`) syntax.

**Goal:** 给 MCP 新增 6 工具（4 读 + 2 写）：CAD 预览/扫类型/冲突检查/覆盖检查/提交类型/批量投产实例；并给 `spawn_instances` 端点加可选 `expected_project_id` 护栏（app.py-only）。

**Architecture:** 无状态链（AI 持中间态）。纯直通式 + `register(mcp, client, registry)`。后端只改 `app.py` 的 `spawn_instances` 端点透传 expected（下游 `spawn`/`update_raw_state` M3 已具锁内护栏，**不改 project_store，无 PG 平价**）。`commit` 目标显式、不加 expected。client/errors 零改动。

**Tech Stack:** Python 3.10；后端 Flask + pytest（`client` fixture）；MCP `mcp`/`httpx` + pytest（fake client）。

## Global Constraints

- **后端改动仅 app.py `spawn_instances`**：加法式，缺省 `expected_project_id`（None）走旧路径，现有后端测试不回归。不改 `project_store`/`project_store_pg`（`spawn`/`update_raw_state` M3 已扩展、PG 未覆盖）。
- **MCP 侧**：直通式、`client`/`errors` 零改动。`expected_project_id: str=""`（M0 式，非空入 body）；`commit` 不带 expected。
- **无路径参数**：M5a 端点均固定路径 + body/multipart，工具不需要 `quote`。
- **无新依赖**。纯加法，现有 78 工具及测试不回归。
- docstring 中文：`commit_cad_types`/`spawn_cad_instances` 写工具标注（spawn 注明 commit=False 为 dry-run）；读工具 `只读：...`。Passthrough。
- 后端测试从 `backend/` 跑；MCP 测试从 `mcp/` 跑。

---

### Task 1: 后端 —— spawn_instances 端点透传 expected

**Files:**
- Modify: `backend/app.py`（`coord_spawn_instances`，约 562–779）
- Test: `backend/tests/test_spawn_cad_expected.py`

**Interfaces:**
- Consumes: 现有 `ProjectMismatch`（M0/M3，app.py 已 import）；`instance_store.spawn`/`update_raw_state`（M3 已支持 `expected_project_id`）；`client` fixture。
- Produces: `coord_spawn_instances` 读 `expected_project_id` 并透传到真写阶段的 spawn/update_raw_state；真写阶段捕获 `ProjectMismatch` → 409 `{error:"project changed", expected, actual}`。dry-run 不受影响。

- [ ] **Step 1: 写失败测试** `backend/tests/test_spawn_cad_expected.py`

```python
def test_spawn_cad_expected_mismatch_409(client, store, monkeypatch):
    # spawn 端点前置校验用 app 模块级 _object_types；塞一个可用类型让 item 过三态校验。
    import app
    monkeypatch.setitem(app._object_types, "TESTBLK",
                        {"rid": "TESTBLK", "name": "测试块", "injected_interfaces": ["I3D_Representable"]})
    body = {
        "items": [{"block_name": "TESTBLK", "cad_xy": [1.0, 2.0]}],
        "transform_matrix": [[1, 0, 0], [0, 1, 0]],
        "commit": True,
        "expected_project_id": "p_other",
    }
    r = client.post("/api/v2/coord/spawn_instances", json=body)
    assert r.status_code == 409
    assert r.get_json().get("expected") == "p_other"


def test_spawn_cad_dry_run_ignores_expected(client, store, monkeypatch):
    import app
    monkeypatch.setitem(app._object_types, "TESTBLK",
                        {"rid": "TESTBLK", "name": "测试块", "injected_interfaces": ["I3D_Representable"]})
    body = {
        "items": [{"block_name": "TESTBLK", "cad_xy": [1.0, 2.0]}],
        "transform_matrix": [[1, 0, 0], [0, 1, 0]],
        "commit": False,               # dry-run
        "expected_project_id": "p_other",
    }
    r = client.post("/api/v2/coord/spawn_instances", json=body)
    assert r.status_code == 200
    assert r.get_json().get("status") == "dry_run"


def test_spawn_cad_expected_match_writes(client, store, monkeypatch):
    import app
    monkeypatch.setitem(app._object_types, "TESTBLK",
                        {"rid": "TESTBLK", "name": "测试块", "injected_interfaces": ["I3D_Representable"]})
    body = {
        "items": [{"block_name": "TESTBLK", "cad_xy": [3.0, 4.0], "instance_id": "TB-1"}],
        "transform_matrix": [[1, 0, 0], [0, 1, 0]],
        "commit": True,
        "expected_project_id": "p_test",   # 与激活项目一致
    }
    r = client.post("/api/v2/coord/spawn_instances", json=body)
    assert r.status_code == 200
    assert r.get_json()["summary"]["written_create"] == 1
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd backend && python -m pytest tests/test_spawn_cad_expected.py -v`
Expected: FAIL（端点尚未读/透传 expected → 带错 expected 仍 200 写入，而非 409）

- [ ] **Step 3: 改 `app.py` `coord_spawn_instances`**

READ 实际函数（约 562–779）。三处改动：
1. 解析处（约 585 之后）加：`expected = data.get("expected_project_id")`。
2. 真写阶段（`if not commit: return ...` 之后，约 719 起的所有写调用）给每个 `instance_store.spawn(...)` 和 `instance_store.update_raw_state(...)` **追加** `expected_project_id=expected`（共 6 处：to_create 的 spawn+update、to_update_coord_only 的 update、conflicts update_coord 的 update、duplicate 的 spawn+update）。
3. 用 try/except 包住整个真写阶段（从第一个写循环到 `return jsonify({"status":"ok",...})` 之前）：
```python
    try:
        # …to_create / to_update_coord_only / conflicts 三个写循环（每个写调用已带 expected_project_id=expected）…
    except ProjectMismatch as e:
        return jsonify({"error": "project changed", "expected": e.expected, "actual": e.actual}), 409
    return jsonify({"status": "ok", "summary": {...}, ...})
```
（`ProjectMismatch` 已在 app.py import；缺省 `expected=None` 时下游不校验，行为不变。写阶段逐 item 非原子——加一行注释说明中途切项目会部分写、后续 item 触发 409，同 M3 writeback。）

- [ ] **Step 4: 跑测试确认通过 + 全量后端不回归**

Run: `cd backend && python -m pytest tests/test_spawn_cad_expected.py -v && python -m pytest tests/ -q`
Expected: PASS（新用例过；既有后端测试不回归。注：全量约 8–9 分钟）

- [ ] **Step 5: 提交**

```bash
git add backend/app.py backend/tests/test_spawn_cad_expected.py
git commit -m "feat(backend): coord/spawn_instances 端点透传可选 expected_project_id（真写阶段护栏，dry-run 不受影响）"
```

---

### Task 2: cad_calibration 域（6 工具）

**Files:**
- Create: `mcp/ontotwin_mcp/tools/cad_calibration.py`
- Modify: `mcp/ontotwin_mcp/tools/__init__.py`
- Test: `mcp/tests/test_tools_cad_calibration.py`

**Interfaces:**
- Consumes: `client.post_json/post_multipart`；`files.resolve_upload`；`config.load()`；`settings.timeout_cadparse`。
- Produces（工具名 → 端点）：见 spec §3。

- [ ] **Step 1: 写失败测试** `mcp/tests/test_tools_cad_calibration.py`

```python
"""cad_calibration 工具单测（fake client）。"""
from ontotwin_mcp.server import build_server


class C:
    def __init__(self):
        self.calls = []

    def post_json(self, op, path, json=None, timeout=None):
        self.calls.append(("post", path, json)); return {"status": "ok"}

    def post_multipart(self, op, path, files, data=None, timeout=None):
        self.calls.append(("multipart", path, list(files), data, timeout)); return {"ok": True}

    def get(self, *a, **k):
        return {}


def _t(mcp, name):
    return mcp._ot_tools[name]


def test_preview_cad_multipart(monkeypatch):
    monkeypatch.setattr("ontotwin_mcp.tools.cad_calibration.resolve_upload",
                        lambda p, s, allowed_ext=None: ("plan.dxf", b"x"))
    monkeypatch.setenv("NEXUS_TIMEOUT_CADPARSE", "77")
    c = C(); mcp = build_server(c)
    _t(mcp, "preview_cad")("whatever.dxf")
    method, path, files, data, timeout = c.calls[-1]
    assert method == "multipart" and path == "/api/v2/coord/preview"
    assert files[0] == ("file", "plan.dxf", b"x")
    assert timeout == 77.0


def test_scan_cad_types_multipart(monkeypatch):
    monkeypatch.setattr("ontotwin_mcp.tools.cad_calibration.resolve_upload",
                        lambda p, s, allowed_ext=None: ("plan.dxf", b"x"))
    c = C(); mcp = build_server(c)
    _t(mcp, "scan_cad_types")("whatever.dxf")
    assert c.calls[-1][1] == "/api/v2/coord/types/scan"


def test_check_type_conflicts_body():
    c = C(); mcp = build_server(c)
    _t(mcp, "check_type_conflicts")(["A", "B"], mode="merge", target_dataset_id="ds1")
    method, path, body = c.calls[-1]
    assert path == "/api/v2/coord/types/check_conflicts"
    assert body == {"rids": ["A", "B"], "mode": "merge", "target_dataset_id": "ds1"}


def test_check_type_conflicts_omits_empty_target():
    c = C(); mcp = build_server(c)
    _t(mcp, "check_type_conflicts")(["A"])
    assert c.calls[-1][2] == {"rids": ["A"], "mode": "publish"}


def test_check_type_coverage_body():
    c = C(); mcp = build_server(c)
    _t(mcp, "check_type_coverage")(["A", "B"])
    method, path, body = c.calls[-1]
    assert path == "/api/v2/coord/types/check_coverage"
    assert body == {"block_names": ["A", "B"]}


def test_commit_cad_types_body():
    c = C(); mcp = build_server(c)
    _t(mcp, "commit_cad_types")([{"block_name": "X"}], "publish",
                                source_file="a.dxf",
                                publish_options={"name": "厂A"})
    method, path, body = c.calls[-1]
    assert path == "/api/v2/coord/types/commit"
    assert body == {"items": [{"block_name": "X"}], "mode": "publish",
                    "source_file": "a.dxf", "publish_options": {"name": "厂A"}}


def test_spawn_cad_instances_dry_run_body():
    c = C(); mcp = build_server(c)
    _t(mcp, "spawn_cad_instances")([{"block_name": "X", "cad_xy": [1, 2]}],
                                   [[1, 0, 0], [0, 1, 0]])
    method, path, body = c.calls[-1]
    assert path == "/api/v2/coord/spawn_instances"
    assert body == {"items": [{"block_name": "X", "cad_xy": [1, 2]}],
                    "transform_matrix": [[1, 0, 0], [0, 1, 0]],
                    "mode": "dxf", "conflict_strategy": "update_coord", "commit": False}
    assert "expected_project_id" not in body


def test_spawn_cad_instances_commit_with_expected():
    c = C(); mcp = build_server(c)
    _t(mcp, "spawn_cad_instances")([{"block_name": "X"}], [[1, 0, 0], [0, 1, 0]],
                                   source_label="a.dxf", commit=True,
                                   expected_project_id="p1")
    body = c.calls[-1][2]
    assert body["commit"] is True
    assert body["source_label"] == "a.dxf"
    assert body["expected_project_id"] == "p1"


def test_cad_calibration_tools_registered():
    c = C(); mcp = build_server(c)
    expected = {
        "preview_cad", "scan_cad_types", "check_type_conflicts",
        "check_type_coverage", "commit_cad_types", "spawn_cad_instances",
    }
    assert expected <= set(mcp._ot_tools)
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd mcp && python -m pytest tests/test_tools_cad_calibration.py -v`
Expected: FAIL（未注册）

- [ ] **Step 3: 建 `mcp/ontotwin_mcp/tools/cad_calibration.py`**

```python
"""cad_calibration 域：CAD 一键成模的交互标定链（无状态，AI 持中间态）。

preview/scan 上传 DXF 出预览/候选类型；check 只读检查；commit 建/并类型数据集；
spawn 批量投产实例（commit=False dry-run，真写带 expected_project_id 护栏）。
"""
from typing import Optional

from .. import config
from ..files import resolve_upload


def register(mcp, client, registry):
    settings = getattr(client, "s", None) or config.load()

    @mcp.tool()
    def preview_cad(file_path: str) -> dict:
        """只读：上传 DXF 出预览数据（几何/图层）。"""
        base, content = resolve_upload(file_path, settings, allowed_ext=[".dxf"])
        return client.post_multipart(
            "preview_cad", "/api/v2/coord/preview",
            [("file", base, content)], timeout=settings.timeout_cadparse)

    @mcp.tool()
    def scan_cad_types(file_path: str) -> dict:
        """只读：扫描 DXF，返回候选 ObjectType 列表（含 preset asset_id）。"""
        base, content = resolve_upload(file_path, settings, allowed_ext=[".dxf"])
        return client.post_multipart(
            "scan_cad_types", "/api/v2/coord/types/scan",
            [("file", base, content)], timeout=settings.timeout_cadparse)

    @mcp.tool()
    def check_type_conflicts(rids: list, mode: str = "publish",
                             target_dataset_id: str = "") -> dict:
        """只读：给定待写入 rids，返回与目标/其它数据集的冲突。"""
        body = {"rids": rids, "mode": mode}
        if target_dataset_id:
            body["target_dataset_id"] = target_dataset_id
        return client.post_json(
            "check_type_conflicts", "/api/v2/coord/types/check_conflicts", json=body)

    @mcp.tool()
    def check_type_coverage(block_names: list) -> dict:
        """只读：给定 block_names，返回激活数据集覆盖/缺失情况。"""
        return client.post_json(
            "check_type_coverage", "/api/v2/coord/types/check_coverage",
            json={"block_names": block_names})

    @mcp.tool()
    def commit_cad_types(items: list, mode: str, source_file: str = "",
                         publish_options: Optional[dict] = None,
                         merge_options: Optional[dict] = None,
                         conflict_strategy: str = "", force: bool = False) -> dict:
        """本操作会修改当前激活项目：提交审核后的候选，发布新数据集或合并到现有。

        mode="publish" 用 publish_options={"name":...} 新建；mode="merge" 用
        merge_options={"target_dataset_id":...} 合并（目标显式，不需 expected_project_id）。
        """
        body = {"items": items, "mode": mode}
        if source_file:
            body["source_file"] = source_file
        if publish_options is not None:
            body["publish_options"] = publish_options
        if merge_options is not None:
            body["merge_options"] = merge_options
        if conflict_strategy:
            body["conflict_strategy"] = conflict_strategy
        if force:
            body["force"] = force
        return client.post_json(
            "commit_cad_types", "/api/v2/coord/types/commit", json=body)

    @mcp.tool()
    def spawn_cad_instances(items: list, transform_matrix: list,
                            source_label: str = "", mode: str = "dxf",
                            conflict_strategy: str = "update_coord",
                            commit: bool = False,
                            expected_project_id: str = "") -> dict:
        """本操作在 commit=True 时会修改当前激活项目：把 CAD 实体批量投产为实例。

        commit=False 为 dry-run（只返回 summary/to_create/conflicts，不写）；真写务必先 dry-run。
        expected_project_id 非空时作乐观并发校验（取自 get_active_project 的 project_id）。
        """
        body = {"items": items, "transform_matrix": transform_matrix,
                "mode": mode, "conflict_strategy": conflict_strategy, "commit": commit}
        if source_label:
            body["source_label"] = source_label
        if expected_project_id:
            body["expected_project_id"] = expected_project_id
        return client.post_json(
            "spawn_cad_instances", "/api/v2/coord/spawn_instances", json=body)

    for f in (preview_cad, scan_cad_types, check_type_conflicts, check_type_coverage,
              commit_cad_types, spawn_cad_instances):
        registry[f.__name__] = f
```

- [ ] **Step 4: 挂进 `register_all`**（`tools/__init__.py`；追加 `cad_calibration`）

```python
from . import (project, ontology, runtime, cad, binding, phase2,
               overlay, scene, spatial, zones, lifecycle, model_binding,
               ontology_edit, floor_pulse, cad_calibration)


def register_all(mcp, client):
    registry = {}
    for mod in (project, ontology, runtime, cad, binding, phase2,
                overlay, scene, spatial, zones, lifecycle, model_binding,
                ontology_edit, floor_pulse, cad_calibration):
        mod.register(mcp, client, registry)
    mcp._ot_tools = registry
    return registry
```

- [ ] **Step 5: 跑测试确认通过 + 全量不回归**

Run: `cd mcp && python -m pytest tests/test_tools_cad_calibration.py tests/test_stdio.py -v`
Expected: PASS

- [ ] **Step 6: 提交**

```bash
git add mcp/ontotwin_mcp/tools/cad_calibration.py mcp/ontotwin_mcp/tools/__init__.py mcp/tests/test_tools_cad_calibration.py
git commit -m "feat(mcp): cad_calibration 域 6 工具（CAD 交互标定链，spawn dry-run+expected 透传）"
```

---

### Task 3: 协议冒烟 + skill 文档

**Files:**
- Modify: `mcp/tests/test_stdio.py`
- Modify: `mcp/skills/ontotwin-nexus/SKILL.md`

（selfcheck 不改：preview/scan 需真 DXF、check 需真 rids。）

**Interfaces:**
- Consumes: Task 2 注册的工具。
- Produces：协议层验证 6 新工具可 list/call；skill 增「CAD 一键成模（交互标定链）」段。

- [ ] **Step 1: 写失败测试**（追加到 `test_stdio.py`）

```python
async def test_cad_calibration_tools_listed_and_callable():
    """M5a CAD 交互标定链 6 工具全部注册；挑一个只读工具走真 call_tool。"""
    routes = {"/api/v2/coord/types/check_coverage": {"total": 0, "covered": 0, "missing": 0}}
    mcp = build_server(FakeClient(routes))
    async with create_connected_server_and_client_session(mcp._mcp_server) as session:
        names = {t.name for t in (await session.list_tools()).tools}
        res = await session.call_tool("check_type_coverage", {"block_names": []})

    new_tools = {
        "preview_cad", "scan_cad_types", "check_type_conflicts",
        "check_type_coverage", "commit_cad_types", "spawn_cad_instances",
    }
    assert new_tools <= names, f"缺工具: {new_tools - names}"
    assert len(names) >= 84, f"工具总数应 ≥84（78+6），实际 {len(names)}"
    assert res.isError is False
```

> `FakeClient.post_json(op, path, json=None, timeout=None)` 返回 `routes.get(path, {})`；本测试命中 `/check_coverage` 路径，call_tool 不报错即可。若 `FakeClient` 无 `post_json` 需补（它已有——见 test_stdio.py 顶部 FakeClient）。

- [ ] **Step 2: 跑测试确认（Task 2 已完成则直接 PASS，属预期）**

Run: `cd mcp && python -m pytest tests/test_stdio.py -k cad_calibration -v`
Expected: PASS（6 工具已注册；回归守卫）

- [ ] **Step 3: skill 增「CAD 一键成模（交互标定链）」段**（`mcp/skills/ontotwin-nexus/SKILL.md`）

先 Read 现有 SKILL.md，在「外部数据监控（floor_pulse）」段之后追加（文档 A）：

````markdown
## CAD 一键成模（交互标定链）

这条链**服务器端无状态**——中间产物（扫描候选、标定矩阵）由你（AI）持有并逐步回传。

**四段流程**
1. `scan_cad_types("路径/xxx.dxf")` → 拿候选类型（AI 按需补每个候选的 `asset_id`）。（`preview_cad` 可先看几何预览。）
2. `check_type_conflicts([rid, ...])` 看是否撞已有数据集的类型。
3. `commit_cad_types(items, mode="publish", publish_options={"name":"厂区A"})` 建类型数据集（或 `mode="merge", merge_options={"target_dataset_id":...}` 合并）。
4. `calibrate_coordinates(anchors)`（基础层）得 `transform_matrix` → `spawn_cad_instances(items, transform_matrix, commit=False)` **先 dry-run** 看 summary（to_create/conflicts/errors）→ 确认 → `commit=True, expected_project_id=<get_active_project 的 project_id>` 真投产。

**金规**
- spawn 是高危批量写：**务必先 `commit=False` dry-run**；真写带 `expected_project_id`；遇 `NEXUS_PROJECT_CHANGED` 说明激活项目被切走，重新确认后再投。
- `items` 结构以 `scan_cad_types` 返回为准（`block_name`/`cad_xy`/`rotation`/`attribs`/可选 `instance_id`/`asset_id`）。

**触发示例**
- 「扫一下这个 DXF 有哪些设备类型」
- 「把这批设备按标定矩阵投产，先 dry-run 看看有没有冲突」
````

- [ ] **Step 4: 跑全量测试确认通过**

Run: `cd mcp && python -m pytest tests/ -v`
Expected: PASS（全绿）

- [ ] **Step 5: 提交**

```bash
git add mcp/tests/test_stdio.py mcp/skills/ontotwin-nexus/SKILL.md
git commit -m "feat(mcp): CAD 交互标定链协议冒烟 + skill playbook"
```

---

## 交付后（人工，需确认）

- **部署后端到 88.66**：`app.py` 一个文件 scp（paramiko）+ `docker compose restart backend`；部署前与用户确认。见 memory `deploy-88-66-method`。
- 重打发行包：`mcp/build-dist.ps1`。
- 真机写验证：`scan_cad_types(demo.dxf)` → `spawn_cad_instances(..., commit=False)` dry-run；带错 expected + commit=True 验 409，只对一次性抛弃项目，不碰生产库。

---

## Self-Review 记录

- **Spec 覆盖**：spec §3 的 6 工具 ↔ Task 2；§4 后端 ↔ Task 1；§6 skill ↔ Task 3；client/errors/project_store/PG 零改动（无对应任务）。
- **类型一致**：`expected_project_id: str=""`（spawn，非空入 body）；`commit: bool=False`（dry-run）；`commit_cad_types` 无 expected；`publish_options`/`merge_options: Optional[dict]=None`。
- **占位符扫描**：无 TBD；每 code step 含完整代码或精确改法。
- **护栏区分**：spawn 加 expected（隐式激活）、commit 不加（目标显式）——贯穿 spec 与 plan。
- **命名无冲突**：6 个新名与现有 78 工具无交集（`preview_cad`≠基础层 `parse_cad_dxf`；`calibrate_coordinates` 是基础层已有、本轮复用不新增）。
