# OntoTwin Nexus M5a —— CAD 交互标定链 MCP 扩展设计

> 「MCP 覆盖整个系统操作面」路线图 M5 的前半（M5a）。M5 拆为 M5a（CAD 交互链）+ M5b（系统一 spatial 写 + coord 杂项）。
> 前置：基础 30 + M1–M4 + M6 = 78 工具，均已交付 main（M3 后端已部署 88.66）。

## 修订记录

- **v1（2026-07-30）**：首版。用户定：M5 拆分（先 M5a）+ 加后端护栏（spawn 加 expected，commit 目标显式不加）。沿用直通式 / 文档 A。

---

## 1. 目标与非目标

### 目标

把 CAD「一键成模」的交互标定链开放给 MCP：扫描 DXF 出候选类型 → 冲突/覆盖检查 → 提交建类型数据集 → 批量投产实例（带 dry-run + 并发护栏）。

### 关键认知：服务器端无状态、客户端编排

这条链**服务器端不存 session**：`preview`/`scan` 上传即返回、不留状态；`commit`/`spawn` 的 `items`、`transform_matrix` 都由**调用方在 body 里传回**。因此**中间态由 AI 在上下文里持有、逐步传递**——每个工具是无状态直通，不需要建会话模型。

### 非目标

- **M5b 本轮不做**：系统一 `/spatial/*` 写（`profile PUT` 全场重算、`frames POST`、`calibrate`、`spatial/preview`）+ `coord/export`、`coord/mapping`。
- **不做 M6**（已交付）。

---

## 2. 架构

- 直通式；`register(mcp, client, registry)`；文档 A。
- **并发护栏（只给隐式激活写）**：`spawn_cad_instances` 写的是**隐式当前激活项目**的实例 → 加可选 `expected_project_id`。`commit_cad_types` 的目标是**显式**的（publish 新建数据集 / merge 指定 `target_dataset_id`），无"切走后误写"漂移面 → **不加** expected。
- **client / errors 零改动**：post_multipart / post_json 已存在；400/404/409/5xx 映射已覆盖（ProjectMismatch→409→`NEXUS_PROJECT_CHANGED` 是 M0 的）。
- **后端改动最小**：仅 `app.py` 的 `spawn_instances` 端点透传 expected（下游 `spawn`/`update_raw_state` 在 M3 已具备锁内护栏，**不改 project_store，无 PG 平价**）。

---

## 3. 工具清单（6 个：4 读 + 2 写）→ MCP 78→84

| 工具 | 方法 + 端点 | 类型 | 参数 |
|---|---|---|---|
| `preview_cad` | POST `/api/v2/coord/preview`（multipart DXF） | 读 | `file_path` |
| `scan_cad_types` | POST `/api/v2/coord/types/scan`（multipart DXF） | 读 | `file_path` |
| `check_type_conflicts` | POST `/api/v2/coord/types/check_conflicts` | 读 | `rids:list`, `mode="publish"`, `target_dataset_id=""` |
| `check_type_coverage` | POST `/api/v2/coord/types/check_coverage` | 读 | `block_names:list` |
| `commit_cad_types` | POST `/api/v2/coord/types/commit` | 写（建/并数据集，目标显式） | `items:list`, `mode`, `source_file=""`, `publish_options=None`, `merge_options=None`, `conflict_strategy=""`, `force=False` |
| `spawn_cad_instances` | POST `/api/v2/coord/spawn_instances` | 写（批量投产，dry-run+护栏） | `items:list`, `transform_matrix:list`, `source_label=""`, `mode="dxf"`, `conflict_strategy="update_coord"`, `commit=False`, `expected_project_id=""` |

### 请求体映射

- `preview_cad` / `scan_cad_types`：multipart，file 字段名 `file`，`.dxf`；超时用 cadparse 超时（同 `parse_cad_dxf`）。
- `check_type_conflicts` → `{rids, mode}` + 非空 `target_dataset_id`。
- `check_type_coverage` → `{block_names}`。
- `commit_cad_types` → `{items, mode}` + 非空 `source_file`、非 None `publish_options`/`merge_options`、非空 `conflict_strategy`、`force`（原样传布尔）。
- `spawn_cad_instances` → `{items, transform_matrix, mode, conflict_strategy, commit}` + 非空 `source_label`、非空 `expected_project_id`。

### 用法故事线（AI 持中间态）

`scan_cad_types(dxf)` → AI 审/补 asset_id → `check_type_conflicts(rids)` → `commit_cad_types(items, mode="publish")` 建类型 → `calibrate_coordinates(anchors)`（基础层）得 `transform_matrix` → `spawn_cad_instances(items, matrix, commit=False)` dry-run 看 summary → 确认 → 再 `commit=True, expected_project_id=<get_active_project.project_id>` 真投产。

---

## 4. 后端能力扩展（加法式，仅 app.py）

### 4.1 spawn_instances 端点透传 expected + 捕获 ProjectMismatch

`app.py` `coord_spawn_instances`（约 562）：
- 读 `expected_project_id = data.get("expected_project_id")`。
- 真写阶段（`commit=true`）的所有 `instance_store.spawn(...)` 与 `instance_store.update_raw_state(...)` 调用**追加** `expected_project_id=expected_project_id`（这两个方法在 M3 已具备锁内 `ProjectMismatch` 校验）。共 4–6 处调用（to_create 的 spawn+update、to_update_coord_only 的 update、conflicts update_coord 的 update、duplicate 的 spawn+update）。
- 用 `try/except ProjectMismatch as e: return jsonify({"error":"project changed","expected":e.expected,"actual":e.actual}), 409` 包住**真写阶段**。dry-run（`commit=false`）不触发写、不受影响。

### 4.2 无 project_store / PG 改动

`spawn`/`update_raw_state` 签名 M3 已扩展；`project_store_pg` 未覆盖这两个（继承）→ **无 PG 平价**。

### 4.3 批量非原子说明（接受）

写阶段逐 item 调 `spawn`/`update_raw_state`，各自锁内校验 expected。若极窄窗口内项目被切，已写入的 item 保留、后续 item 触发 409 → 部分写。与 M3 writeback 的多写非原子同性质，接受（加注释）。

### 4.4 后端测试

`backend/tests/` 加：`spawn_cad_instances` 端点带错 `expected_project_id` + `commit=true` + 合法 item（`block_name` 在 `_object_types`，含 `transform_matrix`）→ 期望 409（monkeypatch `app._object_types` 让 block_name 过三态校验，参照 M3 spawn 端点测试）。dry-run（commit=false）带任意 expected 不报 409。**不改既有行为**：缺省 expected 走旧路径。

---

## 5. 错误映射 / client

**零改动**。M5a 状态码已覆盖：
- `spawn`/`commit` 校验失败 400 → `NEXUS_VALIDATION_ERROR`；ProjectMismatch 409 → `NEXUS_PROJECT_CHANGED`（M0）。
- commit 冲突类 409 → `NEXUS_CONFLICT`（透传 error 文本，可接受）。
- DXF 解析失败 500 → `NEXUS_BACKEND_ERROR`。
- client 用 post_multipart / post_json（均已存在）。

---

## 6. Skill 层（文档 A）

`mcp/skills/ontotwin-nexus/SKILL.md` 增「CAD 一键成模（交互标定链）」段：

- **四段流程**：`scan_cad_types(dxf路径)` 拿候选（AI 补 `asset_id`）→ `check_type_conflicts(rids)` 看有没有撞已有类型 → `commit_cad_types(items, mode="publish", publish_options={"name":"厂区A"})` 建类型数据集 → `calibrate_coordinates(anchors)` 得 `transform_matrix` → `spawn_cad_instances(items, transform_matrix, commit=False)` **先 dry-run** 看 summary（to_create/conflicts/errors）→ 确认无误 → `commit=True, expected_project_id=<get_active_project 的 project_id>` 真投产。
- **金规**：spawn 是高危批量写，务必先 `commit=False` dry-run；真写带 `expected_project_id`；遇 `NEXUS_PROJECT_CHANGED` 说明项目被切走，重新确认后再投。
- 速查（A）：`items` 结构（`block_name`/`cad_xy`/`rotation`/`attribs`/可选 `instance_id`/`asset_id`）以 `scan_cad_types` 返回为准；`transform_matrix` 是 `calibrate_coordinates` 的产物。
- 触发示例：「扫一下这个 DXF 有哪些设备类型」「把这批设备按标定矩阵投产,先 dry-run 看看」。

---

## 7. Repo 布局

```
backend/app.py                 # spawn_instances 端点透传 expected（唯一后端改动）
backend/tests/                 # spawn 端点 409 测试
mcp/ontotwin_mcp/tools/
  cad_calibration.py           # 新增：6 个工具
  __init__.py                  # register_all 追加 cad_calibration
```
client/errors/project_store/PG **不改**。

---

## 8. 测试策略

- **后端**：spawn 端点 409（见 §4.4）。
- **MCP 协议**：stdio 列表新增 6 工具；`call_tool` 挑 `check_type_coverage` 走一遍。
- **MCP 单元（fake client）**：每工具断言 URL/方法/请求体；重点 preview/scan 的 multipart（file 字段+cadparse 超时）、spawn 的 `expected_project_id`/`commit` 透传/省略、commit 的可选项组装。
- **只读冒烟**：preview/scan 需真 DXF，check 需真 rids —— 均不入 selfcheck。
- **写路径**：spawn/commit 只对一次性抛弃项目验证（用 `mcp/sample-data/demo.dxf`），不碰生产库。

---

## 9. 交付里程碑（任务分组，供 writing-plans）

| 组 | 内容 | 独立可测 |
|---|---|---|
| A · 后端 | spawn_instances 端点透传 expected + 捕获 ProjectMismatch + 后端测试 | ✅ |
| B · cad_calibration | 6 个工具 + register + 单测 | ✅ |
| C · skill+协议 | SKILL.md 段 + stdio 协议测试 | ✅ |

A 是前置（B 的 spawn 工具依赖后端 expected 生效才真有护栏，但 B 的 MCP 单测用 fake client、不依赖真后端，可与 A 并行；真机写验证需 A 部署）。B、C 收口。

---

## 10. 依赖与兼容

- **无新依赖**、**client/errors/project_store/PG 零改动**。后端仅 app.py 一处加法式改动。
- 纯加法，现有 78 工具与测试不回归。MCP 工具总数 **78 → 84**。
- **需部署**：app.py 一个文件 scp + restart（像 M3；改生产前与用户确认）。

---

## 11. 风险科普

- **无状态链 vs 有状态会话**：这条看似复杂的多步标定链，服务器端其实每步独立、不留 session——中间产物（scan 候选、标定矩阵）由客户端持有并回传。这是良好的 REST 无状态设计：好处是任一步可独立重试、并发安全、易映射成 MCP 工具；代价是调用方（AI）要负责把上一步结果喂给下一步。M5a 的工具编排（skill playbook）就是在教 AI 怎么串这条链。
- **护栏只给"隐式激活"写**：`spawn` 写隐式当前激活项目 → 需 `expected_project_id`;`commit` 目标显式（新建/指定）→ 不需要。区分"目标是隐式当前态还是显式指定"，是决定要不要加漂移护栏的一般准则。
