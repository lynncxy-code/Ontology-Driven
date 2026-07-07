# OntoTwin 3.4.1 实例树与 UE 迁移分类补充方案

## 背景

历史 UE 项目迁移后，实例如果全部进入 `Legacy 未分类`，产品和验收侧无法判断对象语义；部分蓝图或骨骼资产还可能只被导出为静态网格占位，导致 UE 预览里出现方盒子或资产缺失。同时，正向由 OntoTwin 铸造的实例也需要在 OntoTwin 清单和 UE Outliner 中保持可读的层级结构。

## 决策

- 主产品不新增“迁移分类工作台”。
- 实例树结构以实例字段 `hierarchy_path` 为真源。
- UE Outliner 文件夹不自动回写 OntoTwin；历史迁移时只读取一次原 UE 文件夹。
- 低频迁移分类通过离线 CSV 小工具完成；必要时生成 Neo4j Cypher 补丁，先补本体图数据库，再同步回 OntoTwin 项目类型缓存。

## 数据字段

实例新增元数据：

- `display_name`：实例显示名，默认等于 `instance_id`。
- `hierarchy_path`：实例树路径，正向铸造默认 `[object_type_name]`。
- `source_folder_path`：历史迁移来源 UE 文件夹。
- `source_asset_path`：历史迁移来源资产路径。
- `classification_status`：`confirmed / needs_review / legacy`。
- `classification_key`：迁移分组键，如 `static_mesh_asset:/Game/...`。

## UE 行为

- 运行时实例文件夹：`TwinInstances/<hierarchy_path...>`。
- 编辑器预览文件夹：`TwinPreview/<hierarchy_path...>`。
- UE 导出历史 Actor 时补充：
  - `actor_label`
  - `actor_name`
  - `source_folder_path`
  - `actor_class`
  - `actor_class_path`
  - `blueprint_class_path`
  - `static_mesh_asset/static_mesh_assets`
  - `skeletal_mesh_asset/skeletal_mesh_assets`
  - `component_summary`

## 离线工具流程

1. UE 导出历史 Actor JSON。
2. 生成可编辑 CSV：

```powershell
python -m tools.generate_migration_classification_csv --input tools/ue_actors_export.json --output tools/ue_migration_classification.csv
```

3. 用 Excel 编辑 CSV：
   - 映射已有类型：填 `suggested_object_type_rid`，`action=map_existing`。
   - 创建实验态候选类型：填 `suggested_object_type_name`，`action=create_experimental`。
   - 调整 `hierarchy_path`，控制 OntoTwin 实例树和 UE 文件夹。

4. 如需补 Neo4j 本体库，生成 Cypher：

```powershell
python -m tools.build_migration_ontology_patch --csv tools/ue_migration_classification.csv --output tools/ue_migration_ontology_patch.cypher
```

5. 灌入 Neo4j 后，同步类型缓存：

```powershell
python -m tools.sync_types_from_graph --apply --add-missing
```

6. 执行迁移：

```powershell
python -m tools.migrate_ue_actors --input tools/ue_actors_export.json --classification-csv tools/ue_migration_classification.csv
```

## 验收标准

- OntoTwin 实例清单按 `hierarchy_path` 分组展示。
- 正向铸造实例默认进入 `object_type_name` 分组。
- UE 拉取预览后，Actor 位于 `TwinPreview/<类型或层级>`。
- UE 运行时轮询生成后，Actor 位于 `TwinInstances/<类型或层级>`。
- 历史迁移导出的 JSON 包含原 UE 文件夹、蓝图/类路径、静态网格、骨骼网格信息。
- CSV 修改后的 `hierarchy_path` 能影响迁移实例在 OntoTwin 和 UE 的层级。
- 低频历史分类不进入主产品 UI。
