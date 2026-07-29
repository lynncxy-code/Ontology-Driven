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
