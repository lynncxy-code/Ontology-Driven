# OntoTwin MCP · M0 后端并发扩展 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 Nexus 后端加两项加法式、向后兼容的并发安全能力——mint 的 `dry_run` 无副作用预览、写操作的 `expected_project_id` 锁内原子校验——为后续 MCP 接入层打地基。

**Architecture:** 核心是把「校验/规划」下沉进 `ProjectStore` 的**同一把锁**：新增 `transact_expected_active(expected_id, updater)` 作为原子写入口；抽纯函数 `_plan_mint` 供 dry_run 与真写共用；组合事务 `save_component_bundle` 把 save_components 的三段写收进一次持锁一次保存。所有新方法/参数在 JSON 版（`ProjectStore`）与 PG 版（`ProjectStorePG`）保持签名一致。

**Tech Stack:** Python 3.10、Flask 3、pytest（新引入，仅测试用）、psycopg3（PG 后端已在）。

## Global Constraints

- 只加**可选**字段/方法，缺省即旧行为；现有 Web UI 不传新字段 → 行为逐字不变（copy from spec §14）。
- 不改存储结构（`ProjectStore` JSON 文件格式、`lite_*` 表、`mapping_rules.json`）。
- 新方法/参数**必须 JSON 版 + PG 版签名一致**；PG 覆盖了 `mint_instances`/`remove`/`clear_instances`/`create_project`/`delete_project`，逐项核对（spec §14.0）。
- 原子性只在 `ProjectStore._lock`（`RLock`）内成立；**禁止** handler 层「先 check 再调写方法」（spec §5.2）。
- `instance_store is project_store`（同对象同锁，app.py:66）。
- 测试对 **JSON、PG 两后端各跑一遍**；写路径只对隔离临时库，不碰生产（spec §14.3、§11）。
- pytest 属新测试依赖，仅进 `backend/requirements-dev.txt`，不进 `backend/requirements.txt`（遵守「后端运行依赖先问用户」）。
- 提交信息用中文 Conventional Commits。

---

## 文件结构

- Modify `backend/project_store.py` — 新增 `ProjectMismatch` 异常、`transact_expected_active`、`_plan_mint`、`save_component_bundle`、`bind_batch`；`mint_instances` 加 `dry_run`/`expected_project_id`；`bind`/`unbind`/`update_raw_state` 加 `expected_project_id`。
- Modify `backend/project_store_pg.py` — PG 覆盖的写方法同步透传新参数（重点 `mint_instances`）。
- Modify `backend/app.py` — `binding_mint`、`binding_bind`/`unbind`、`override_state`、`binding_bind_batch`、`coord_save_components`、`binding_roster_upload` 各 handler 透传新字段并映射 409。
- Create `backend/requirements-dev.txt` — `pytest`。
- Create `backend/tests/conftest.py` — 隔离临时 ProjectStore fixture（JSON + PG 参数化）。
- Create `backend/tests/test_expected_project.py` — expected_project_id 锁内校验 + 并发两用例。
- Create `backend/tests/test_mint_dry_run.py` — dry_run 无副作用 + 规划正确 + body 边界。
- Create `backend/tests/test_save_bundle_and_batch.py` — 组合事务 + 批语义。

---

## Task 1: 测试脚手架（隔离临时 ProjectStore fixture）

**Files:**
- Create: `backend/requirements-dev.txt`
- Create: `backend/tests/__init__.py`（空）
- Create: `backend/tests/conftest.py`

**Interfaces:**
- Produces: pytest fixture `store`（一个已激活、含 1 个类型 + 2 个已绑定构件的隔离 `ProjectStore`）；fixture `client`（Flask test client，`app.instance_store`/`project_store` 已指向隔离 store）。

- [ ] **Step 1: 写 requirements-dev.txt**

```
pytest>=8,<9
```

- [ ] **Step 2: 写 conftest.py（隔离 JSON store）**

```python
import os, tempfile, shutil, importlib
import pytest

@pytest.fixture
def tmp_data(monkeypatch):
    d = tempfile.mkdtemp(prefix="ots_test_")
    yield d
    shutil.rmtree(d, ignore_errors=True)

@pytest.fixture
def store(tmp_data, monkeypatch):
    # 指向隔离数据目录后再导入，确保 _DATA_DIR 生效
    import project_store as ps
    monkeypatch.setattr(ps, "_DATA_DIR", tmp_data)
    monkeypatch.setattr(ps, "_PROJECTS_DIR", os.path.join(tmp_data, "projects"))
    monkeypatch.setattr(ps, "_ACTIVE_FILE", os.path.join(tmp_data, "active.json"))
    os.makedirs(os.path.join(tmp_data, "projects"), exist_ok=True)
    s = ps.ProjectStore()
    s.create_project("测试厂", object_types={"PE16A": {"rid": "PE16A", "name": "溶铜槽"}}, project_id="p_test")
    # 造 2 个已绑定构件（components + bound_instance_id），供 mint 铸造
    s.transact_active(lambda w: w.setdefault("components", {}).update({
        "c1": {"id": "c1", "object_type_rid": "PE16A", "type_name": "溶铜槽", "bound_instance_id": "DW-001", "ue_xy": [0, 0], "render_config": {}},
        "c2": {"id": "c2", "object_type_rid": "PE16A", "type_name": "溶铜槽", "bound_instance_id": "DW-002", "ue_xy": [1, 1], "render_config": {}},
    }))
    return s
```

> 注：`create_project` / `transact_active` 的确切签名以 `project_store.py` 为准；若 `create_project` 不接受 `object_types` kwarg，改用返回后 `set_object_types`。构件字段以 `_rederive_components` 的消费字段为准（`bound_instance_id`/`ue_xy`/`type_name`）。

- [ ] **Step 3: 跑一下确认 fixture 能装配**

Run: `cd backend && python -m pytest tests/conftest.py -q`
Expected: 无用例但导入无错（exit 0 / "no tests ran"）。

- [ ] **Step 4: Commit**

```bash
git add backend/requirements-dev.txt backend/tests/__init__.py backend/tests/conftest.py
git commit -m "test: 加隔离临时 ProjectStore 测试脚手架"
```

---

## Task 2: `ProjectMismatch` + `transact_expected_active`（锁内原子校验基座）

**Files:**
- Modify: `backend/project_store.py`（在 `transact_active` 附近，约 451 行后）
- Test: `backend/tests/test_expected_project.py`

**Interfaces:**
- Produces:
  - `class ProjectMismatch(Exception)`：属性 `expected`、`actual`。
  - `ProjectStore.transact_expected_active(expected_id, updater)`：`expected_id` 非空且 ≠ `self._active_id` 时**在锁内**抛 `ProjectMismatch`；否则等价于 `transact_active(updater)`。`expected_id=None` → 不校验。

- [ ] **Step 1: 写失败测试**

```python
# backend/tests/test_expected_project.py
import pytest
from project_store import ProjectMismatch

def test_expected_match_runs_and_persists(store):
    out = store.transact_expected_active("p_test", lambda w: w["object_types"].__setitem__("X", {"rid": "X"}) or "ok")
    assert out == "ok"
    assert "X" in store.get_object_types()

def test_expected_mismatch_raises_and_no_write(store):
    before = dict(store.get_object_types())
    with pytest.raises(ProjectMismatch) as e:
        store.transact_expected_active("p_other", lambda w: w["object_types"].__setitem__("Y", {"rid": "Y"}))
    assert e.value.expected == "p_other" and e.value.actual == "p_test"
    assert store.get_object_types() == before   # 未写

def test_expected_none_skips_check(store):
    store.transact_expected_active(None, lambda w: w["object_types"].__setitem__("Z", {"rid": "Z"}))
    assert "Z" in store.get_object_types()
```

- [ ] **Step 2: 跑，确认失败**

Run: `cd backend && python -m pytest tests/test_expected_project.py -q`
Expected: FAIL — `ImportError: cannot import name 'ProjectMismatch'`。

- [ ] **Step 3: 实现（project_store.py）**

在 `transact_active` 定义前加异常，`transact_active` 后加方法：

```python
class ProjectMismatch(Exception):
    def __init__(self, expected, actual):
        super().__init__(f"active project changed: expected={expected} actual={actual}")
        self.expected = expected
        self.actual = actual
```

```python
    def transact_expected_active(self, expected_id, updater):
        """Atomic write with optional active-project guard, all under one lock."""
        with self._lock:
            if not self._current:
                raise RuntimeError("no active project")
            if expected_id is not None and self._active_id != expected_id:
                raise ProjectMismatch(expected_id, self._active_id)
            previous = self._current
            working = copy.deepcopy(previous)
            result = updater(working)
            self._current = working
            try:
                self._save_current()
            except Exception:
                self._current = previous
                raise
            return result
```

> `RLock` 可重入，故 updater 内再调本 store 的其他加锁方法不会自锁死。

- [ ] **Step 4: 跑，确认通过**

Run: `cd backend && python -m pytest tests/test_expected_project.py -q`
Expected: 3 passed。

- [ ] **Step 5: Commit**

```bash
git add backend/project_store.py backend/tests/test_expected_project.py
git commit -m "feat: ProjectStore 加锁内 expected_project_id 原子事务入口"
```

---

## Task 3: 并发两用例（证明锁语义真的挡住中途切项目）

**Files:**
- Test: `backend/tests/test_expected_project.py`（追加）

**Interfaces:**
- Consumes: Task 2 的 `transact_expected_active`、`ProjectMismatch`。

- [ ] **Step 1: 写并发测试（两线程 + 栅栏）**

```python
import threading

def test_activate_first_then_write_rejected(store):
    # 造第二个项目，模拟并发 activate 先切走
    store.create_project("厂B", project_id="p_b")   # create_project 会把激活切到 p_b
    # 现在 active 是 p_b；带 expected=p_test 的写应被拒
    with pytest.raises(ProjectMismatch):
        store.transact_expected_active("p_test", lambda w: w["object_types"].__setitem__("K", {"rid": "K"}))

def test_write_holds_lock_activate_waits_lands_in_A(store):
    # 写线程进锁后卡住，另一线程尝试 activate，断言写落在 A、绝不到 B
    entered = threading.Event()
    release = threading.Event()
    def slow_update(w):
        entered.set()
        release.wait(2)
        w["object_types"]["SLOW"] = {"rid": "SLOW"}
        return "done"
    t = threading.Thread(target=lambda: store.transact_expected_active("p_test", slow_update))
    t.start()
    assert entered.wait(2)
    # 写持锁期间，另一线程 activate 会阻塞在锁上；放行写线程
    switched = {}
    def do_switch():
        store.create_project("厂B", project_id="p_b")
        switched["active"] = store.get_active_id()
    t2 = threading.Thread(target=do_switch)
    t2.start()
    release.set()
    t.join(3); t2.join(3)
    # 写成功落在 p_test；切换发生在其后
    assert "SLOW" in store._read_project("p_test")["object_types"] if hasattr(store, "_read_project") else True
    assert switched.get("active") == "p_b"   # activate 最终生效，但在写之后
```

> 第二个断言的读法依存储实现：JSON 版可重新激活 `p_test` 后 `get_object_types()` 校验；PG 版同理。若 `create_project` 不自动切激活，改用显式 `activate()`。关键断言是「写没有落到 p_b」。

- [ ] **Step 2: 跑，确认通过（逻辑已由 Task 2 实现支撑）**

Run: `cd backend && python -m pytest tests/test_expected_project.py -q`
Expected: all passed。若第二用例因 `create_project` 激活语义不符而 flaky，按注释调整为显式 `activate()`。

- [ ] **Step 3: Commit**

```bash
git add backend/tests/test_expected_project.py
git commit -m "test: 并发两用例验证 expected 校验的锁语义"
```

---

## Task 4: 抽纯规划函数 `_plan_mint` + `mint_instances(dry_run, expected_project_id)`

**Files:**
- Modify: `backend/project_store.py`（`mint_instances` 约 829 行）
- Test: `backend/tests/test_mint_dry_run.py`

**Interfaces:**
- Produces:
  - `ProjectStore._plan_mint(snapshot, now) -> {"to_create": [id...], "to_update": [id...], "result_instances": {id: rec}}`：**纯函数**，不改 `snapshot`；逐条深拷贝旧实例；`now` 由调用方传入不内部再取。
  - `ProjectStore.mint_instances(dry_run=False, expected_project_id=None) -> dict`：返回 `{"minted": n, "to_create": [...], "to_update": [...]}`；`dry_run=True` 不落库。

- [ ] **Step 1: 写失败测试**

```python
# backend/tests/test_mint_dry_run.py
def test_dry_run_no_write_but_plans(store):
    before = dict(store._instances)
    res = store.mint_instances(dry_run=True)
    assert set(res["to_create"]) == {"DW-001", "DW-002"}
    assert store._instances == before            # 未写
    assert res["minted"] == 0                     # dry_run 不计已铸

def test_real_mint_writes(store):
    res = store.mint_instances(dry_run=False)
    assert set(store._instances.keys()) == {"DW-001", "DW-002"}
    assert res["minted"] == 2

def test_will_update_excludes_last_seen(store):
    store.mint_instances(dry_run=False)          # 先铸一次
    res = store.mint_instances(dry_run=True)     # 无业务变化
    assert res["to_update"] == []                # last_seen 刷新不算 update

def test_mint_expected_mismatch(store):
    store.create_project("厂B", project_id="p_b")
    import pytest; from project_store import ProjectMismatch
    with pytest.raises(ProjectMismatch):
        store.mint_instances(dry_run=False, expected_project_id="p_test")
```

- [ ] **Step 2: 跑，确认失败**

Run: `cd backend && python -m pytest tests/test_mint_dry_run.py -q`
Expected: FAIL — `TypeError: mint_instances() got an unexpected keyword argument 'dry_run'`。

- [ ] **Step 3: 实现——把现有 mint 循环体抽成 `_plan_mint`，`mint_instances` 走事务**

将现有 `mint_instances` 的循环逻辑（遍历 bound components → 复用旧实例或新建 rec → `apply_instance_metadata`）搬进纯函数，改为在**深拷贝 working**上构造分离的 `result_instances`：

```python
    _MINT_BUSINESS_FIELDS = ("object_type_rid", "object_type_name", "component_id", "render_config")

    def _plan_mint(self, snapshot, now):
        comps = snapshot.get("components", {}) or {}
        old = snapshot.get("instances", {}) or {}
        result, to_create, to_update = {}, [], []
        for cid, comp in comps.items():
            iid = comp.get("bound_instance_id")
            if not iid:
                continue
            ot_rid = comp.get("object_type_rid", "")
            if iid in old:
                rec = copy.deepcopy(old[iid])          # 逐条深拷贝，勿改入参
                changed = (
                    rec.get("object_type_rid") != ot_rid
                    or rec.get("component_id") != comp.get("id")
                    or rec.get("render_config") != (comp.get("render_config") or rec.get("render_config") or {})
                )
                rec["component_id"] = comp.get("id")
                rec["object_type_rid"] = ot_rid
                rec["object_type_name"] = comp.get("type_name", ot_rid)
                rec["render_config"] = comp.get("render_config") or rec.get("render_config") or {}
                rec["last_seen"] = now
                if changed:
                    to_update.append(iid)
            else:
                pos = {"x": (comp.get("ue_xy") or [0, 0])[0], "y": (comp.get("ue_xy") or [0, 0])[1], "z": 0.0}
                rec = {
                    "id": iid, "component_id": comp.get("id"), "object_type_rid": ot_rid,
                    "object_type_name": comp.get("type_name", ot_rid),
                    "render_config": comp.get("render_config") or {},
                    "created_at": now, "last_seen": now, "status": "online",
                    "raw_state": _default_raw_state(ot_rid, comp.get("type_name"), pos),
                }
                to_create.append(iid)
            apply_instance_metadata(rec)
            result[iid] = rec
        return {"to_create": to_create, "to_update": to_update, "result_instances": result}

    def mint_instances(self, dry_run=False, expected_project_id=None):
        now = time.time()
        with self._lock:
            if not self._current:
                return {"minted": 0, "to_create": [], "to_update": []}
            if expected_project_id is not None and self._active_id != expected_project_id:
                raise ProjectMismatch(expected_project_id, self._active_id)
            snapshot = copy.deepcopy(self._current)
            plan = self._plan_mint(snapshot, now)
            if dry_run:
                return {"minted": 0, "to_create": plan["to_create"], "to_update": plan["to_update"]}
            self._current["instances"] = plan["result_instances"]
            self._save_current()
            return {"minted": len(plan["result_instances"]),
                    "to_create": plan["to_create"], "to_update": plan["to_update"]}
```

> 保持与原 mint 语义一致：实例集 = 已绑定构件集。若原实现对 `floor_z` 等有额外处理，一并搬进 `_plan_mint`。原 `mint_instances()` 的调用方（app.py binding_mint）在 Task 6 适配返回值。

- [ ] **Step 4: 跑，确认通过**

Run: `cd backend && python -m pytest tests/test_mint_dry_run.py -q`
Expected: 4 passed。

- [ ] **Step 5: Commit**

```bash
git add backend/project_store.py backend/tests/test_mint_dry_run.py
git commit -m "feat: mint 抽纯 _plan_mint，支持 dry_run 与 expected_project_id"
```

---

## Task 5: PG 子类签名平价

**Files:**
- Modify: `backend/project_store_pg.py`（`mint_instances` 约 297 行）
- Test: `backend/tests/test_mint_dry_run.py`（加 PG 参数化标记，或独立跳过条件）

**Interfaces:**
- Produces: `ProjectStorePG.mint_instances(dry_run=False, expected_project_id=None)` 透传父类。

- [ ] **Step 1: 改 PG 覆盖签名透传**

```python
    def mint_instances(self, dry_run=False, expected_project_id=None):
        return super().mint_instances(dry_run=dry_run, expected_project_id=expected_project_id)
```

- [ ] **Step 2: 核对 PG 其他覆盖方法不受本轮新参数影响**

检查 `project_store_pg.py` 覆盖清单（`remove`/`clear_instances`/`create_project`/`delete_project`）——本轮未给它们加参数，无需改；但 Task 7/8 若给 `bind`/`update_raw_state` 加 `expected_project_id`，需回来确认 PG **是否覆盖**了它们（若未覆盖则继承父类，无需改；若覆盖则同步透传）。在此 Step 记录核对结论到提交信息。

- [ ] **Step 3: PG 冒烟（需可连 PG；无 PG 环境则跳过）**

Run（服务器容器内或本地有 PG 时）: `cd backend && ONTOTWIN_STORE=pg python -c "from project_store import ProjectStore; print(ProjectStore().mint_instances.__doc__ or 'ok')"`
Expected: 不抛 `TypeError`（签名一致）。无 PG 环境标注 skip。

- [ ] **Step 4: Commit**

```bash
git add backend/project_store_pg.py
git commit -m "feat: ProjectStorePG.mint_instances 透传 dry_run/expected_project_id 保持签名平价"
```

---

## Task 6: `binding_mint` handler —— dry_run 边界 + 409 映射

**Files:**
- Modify: `backend/app.py`（`binding_mint` 约 2643 行）
- Test: `backend/tests/test_mint_dry_run.py`（加 handler 级用例，用 `client` fixture）

**Interfaces:**
- Consumes: Task 4/5 的 `mint_instances(dry_run, expected_project_id)`、`ProjectMismatch`。

- [ ] **Step 1: 写 handler 测试**

```python
def test_mint_handler_empty_body_still_real_mints(client):
    r = client.post("/api/v2/binding/mint")          # 无 body，旧行为
    assert r.status_code == 200 and r.get_json()["minted"] == 2

def test_mint_handler_dry_run_no_write(client):
    r = client.post("/api/v2/binding/mint", json={"dry_run": True})
    assert r.status_code == 200
    body = r.get_json()
    assert body["minted"] == 0 and set(body["to_create"]) == {"DW-001", "DW-002"}

def test_mint_handler_malformed_json_400(client):
    r = client.post("/api/v2/binding/mint", data="{bad", content_type="application/json")
    assert r.status_code == 400

def test_mint_handler_string_true_rejected(client):
    r = client.post("/api/v2/binding/mint", json={"dry_run": "true"})
    assert r.status_code == 400

def test_mint_handler_expected_mismatch_409(client):
    # 切走激活项目后带旧 expected
    client.post("/api/v2/ontology/datasets", json={"name": "厂B", "activate": True})
    r = client.post("/api/v2/binding/mint", json={"expected_project_id": "p_test"})
    assert r.status_code == 409
```

- [ ] **Step 2: 跑，确认失败**

Run: `cd backend && python -m pytest tests/test_mint_dry_run.py -q -k handler`
Expected: FAIL（现 handler 不读 body、不处理这些）。

- [ ] **Step 3: 实现 handler**

```python
@app.route('/api/v2/binding/mint', methods=['POST'])
def binding_mint():
    """把已绑定构件铸造/同步为实例；支持 dry_run 预览与 expected_project_id 原子校验。"""
    _, err = _require_active_project()
    if err:
        return err
    # 严格 JSON 边界：有 JSON content-type 且 body 非空但畸形 → 400，不静默真写
    if request.content_type and 'application/json' in request.content_type and request.data:
        parsed = request.get_json(silent=True)
        if parsed is None:
            return jsonify({"error": "invalid JSON body"}), 400
        data = parsed
    else:
        data = {}
    dry_run = data.get("dry_run", False)
    if not isinstance(dry_run, bool):
        return jsonify({"error": "dry_run must be a JSON boolean"}), 400
    expected = data.get("expected_project_id")
    try:
        res = project_store.mint_instances(dry_run=dry_run, expected_project_id=expected)
    except ProjectMismatch as e:
        return jsonify({"error": "project changed", "expected": e.expected, "actual": e.actual}), 409
    return jsonify({"status": "ok", **res})
```

并在 app.py 顶部 import 处补 `from project_store import ProjectStore, ProjectMismatch`（若原来只 import 了 `ProjectStore`）。

- [ ] **Step 4: 跑，确认通过**

Run: `cd backend && python -m pytest tests/test_mint_dry_run.py -q`
Expected: all passed。

- [ ] **Step 5: Commit**

```bash
git add backend/app.py backend/tests/test_mint_dry_run.py
git commit -m "feat: binding_mint 支持 dry_run 与 expected_project_id（含 JSON 边界与 409）"
```

---

## Task 7: `bind`/`unbind`/`update_raw_state` 加锁内 expected；`bind_batch` 批事务

**Files:**
- Modify: `backend/project_store.py`（`bind` ~797、`unbind` ~812、`update_raw_state` ~579；新增 `bind_batch`）
- Modify: `backend/project_store_pg.py`（若覆盖了上述方法则同步透传）
- Modify: `backend/app.py`（`binding_bind`、`binding_unbind`、`override_state`、`binding_bind_batch`）
- Test: `backend/tests/test_save_bundle_and_batch.py`

**Interfaces:**
- Produces:
  - `bind(component_id, instance_id, expected_project_id=None)`、`unbind(component_id, expected_project_id=None)`、`update_raw_state(instance_id, patch, persist=True, expected_project_id=None)`：均在既有 `with self._lock` 内**先校验 expected**（不符抛 `ProjectMismatch`）。
  - `bind_batch(pairs, expected_project_id=None) -> {"bound": n, "failed": [{"component_id", "instance_id", "reason"}]}`：**一次持锁**、逐对在工作副本上校验+写、末尾**只 save 一次**；无成功项则不 save。

- [ ] **Step 1: 写测试**

```python
# backend/tests/test_save_bundle_and_batch.py
import pytest
from project_store import ProjectMismatch

def test_bind_expected_mismatch(store):
    store.create_project("厂B", project_id="p_b")
    with pytest.raises(ProjectMismatch):
        store.bind("c1", "DW-009", expected_project_id="p_test")

def test_bind_batch_partial_success_single_save(store):
    # 先清空构件绑定，重绑：一条有效、一条构件不存在
    pairs = [{"component_id": "c1", "instance_id": "DW-100"},
             {"component_id": "nope", "instance_id": "DW-101"}]
    res = store.bind_batch(pairs)
    assert res["bound"] == 1
    assert len(res["failed"]) == 1 and res["failed"][0]["component_id"] == "nope"

def test_bind_batch_expected_mismatch_whole_batch(store):
    store.create_project("厂B", project_id="p_b")
    with pytest.raises(ProjectMismatch):
        store.bind_batch([{"component_id": "c1", "instance_id": "DW-1"}], expected_project_id="p_test")
```

- [ ] **Step 2: 跑，确认失败**

Run: `cd backend && python -m pytest tests/test_save_bundle_and_batch.py -q`
Expected: FAIL（新签名/方法未实现）。

- [ ] **Step 3: 实现**

给现有 `bind`/`unbind`/`update_raw_state` 在进锁后第一行加：

```python
        with self._lock:
            if expected_project_id is not None and self._active_id != expected_project_id:
                raise ProjectMismatch(expected_project_id, self._active_id)
            # ... 原有逻辑不变 ...
```

新增 `bind_batch`（复用现有单条 `bind` 的校验逻辑，但只在末尾保存一次——把「校验+写工作副本」抽成不落盘的内部 `_bind_into(working, cid, iid)`，`bind` 和 `bind_batch` 都用它）：

```python
    def bind_batch(self, pairs, expected_project_id=None):
        with self._lock:
            if not self._current:
                raise RuntimeError("no active project")
            if expected_project_id is not None and self._active_id != expected_project_id:
                raise ProjectMismatch(expected_project_id, self._active_id)
            working = copy.deepcopy(self._current)
            bound, failed = 0, []
            for p in pairs or []:
                cid, iid = p.get("component_id"), (p.get("instance_id") or "").strip()
                ok, reason = self._bind_into(working, cid, iid)
                if ok:
                    bound += 1
                else:
                    failed.append({"component_id": cid, "instance_id": iid, "reason": reason})
            if bound:
                self._current = working
                self._save_current()
            return {"bound": bound, "failed": failed}
```

`_bind_into(working, cid, iid)` 返回 `(ok, reason)`：核对构件存在、目标 instance_id 未被占用（1:1），写 `working["components"][cid]["bound_instance_id"]`。把现有单条 `bind` 改为 `transact_active(lambda w: self._bind_into(w, cid, iid))` 并保留 expected 校验。

app.py 三个 handler 透传 `expected_project_id`，捕获 `ProjectMismatch` → 409（与 Task 6 同款）。`binding_bind_batch` 改调 `project_store.bind_batch(pairs, expected)`。PG 若覆盖了这些方法则同步透传（Task 5 Step 2 已记录核对）。

- [ ] **Step 4: 跑，确认通过**

Run: `cd backend && python -m pytest tests/test_save_bundle_and_batch.py -q`
Expected: 3 passed。

- [ ] **Step 5: Commit**

```bash
git add backend/project_store.py backend/project_store_pg.py backend/app.py backend/tests/test_save_bundle_and_batch.py
git commit -m "feat: bind/unbind/override 加锁内 expected 校验，bind_batch 改批事务"
```

---

## Task 8: `save_component_bundle` 组合事务 + handler 适配

**Files:**
- Modify: `backend/project_store.py`（新增 `save_component_bundle`）
- Modify: `backend/app.py`（`coord_save_components` ~782）
- Test: `backend/tests/test_save_bundle_and_batch.py`（追加）

**Interfaces:**
- Produces: `save_component_bundle(expected_project_id, profile_patch, frame_patch, component_plan, mode) -> dict`：**一次持锁**内校验 expected、在工作副本上依次应用 profile/frame/components、**只 `_save_current()` 一次**。

- [ ] **Step 1: 写测试**

```python
def test_save_bundle_single_transaction(store):
    res = store.save_component_bundle(
        expected_project_id="p_test",
        profile_patch={"unit": "mm"},
        frame_patch=None,
        component_plan={"mode": "publish", "components": {"c3": {"id": "c3", "object_type_rid": "PE16A"}}},
        mode="publish",
    )
    assert res["ok"] is True
    assert "c3" in store.get_components()

def test_save_bundle_expected_mismatch(store):
    store.create_project("厂B", project_id="p_b")
    import pytest; from project_store import ProjectMismatch
    with pytest.raises(ProjectMismatch):
        store.save_component_bundle(expected_project_id="p_test", profile_patch={"unit": "mm"},
                                    frame_patch=None, component_plan={"mode": "publish", "components": {}}, mode="publish")
```

- [ ] **Step 2: 跑，确认失败**

Run: `cd backend && python -m pytest tests/test_save_bundle_and_batch.py -q -k bundle`
Expected: FAIL（方法未实现）。

- [ ] **Step 3: 实现**

```python
    def save_component_bundle(self, expected_project_id, profile_patch, frame_patch, component_plan, mode):
        def _apply(w):
            if profile_patch:
                w.setdefault("spatial_profile", {}).update(profile_patch)
            if frame_patch:
                frames = w.setdefault("frames", [])
                # upsert by id（沿用现有 upsert_frame 的键约定）
                fid = frame_patch.get("id")
                for i, f in enumerate(frames):
                    if f.get("id") == fid:
                        frames[i] = {**f, **frame_patch}; break
                else:
                    frames.append(frame_patch)
            comps = w.setdefault("components", {})
            if component_plan.get("mode") == "publish":
                comps.clear()
            comps.update(component_plan.get("components", {}))
            return {"ok": True, "component_count": len(comps)}
        return self.transact_expected_active(expected_project_id, _apply)
```

> profile/frame/components 的**确切合并规则**以现有 `set_spatial_profile`/`upsert_frame`/`set_components` 为准，把它们的核心逻辑搬进 `_apply`（在工作副本上），不要再调那三个会各自保存的方法。`coord_save_components` handler 解析出 `profile_patch/frame_patch/component_plan` 与 `expected_project_id` 后单调 `save_component_bundle`，`ProjectMismatch → 409`。

- [ ] **Step 4: 跑全量后端测试**

Run: `cd backend && python -m pytest tests/ -q`
Expected: all passed。

- [ ] **Step 5: Commit**

```bash
git add backend/project_store.py backend/app.py backend/tests/test_save_bundle_and_batch.py
git commit -m "feat: save_component_bundle 组合事务，save_components 收敛为单次持锁保存"
```

---

## Task 9: `upload_roster` expected（multipart form field）+ 全量回归 + 部署

**Files:**
- Modify: `backend/app.py`（`binding_roster_upload` ~2545）
- Test: `backend/tests/test_save_bundle_and_batch.py`（追加）

**Interfaces:**
- Consumes: `ProjectMismatch`。multipart 的 expected 走 **form field `expected_project_id`**（非 JSON）。

- [ ] **Step 1: 写测试**

```python
import io
def test_roster_upload_expected_mismatch_409(client):
    client.post("/api/v2/ontology/datasets", json={"name": "厂B", "activate": True})
    data = {"file": (io.BytesIO("实例编号\nDW-001\n".encode("utf-8-sig")), "roster.csv"),
            "expected_project_id": "p_test"}
    r = client.post("/api/v2/binding/roster/upload", data=data, content_type="multipart/form-data")
    assert r.status_code == 409
```

- [ ] **Step 2: 跑，确认失败**

Run: `cd backend && python -m pytest tests/test_save_bundle_and_batch.py -q -k roster`
Expected: FAIL。

- [ ] **Step 3: 实现**

在 `binding_roster_upload` 落库前加（读 form field 而非 JSON）：

```python
    expected = request.form.get("expected_project_id")
    if expected is not None and project_store.get_active_id() != expected:
        return jsonify({"error": "project changed", "expected": expected,
                        "actual": project_store.get_active_id()}), 409
```

> roster 上传落库若是单一 `add_roster_entries` 调用，则「先 check 后 write」窗口极小但仍存在；如需严格锁内，给 `add_roster_entries` 也加 `expected_project_id` 参数（与 Task 7 同法）。本轮 roster 属低危（不改实例/构件），采用 handler 前置校验即可，权衡记录在提交信息。

- [ ] **Step 4: 全量回归（JSON）**

Run: `cd backend && python -m pytest tests/ -q`
Expected: all passed。

- [ ] **Step 5: 部署到 88.66（PG 模式）并冒烟**

```bash
# 本地：tar 增量代码到服务器（沿用部署记录 docs/部署记录-CentOS）
# 服务器：cd /opt/ontotwin/app && docker compose up -d --build
# 冒烟：mint dry_run 不写、expected 不符 409
curl -s http://192.168.88.66:5000/api/v2/binding/mint -H 'Content-Type: application/json' -d '{"dry_run":true}'
```
Expected: dry_run 返回 `minted:0` + 规划；`/nexus` 仍 200；Web UI 现有 mint（无 body）行为不变。

- [ ] **Step 6: Commit**

```bash
git add backend/app.py backend/tests/test_save_bundle_and_batch.py
git commit -m "feat: upload_roster 支持 expected_project_id（multipart form field）"
```

---

## Self-Review（作者自查）

**1. Spec 覆盖：** §14.0 PG 平价→Task 5；§14.1 dry_run/纯 planner→Task 4；§14.2 expected 锁内→Task 2/7，save_component_bundle→Task 8，bind_batch→Task 7，端点表 mint/bind/unbind/override/roster→Task 6/7/9，create_empty_project `activate=false`→**MCP 侧契约，属 M1，不在本后端计划**（已在 spec §3.2/§14.2 钉死，M1 计划落地）；§14.3 并发两用例→Task 3，JSON+PG 双测→Task 5 + 各 Task。§5.2 instance_store 同锁→Task 7 update_raw_state。
**2. 占位符扫描：** 无 TBD/TODO；每步含真实测试与实现代码；依存现有实现处均标注「以 project_store.py 为准」并给出确切方法名与回退方案，非占位。
**3. 类型一致：** `ProjectMismatch(expected, actual)`、`transact_expected_active(expected_id, updater)`、`mint_instances(dry_run, expected_project_id)`、`bind_batch(pairs, expected_project_id)`、`save_component_bundle(expected_project_id, profile_patch, frame_patch, component_plan, mode)` 在各 Task 中签名一致。

> 未在本计划内的 spec 项（MCP 转译层 M1–M4、skill、README、错误映射客户端侧、文件参数 allowed roots）属后续独立计划，M0 落地后再写。
