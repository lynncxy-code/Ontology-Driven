# OntoTwin 4.4.0 实施记录

> PRD 编号：`PRD-OT-4.4-001`
> 状态：开发、编译与 SCC Machine 蓝图接入完成；待业务数据配置后的 PIE 视觉验收
> 日期：2026-08-20
> 关联 PRD：`docs/PRD/OntoTwin 4.4 BP容器化表现能力 (PRD).md`

## 1. 实施范围

- ObjectType 级 Blueprint 表现容器配置、清除和批量应用。
- 新实例冻结配置、旧实例实时继承、跨数据集快照与 delta 变更检测。
- `ATwinInstance` 创建容器 ChildActor，并将单个 Cooked StaticMesh 注入逻辑槽位。
- 容器显隐、卸载/重载、资产/容器热切换，以及视觉/行为状态事件转发。
- 类型页配置 UI、批量确认 UI，以及实例页有效配置展示。
- SCC Machine Blueprint 接入 `UTwinRepresentationHostComponent`。

## 2. 已确认设计

- 容器配置属于 ObjectType；首版不开放实例级容器覆盖。
- 容器与 `assembly_v1/render_parts` 互斥；组合模型始终按原组合路径渲染。
- 首版只向容器注入 `/Game` 或 `/Engine` 下的 Cooked StaticMesh。
- 容器 BP 仍拥有自身 Tick、碰撞、动画和业务组件；OntoTwin 只管理目标表现槽位。
- `UTwinRepresentationHostComponent` 是显式协议，不使用“找到的第一个 Mesh”推断。
- 当前工程只维护主线插件；`DigitalFactoryBase_SCC` 通过 Junction 使用该主线。

## 3. 变更清单

| 模块 | 文件 | 状态 |
|---|---|---|
| Backend | `backend/representation_container/` | 已完成 |
| Backend | `backend/app.py`、`dataset_activation.py`、`snapshot_delta.py` | 已完成 |
| Backend | `backend/instance_model_binding/service.py` | 已完成 |
| Web | `frontend/ontology.html`、`frontend/instance.html` | 已完成 |
| UE Runtime | `TwinRepresentationHostComponent.h/.cpp` | 已完成 |
| UE Runtime | `TwinInstance.h/.cpp`、`TwinSceneManager.cpp` | 已完成 |
| UE Blueprint | `BP_Item_base_SCC_Machine` Host 配置脚本 | 已执行并复验 |
| Version | `OntoTwinSync.uplugin`、插件 README | 已更新到 4.4.0 |

## 4. 协议与优先级

`I3D_Representable` 在单模型模式下可增加：

```json
{
  "asset_id": "/Game/.../SM_Machine.SM_Machine",
  "container_blueprint_id": "/Game/SCC/Program/Function/Machine/BP_Item_base_SCC_Machine.BP_Item_base_SCC_Machine",
  "container_slot": "primary"
}
```

有效配置解析顺序：实时 ObjectType 配置优先；类型不可用时使用实例冻结配置；有效模型为 `original_assembly` 时强制抑制容器。

## 5. 后端与 Web 实施结果

- 新增类型级 GET、PUT、DELETE 和批量 POST API。
- 所有写操作必须携带 `expected_project_id`；项目切换返回 409。
- 保存前校验 `I3D_Representable`、资产路径、槽位名称和 assembly 冲突。
- 批量应用只处理已启用三维表现且已绑定类型模型的类型，并返回逐类型跳过原因。
- 类型响应、实例模型摘要、快照和 delta token 均纳入有效容器配置。
- 类型页支持保存、恢复直接表现和带自定义确认框的批量应用；实例页展示最终有效容器。

## 6. UE Runtime 实施结果

- `UTwinRepresentationHostComponent` 提供 `SlotName`、显式 `FComponentReference` 和精确名称兼容回退。
- `ATwinInstance` 加载并校验普通 Actor Blueprint 生成类，通过 `UChildActorComponent` 保持子 BP 生命周期。
- Host 匹配后注入 StaticMesh；缺少 Host、槽位不匹配、模型类型不兼容或资源加载失败时使用 Cube fallback 并记录明确日志。
- 容器和模型字段变化会热重建当前单资产表现；从 assembly 退出时按当前有效配置恢复容器或直接模式。
- 视觉可见性和行为状态通过 Host 动态多播事件交给业务 BP；子 BP 本身的 Tick 与碰撞不被覆盖。
- 现有射线选择通过 ChildActor 的 Owner/AttachParent 回溯到 `ATwinInstance`；包围盒继续包含 ChildActor 及附着后代。

## 7. 验证记录

- Python 语法编译：通过。
- 新增 `test_representation_container.py`：6 项通过。
- `test_migration_assembly.py` 与 `test_snapshot_delta.py`：23 项通过。
- `ontology.html`、`instance.html` 内联 JavaScript：`node --check` 通过。
- `DigitalFactoryBaseEditor Win64 Development`：UHT、C++、静态库与 DLL 链接通过，结果 `Succeeded`。
- `DigitalFactoryBase Win64 Development`：非编辑器运行时目标编译并链接通过，结果 `Succeeded`。
- SCC Machine 蓝图脚本执行结果：`status=ok`，新增 `OntoTwinRepresentationHost`，`slot=primary`，`target=StaticMesh`；保存后复验通过。
- PIE 视觉验收未自动执行：开发过程不修改当前项目的 ObjectType 业务配置，需在类型页选择单类型保存或确认批量应用后进行。

## 8. 当前验收边界

- 不自动修改当前项目的 ObjectType 业务数据；由类型页选择单类型保存或批量应用。
- 不支持 glTF、ArtStudio 标识、SkeletalMesh 或 assembly 部件注入容器。
- Host 只接管目标 StaticMeshComponent；材质变体的业务映射由容器 BP 订阅事件实现。
