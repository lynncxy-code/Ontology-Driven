# 并发硬化（Codex 复审整改）实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. Steps use checkbox (`- [ ]`) syntax.

**Goal:** 整改 Codex 复审的 6 条 Important：修 F3（calibrate 别名）+ F2（zones TOCTOU）；F1（overlay/scene/routes 绑项目身份，A 硬化）；F4/5/6（多步非原子，B 标注）。

**Architecture:** 复用 `transact_expected_active`（锁内绑项目身份 + 原子写）与 `copy.deepcopy`。加法式：所有 `expected_project_id` 缺省 None 走旧路径。`ProjectMismatch → 409 {expected,actual} → NEXUS_PROJECT_CHANGED`（errors.py 现成）。client/errors/PG 零改动。

**Tech Stack:** Python 3.10；后端 Flask + pytest（`store`/`client` fixture）；MCP `mcp`/`httpx` + pytest（fake client）。

## Global Constraints

- **加法式**：缺省 `expected_project_id=None` 保留旧行为；现有后端 + mcp 测试不回归。
- **不改 project_store_pg**（本轮涉及的 assign_zone/transact_*/get_frame 均未被 PG 覆盖 → 继承）。
- **不改 errors.py/client.py**。
- 后端测试从 `backend/` 跑；MCP 测试从 `mcp/` 跑。
- 中文 docstring；写工具标注。行号为近似，实现前 READ 实际代码。

---

### Task 1（组 A）: F3 calibrate 别名 + F2 zones 锁内护栏

**Files:**
- Modify: `backend/app.py`（`spatial_frame_calibrate`）
- Modify: `backend/project_store.py`（`assign_zone`）
- Modify: `backend/zone_management/service.py`（`assign`）
- Test: `backend/tests/test_hardening_f3_f2.py`

**Interfaces:**
- Consumes: `ProjectMismatch`、`copy`、`ZoneManagementConflictError`、`store`/`client` fixtures。
- Produces: calibrate 深拷贝 get_frame；`assign_zone(..., expected_project_id=None)` 锁内校验；service.assign 透传 + 捕获转 ConflictError。

- [ ] **Step 1: 写失败测试** `backend/tests/test_hardening_f3_f2.py`

```python
import copy
import pytest
from project_store import ProjectMismatch


# ── F3: calibrate 别名 ──────────────────────────────────────────
def test_calibrate_409_does_not_mutate_existing_frame(client, store):
    # 先建一个帧，记下它的 from_canonical（None）
    store.upsert_frame({"id": "fcal", "kind": "custom", "unit": "mm"},
                       expected_project_id="p_test")
    before = copy.deepcopy(next(f for f in store.list_frames() if f["id"] == "fcal"))
    r = client.post("/api/v2/spatial/frames/fcal/calibrate", json={
        "anchors": [{"src": [0, 0], "dst": [1, 1]}, {"src": [1, 0], "dst": [2, 1]}],
        "name": "改名", "expected_project_id": "p_other"})
    assert r.status_code == 409
    after = next(f for f in store.list_frames() if f["id"] == "fcal")
    assert after == before, f"被拒的 calibrate 污染了内存帧: {after}"


# ── F2: zones 锁内护栏 ──────────────────────────────────────────
def test_assign_zone_expected_mismatch_raises(store):
    with pytest.raises(ProjectMismatch):
        store.assign_zone(["i1"], "A区", expected_project_id="p_other")


def test_assign_zone_expected_match_ok(store):
    # p_test 下应正常（可能 missing，但不抛 ProjectMismatch）
    store.assign_zone([], "A区", expected_project_id="p_test")


def test_zones_assignments_endpoint_409(client, store):
    r = client.put("/api/v2/zones/assignments",
                   json={"instance_ids": ["i1"], "zone_id": "A区",
                         "expected_project_id": "p_other"})
    assert r.status_code == 409
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd backend && python -m pytest tests/test_hardening_f3_f2.py -v`
Expected: FAIL（calibrate 污染内存帧；assign_zone 无 expected 参数 → TypeError；端点非 409）

- [ ] **Step 3: 改 `app.py` calibrate**（约 1081）

```python
    import copy
    # 深拷贝已存在帧再改：get_frame 返回活引用，被 expected 护栏拒绝后活帧会被污染（同 profile 别名类）
    frame = copy.deepcopy(project_store.get_frame(frame_id)) or {"id": frame_id, "kind": "custom", "unit": "mm"}
```
（其余 1082-1092 不变。）

- [ ] **Step 4: 改 `project_store.assign_zone`**（约 639）

签名加 `expected_project_id=None`；`with self._lock:` 内、`if not self._current` 分支**之后**、首个写之前：
```python
def assign_zone(self, instance_ids, zone_id, expected_project_id=None):
    with self._lock:
        if not self._current:
            return {...}   # 原样
        if expected_project_id is not None and self._active_id != expected_project_id:
            raise ProjectMismatch(expected_project_id, self._active_id)
        # …原有逻辑不变…
```

- [ ] **Step 5: 改 `zone_management/service.assign`**（约 104）

```python
        expected_project_id = str(payload.get("expected_project_id") or "").strip()
        # 锁外快速失败保留（友好错误），真护栏在 assign_zone 锁内
        if expected_project_id and expected_project_id != project.get("id"):
            raise ZoneManagementConflictError(...)   # 原样
        instance_ids = _normalize_instance_ids(payload.get("instance_ids"))
        zone_id = _normalize_zone_id(payload.get("zone_id"))
        try:
            result = self.store.assign_zone(instance_ids, zone_id,
                                            expected_project_id=expected_project_id or None)
        except ProjectMismatch as e:
            raise ZoneManagementConflictError(
                f"激活项目已从 {e.expected} 切换为 {e.actual}，请刷新后重试")
        ...
```
（`from project_store import ProjectMismatch` 加到 service.py 顶部。）

- [ ] **Step 6: 跑测试确认通过 + 全量后端不回归**

Run: `cd backend && python -m pytest tests/test_hardening_f3_f2.py -v && python -m pytest tests/ -q`
Expected: PASS（新用例过；既有不回归。全量约 8–9 分钟，FOREGROUND）

- [ ] **Step 7: 提交**

```bash
git add backend/app.py backend/project_store.py backend/zone_management/service.py backend/tests/test_hardening_f3_f2.py
git commit -m "fix(backend): F3 calibrate 深拷贝防别名污染 + F2 assign_zone 锁内 expected 护栏"
```

---

### Task 2（组 B）: F1 —— overlay 服务/端点绑项目身份

**Files:**
- Modify: `backend/overlay/service.py`（5 写方法）
- Modify: `backend/overlay/api.py`（写端点 + execute 捕获 ProjectMismatch）
- Test: `backend/tests/test_hardening_overlay_expected.py`

**Interfaces:**
- Consumes: `transact_expected_active`（project_store:474）、`ProjectMismatch`。
- Produces: overlay 写方法/端点透传 `expected_project_id`，锁内绑项目身份。

**改法（对每个写方法机械套用；READ 实际签名）：**
- 服务方法加末位参 `expected_project_id=None`；把结尾的 `return self.store.transact_active(update)` 改为 `return self.store.transact_expected_active(expected_project_id, update)`。涉及：`save_type`、`save_instance`、`clear_instance`、`batch_instances`、`save_media_policy`（`clear_instance` 若委托 save_instance 则只需上游透传）。
- api 端点从 body 读 `data.get("expected_project_id")` 传给对应 service 方法。
- api `execute()` 增分支：`except ProjectMismatch as e: return jsonify({"error":"project changed","expected":e.expected,"actual":e.actual}), 409`；`from project_store import ProjectMismatch` 加到 api.py 顶部。

- [ ] **Step 1: 写失败测试** `backend/tests/test_hardening_overlay_expected.py`

```python
def test_overlay_save_type_endpoint_409(client, store, monkeypatch):
    # 需要类型启用 overlay 能力；用 store 造一个带能力的类型再打端点
    import app
    monkeypatch.setitem(app._object_types, "TB",
                        {"rid": "TB", "name": "T", "injected_interfaces": ["I3D_Representable", "I3D_Overlay"]})
    # 直接打端点：带错 expected_project_id → 409
    r = client.put("/api/v2/overlays/object-types/TB", json={
        "config": {}, "expected_revision": 0, "expected_project_id": "p_other"})
    assert r.status_code == 409
    assert r.get_json().get("expected") == "p_other"
```

> 若该端点因能力/校验在 expected 之前返回其它码，实现者据实调整前置条件（目的是覆盖「带错 expected → 409 project changed」这条路径）。

- [ ] **Step 2: 跑测试确认失败** → `cd backend && python -m pytest tests/test_hardening_overlay_expected.py -v`（Expected: FAIL，端点未读/透传 expected）

- [ ] **Step 3: 按上面「改法」改 `overlay/service.py` 5 写方法 + `overlay/api.py` 端点与 execute**

- [ ] **Step 4: 跑测试通过 + 后端全量不回归** → `cd backend && python -m pytest tests/test_hardening_overlay_expected.py tests/test_overlay.py -v && python -m pytest tests/ -q`（FOREGROUND）

- [ ] **Step 5: 提交** → `git commit -m "feat(backend): F1 overlay 写绑 expected_project_id（transact_expected_active + 端点 409）"`

---

### Task 3（组 C）: F1 —— scene 服务/端点绑项目身份

**Files:**
- Modify: `backend/scene_interaction/service.py`（6 写方法）
- Modify: `backend/scene_interaction/api.py`（写端点 + execute 捕获 ProjectMismatch）
- Test: `backend/tests/test_hardening_scene_expected.py`

**改法（同 Task 2 套路）：**
- 服务方法 `save_roaming`/`create_route`/`update_route`/`delete_route`/`review_route`/`set_default_route` 加 `expected_project_id=None`；`self.store.transact_active(update)` → `self.store.transact_expected_active(expected_project_id, update)`。
- api 各写端点读 `data.get("expected_project_id")` 透传；`execute()` 增 `except ProjectMismatch → 409 {expected,actual}`；import ProjectMismatch。

- [ ] **Step 1: 写失败测试** `backend/tests/test_hardening_scene_expected.py`

```python
def test_scene_save_roaming_endpoint_409(client, store):
    r = client.put("/api/v2/scene-interactions/roaming", json={
        "config": {}, "expected_revision": 0, "expected_project_id": "p_other"})
    assert r.status_code == 409
    assert r.get_json().get("expected") == "p_other"
```

- [ ] **Step 2: 跑确认失败** → `cd backend && python -m pytest tests/test_hardening_scene_expected.py -v`

- [ ] **Step 3: 按「改法」改 `scene_interaction/service.py` 6 写方法 + `scene_interaction/api.py`**

- [ ] **Step 4: 通过 + 后端全量不回归** → `cd backend && python -m pytest tests/test_hardening_scene_expected.py tests/test_scene_interaction.py -v && python -m pytest tests/ -q`（FOREGROUND）

- [ ] **Step 5: 提交** → `git commit -m "feat(backend): F1 scene 写绑 expected_project_id（transact_expected_active + 端点 409）"`

---

### Task 4（组 D）: MCP overlay/scene 写工具补 expected_project_id

**Files:**
- Modify: `mcp/ontotwin_mcp/tools/overlay.py`
- Modify: `mcp/ontotwin_mcp/tools/scene.py`
- Test: `mcp/tests/test_tools_overlay.py`、`mcp/tests/test_tools_scene.py`（追加）

**Interfaces:**
- Produces: overlay 写工具（save_overlay_type_config/save_overlay_instance_override/clear_overlay_instance_override/batch_overlay_instance_override/save_overlay_media_policy）与 scene 写工具（save_roaming_config/create_route/update_route/delete_route/review_route/set_default_route）加 `expected_project_id: str = ""`，非空入 body。

- [ ] **Step 1: 写失败测试**（追加到各自测试文件）

```python
# test_tools_overlay.py 追加
def test_save_overlay_type_config_threads_expected():
    c = C(); mcp = build_server(c)
    _t(mcp, "save_overlay_type_config")("rid.a", {"slots": {}}, 4, expected_project_id="p1")
    body = c.calls[-1][2]
    assert body == {"config": {"slots": {}}, "expected_revision": 4, "expected_project_id": "p1"}


def test_save_overlay_type_config_omits_empty_expected():
    c = C(); mcp = build_server(c)
    _t(mcp, "save_overlay_type_config")("rid.a", {"slots": {}}, 4)
    assert "expected_project_id" not in c.calls[-1][2]
```
```python
# test_tools_scene.py 追加
def test_save_roaming_config_threads_expected():
    c = C(); mcp = build_server(c)
    _t(mcp, "save_roaming_config")({"spawn": {}}, 7, expected_project_id="p1")
    body = c.calls[-1][2]
    assert body == {"config": {"spawn": {}}, "expected_revision": 7, "expected_project_id": "p1"}
```

- [ ] **Step 2: 跑确认失败** → `cd mcp && python -m pytest tests/test_tools_overlay.py tests/test_tools_scene.py -k expected -v`

- [ ] **Step 3: 给 overlay.py / scene.py 的写工具加 `expected_project_id: str = ""` 参数**，body 非空时加 `body["expected_project_id"] = expected_project_id`。示例（save_overlay_type_config）：

```python
    def save_overlay_type_config(object_type_rid: str, config: dict,
                                 expected_revision: int, expected_project_id: str = "") -> dict:
        """..."""
        body = {"config": config, "expected_revision": expected_revision}
        if expected_project_id:
            body["expected_project_id"] = expected_project_id
        return client.put_json(
            "save_overlay_type_config",
            f"/api/v2/overlays/object-types/{quote(object_type_rid, safe='/')}", json=body)
```
对每个 overlay/scene 写工具套用（batch 的 body 也加；delete/review/set_default 同理）。

- [ ] **Step 4: 跑测试通过 + mcp 全量不回归** → `cd mcp && python -m pytest tests/ -q`

- [ ] **Step 5: 提交** → `git commit -m "feat(mcp): overlay/scene 写工具补可选 expected_project_id（绑项目身份）"`

---

### Task 5（组 E）: 标注 B + skill + 修正措辞

**Files:**
- Modify: `backend/app.py`（`_rederive_components` 注释）
- Modify: `mcp/skills/ontotwin-nexus/SKILL.md`

- [ ] **Step 1: `_rederive_components`（app.py:967）加注释**

```python
def _rederive_components():
    # 已知限制（并发）：本函数独立取当前激活项目、逐步 set_components/mint_instances/update_raw_state，
    # 无整段项目护栏。调用它的 profile PUT / transform PUT 在初始护栏通过后若激活项目被切，
    # 重算可能落到新项目。多步非原子，接受为已知限制（单用户顺序调用风险低）。
```

- [ ] **Step 2: SKILL.md 增「并发已知限制」小节 + 修正 M1/M2 措辞**

在文件合适处（如末尾"金规/限制"区）追加：

````markdown
## 并发已知限制

- **配置/分区写已绑项目身份**：overlay/scene/routes/zones 的写在 `expected_project_id` 非空时锁内校验激活项目（防"切项目后误写"）。`expected_revision` 只防**同项目**的丢失更新——跨项目漂移靠 `expected_project_id` 兜底，写这些配置时建议一并带上（从 `get_active_project` 取）。
- **多步写端点非整段原子**：CAD 批量投产（`spawn_cad_instances`）、空间回写（`writeback_instance_transform`）、以及 `set_spatial_profile`/`set_instance_transform` 触发的全场重算，是多步逐个加锁。中途切激活项目可能"部分写 + 409"——重试前请核对已写状态（如 `list_instances`），避免重复 id 冲突。
````

同时把 SKILL.md / 相关 docstring 里"revision 兼作跨项目护栏"之类措辞修正为上述准确表述。

- [ ] **Step 3: 跑 mcp 全量确认不回归** → `cd mcp && python -m pytest tests/ -q`

- [ ] **Step 4: 提交** → `git commit -m "docs: 标注多步非原子已知限制 + 修正 revision 护栏措辞（F4-6 走 B）"`

---

## 交付后（人工，需确认）

- **部署到 88.66**：`project_store.py` + `app.py` + `overlay/` + `scene_interaction/` + `zone_management/` scp（paramiko）+ restart；部署前确认。
- 重打发行包：`mcp/build-dist.ps1`。
- 部署后探针：`assign_zones` / `save_overlay_type_config` / `save_roaming_config` / `calibrate_spatial_frame` 带错 expected → 期望 409 `NEXUS_PROJECT_CHANGED`、不落库/不改内存。

---

## Self-Review 记录

- **Spec 覆盖**：spec §3.1 F3 ↔ Task 1；§3.2 F2 ↔ Task 1；§3.3 F1 后端 ↔ Task 2/3、MCP ↔ Task 4；§3.4 标注 ↔ Task 5。errors/client/PG 零改动。
- **类型一致**：`expected_project_id: str=""`（MCP，非空入 body）/ `=None`（后端方法）；overlay/scene 工具在既有 `expected_revision` 之外**追加** expected_project_id，不动 revision。
- **占位符**：Task 1/4/5 含完整代码；Task 2/3 给精确「改法」+ 方法清单 + api 统一改点（机械套用，实现者 READ 实际签名）。
- **PG 平价**：assign_zone/transact_*/get_frame 均未被 PG 覆盖，无平价。
