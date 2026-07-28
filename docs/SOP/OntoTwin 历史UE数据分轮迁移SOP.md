# OntoTwin 历史 UE 数据分轮迁移 SOP

> 版本：1.0  
> 更新日期：2026-07-24  
> 适用范围：将既有 Unreal Engine 场景中的历史 Actor，按业务目录、模型类型和装配实例迁入 OntoTwin 已有项目数据库，并安全删除已迁移的 UE 源 Actor。  
> 基准案例：ZHHZ 项目三轮迁移。本文以其路径和数量作为示例，但每一轮必须重新计算门禁值，不得照抄历史数字。

## 1. 目的

本 SOP 用于让 UE 操作员、开发人员或其他 AI 按同一套可审计流程执行大规模迁移，确保：

1. 一个“母 Actor”对应一个业务实例，而不是把其下每个 `StaticMeshActor` 都拆成实例。
2. 模型不同则定义为不同 ObjectType；同一模型的多个母 Actor 共享一个 ObjectType。
3. 业务目录 `hierarchy_path` 与模型类型 ObjectType 分开管理。
4. 迁移先预览、后写库，再由人工在 UE 中验收，最后才清理源 Actor。
5. 数据库、迁移结果文件、UE 关卡保存状态能够相互核对并可以回滚。
6. 每一轮都产出独立审计文件，避免通用文件被下一轮覆盖后失去证据。

## 2. 核心概念与不可违反的规则

### 2.1 实例边界

- 默认实例边界是场景大纲中的母 Actor，例如 `Group2136...`、具名航模 Actor 或业务装置 Actor。
- 母 Actor 下的静态网格组件、子 Actor、材质槽等是该实例的 `render_parts`，不是独立实例。
- 独立 `StaticMeshActor` 默认不作为实例。只有用户明确点名、且确认其在业务上是完整独立对象时，才允许作为单体实例迁移。
- 清理名单是母 Actor `ext_guid` 与所有 `source_actor_guids` 的唯一并集，不等于实例数，也不等于渲染部件数。

### 2.2 ObjectType 分组

- 一个不同模型对应一个 ObjectType。
- 相同模型的多个摆放位置对应同一 ObjectType 下的多个实例。
- 不得仅凭 Actor 名称相同或 `assembly_signature` 相同就断定模型相同。
- 模型一致性应综合判断：Datasmith 几何签名、网格资产集合、材质集合、渲染部件结构、组件相对变换及人工视觉检查。
- `assembly_signature` 适合把分类 CSV 精确映射回某个导出装配，但不能代替全部模型同一性判断。

### 2.3 业务目录与模型类型分离

- `hierarchy_path` 是实例树和 UE 预览目录的业务真源。
- ObjectType 表示模型/设备类型，不承担展区、楼层、业务系统等目录职责。
- 同一个 ObjectType 的实例可以位于不同 `hierarchy_path`。
- 原 UE Outliner 文件夹只在历史导出时读取一次，迁移后不作为 OntoTwin 的持续真源。

### 2.4 预览、正式实例与源 Actor

- UE 数据库预览 Actor 必须为临时对象，位于 `TwinPreview/<hierarchy_path>`，不得保存进 `.umap`。
- 正式运行态实例位于 `TwinInstances/<hierarchy_path>`。
- 原始历史 Actor 只有在数据库写入成功、API 校验通过、UE 预览通过且人工明确批准后才能删除。
- “清理预览”与“清理迁移源 Actor”是不同操作，严禁混淆。

### 2.5 每轮独立性

- 每轮开始时重新读取当前数据库总量，计算本轮预期增量和迁移后总量。
- `ue_actors_export.json`、`ue_migration_result.json`、`ue_snapshots.json` 是活动交接槽，可能被覆盖；每轮必须复制为带轮次的归档文件。
- 每轮正式写库前必须创建新的数据库备份。
- 每轮 UE 源清理前必须创建新的目标子关卡备份。
- 不能混用不同轮次或不同门禁时刻的数据库备份与关卡备份。

## 3. 角色和权限边界

| 角色 | 可以自动完成 | 必须人工确认或执行 |
|---|---|---|
| 迁移 AI/脚本 | 读取 PRD、扫描候选、只读导出、去重、分类建议、生成 CSV、生成清单、备份、dry-run、正式迁移、API 校验、日志解析、磁盘复核 | 不得自行决定模糊对象的业务语义；不得跳过视觉验收；不得在未获批准时删除源 Actor |
| UE 操作员 | 可运行已审查的脚本和命令 | 打开正确主场景、核对模型、批准分类、执行预览、视觉验收、点击源 Actor 清理、执行 Save All、最终复核 |
| OntoTwin/本体负责人 | 批量审核分类和命名 | 决定是否复用正式类型、创建实验类型、合并或晋升到正式本体 |

建议将数据库写入和 UE 源清理设置成两个独立人工门禁。数据库写入具有可回滚性；UE 源清理涉及关卡资产删除，风险更高。

## 4. ZHHZ 基准配置

以下是当前项目的已验证配置，后续轮次开始时仍需重新确认：

| 项目 | 值 |
|---|---|
| UE 项目 | `D:\ZHHZ\ZHHZ\ZHHZ.uproject` |
| UE 版本 | `D:\UE_5.6` |
| 操作员打开的主场景 | `/Game/AVIC_Show/Art/Maps/L_AVIC_SHOW_Main_onto` |
| 历史源 Actor 所在流式子关卡 | `/Game/AVIC_Show/Art/Maps/L_AS_Arch` |
| OntoTwin 仓库 | `D:\tmp\digital_twin_aircraft` |
| UE 项目标识 | `ueproj_ZHHZ` |
| UE 项目名称 | `ZHHZ` |
| 当前数据集示例 | `ds_1784694647848`，执行时必须从 API 重新读取 |

重要说明：操作员应停留在 `L_AVIC_SHOW_Main_onto` 中进行联合场景预览；被源 Actor 删除操作标脏、必须真正保存的是流式子关卡 `L_AS_Arch`。二者不是同一张地图。

截至第三轮复核通过时的基准总量是 80 个 ObjectType、228 个实例、8,068 个渲染部件。该数字只能用于发现意外回退，不能代替新一轮开始时的实时查询。

## 5. 每轮输入、输出与目录约定

### 5.1 每轮输入

- 本轮编号，例如 `round4`。
- 目标母 Actor 名称、ActorGuid 或明确的选择规则。
- 本轮业务类别，例如家具、展陈装置、显示与媒体设备、操作终端、航模设备。
- 实例显示名规则。
- ObjectType 复用/新建规则。
- 当前活动数据集、UE 绑定和迁移前总量。

### 5.2 推荐工作目录

```text
migration_runs/
└─ round4_20260724/
   ├─ 00_input/
   ├─ 01_export/
   ├─ 02_classification/
   ├─ 03_backup/
   ├─ 04_dry_run/
   ├─ 05_migration/
   ├─ 06_preview/
   ├─ 07_cleanup/
   └─ 08_final_audit/
```

建议每轮保存以下文件：

| 阶段 | 文件示例 |
|---|---|
| 输入 | `requested_actors_round4.txt`、`round4_context.json` |
| 导出 | `ue_actors_export_round4.json`、`candidate_audit_round4.json` |
| 分类 | `ue_migration_classification_round4.csv`、`type_manifest_round4.csv`、`instance_manifest_round4.csv` |
| 备份 | `ontotwin_before_round4.dump`、`L_AS_Arch_before_round4.umap`、文件哈希记录 |
| dry-run | `dry_run_round4.json` 或完整控制台日志 |
| 正式迁移 | `ue_migration_result_round4.json`、`migration_verify_round4.json` |
| UE 预览 | `ue_snapshots_all_after_round4.json`、`preview_audit_round4.json`、必要的截图 |
| 清理 | `cleanup_log_round4.txt`、`cleanup_disk_verify_round4.json` |
| 最终审计 | `final_acceptance_round4.md` |

## 6. 总体流程与人工门禁

```text
准备与绑定检查
  → 候选发现和只读导出
  → AI 分类、命名、模型分组
  → [人工门禁 A：批准清单和类型]
  → 数据库与关卡备份
  → dry-run
  → [人工门禁 B：批准正式写库]
  → 正式迁移和 API 校验
  → UE 全量预览
  → [人工门禁 C：确认预览正确]
  → 清理本轮源 Actor
  → Save All
  → 磁盘级复核和最终全量预览
  → [人工门禁 D：本轮结项]
```

任何门禁失败时应停在当前阶段，不得以“后面再修”为由继续删除源数据。

## 7. 分阶段详细 SOP

### 阶段 0：建立本轮上下文

#### 自动化步骤

1. 创建轮次目录和 `round_context` 文件。
2. 记录 UE 项目路径、主场景、源子关卡、OntoTwin 仓库、数据集 ID、UE 项目标识、当前时间和操作者。
3. 读取当前数据库并记录：ObjectType 总数、实例总数、渲染部件总数、现有实例的源 GUID 集合。
4. 记录以下关键文件的大小、修改时间和 SHA-256：
   - `L_AVIC_SHOW_Main_onto.umap`
   - `L_AS_Arch.umap`
   - 当前活动的 `ue_migration_result.json`
   - 当前活动的 `ue_snapshots.json`

#### 手动步骤

1. 启动 UE 项目并打开 `/Game/AVIC_Show/Art/Maps/L_AVIC_SHOW_Main_onto`。
2. 确认 `/Game/AVIC_Show/Art/Maps/L_AS_Arch` 已作为流式子关卡加载、可见且可编辑。
3. 确认没有未理解的关卡脏标记；如果已有用户改动，先由用户保存或另存，不能让迁移流程覆盖其工作。
4. 若本轮修改过 `OntoTwinSync` C++ 插件，先关闭编辑器执行完整 Editor Build，再重启。Live Coding 成功不等于插件模块和面板状态已完全刷新。

完整编译示例：

```powershell
& 'D:\UE_5.6\Engine\Build\BatchFiles\Build.bat' `
  'ZHHZEditor' 'Win64' 'Development' `
  '-Project=D:\ZHHZ\ZHHZ\ZHHZ.uproject' `
  -WaitMutex
```

#### 通过条件

- 主场景、源子关卡、活动数据集和 UE 绑定全部唯一且明确。
- 后端数据库和 API 可用。
- 已生成迁移前基线，且没有未处理的用户修改。

#### 停止条件

- 打开的不是指定主场景。
- 源 Actor 实际所在关卡不明。
- 数据集或 UE 项目绑定不匹配。
- 后端不可用或基线总量无法读取。
- UE 中存在来源不明的未保存修改。

### 阶段 1：候选发现与目标清单

候选有两种来源：用户直接给出名称/GUID，或 AI 扫描大纲和模型后提出候选。两者最终都必须形成显式 allowlist。

#### 自动化步骤

1. 对输入名称去除空行和完全重复项，但在报告中保留“原始输入数”和“唯一输入数”。
2. 在联合场景中按 Actor Label、Actor Name 和 ActorGuid 精确解析。
3. 输出每个请求项的：匹配数量、类、所属关卡、父子关系、原文件夹、组件数、网格资产、材质、位置、包围盒和可见性。
4. 报告缺失项、重名歧义项、落在错误关卡的项，以及与数据库已有 `ext_guid/source_actor_guids` 重叠的项。
5. 对母 Actor 展开装配结构，但不自动把每个子静态网格提升成实例。

#### 手动步骤

1. 在 UE 大纲和视口中确认每个母 Actor 的业务边界。
2. 对 AI 标记为歧义的名称，用 ActorGuid 或完整大纲路径消歧。
3. 明确指出需要作为独立实例的单体 `StaticMeshActor`。
4. 删除不属于本轮类别的候选。

#### 通过条件

- `requested_unique == resolved_unique`。
- 每个输入唯一对应一个明确目标；没有未解释的重复名称。
- 与既有数据库实例没有非预期 GUID 重叠。
- 最终 allowlist 经人工确认。

#### 停止条件

- 名称匹配多个 Actor 且无法消歧。
- 请求对象找不到或位于未加载关卡。
- 候选与已迁移对象重叠，但没有明确的幂等重跑计划。
- AI 无法判断母 Actor 边界，且用户尚未确认。

### 阶段 2：只读 UE 导出

#### 自动化步骤

推荐使用 `UnrealEditor-Cmd.exe` 执行经过审查的 Python 导出脚本：

```powershell
& 'D:\UE_5.6\Engine\Binaries\Win64\UnrealEditor-Cmd.exe' `
  'D:\ZHHZ\ZHHZ\ZHHZ.uproject' `
  '-ExecutePythonScript=C:\path\to\ue_export_round4.py' `
  -unattended -nop4 -nosplash -nullrhi -nosound -stdout -FullStdOutLogOutput
```

导出脚本应做到：

1. 加载 `L_AVIC_SHOW_Main_onto` 联合场景。
2. 只解析 allowlist，不以模糊前缀批量吞入其他 Actor。
3. 如导出器依赖迁移文件夹，可临时将目标母 Actor 移入 `ToMigrateAudit`，导出后恢复原文件夹。
4. 不保存任何关卡。
5. 输出 `assembly_v1` JSON，至少包含：
   - `ext_guid`
   - `actor_label/actor_name`
   - `source_folder_path`
   - `actor_class/actor_class_path/blueprint_class_path`
   - `source_actor_guids`
   - `render_parts`
   - 静态/骨骼网格资产
   - 材质和组件摘要
   - `assembly_signature`
   - 不支持组件、负缩放等阻断信息
6. 输出导出前后 Actor 文件夹对比，证明现场状态已恢复。

#### 手动步骤

1. 在运行脚本前保存或关闭正在编辑的同一项目，避免命令行实例与编辑器争用或读取脏内存状态。
2. 检查导出日志中是否加载了正确的主场景和子关卡。
3. 随机抽查若干导出装配的部件数和 UE 视口中的实际模型是否相符。

#### 通过条件

- 请求目标全部导出一次，无遗漏、无重复实例。
- `unsupported_components`、负缩放或其他阻断项为 0；如确需放行，必须另行人工批准并记录原因。
- 导出后 UE 资产没有被保存修改。
- 导出 JSON 可由后端工具正常解析。

### 阶段 3：业务分类、命名和模型归类

#### 自动化步骤

1. 先按业务用途提出 `hierarchy_path`，例如：
   - `展厅/航模设备`
   - `展厅/家具`
   - `展厅/展陈装置`
   - `展厅/显示与媒体设备`
   - `展厅/操作终端`
2. 再独立计算模型分组，生成 ObjectType 候选。
3. 对 `Group xxx` 一类无语义名称，综合以下证据提出中文名：
   - 模型外观截图和包围盒比例
   - 网格、材质和贴图资产名
   - 组件结构和相对变换
   - 场景位置及附近已知展项
   - 相同几何在其他位置的重复情况
4. 证据不足时使用保守的“类别 + 稳定编号”名称，例如 `落地式展陈装置 EXH-07`，不得编造具体型号。
5. 为每个实例生成可读 `display_name`，为每个模型组生成稳定的 ObjectType RID 和名称。
6. 生成分类 CSV。推荐 `classification_key` 使用 `assembly_signature:<signature>`，并填入：
   - `action=map_existing`：映射现有正式类型；必须填 `suggested_object_type_rid`。
   - `action=create_experimental`：创建本轮实验态类型；必须填 `suggested_object_type_name`。
   - `hierarchy_path`
   - `classification_status=confirmed`
7. 生成类型清单和实例清单，明确每个类型包含哪些实例以及模型相同的证据。

可从标准工具生成 CSV 骨架：

```powershell
Set-Location 'D:\tmp\digital_twin_aircraft\backend'
python -m tools.generate_migration_classification_csv `
  --input tools/ue_actors_export.json `
  --output tools/ue_migration_classification.csv
```

#### 手动步骤：门禁 A

1. 逐类审核 `hierarchy_path` 是否符合业务结构。
2. 在 UE 视口中检查 AI 命名是否与模型外观相符。
3. 审核“同模型共用一个 Type”的分组；若模型明显不同则拆 Type。
4. 确认实例名可读且能够在 OntoTwin 页面中区分。
5. 对不确定项改为 `needs_review` 并移出本轮，或使用保守名称后明确批准。
6. 明确回复“本轮分类清单正确，可以 dry-run”。

#### 通过条件

- 每个实例恰好归属一个 ObjectType 和一个业务目录。
- 相同模型没有无故重复建 Type，不同模型没有错误合并。
- 不再使用仅含 `Group xxx` 的最终显示名。
- 所有本轮入库行均为 `confirmed`。

### 阶段 4：写库前备份

#### 自动化步骤

1. 创建 PostgreSQL 自包含备份：

```powershell
Set-Location 'D:\tmp\digital_twin_aircraft'
docker compose exec -T db pg_dump -U ontotwin -d ontotwin -Fc `
  -f /tmp/ontotwin_before_round4.dump
docker compose cp `
  db:/tmp/ontotwin_before_round4.dump `
  'D:\path\to\round4\03_backup\ontotwin_before_round4.dump'
```

2. 复制源子关卡 `L_AS_Arch.umap` 到本轮备份目录。
3. 同时归档当前活动的迁移结果、全量快照、分类 CSV、导出 JSON 和迁移前 API 快照。
4. 对备份文件计算 SHA-256，并尝试列出 dump 内容或在隔离环境做恢复演练。

#### 手动步骤

1. 确认备份时间晚于本轮分类批准时间。
2. 确认关卡备份对应当前磁盘上的 `L_AS_Arch`，不是 Autosaves 目录中的文件。
3. 记录“数据库备份 + 关卡备份”为同一个恢复点。

#### 通过条件

- 数据库 dump 和 `L_AS_Arch` 备份均存在、非空、哈希已记录。
- 可以清楚指出恢复时应使用的同组文件。

### 阶段 5：dry-run

#### 自动化步骤

将本轮文件复制或挂载到后端容器可见位置，然后运行：

```powershell
Set-Location 'D:\tmp\digital_twin_aircraft'
docker compose run --rm backend python -m tools.migrate_ue_actors `
  --input tools/ue_actors_export.json `
  --classification-csv tools/ue_migration_classification.csv `
  --dry-run
```

解析并保存统计：

- `new`
- `updated`
- `matched`
- `legacy`
- `skipped`
- `blocked`
- 新增类型数、实例数和渲染部件数
- `delete_actor_guids` 唯一数量

计算预期总量：

```text
迁移后实例数 = 迁移前实例数 + 本轮新增实例数
迁移后类型数 = 迁移前类型数 + 本轮新建类型数
迁移后部件数 = 迁移前部件数 + 本轮新增 render_parts 数
```

若本轮映射已有类型，类型增量可以小于模型组数。若是明确的幂等重跑，允许 `new=0, updated=N`；首次正式迁移前不应出现非预期 `updated`。

#### 手动步骤：门禁 B

1. 审核 dry-run 统计与清单预期是否一致。
2. 特别核对 `delete_actor_guids`，它应是根 Actor 和所有来源 Actor GUID 的唯一并集。
3. 确认没有 `legacy`、`skipped`、`blocked`。
4. 明确回复“dry-run 正确，可以正式写库”。

#### 停止条件

- 本轮首次执行却出现已有实例更新。
- 任何对象进入 Legacy 未分类。
- 出现跳过、阻断、不支持组件或数量不一致。
- 清理 GUID 数量明显小于或大于导出来源 GUID 的唯一并集。

不要为了通过门禁直接使用 `--allow-unsupported`。该参数只能在明确理解组件缺失或负缩放后，经人工批准使用。

### 阶段 6：正式迁移和数据库校验

#### 自动化步骤

1. 使用与 dry-run 完全相同的输入执行正式迁移，仅移除 `--dry-run`：

```powershell
Set-Location 'D:\tmp\digital_twin_aircraft'
docker compose run --rm backend python -m tools.migrate_ue_actors `
  --input tools/ue_actors_export.json `
  --classification-csv tools/ue_migration_classification.csv
```

2. 立即将 `backend/tools/ue_migration_result.json` 复制为 `ue_migration_result_round4.json`。下一轮会覆盖通用文件。
3. 重启后端以刷新激活项目缓存：

```powershell
docker compose restart backend
```

4. 通过 API 和数据库读取校验：
   - 活动数据集仍是预期数据集。
   - UE 绑定仍是 `ueproj_ZHHZ/ZHHZ`。
   - 总类型数、总实例数、总部件数等于本轮公式结果。
   - 每个实例的 `display_name`、`object_type_rid/name`、`hierarchy_path`、变换和 `render_parts` 正确。
   - 类型清单、实例清单、项目快照和图节点名称一致。
   - `blocked_actors=[]`。
   - `delete_actor_guids` 数量与 dry-run 一致。
5. 生成迁移后全量快照 `ue_snapshots_all_after_round4.json`，供 UE 预览。

#### 可选：正式本体图同步

如果本轮类型必须立即成为正式 Neo4j 本体，而不是项目内实验类型，则在审核后执行：

```powershell
python -m tools.build_migration_ontology_patch `
  --csv tools/ue_migration_classification.csv `
  --output tools/ue_migration_ontology_patch.cypher
python -m tools.sync_types_from_graph --apply --add-missing
```

实验类型可以先完成迁移，再在后续治理中合并或晋升。无论何种方式，都不得改变已经确认的实例身份、模型分组和空间变换。

#### 通过条件

- 正式结果与 dry-run 相同。
- API、项目存储和图语义中的名称及类型关联一致。
- 本轮迁移结果已独立归档。
- 此时尚未删除任何 UE 源 Actor。

### 阶段 7：准备 UE 活动交接文件

#### 自动化步骤

1. 将本轮 `ue_migration_result_round4.json` 复制到：

```text
<UE项目>/Saved/OntoTwinMigration/ue_migration_result.json
```

2. 确认该文件只包含本轮的清理名单，不能是上一轮结果，也不能是合并后的多轮清理名单。
3. 将当前数据库的全量快照准备给 UE。全量快照应包含“历史已迁移对象 + 本轮新对象”，用于联合预览。
4. 优先让 UE 从当前后端 HTTP API 拉取；本地 `ue_snapshots.json` 只作为断网回退，并且必须是当前全量快照。
5. 计算两个独立门禁值：
   - 本轮清理 GUID 数量。
   - 数据库当前全量实例和渲染部件数量。

#### 手动步骤

1. 检查 UE 面板连接的是正确后端和数据集。
2. 确认“清理源 Actor”将读取本轮结果文件。
3. 不要在文件未核对时点击任何清理按钮。

### 阶段 8：UE 全量预览和视觉验收

#### 手动步骤

1. 保持打开 `/Game/AVIC_Show/Art/Maps/L_AVIC_SHOW_Main_onto`。
2. 点击“清理预览”，移除旧的临时预览 Actor。
3. 点击“从数据库预览”或对应按钮，生成当前数据库的全量预览。
4. 查看 UE 输出日志或审计结果，应满足：
   - 请求实例数 = 生成实例数 = 数据库当前全量实例数。
   - 预期部件数 = 成功加载部件数 = 数据库当前全量渲染部件数。
   - 完整装配数 = 全量实例数。
   - `malformed=0`
   - `incomplete=0`
   - `part_state_failures=0`
   - `spatial_mismatches=0`
   - `schema_errors=0`
   - 所有预览 Actor 均为 transient。
5. 每个业务类别至少抽查一组；高风险复杂装配应全检：
   - 位置、旋转、缩放正确。
   - 外观、材质和颜色正确。
   - 装配无缺件、无白盒占位。
   - 与原场景没有明显双影或错误重复。
   - Outliner 位于 `TwinPreview/<hierarchy_path>`。
   - OntoTwin 中显示名和类型名可理解。
6. 预览 Actor 不需要保存。正常情况下保存关卡不应持久化 transient 预览对象。

#### 自动化辅助

- 解析 UE 日志生成 `preview_audit_round4.json`。
- 自动比对期望和实际实例/部件数量。
- 自动检查 transient 标记、文件夹路径、部件状态和空间快照。
- 对每类生成视口截图清单，供人工快速抽样。

#### 人工门禁 C

只有用户明确回复“本轮预览正确，可以清理”后，才进入下一阶段。

### 阶段 9：清理本轮 UE 源 Actor 并保存

这是全流程风险最高的步骤，必须有人在 UE 前操作和观察。

#### 清理前自动检查

1. `Saved/OntoTwinMigration/ue_migration_result.json` 的哈希与本轮归档结果一致。
2. `delete_actor_guids` 数量与正式迁移结果一致。
3. `L_AS_Arch_before_round4.umap` 备份存在且哈希有效。
4. 数据库 API 校验仍然通过。
5. UE 当前仍打开正确联合主场景。

#### 手动步骤

1. 点击“清理迁移源 Actor”，不要点击“清理预览”代替。
2. 观察日志，必须出现类似：

```text
result contains G GUIDs, matched G, deleted G
```

其中三个 `G` 均应等于本轮清理 GUID 唯一数量。
3. 在 Outliner 中抽查本轮母 Actor 和子源 Actor 已消失。
4. 执行 **File → Save All**。
5. 等待保存结束，确认日志中出现指向 Content 正式目录的：

```text
OBJ SAVEPACKAGE PACKAGE="/Game/AVIC_Show/Art/Maps/L_AS_Arch"
```

6. 保存完成前不要关闭 UE。

#### 为什么不能只按 Ctrl+S

操作员当前打开的是持久主场景 `L_AVIC_SHOW_Main_onto`，而删除动作实际标脏的是流式子关卡 `L_AS_Arch`。Ctrl+S 可能只保存当前地图，或只生成 Autosave；这会造成“当前会话里看似已删除，重开后源 Actor 又出现”。必须使用 Save All，并以 Content 中 `L_AS_Arch.umap` 的真实写盘变化和保存日志作为证据。

### 阶段 10：清理后的自动磁盘复核

#### 自动化步骤

1. 解析 UE 日志，核对匹配数、删除数和正式 `SAVEPACKAGE` 记录。
2. 重新计算地图文件哈希：
   - `L_AS_Arch.umap` 的修改时间、大小或哈希必须发生符合预期的变化。
   - `L_AVIC_SHOW_Main_onto.umap` 不应无故变化；若变化必须解释。
3. 使用新的只读 Unreal 命令行进程从磁盘重新加载联合主场景。
4. 精确查找本轮 allowlist 中的 Actor Label、Actor Name 和 GUID。
5. 输出 `residual_count`，必须为 0。
6. 确认数据库总量仍等于正式迁移后的预期值。

#### 停止条件

- 删除计数不一致。
- 只有 Autosave，没有 Content 正式保存记录。
- `L_AS_Arch.umap` 没有真实写盘变化。
- 从磁盘重载后仍能找到本轮目标 Actor。
- 主场景或其他无关关卡发生无法解释的修改。

如失败，不要继续下一轮。应保持 UE 关闭或停止编辑，选择重新保存或按第 10 节回滚。

### 阶段 11：最终复核与结项

#### 手动步骤：门禁 D

1. 关闭并重新打开 UE，加载 `L_AVIC_SHOW_Main_onto`。
2. 确认本轮历史源 Actor 没有恢复。
3. 再次清理旧预览并从数据库生成全量预览。
4. 核对全量实例和部件数量，以及每个业务类别的视觉样本。
5. 确认无双影、无缺件、无错误目录、无不可读名称。
6. 预览是临时对象，不要求保存。
7. 明确记录“第 N 轮复核完成”。

#### 自动化步骤

生成 `final_acceptance_round4.md`，至少包含：

- 本轮输入数、唯一目标数。
- 新建/复用类型数、新增实例数、新增部件数。
- 迁移前和迁移后全量统计。
- 清理 GUID 数量和磁盘残留数量。
- 数据库 dump、关卡备份和关键产物哈希。
- 人工门禁 A/B/C/D 的批准人和时间。
- 已知问题和推迟项。

## 8. 名称与类型治理细则

### 8.1 推荐命名结构

ObjectType 名称应表达模型类型，例如：

```text
双人浅色沙发
落地式触控操作终端
横向 LED 主屏
歼-20 航空模型
矩形玻璃展柜 A 型
```

实例名应表达可区分的摆放实体，例如：

```text
双人浅色沙发 01
双人浅色沙发 02
一层北区落地式触控终端
主展厅歼-20 航模
```

稳定编号只是消歧手段，不应替代可以识别的业务名称。

### 8.2 模糊 Group 对象的识别顺序

1. 看模型整体轮廓和尺寸。
2. 看资产路径、网格名、材质名和贴图名。
3. 看组件数量、结构和相对变换。
4. 看场景位置与邻近展项。
5. 搜索相同几何签名的其他实例。
6. 由人工在视口确认。
7. 仍不确定时使用保守类别名并标注待治理，不猜测品牌、型号或用途。

### 8.3 迁移后的语义重命名

如果迁移后要修正名称，必须一次性同步更新：

- ObjectType 显示名。
- 实例 `display_name`。
- 实例 `object_type_name`。
- 图数据库/类型注册中的节点名称。
- 需要调整时的 `hierarchy_path`。
- 类型清单、实例清单和全量快照。

重命名不得改变 RID、实例 ID、模型分组、空间变换或渲染部件归属。重命名后仍需做 API 校验和 UE 预览抽查。

## 9. 大规模分批策略

建议按“业务类别 × 空间区域”分轮，而不是一次迁完整场景。每轮应满足：

- 人工可以在一次预览中完成视觉核对。
- 清理 GUID 数量在日志中容易审计。
- 同一模型族尽量在同一轮完成，便于复用 Type。
- 高风险蓝图、骨骼资产、负缩放对象和普通静态装配分开处理。
- 不确定对象单独进入 `needs_review` 批次，不阻塞明确对象。

推荐批次顺序：

1. 语义明确、装配简单、重复度高的设备。
2. 家具、展陈装置等中等复杂对象。
3. 显示设备、操作终端等带材质或屏幕表现的对象。
4. 蓝图、骨骼网格、动态组件或特殊缩放对象。

在大规模运行中，AI 可以并行做候选分析、模型聚类和名称建议，但最终写库必须使用合并后、去重后、人工批准的一份权威 CSV；不得让多个 AI 同时写同一活动数据集。

## 10. 回滚 SOP

### 10.1 数据库写入失败，但尚未清理 UE 源 Actor

1. 停止后端写入。
2. 使用本轮写库前的 PostgreSQL dump 恢复数据库。
3. 重启后端并重新读取活动数据集、绑定和基线总量。
4. UE 场景无需恢复，因为源 Actor 尚未删除。
5. 修复分类或迁移脚本后从 dry-run 重新开始。

### 10.2 已点击清理，但尚未正确 Save All

1. 不继续编辑场景。
2. 如果删除只存在于内存，可不保存并关闭 UE，然后从磁盘重新打开。
3. 若状态不确定，先备份当前文件，再与本轮备份哈希比较。
4. 数据库可暂时保留迁移结果；重新预览正确后再执行清理。

### 10.3 已清理且已保存，需要完整回滚

1. 关闭 UE，停止后端服务。
2. 恢复本轮写库前的数据库 dump。
3. 恢复同一恢复点的 `L_AS_Arch_before_roundN.umap`。
4. 如 UE 依赖本地迁移结果或快照，恢复与该数据库状态相匹配的文件。
5. 启动后端，核对数据集和绑定。
6. 只读加载 UE，确认源 Actor 已恢复、数据库新增对象已消失。
7. 重新建立基线后才能再迁移。

严禁只恢复数据库而不恢复已清理的关卡，或只恢复关卡而保留数据库新增实例，否则会出现缺失或双影。

## 11. 常见故障与处理

| 现象 | 常见原因 | 处理 |
|---|---|---|
| UE 面板缺少新按钮 | 只做 Live Coding，模块或面板未完整刷新 | 关闭 UE，完整编译 `ZHHZEditor`，重新打开 |
| Live Coding 报 `C4800`，指向 `FJsonValueBoolean` | UE 位字段如 `bHiddenInGame` 的底层类型是 `uint8`，新编译器拒绝隐式转 bool | 在插件代码中显式写成 `PartComponent->bHiddenInGame != 0`，重新编译；不要关闭该编译器诊断 |
| 导出为 0 | 主场景/子关卡未加载、SceneId 过滤错误、名称未精确匹配 | 记录当前地图和 loaded levels，取消错误过滤，按 GUID 消歧 |
| 预览出现白盒 | 蓝图/骨骼/不支持组件未正确导出，资产路径无效 | 停止清理，检查导出组件和资产路径，修复后重迁 |
| dry-run 出现 Legacy | 分类 CSV 未覆盖所有 assembly key | 补全 CSV，重新生成并审核 |
| 同模型生成多个 Type | 只按名称或导入上下文分组 | 比较几何、网格、材质和视觉外观，合并模型组 |
| 不同模型被合成一个 Type | 只依赖 `assembly_signature` | 拆分 Type，使用更可靠的模型证据 |
| 清理按钮删除数为 0 | `ue_migration_result.json` 路径或轮次错误 | 比对文件哈希和 `delete_actor_guids`，不要重复点击 |
| 当前会话已删除，重开又出现 | 只 Ctrl+S 或只写入 Autosave，未保存 `L_AS_Arch` | 再次清理并执行 File → Save All，检查正式 `SAVEPACKAGE` |
| 预览数量少于数据库 | 本地快照不是全量或后端缓存未刷新 | 重启后端，重新生成全量快照并清理旧预览 |
| 预览双影 | 源 Actor 尚未清理，或旧预览未先清除 | 在验收时区分“预期源+预览双影”；正式复核前清理源和旧预览 |
| 第二轮误清第一轮对象 | 通用迁移结果文件被后续覆盖或混合 | 每轮归档结果；活动结果只能放当前轮次 |

## 12. 交给其他 AI 的标准任务包

每次交接至少提供以下内容：

```text
目标：执行 OntoTwin 历史 UE 数据第 {N} 轮迁移。

固定环境：
- UE 项目：{uproject}
- 操作主场景：{main_map}
- 源 Actor 子关卡：{source_sublevel}
- OntoTwin 仓库：{repo}
- 活动数据集：{dataset_id}
- UE 绑定：{ue_project_id}/{ue_project_name}
- 迁移前总量：Types={types_before}, Instances={instances_before}, Parts={parts_before}

本轮输入：
- 目标 Actor 名称/GUID：{allowlist}
- 业务类别：{categories}
- 实例边界：母 Actor 为实例；子静态网格是 render parts；仅显式点名的单体 StaticMeshActor 可成为实例。
- 类型规则：不同模型不同 Type；相同模型多实例共享 Type。
- 命名规则：不得保留纯 Group 名；证据不足时使用保守类别名和稳定编号。

必须输出：
1. 候选解析和歧义报告。
2. assembly_v1 导出及审计。
3. ObjectType/实例/目录分类清单和 CSV。
4. 新增量及迁移后总量预测。
5. DB dump 和 L_AS_Arch 备份及哈希。
6. dry-run 报告；等待人工批准。
7. 正式迁移结果、全量 API 校验和全量快照。
8. 等待人工完成 UE 预览并明确批准。
9. 为人工清理准备本轮结果文件；不得自动点击清理。
10. Save All 后执行日志、文件哈希和磁盘重载残留校验。
11. 最终验收报告。

禁止：
- 不经批准写库或删除源 Actor。
- 把每个 StaticMeshActor 拆成实例。
- 只按 assembly_signature 合并模型类型。
- 使用上一轮 ue_migration_result.json 清理。
- 用 Ctrl+S 代替 Save All。
- 保存 TwinPreview 临时 Actor。
- 修改与本轮无关的关卡、Actor 或数据库对象。

每遇到以下情况立即停止：名称歧义、绑定不符、已有 GUID 重叠、unsupported、dry-run 数量异常、预览审计失败、删除数不符、正式关卡未写盘、磁盘重载仍有残留。
```

## 13. 每轮执行勾选表

### 准备

- [ ] 已确定轮次编号、业务类别和目标 allowlist。
- [ ] 已打开正确主场景，确认源 Actor 位于正确流式子关卡。
- [ ] 已确认活动数据集和 UE 项目绑定。
- [ ] 已记录迁移前 Types/Instances/Parts 总量。
- [ ] 已确认没有来源不明的未保存 UE 修改。

### 导出与分类

- [ ] 所有输入名称已去重、解析、消歧。
- [ ] 母 Actor 实例边界已人工确认。
- [ ] 只读导出未保存关卡，导出后文件夹已恢复。
- [ ] 无 unsupported/负缩放阻断项，或有单独批准。
- [ ] 不同模型不同 Type，相同模型共享 Type。
- [ ] `hierarchy_path` 和 ObjectType 已分开审核。
- [ ] Group 对象已有可理解名称。
- [ ] 门禁 A 已批准。

### 备份与迁移

- [ ] 本轮数据库 dump 已创建并校验。
- [ ] 本轮 `L_AS_Arch` 备份已创建并校验。
- [ ] dry-run 无 Legacy/Skipped/Blocked，数量正确。
- [ ] 门禁 B 已批准。
- [ ] 正式迁移结果与 dry-run 一致。
- [ ] 通用结果已立即归档为本轮结果。
- [ ] 后端已重启，API 和数据库总量正确。

### UE 预览与清理

- [ ] UE 活动结果文件是本轮结果，哈希一致。
- [ ] UE 使用当前数据库全量快照。
- [ ] 已清除旧预览并完成全量预览。
- [ ] 实例、部件、装配、空间和 transient 审计全部通过。
- [ ] 已完成每类视觉抽查。
- [ ] 门禁 C 已明确批准清理。
- [ ] 已有本轮清理前关卡备份。
- [ ] 源 Actor 匹配数 = 删除数 = 本轮清理 GUID 数。
- [ ] 已执行 File → Save All。
- [ ] 日志确认正式保存 `/Game/AVIC_Show/Art/Maps/L_AS_Arch`。

### 最终验收

- [ ] `L_AS_Arch.umap` 已真实写盘并发生预期变化。
- [ ] `L_AVIC_SHOW_Main_onto.umap` 无非预期变化。
- [ ] 磁盘重载后本轮目标残留为 0。
- [ ] 重启 UE 后全量预览仍通过。
- [ ] 无双影、缺件、白盒、错误目录或不可读名称。
- [ ] 最终审计文件和所有哈希已归档。
- [ ] 门禁 D 已记录，本轮结项。

## 14. ZHHZ 三轮迁移结果基线

| 轮次 | 新增 Type | 新增实例 | 新增 render parts | 清理源 GUID | 迁移后累计 |
|---|---:|---:|---:|---:|---|
| 第一轮 | 8 | 141 | 3,771 | 4,462 | 8 Types / 141 Instances / 3,771 Parts |
| 第二轮 | 52 | 66 | 3,878 | 4,047 | 60 Types / 207 Instances / 7,649 Parts |
| 第三轮 | 20 | 21 | 419 | 441 | 80 Types / 228 Instances / 8,068 Parts |

第三轮输入原有 22 行，其中 `LE360` 重复，最终是 21 个唯一 Actor。`Group2136670272` 与 `Group2136670331` 被确认为同一模型的两个实例；`Rectangle2133395720` 是用户明确指定的单体 `StaticMeshActor` 例外。这三个案例应作为后续去重、模型分组和实例边界判断的回归样例。

## 15. 参考实现

通用后端工具：

- `backend/tools/generate_migration_classification_csv.py`
- `backend/tools/build_migration_ontology_patch.py`
- `backend/tools/sync_types_from_graph.py`
- `backend/tools/migrate_ue_actors.py`

ZHHZ 第三轮的轮次化参考脚本：

- `C:\Users\ADMIN\Documents\zhhz\.codex_migration_work\scripts\ue_export_zhhz_round3_named.py`
- `C:\Users\ADMIN\Documents\zhhz\.codex_migration_work\scripts\ue_verify_zhhz_round3_cleanup.py`
- `C:\Users\ADMIN\Documents\zhhz\scripts\build_zhhz_round3_classification.py`
- `C:\Users\ADMIN\Documents\zhhz\scripts\verify_zhhz_round3_migration.py`
- `C:\Users\ADMIN\Documents\zhhz\scripts\build_zhhz_all_snapshot_file.py`

这些脚本可以作为其他 AI 生成新一轮 allowlist 导出、分类构建和清理复核脚本的参考，但不得直接把第三轮的 Actor 名单、路径或数量当成新一轮输入。
