---
name: ontotwin-nexus
description: 编排 OntoTwin Nexus MCP 工具搭建/运维数字孪生场景。涉及数字孪生场景、设备实例、坐标标定、本体类型、DXF/花名册导入、实例绑定与铸造、Nexus 项目（数据集）时使用。教 AI 走「类型 → 构件 → 实例 → 运行」四段流水线，并守住写安全铁律。
---

# OntoTwin Nexus 编排手册

Nexus 把一个工厂/楼层场景的全部数据装进「当前激活项目」。所有工具**只认当前激活项目**——切错项目 = 写错场景。本手册教你用 30 个 MCP 工具把「一份 DXF + 一份设备清单」变成可运维的数字孪生。

## 四段流水线心智图

```
类型(ObjectType)  →  构件(Component)  →  实例(Instance)  →  运行(Runtime)
   本体是什么          图纸上在哪            场景里的一台         活着的状态
```

术语链不可混：**类型**是抽象定义（如「离心泵」这一类）；**构件**是 DXF 里被标定到坐标系的一个图块（还没身份）；**实例**是场景中一台具体设备（有身份、有状态）；构件经绑定→铸造才变成实例。

| 阶段 | 目标 | 主力工具（读 / 写） |
| :-- | :-- | :-- |
| 类型 | 从 CSV 建类型库并激活 | 读 `list_object_types` `get_object_type` `get_import_staging_graph` `get_project_ontology_graph` · 写 `import_ontology_csv` `publish_ontology_dataset` `activate_project` `create_empty_project` |
| 构件 | 解析 DXF、标定坐标、存构件 | 读 `list_components` `get_spatial_profile` · 计算 `parse_cad_dxf` `calibrate_coordinates` · 写 `save_components` |
| 实例 | 花名册撮合、绑定、铸造 | 读 `list_roster` · 计算 `automatch_bindings` · 写 `upload_roster` `bind_instance` `bind_instances_batch` `unbind_instance` `mint_instances` |
| 运行 | 查状态、改状态、看快照 | 读 `list_instances` `get_instance_state` `get_instance_snapshot` `get_state_snapshots` · 写 `set_instance_state` |
| 项目/元 | 选场景、确认可写 | 读 `list_projects` `get_active_project` |
| 二期诊断 | 查位置变换 / UE 绑定态 / 空间坐标系（均只读） | 读 `get_instance_transform` `get_ue_binding_status` `list_spatial_frames` |

`parse_cad_dxf` / `calibrate_coordinates` / `automatch_bindings` 是**无副作用的计算或暂存**，可放心多跑；带「会修改当前激活项目」的才是落库写（persist-write），须走下面的铁律。

## 黄金铁律（写前逐条过）

1. **先确认可写**：任何写操作前先 `get_active_project`，只有 `writable=true`（即 `kind=project`）才能写。`kind=demo` 是内置只读、`kind=none` 是没激活，两者都必须先 `activate_project` 换到真实项目。
2. **写工具必带 `expected_project_id` 且先向人复述**：把 `get_active_project` 返回的 `project_id` 传给每个 persist-write 工具（`upload_roster` / `save_components` / `bind_instance` / `bind_instances_batch` / `unbind_instance` / `mint_instances` / `set_instance_state`），后端会在锁内原子校验「现在还是不是这个项目」，不符则 409。注意 `upload_roster` 虽是上传 CSV，但后端会把花名册**直接写进当前激活项目**（persist-write），同样必带 `expected_project_id`。动手前用一句话向人复述「**将在项目 X 做 Y**」。
3. **术语链不可混**：类型 / 构件 / 实例 三层含义固定（见上）。别把「构件」当「实例」去 `set_instance_state`，也别在类型库为空时急着 `save_components`（后端会拒块）。
4. **铸造前先 dry_run**：先 `mint_instances(dry_run=true)` 看**真实无副作用预览**（返回 `to_create` / `to_update`），确认无误后再 `mint_instances(dry_run=false, expected_project_id=X)` 真写。注意预览与真写是两次请求，其间若有人改了绑定，结果可能有出入——预览不是提交保证。

## 端到端配方：从 DXF + 清单搭一个孪生

「用这份 DXF 和设备清单，搭一个五楼孪生」——**不是**「建空项目再导入」，而是导入→发布→激活直接从 CSV 生成并激活类型库：

```
① import_ontology_csv(file_paths=[6 张 CSV])         → 写入 staging 缓存（不改激活项目）
② get_import_staging_graph()                          → 预览导入内容，人工确认
③ publish_ontology_dataset(name="五楼")               → 固化为数据集，得 dataset_id = ds_...
④ get_active_project()                                → 记下切换前是谁（复述用）
⑤ activate_project(ds_id)                             ⚠ 高危：建立类型库 + 切全局激活态
⑥ list_object_types()                                 → 验证类型库非空，拿到 project_id
⑦ parse_cad_dxf(file_path=五楼.dxf)                   → 扫描 INSERT 块得设备候选
⑧ calibrate_coordinates(anchors=[4 组锚点])           → 求仿射矩阵 + RMSE，先看误差
⑨ save_components(payload=..., expected_project_id=X) ⚠ persist-write
⑩ upload_roster(file_path=清单.csv, expected_project_id=X) + list_roster  ⚠ persist-write：花名册写进激活项目
⑪ automatch_bindings()                                → 只出建议，不落库
⑫ bind_instances_batch(pairs=..., expected_project_id=X) ⚠ persist-write
⑬ mint_instances(dry_run=true)                        → 真实预览 to_create/to_update
⑭ mint_instances(dry_run=false, expected_project_id=X)  ⚠ 真写：铸造实例
```

关键：步骤 ⑤ 才真正建库并切激活态；步骤 ①–③ 全在 staging，不套 `expected_project_id`（`import` / `publish` / `activate` / `create_empty_project` 均为全局或切换语义，无「项目级 expected」）。

## 三个范例

**例 1 · 只读查询**——「场景里现在有哪些设备，在线几个?」
`get_active_project`（确认有激活项目）→ `list_instances`（拿设备清单）→ `get_state_snapshots`（拿状态）→ 汇总。全程只读，无需复述、无需 expected。

**例 2 · 端到端搭孪生**——见上「端到端配方」。

**例 3 · 运行态运维**——「把 DW-007 标成告警」
`get_active_project`（回显项目、确认 `writable=true`，拿 `project_id`）→ `list_instances`（定位 DW-007 的 instance_id）→ 向人复述「将在项目 X 把 DW-007 置为告警」→ `set_instance_state(instance_id=..., patch={"status":"warning"}, expected_project_id=X)`。

## 失败自救

- **无激活项目**（`get_active_project` 返回 `kind=none`，或写工具报「无激活项目」）：先 `list_projects` 看有哪些，再 `activate_project` 切到目标；确认没有目标项目时才 `create_empty_project` 或走导入链新建。
- **Demo 只读**（`kind=demo`、`writable=false`）：内置演示数据集不可写。先 `activate_project` 换到真实项目再写，别对着 demo 试。
- **图库降级**：本体图 / 语义相关调用报「语义图库暂不可达（Neo4j）」时，如实说明该能力暂降级，**不要**一律承诺「不影响主功能」——本体导入/图谱确实受影响；坐标/绑定/运行态可能仍可用，逐项确认而非笼统安抚。
- **后端不可达 / 超时**：连接或读超时 → 报「Nexus 后端暂不可达」，检查 `NEXUS_BASE_URL`。**非幂等写**（`upload_roster` / `save_*` / `mint_*` / `bind_*` / `activate_*` / `set_instance_state`）超时后**禁止自动重试**（结果状态不确定）；只读 / 纯计算可有限次退避重试。CAD 解析超时后先查是否实际已完成再决定，别贸然重解析。

## 场景配置（信息面板 / 人物漫游 / 漫游路线）

三块配置都走「读活配置 → 改 → 带 revision 写回」，后端 validator 兜底。

**金规**
1. **写前必先读**：`get_overlay_context` / `get_roaming_config` / `get_route` 返回里带 revision，写工具的 `expected_revision` 必填，取自刚读到的值。
2. **遇 `NEXUS_REVISION_CONFLICT`**：配置被他处改过 → 重新读 → 合并意图 → 重写。注意漫游/路线共享**同一个 scene revision 计数器**（roaming 配置、每条路线、评审、设默认全在这一份文档上），**每次写都会把它 +1**；连续多步写时，每步的 `expected_revision` 必须用上一步返回的最新值，不能复用最初读到的那个。
3. **config 结构以读到的活配置为准**，不臆造字段；结构非法后端返回 `NEXUS_VALIDATION`，按 `fields` 里的 path/message 纠正。
4. **类型首次配面板**先 `enable_info_panel(object_type_rid)` 注入能力，再 `save_overlay_type_config`。

**信息面板 config 速查**（详细字段以 `get_overlay_context` 返回为准）
- 槽位 slots：`body`（正文）/`status`（状态灯+文案）/`media`（视频）/`metrics`（指标）。
- 绑定源 4 种：`literal`（固定值）/`instance`（实例信息）/`object_type`（类型信息）/`raw_state`（实时数据，如 `status`/`capacity`）。
- 状态分级配色：`slots.status.appearance[level] = {label, color}`，level 取 `statusLevelOptions`。

**典型流程**
- 改某类型面板的状态配色：`enable_info_panel(rid)` →（若已启用可跳过）`get_overlay_context(object_type_rid=rid)` → 改 `config.slots.status.appearance` → `save_overlay_type_config(rid, config, expected_revision)`。
- 批量给一批实例覆盖标签：`get_overlay_context(object_type_rid=rid)` 拿各实例 `override_revision` → `batch_overlay_instance_override(rid, ids, merge_patch, expected_revisions)`。
- 新建漫游路线并设默认：`list_routes()` 拿集合 revision → `create_route(route, expected_revision)`（**用它返回的新 revision**）→ `review_route(new_id, <上一步返回的 revision>)` 使其变为 ready → `set_default_route(new_id, <再上一步返回的 revision>)`。**每一步都用上一步返回的最新 revision**，别复用旧值，否则必撞 `NEXUS_REVISION_CONFLICT`；且未 `review_route` 变 ready、未启用的路线，`set_default_route` 会 422。

**触发示例**
- 「把货架类型信息面板的『缺货』状态配成红色」
- 「给这批 AGV 实例的面板标题统一改成设备编号」
- 「新建一条从入口到 A 区的巡检漫游路线，并设为默认」

**已知限制**
- 漫游路线的「路线不存在」(bad route_id) 目前会被后端用与「无激活项目」相同的错误码返回，MCP 侧因而报成 `NEXUS_NO_ACTIVE_PROJECT`。若你确信项目已激活却收到该错误，多半是 route_id 不存在，请核对 `list_routes()`。（根因在后端错误码复用，待后续版本区分。）

## 空间参考帧 / 分区

**空间标定底图参考帧**（`reference_frame`，别与坐标系的 `list_spatial_frames` 混淆）
- playbook：`create_reference_frame(底图路径, floor=…)` → `get_reference_frame(frame_id)` 拿 `draft_revision` → 改 `draft`（锚点/楼层参照）→ `save_reference_frame_draft(frame_id, draft, expected_draft_revision)` → `publish_reference_frame(frame_id, expected_draft_revision=…)`。
- 金规：写前先 `get_reference_frame` 拿 `draft_revision`；遇 `NEXUS_REVISION_CONFLICT` 重读重写；`draft` 结构以读到的活帧为准。
- 已知限制：无激活项目时，参考帧工具会因后端复用 `spatial_frame_not_found` 错误码而报成 `NEXUS_NOT_FOUND`（而非 `NEXUS_NO_ACTIVE_PROJECT`）。若确信项目已激活却收到该错误，多半是 frame_id 不存在。

**实例分区**（zones）
- `get_zones()` 看各分区实例数 → `assign_zones(instance_ids, zone_id)` 批量指派；`zone_id` 传空串=解除分区。
- 并发多写时带 `expected_project_id`（从 `get_active_project` 的 `project_id` 取）。

**触发示例**
- 「上传这张一楼底图作空间参考帧，楼层填 1」
- 「把这批实例划到 A 区」 / 「解除这些实例的分区」

## 实例生命周期 / 换模型

这些是**高危写**（尤其 delete 不可逆）。并发多写带 `expected_project_id`（从 `get_active_project` 的 `project_id` 取）；遇 `NEXUS_PROJECT_CHANGED` 说明激活项目被切走，重新确认后再写。

**建 / 删实例**
- `create_instance(instance_id, object_type_rid, initial_position={"x":..,"y":..,"z":..})`。前提：类型已注入三维接口（否则 400），id 不得重复（否则 409）。
- `delete_instance(instance_id, expected_project_id=…)`。

**改位置**
- `set_instance_transform(instance_id, {"canonical_xy":[x,y], "canonical_z":z, "rotation":deg, "floor":n})` — 规范坐标微调。
- `writeback_instance_transform(instance_id, {"tx":..,"ty":..,"tz":..,"rx":..,"ry":..,"rz":..,"sx":..,"sy":..,"sz":..})` — UE cm 回写。

**换模型**
- `get_model_binding(instance_id)` 看现状 → `set_model_binding(instance_id, selection, expected_project_id=…)` 换模型 → `clear_model_binding(instance_id)` 恢复类型默认。
- 类型级：`clear_type_model_default(rid)`、`promote_model_binding(rid, source_asset_path)`（把迁移模型提为默认，source_asset_path 必须属于该类型历史实例模型）。

**触发示例**
- 「在当前项目建一个货架实例 shelf-A3，放在规范坐标 (1200, 800)」
- 「把 shelf-A3 挪到 (1500, 900)」
- 「给 shelf-A3 换成高精模型」/「把 shelf-A3 恢复成类型默认模型」

## 本体深编辑（能力接口 / 定义 / 暂存图）

**配能力接口**
- `list_interface_defs()` 看有哪些接口 → `inject_interfaces(rid, ["I3D_Representable", "I3D_Spatial", ...])` 挂载（合并追加）。子接口（Spatial/Visual/Behavioral/Overlay）必须已有或同时挂 `I3D_Representable`，否则 400。
- `remove_interface(rid, "I3D_Spatial")` 移除；移 `I3D_Representable` 会级联清空所有子接口 + 清资产。
- 注：`enable_info_panel(rid)` 是「注入 I3D_Representable + I3D_Overlay」的便捷特例；要挂别的接口用 `inject_interfaces`。

**查定义**
- `list_property_defs()` / `list_transform_types()`（静态定义）；`get_ontology_registry()`（Neo4j 注册表，不可达返回 `NEXUS_DEGRADED`，不影响其它功能）。

**暂存图**
- `build_staging_graph_from_registry()` 从图库出暂存图 → `get_import_staging_graph()` 读回 → `publish_ontology_dataset(name)` 发布。

**触发示例**
- 「给货架类型挂上 I3D_Representable 和 I3D_Spatial」
- 「看看有哪些能力接口可以挂」
- 「从本体图库重建暂存图并发布成新数据集」

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
