# OntoTwin 4.3.0 实施记录

> 状态：开发完成，待 UE 启动后完成按需目录扫描验收  
> 日期：2026-08-18；更新：2026-08-19  
> 关联 PRD：`docs/PRD/OntoTwin 4.3.0 多形态UE资产运行时加载 (PRD).md`、`docs/PRD/OntoTwin 4.2 CAD类型级UE资产选择与推荐 (PRD).md`

## 1. 实施范围

- `ATwinInstance` 多形态表现与热切换。
- Actor Blueprint 生成类加载、校验和 ChildActor 生命周期。
- SkeletalMesh 组件、材质、显隐和卸载。
- Blueprint 子 Actor 包围盒与现有交互/Runtime Gizmo 兼容。
- UE 资产目录的运行时可用性元数据。
- OntoTwin 后端/UI 的运行时支持状态。
- 宿主项目已确认资产目录的 Cook 配置。
- 通用 UE 目录树发布、Web 目录选择/填写、UE 按需扫描与限定目录推荐闭环。

## 2. 设计约束

- 不改变 ProjectStore、mapping rules 或快照字段结构。
- 不新增第三方依赖。
- 保留 StaticMesh、glTF、ArtStudio、assembly_v1 代码路径。
- Blueprint 仅支持普通 Actor 生成类。
- 直接 SkeletalMesh 不推断动画。

## 3. 变更清单

| 模块 | 文件 | 状态 |
|---|---|---|
| UE Runtime | `TwinInstance.h/.cpp` | 已完成 |
| UE Runtime Editor | `TwinSceneManager.cpp` | 已完成 |
| UE Catalog | `UEAssetCatalogSyncComponent.h/.cpp` | 已完成 |
| Backend | `backend/ue_asset_catalog/service.py` | 已完成 |
| Web | `frontend/coord_workbench.html` | 已完成 |
| Packaging | `DigitalFactoryBase_SCC/Config/DefaultGame.ini` | 已完成 |
| Version | `OntoTwinSync.uplugin` | 已完成，4.3.0 |

## 4. 实施记录

### 2026-08-18

- `ATwinInstance` 新增 `USkeletalMeshComponent` 与 `UChildActorComponent`，通过互斥主表现保持实例身份稳定。
- `/Game` 与 `/Engine` 资产按 StaticMesh、SkeletalMesh、Actor Blueprint 生成类顺序识别；失败回退 Cube。
- Blueprint 仅允许普通 Actor 生成类，并拒绝 Pawn、Controller、LevelScriptActor、抽象类与废弃类。
- Blueprint 子 Actor 已接入射线所属解析、聚焦包围盒、Runtime Gizmo 局部包围盒和信息面板锚点。
- Representable 卸载会释放单资产表现；Visual 显隐只隐藏并保留状态。
- 资产目录新增 `generated_class_path / runtime_loadable / runtime_reason`；后端只允许运行时可用资产参与推荐和确认。
- SkeletalMesh bounds 纳入目录同步，直接加载使用参考姿势。
- 资产目录组件增加“配置扫描目录用于打包”按钮和 Cook 缺失诊断。
- 当前宿主工程 `/Game/Art` 已加入 `DirectoriesToAlwaysCook`。
- 当前工程的 OntoTwinSync 是指向主仓插件源码的 Junction，无需维护第二份源码副本。

### 2026-08-19

- UE 插件周期性发布 `/Game` 轻量目录树，只传目录名，不预扫描整个工程的资产详情。
- 类型审核页增加“推荐模型目录”：可从 UE 目录列表选择，也可填写任意 `/Game/...` 目录。
- 用户点击“同步并推荐”后，后端创建带唯一 ID 的待扫描请求；UE 编辑器、PIE 或运行时轮询请求，只递归扫描本次选择的目录。
- UE 上传本次目录簿后自动完成请求；Web 轮询到完成状态后，才在该目录及其子目录范围内生成推荐。
- 后端新增目录索引、扫描请求创建/查询、UE 待办查询和失败回报接口，并保留最近一次目录树与请求状态。
- 源码中移除默认 `/Game/Art` 扫描根；`AssetRoots` 和“启动时同步”仅作为显式配置的兼容入口，不参与默认按需流程。
- `/Game/SCC/Art` 仅作为本次验收输入保存为待扫描请求，不存在 SCC 专用分支或目录常量。
- 修复验收缺陷：合并已有类型并选择“保留原类型”时，类型结构继续保留，但人工确认的 `asset_id / ue_asset_path` 作为独立模型补丁写入，不再随结构冲突一起跳过。
- 合并接口新增实际模型写入/变更计数；类型审核页明确区分“保留类型结构”和“更新确认模型”，成功提示不再以推荐记忆数量冒充类型模型写入数量。

## 5. 编译结果

- `DigitalFactoryBaseEditor Win64 Development`：C++、UHT、静态库均通过；因正在运行的 UnrealEditor 占用默认 DLL，使用模块后缀 `4300` 完成 DLL 链接，结果 `Succeeded`。
- `DigitalFactoryBase Win64 Development`：非编辑器目标完整编译和链接成功，结果 `Succeeded`。
- 后端 Python AST 解析通过；隔离目录烟雾检查结果为 4 个资产中 3 个可运行、无效 Blueprint 被拒绝。
- 2026-08-19 通用目录按需同步最终改动完成 `DigitalFactoryBaseEditor Win64 Development` 编译，模块后缀 `4340`，结果 `Succeeded`。
- 2026-08-19 通用目录按需同步最终改动完成 `DigitalFactoryBase Win64 Development` 非编辑器目标完整编译和链接，结果 `Succeeded`。

## 6. 当前生效条件

启动 UnrealEditor 后应加载最新 OntoTwinSync 模块。类型审核页已为当前绑定工程保留 `/Game/SCC/Art` 的待扫描请求；UE 的 TwinSceneManager 存在且组件启用时会自动发布真实目录树、领取请求并上传该目录簿。无需把目录写入插件源码或手工点击旧的全量同步按钮。

## 7. 已知边界

- 直接 SkeletalMesh 只显示参考姿势；动画由绑定的 Actor Blueprint 提供。
- 任意 Blueprint 内部材质和业务逻辑不由 OntoTwin 强制覆写。
- UE 不在线时扫描请求保持等待；目录不存在或扫描失败时 Web 展示 UE 返回的错误，不能回退到其他目录推荐。
- 尚未执行 Shipping Cook/Package 和视觉人工验收；见验收清单。
