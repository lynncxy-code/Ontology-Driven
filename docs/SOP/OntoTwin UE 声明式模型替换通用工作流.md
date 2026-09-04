# OntoTwin UE 声明式模型替换通用工作流

## 适用场景

当 UE 场景已经完成一轮迁移，但需要用一批经过确认的新模型替换旧的迁移实例时使用。
典型流程是：模型重分类、Group 拆分、模型修正或离线重建后，保留手工/实时实例，只替换本轮明确声明的旧迁移实例。

这不是日常的新实例迁移工具，也不是 UE 源 Actor 清理工具，更不是运行时 transform 回写接口。

## 组件分工

```text
backend/tools/migrate_ue_actors.py
    └─ 生成新实例与迁移结果

backend/tools/ue_replacement.py
    └─ 通用安全门禁：身份、scope、GUID、类型、digest、hash、apply 比对

backend/tools/test0316_onboarding_20260827/replace_test0316_models.py
    └─ test0316 适配器，只提供项目专属 RID、夹具和输入转换
```

`ue_replacement.py` 不直接读写数据库或 UE 文件；数据库备份、UE 地图备份、冷启动和 PIE 验收仍由 `ue-super-steward` 的阶段 4–9 负责。

## 通用调用原则

替换输入必须包含：

- `project_id`
- `ue_project_id`，可选 `ue_project_name`
- 新 Actor 列表和类型规格
- `replacement.old_instance_ids`
- `replacement.source_actor_guids`
- 新实例 ID hash、数量和清理 GUID 数

禁止用“当前项目内所有 `source == ue_migrated`”作为通用替换范围。

## test0316 适配器调用

### 1. 先做 dry-run

```powershell
python backend/tools/test0316_onboarding_20260827/replace_test0316_models.py `
  --project-id ds_<target> `
  --input test0316_confirmed_export.json `
  --types test0316_type_specs.json `
  --scope approved_replacement_scope.json `
  --manifest dry_run_manifest.json
```

`approved_replacement_scope.json` 只描述旧实例，例如：

```json
{
  "old_instance_ids": ["ue_old_001", "ue_old_002"],
  "source_actor_guids": ["GUID-OLD-001", "GUID-OLD-002"],
  "expected_old_instance_count": 2,
  "expected_new_instance_count": 421,
  "new_instance_ids_hash": "sha256:<dry-run 生成的值>",
  "expected_delete_actor_guid_count": 423
}
```

dry-run 后必须人工检查：

- 替换旧实例是否全部属于本轮迁移批次。
- 手工、AGV、人物和实时实例是否在 `preserved_live_instance_ids` 中。
- Types、Instances、Parts 和清理 GUID 数量是否符合预测。
- `stale_component_bindings` 和 `stale_roster_bindings` 是否需要人工处理。

### 2. 通过批准的 manifest 执行 apply

```powershell
python backend/tools/test0316_onboarding_20260827/replace_test0316_models.py `
  --project-id ds_<target> `
  --input test0316_confirmed_export.json `
  --types test0316_type_specs.json `
  --scope approved_replacement_scope.json `
  --manifest apply_manifest.json `
  --expected-manifest dry_run_manifest.json `
  --apply
```

没有 `--expected-manifest` 时，工具拒绝 apply。输入、类型规格、旧项目 digest、实例 hash 或数量发生变化时，必须重新 dry-run。

## 普通 UE 迁移器中的声明式替换

已有 `migrate_ue_actors.py` 的 assembly 迁移流程可复用同一安全函数：

```powershell
python backend/tools/migrate_ue_actors.py `
  --input assembly_export.json `
  --mapping mesh_type_mapping.json `
  --replace-declared-in-input `
  --dry-run
```

调用方必须在输入 JSON 的 `replacement` 中提供显式旧实例和源 Actor 范围。`ue_replacement.py` 会拒绝缺少 scope、来源不匹配、GUID 重复、类型缺失、unsupported 或新旧 ID 重叠的计划。

## 不应使用的场景

- 只是新增一批普通 UE 实例：使用标准迁移流程，不要声明 replacement。
- 只想删除源 Actor：先完成数据预览和 PIE 验收，再使用精确 GUID 清理门禁。
- 运行时位置同步：使用 runtime/writeback 接口，不要重写项目快照。
- 处理手工、AGV、人物或实时实例：除非它们明确属于本轮替换清单，否则不得加入 scope。
- 不同项目之间复制模型：先建立新的四层身份和独立输入清单。

## 安全门禁顺序

```text
建立四层身份
  → 备份数据库和 UE 地图
  → 生成 dry-run
  → 审查 scope / counts / hashes
  → apply
  → API + PG 回读
  → 冷启动 / PIE 验收
  → 另行批准源 Actor 清理
```

声明式替换完成，不等于源 Actor 已经可以删除；数据库写入和 UE 清理必须保持两个独立门禁。
