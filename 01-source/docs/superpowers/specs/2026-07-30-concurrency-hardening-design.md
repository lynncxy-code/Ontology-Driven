# OntoTwin Nexus —— 并发硬化（Codex 复审整改）设计

> 针对 Codex 对今日 MCP 全量（`6c2cf26..2c65b06`）的复审 6 条 Important findings 的整改。
> 用户裁定：**F3+F2 立刻修；F1 走 A（后端硬化，锁内绑项目身份）；多步 F4/F5/F6 走 B（标注接受）**。

## 修订记录

- **v1（2026-07-30）**：首版。

---

## 1. 目标与非目标

### 目标

把「配置写 / 分区写」的并发护栏从「仅数字 revision / 锁外校验」硬化为「锁内绑项目身份」，并修掉一个与已修 profile 同类的别名 bug；对彻底原子化成本高的多步端点，如实标注为已知限制。

### 背景（Codex findings）

- **F3（真 bug，漏修）**：`spatial_frame_calibrate`（app.py:1081）`get_frame()` 返回活引用，端点在护栏前原地改帧 → 被拒后内存脏。同 `spatial_profile_put` 已修的别名类。
- **F2（真 TOCTOU）**：`zone_management/service.assign` 锁外校验 expected（service.py:107-112），之后 `store.assign_zone`（project_store:639）锁内无护栏 → 两步间切项目会误落。
- **F1（护栏过弱）**：overlay/scene 配置写只在 `transact_active` 内校验**项目内局部的数字 revision**（常从 0 起）。A→B 切换且 revision 撞号时，从 A 备好的写落到 B。MCP 曾宣称「revision 兼作跨项目护栏」——不成立。
- **F4/F5/F6（多步非原子，走 B）**：`_rederive_components`、`spawn_cad_instances` 批量、`writeback` 绑定实例——逐步各自加锁，中途切项目会「部分写 + 409」。接受为已知限制、加注释/skill 说明。

### 非目标

- 不做 F4/F5/F6 的原子化重构（成本高、单用户顺序调用风险低）——走 B 标注。
- 不改现有 revision 契约（前端仍用）；F1 是在 revision 之外**叠加**项目身份校验。

---

## 2. 架构与关键原语

- **F1/F2 复用 `transact_expected_active(expected_id, updater)`**（project_store:474）：锁内先 `if expected_id is not None and self._active_id != expected_id: raise ProjectMismatch` 再原子写。把 overlay/scene 的 `transact_active(fn)` 改为 `transact_expected_active(expected_project_id, fn)`；`assign_zone` 直接加锁内同款校验。
- **F3 复用 `copy.deepcopy`**（同 profile 修法）。
- **错误映射零改动**：`ProjectMismatch` → 端点回 409 `{error:"project changed", expected, actual}` → `NEXUS_PROJECT_CHANGED`（M0 映射，已在）。与既有 overlay/scene `revision_conflict`（→ `NEXUS_REVISION_CONFLICT`）区分:errors.py 的 409 分支「项目漂移」判定**优先于** revision_conflict，已保证。
- **加法式、向后兼容**：所有 `expected_project_id` 参数缺省 None → 走旧路径。缺省时行为不变。
- **PG 平价**：本轮不改 project_store 被 PG 覆盖的方法（`assign_zone`、`transact_*`、`get_frame` 均未被 PG 覆盖 → 继承，无平价）。

---

## 3. 改动清单

### 3.1 F3 —— calibrate 别名（app.py）

`spatial_frame_calibrate`（1081）：`frame = copy.deepcopy(project_store.get_frame(frame_id)) or {...}`。深拷贝已存在的帧再改；被拒时活帧不动。（`or {...}` 在帧不存在时创建新 dict，本就安全。）

### 3.2 F2 —— zones 锁内护栏

- `project_store.assign_zone(self, instance_ids, zone_id, expected_project_id=None)`：`with self._lock:` 内、`if not self._current` 之后、首个写之前加 `if expected_project_id is not None and self._active_id != expected_project_id: raise ProjectMismatch(...)`。
- `zone_management/service.assign`：把 `payload.get("expected_project_id")` 透传给 `assign_zone`；捕获 `ProjectMismatch` → `raise ZoneManagementConflictError(...)`（api 已把它映射为 409 `active_project_changed` → `NEXUS_PROJECT_CHANGED`）。锁外的旧校验（109-112）可保留为快速失败，但真护栏在锁内。
- `zone_management/api.py` 导入 `ProjectMismatch`（若走服务转 ConflictError 则不需）。

### 3.3 F1 —— overlay/scene 绑项目身份（后端 + MCP）

**后端（overlay/service.py、scene_interaction/service.py）**：写方法加 `expected_project_id=None` 参数，把 `project_store.transact_active(fn)` 改为 `project_store.transact_expected_active(expected_project_id, fn)`。涉及：
- overlay：`save_type`、`save_instance`、`clear_instance`、`batch_instances`、`save_media_policy`。
- scene：`save_roaming`、`create_route`、`update_route`、`delete_route`、`review_route`、`set_default_route`。

**后端 api（overlay/api.py、scene_interaction/api.py）**：各写端点读 `data.get("expected_project_id")` 透传；`execute()` 增 `except ProjectMismatch as e: return jsonify({"error":"project changed","expected":e.expected,"actual":e.actual}), 409`（import ProjectMismatch）。

**MCP（overlay.py、scene.py）**：上述写工具加 `expected_project_id: str = ""` 参数，非空入 body。zones 的 `assign_zones` 已有,无需改。

### 3.4 F4/F5/F6 —— 标注（B）

- `_rederive_components`（app.py:967）加注释：独立取当前激活项目、逐步 set_components/mint/update_raw_state 无整段护栏；调用它的 profile PUT / transform PUT 在初始护栏后若切项目，重算可能落到新项目——已知限制。
- `spawn_cad_instances`（F5）、`writeback` 绑定路径（F6）已有注释，补齐/统一措辞。
- `mcp/skills/ontotwin-nexus/SKILL.md` 增「并发已知限制」小节：多步写端点（CAD 批量投产、writeback、profile/transform 触发的全场重算）非整段原子——中途切激活项目可能部分写 + 409；重试前需核对已写状态。并**修正 M1/M2 措辞**：overlay/scene/routes 的 `expected_revision` 是「同项目编辑并发护栏」，跨项目漂移由本轮新增的 `expected_project_id` 兜底。

---

## 4. 测试策略

- **后端**：F3 calibrate 端点带错 expected 重标定已存在帧 → 409 且内存帧未变（回归，撤销修复即 FAIL）；F2 `assign_zone` 方法级 + 端点 409；F1 overlay/scene 各写方法/端点带错 expected → 409（可挑代表性覆盖，不必逐个）。
- **MCP 单元**：overlay/scene 写工具 `expected_project_id` 透传/省略。
- **回归**：后端全量 + mcp 全量不回归。
- **部署后探针**：`assign_zones`/`save_overlay_type_config`/`calibrate_spatial_frame` 带错 expected → 期望 409 `NEXUS_PROJECT_CHANGED`、不落库/不改内存。

---

## 5. 交付里程碑（任务分组，供 writing-plans）

| 组 | 内容 | 独立可测 |
|---|---|---|
| A · 后端 F3+F2 | calibrate deepcopy + assign_zone 锁内护栏 + 测试 | ✅ |
| B · 后端 F1-overlay | overlay 服务/端点 threadexpected + ProjectMismatch→409 + 测试 | ✅ |
| C · 后端 F1-scene | scene 服务/端点同上 + 测试 | ✅ |
| D · MCP F1 | overlay.py + scene.py 工具补 expected_project_id + 单测 | ✅ |
| E · 标注 B + skill | rederive/多步注释 + skill 并发已知限制 + 修正 M1/M2 措辞 | ✅ |

A 先落地（F3+F2 立刻修）；B/C 后端 F1；D 依赖 B/C 的端点读 expected（但 MCP 单测用 fake client，可并行）；E 收口。

---

## 6. 依赖与兼容

- **无新依赖**、**client/errors/PG 零改动**。后端加法式（overlay/scene/zones 服务+api、app.py calibrate）+ MCP overlay/scene 工具加可选参。
- 纯加法,现有 91 工具与测试不回归。工具数不变（91，只是 overlay/scene 写工具多了可选参）。
- **需部署**：project_store.py + app.py + overlay/ + scene_interaction/ + zone_management/ 到 88.66。

---

## 7. 风险科普

- **锁内校验 vs 锁外校验**：并发护栏必须和它守护的写在**同一把锁内、同一临界区**完成「校验→写」。锁外先查、锁内再写（F2 的原样、以及 overlay 只查 revision 不查项目）都留了 TOCTOU 窗口。`transact_expected_active` 的价值就是把「项目身份校验 + 深拷贝改 + 落盘」全塞进一次持锁,任何交错都无法让写落到校验之外的项目。
- **数字 revision 为什么不够当跨项目护栏**：revision 是项目内单调计数,不含项目身份,两个项目可以同号。要防「写落到错项目」,护栏里必须有**项目身份**本身（`expected_project_id`），不能靠一个可能撞号的数字。这正是 F1 的教训。
