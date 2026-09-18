# OntoTwin 4.5 语义表现路由层（PRD）

> 2026-09-17 基础运动变更：以[4.5／4.6 基础运动行为增补](<OntoTwin 4.5-4.6 基础运动行为增补 (2026-09-17).md>)为准。实际模型运动取代新目录中的旋转指示示例；来源名称为“行为库／项目自带”。本文件的历史范围不代表全部已验收。

| 项目 | 内容 |
|---|---|
| PRD 编号 | `PRD-OT-4.5-001` |
| 版本 | v1.0（范围确认稿） |
| 状态 | 已进入实施，待验收 |
| 确认日期 | 2026-08-28 |
| 目标版本 | `OntoTwinSync 4.5.0` |
| 前置版本 | 4.4.0 BP 容器化表现能力（单独验收） |
| 归属 | OntoTwin 核心表现路由层 |

## 1. 背景与问题

当前运行时快照以 `animation_state`、`fx_trigger`、`material_variant` 等平面字段直接驱动 UE 表现。字段能够完成兼容和调试，但不能表达“主状态 + 修饰条件 + 一次性动作”，也不能在项目实现、平台通用行为和安全回退之间进行可解释、可诊断的选择。`I3D_Visual` 与 `I3D_Behavioral` 目前分别承载视觉和行为字段，缺少跨通道的一致决策边界。

4.5 在保留旧字段的前提下增加语义表现路由层：Nexus 负责将输入状态归一化并生成表现意图及路由决策；UE Blueprint、Animation Blueprint 或平台行为库负责执行。首期服务工业设备实时状态，不把本轮扩展为通用规则引擎或流程时间轴。

面向业务用户的入口不是行为 ID 编辑器：Nexus 的“设备表现策略”只提供“工业设备默认表现”和“安全静态表现”两种可读方案；内部逻辑行为 ID、受控槽位和解析证据仅在开发者技术诊断区显示。工业默认行为库保持独立 PRD/版本线，但验收向导必须从当前类型卡片继续进入，不能在左侧菜单另设一个脱离上下文的入口。

## 1.1 编号与归属依据

- 本需求不是 4.4 的小补丁：`PRD-OT-4.4-001` 的核心是 ObjectType 级 BP 容器、单 StaticMesh 槽位和事件转发契约，并明确不在当轮定义项目业务映射；4.5 新增的是跨通道语义模型、归一化、路由优先级和执行器发现，改变了表现决策边界。
- 本需求也不是脱离现有表现链路的新产品线：它延续 4.3 多形态资产和 4.4 BP 容器能力，仍服务 `OntoTwinSync` 运行时表现，因此归入 4.5 表现能力演进。
- 路由层与行为库采用两条独立能力线：`PRD-OT-4.5-001` 只定义必须安装的核心协议/路由能力；工业默认行为库另立 `PRD-OT-4.6-001`，拥有独立的版本、实施计划、验收清单和启停/回滚边界。
- 既有 RID `I3D_Behavioral` 保留并扩展；既有 RID `I3D_Visual` 同样属于本轮表现层，但作为可独立挂载的执行投影纳入协调边界，不被删除、改名或强制迁移。

## 2. 目标

1. 建立可版本化的 `I3D_Presentation` 协调接口，作为表现意图和路由决策的唯一权威来源。
2. 统一表达主状态、可组合修饰条件和一次性动作，并支持动画、材质、特效、标签等多通道。
3. 对每个通道实施确定性的三级解析：项目显式实现 > 平台通用行为库 > 静态安全回退。
4. 通过 UE `IModularFeatures` 执行器注册机制接入可选行为库，核心层在行为库缺失时仍可安全运行。
5. 让现有 `I3D_Visual`、`I3D_Behavioral` 和旧字段保持兼容，同时禁止同一语义在新旧通道被重复执行。
6. 为工业设备建立受控表现槽位和稳定逻辑行为 ID，避免 Nexus 依赖 UE 资产路径。

## 3. 非目标与边界

- v1 不实现通用规则引擎、任意脚本表达式、流程时间轴或后端动作队列。
- v1 不改变 `ProjectStore` 文件格式、`mapping_rules.json` 或其他既有存储结构；若实施需要新增持久化字段，必须先完成兼容性评审和单独批准。
- v1 不允许实例级路由覆盖；表现配置挂在 ObjectType 的 `presentation_profile`。
- Nexus 不直接加载、解析或持有 UE Blueprint/Animation Blueprint 资产路径。
- 不替换 4.4 BP 容器能力；4.4 仍是独立前置能力和验收门槛。
- 不修改 `test0316` UE 母工程；集成测试使用隔离工程、测试插件或固定快照夹具。

## 4. 已确认的设计决策

| 主题 | 决策 |
|---|---|
| 编号与归属 | 4.5 只归属核心路由；工业默认行为库独立归属 4.6，不作为 4.5 子编号 |
| 表现协调接口 | 新增 `I3D_Presentation`，作为 `I3D_Representable` 下的逻辑协调兄弟接口 |
| 既有接口关系 | `I3D_Visual`、`I3D_Behavioral` 继续可独立挂载；它们是 `I3D_Presentation` 的执行投影，不强制迁移或多级继承 |
| 权威来源 | `I3D_Presentation` 权威；Visual/Behavioral 只执行其投影；旧字段仅兼容/调试 |
| 输入来源 | Nexus 归一化；HTTP 快照、增量快照及后续实时输入共用同一投影；通道健康度单独处理 |
| 执行发现 | UE 核心通过 `IModularFeatures` 查询表现执行器注册表 |
| 解析优先级 | 每个通道独立按项目 > 平台 > 安全回退解析 |
| 主状态 | 少量平台无关核心词汇，加工业命名空间扩展（如 `industrial.*`） |
| 修饰条件 | 多个修饰可组合；按通道确定优先级和冲突处理 |
| 一次性动作 | 至少一次投递；UE 以 `event_id` 去重，不新增后端确认队列 |
| 项目配置 | ObjectType 级 `presentation_profile`；v1 无实例路由覆盖 |
| 标识方式 | 稳定逻辑行为 ID + 受控表现槽位；不传 UE 资产路径 |
| 归一化方式 | Nexus 内置、版本化的工业归一化 Profile；仅有限算子/阈值，不做通用规则引擎 |

## 5. 概念模型

表现决策由三部分组成：

```text
PresentationIntent =
  primary_state  +  modifiers[]  +  actions[]
```

- `primary_state`：当前持续状态，例如 `idle`、`running`、`fault`、`offline`。
- `modifiers[]`：可同时成立的条件，例如低电量、告警等级、维护模式、通信降级；每项带优先级和适用通道。
- `actions[]`：一次性事件，例如告警闪烁、启动脉冲、复位提示；每项必须有稳定的 `event_id`。

路由层把意图解析成每个表现通道的决定（逻辑行为 ID、槽位、来源和诊断），执行器只消费已经归一化的结果。

## 6. 接口与数据契约（v1 草案，实施前冻结）

下列示例用于说明边界，不代表已上线接口；字段名称、必填性、长度限制和错误码必须在实施阶段的契约冻结门中确认。

```json
{
  "I3D_Presentation": {
    "schema_version": "1.0",
    "presentation_revision": 42,
    "decision_id": "pres-<instance>-42",
    "primary_state": { "id": "industrial.running" },
    "modifiers": [
      {
        "id": "industrial.low_battery",
        "level": "warning",
        "active": true,
        "priority": 50,
        "channels": ["visual", "fx"]
      }
    ],
    "actions": [
      {
        "id": "industrial.warning_flash",
        "event_id": "evt-00042",
        "sequence": 1,
        "params": {}
      }
    ],
    "resolution": {
      "channels": {
        "animation": {
          "source": "project",
          "behavior_id": "industrial.machine.running",
          "slot": "motion",
          "status": "resolved"
        },
        "visual": {
          "source": "platform",
          "behavior_id": "industrial.visual.warning",
          "slot": "status_indicator",
          "status": "resolved"
        },
        "fx": {
          "source": "safe_fallback",
          "behavior_id": "safe.none",
          "slot": "alarm",
          "status": "fallback"
        }
      }
    },
    "diagnostics": []
  }
}
```

契约约束：

1. `presentation_revision` 用于快照、增量和重连后的幂等判断；不替代实例状态版本。
2. `resolution` 必须按通道独立产生；缺失某个通道不得阻断其他通道。
3. `source` 只能是 `project`、`platform` 或 `safe_fallback`；解析失败必须留下可诊断原因。
4. `actions` 至少一次送达，`event_id` 在 UE 执行器侧去重；去重窗口、过期策略和序列语义在实施前冻结。
5. `primary_state.id` 和修饰/动作 ID 使用受控命名空间；工业首期使用 `industrial.*`，核心词汇保持平台无关。

### 6.1 与既有接口的关系

- `I3D_Visual` 继续输出 `material_variant`、`is_visible` 等兼容字段，并可附带 `presentation_revision` 与视觉投影诊断。
- `I3D_Behavioral` 继续输出 `animation_state`、`fx_trigger`、`ui_label_content` 等兼容字段，并可附带行为投影诊断。
- 新实现只允许由 `I3D_Presentation` 触发一次执行；旧字段仅在未提供 `I3D_Presentation` 的旧快照或显式调试模式下走兼容路径。
- 当新接口与旧字段同时存在时，以新接口为准，旧字段不得再次触发同一动画、特效或材质变更。

## 7. Nexus 归一化与路由

Nexus 建立版本化的工业归一化 Profile，将 HTTP 快照、增量快照及未来实时输入映射到同一 `PresentationIntent`。v1 仅允许有限、可审计的算子：枚举映射、阈值判断、缺失值处理、固定优先级和通道白名单。禁止任意表达式、脚本、递归规则和时间轴。

归一化结果应包含 Profile 版本、输入摘要、决策 ID 和诊断信息，便于重放与验收。通道路由只读取归一化结果和 ObjectType 的 `presentation_profile`，不重新解释原始业务字段。

## 8. ObjectType 配置与执行器发现

ObjectType 通过 `presentation_profile` 声明项目显式实现所需的逻辑行为 ID 与受控槽位，例如：

```json
{
  "presentation_profile": {
    "version": "1.0",
    "channels": {
      "animation": { "slot": "motion", "behavior_id": "project.crane.running" },
      "visual": { "slot": "status_indicator", "behavior_id": "project.crane.warning" }
    }
  }
}
```

UE 核心提供 `IOntoTwinPresentationExecutor`（名称为实施期可调整）模块化特征契约。执行器声明支持的逻辑行为 ID、槽位和通道，并由核心按优先级选择：项目显式执行器优先，平台通用行为库其次，最后使用静态安全回退。多个执行器声明同一 ID 时必须在注册阶段报错或按明确优先级拒绝歧义，不得随机选择。

## 9. 兼容、增量与故障策略

- 不带 `I3D_Presentation` 的旧快照继续按现有 Visual/Behavioral 逻辑处理。
- 带新接口的快照和增量以完整 `I3D_Presentation` 对象为边界；不得因单个通道缺失而清空其他通道。
- 增量合并沿用现有接口合并语义，同时对 `presentation_revision`、`event_id` 做幂等检查。
- 执行器缺失、行为 ID 未知、槽位不受控或输入不完整时，通道进入静态安全回退，并输出诊断；不得阻塞实例同步。
- 通道健康度、UE 连接和轮询存活状态继续由独立健康链路管理，不伪装成业务表现状态。

## 10. 实施范围（不等于已完成）

1. 后端新增独立的语义归一化/表现路由模块，扩展接口注册和快照投影；不扩大 `backend/app.py` 为新的业务大文件。
2. 更新快照与增量传输契约，使 `I3D_Presentation` 可选、可诊断、可幂等。
3. UE 核心增加解析、投影、模块化执行器注册和旧字段兼容门控。
4. 工业默认行为库作为独立可选包，见 `PRD-OT-4.6-001`；它不是 4.5 核心路由的必需交付物。
5. 前端只提供 ObjectType 级配置和只读诊断所需的最小入口；任何现有路由或页面变更需单独确认。

## 11. 成功标准

- 同一工业输入在 HTTP 全量、增量和重连重放后产生一致的 `decision_id`/路由结果。
- 三个通道可独立解析并显示实际来源（项目、平台或安全回退）。
- Visual 与 Behavioral 可继续独立挂载，且新旧字段不会双重执行。
- 行为库缺失或单个行为不可用时，实例仍可同步并进入可诊断的安全回退。
- 一次性动作重复投递时，UE 按 `event_id` 至少一次执行且不重复触发。
- 旧 4.3/4.4 快照、容器和调试 override 行为不回归。

## 12. 实施前必须冻结的事项

字段必填性、核心状态词汇全集、修饰冲突优先级、动作过期/去重窗口、增量删除语义、诊断错误码、`presentation_profile` 的持久化位置与迁移策略、执行器接口精确 C++ 签名、受控槽位清单和性能预算，均必须在实施计划的契约冻结门完成后才能编码。

本 PRD 只确认范围、边界和架构决策；截至文档创建日不代表已完成代码、UE 编译或验收。
