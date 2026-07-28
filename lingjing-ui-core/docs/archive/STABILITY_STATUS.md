## 📊 STABILITY_STATUS — 已收口说明（请以 TRUTH_SOURCES 为准）

> **重要说明**：本文件在 v3.0.0 早期阶段曾用于记录各场景的稳定度状态表。
>  从当前阶段开始，**稳定度状态表的唯一正式入口已收口到 `TRUTH_SOURCES.md` 中的 `§6 Phase 1 稳定度状态表`**。
>
> 本文件仅保留为历史说明与导航用途，不再单独维护稳定度数据，也不应被视为真值源。

---

### 1. 正式稳定度状态表入口

- 请始终以下述位置为准获取当前版本的稳定度状态表：
  - `TRUTH_SOURCES.md` → `## 6. Phase 1 稳定度状态表（v3.0.0）`
- 该表统一描述了：
  - `b_system` 主线的 `list` / `advanced_list` / `detail`；
  - `ue5_overlay` 主线的 `Mode 1` / `Mode 2` / `Mode 3` / `minimal overlay`；
  - 以及 `website` / `presentation` / `ai_assistant` 的兼容支持定位。

---

### 2. 对 AI 工具和维护者的要求

- 若需要判断某个「场景 × 类型/Mode」是否已达到“已稳定 / 基本稳定 / 兼容支持”等状态：
  - 请直接读取 `TRUTH_SOURCES.md`，不要再从本文件推断；
  - 当 `TRUTH_SOURCES.md` 与其他文档出现不一致时，以 `TRUTH_SOURCES.md` + `scene_coverage_matrix.yml` 为准。
- 若在迭代中需要更新稳定度状态：
  - 仅更新 `TRUTH_SOURCES.md` 中的状态表；
  - 不再在本文件中重复维护；
  - 如确需补充说明，可在本文件追加“变更记录”文字描述，但不得重新创建第二份状态表。

---

### 3. 历史背景（简述）

早期版本中，`STABILITY_STATUS.md` 曾尝试通过一张较大表格同时描述：

- 各场景（`b_system` / `ue5_overlay` / `website` / `presentation` / `ai_assistant`）的成熟度；
- 对应的证据来源（task_router / matrix / Guard / audit / baseline 等）。

随着 Phase 1 主线收口完成，这部分内容已被精简并正式迁移至 `TRUTH_SOURCES.md`，并与真值源说明合并，避免出现双份状态表长期漂移的问题。

> **结论**：阅读或判断当前版本的稳定度状态时，请一律以 `TRUTH_SOURCES.md §6` 为准；本文件仅保留为历史背景与跳转说明。