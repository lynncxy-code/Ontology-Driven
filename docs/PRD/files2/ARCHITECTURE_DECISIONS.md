# ARCHITECTURE_DECISIONS.md — 架构决策记录（ADR）

> 本文档记录用户与 Claude 讨论后已定下的所有架构决策。
> **Claude Code 不要再次对这些问题提出方案或询问用户。**
> 如果遇到某个决策不适用的边缘情况，先告诉用户，等确认再动。

---

## ADR-001：导出方向为单向

**决策**：Nexus 数据 → USD 文件，单向导出。不做反向导入（USD → Nexus）。

**否决方案**：Schema 双向映射（Isaac Sim 改的参数回流到本体）。

**理由**：一人开发，双向映射工作量大，收益低。只做单向 + customData 留回流口子。

---

## ADR-002：导出的 USD 不含动态行为

**决策**：USD 只包含静态场景（几何 + 材质 + 物理属性 + 初始位姿）。

**不包含**：
- 工人动画（Idle / Walk / Working 状态）
- AGV 巡逻轨迹
- 任何 TimeSamples 时间采样数据

**理由**：动态行为和训练场景无关，具身训练的机器人自己就是动态源。

---

## ADR-003：坐标系标准

**决策**：

| 项 | 值 |
|---|---|
| 单位 | 米（m） |
| 上轴 | Z-up |
| 坐标系 | 右手系 |

**Nexus 数据库存的坐标 = 上述规范**，UE 端在加载/回写时做一次转换。

**UE 端转换**：
- Nexus → UE：米 × 100 = cm，Y 轴取反（右手→左手）
- UE → Nexus：cm ÷ 100 = 米，Y 轴取反

---

## ADR-004：训练框架为 Isaac Sim + Isaac Lab

**决策**：训练侧使用 NVIDIA Isaac Sim + Isaac Lab。

**影响**：
- 导出的 USD 按 Isaac Sim 的 Schema 要求配置（`UsdPhysics.CollisionAPI` / `RigidBodyAPI` / `MassAPI`）
- graspable 物体必须 mesh 精确碰撞（不能用 convex hull）

---

## ADR-005：训练任务为抓取分拣

**决策**：第一版训练任务是"按尺寸分拣箱子"。

**场景要素**：
- 1 个 Franka 机械臂
- 3 个存放区域（外侧货架 / 上层货架 / 回收篮）
- 6-8 个箱子（大/中/小）

**规则**：
- 大箱子（边长 ≥ 25cm）→ 外侧货架
- 中箱子（15-25cm）→ 上层货架
- 小箱子（< 15cm）→ 回收篮

详见 `TRAINING_BRIEF.md`（M2 阶段创建）。

---

## ADR-006：物理类型三分法

**决策**：每个 Instance 通过 `I3D_PhysicsHint.collision_type` 标记三种类型之一：

| 值 | 含义 | USD Schema |
|---|---|---|
| `static` | 不动，仅障碍物 | `CollisionAPI` 单独 |
| `dynamic` | 可被推动 | `CollisionAPI + RigidBodyAPI + MassAPI`，convex hull |
| `graspable` | 可抓取 | `CollisionAPI + RigidBodyAPI + MassAPI`，**mesh 精确碰撞** |

**否决方案**：`articulated`（关节物体）类型 — 第一版不需要。

---

## ADR-007：场景管理的数据模型

**决策**：新增 Scene 概念，挂在现有 Dataset 下。

**关系**：

```
Dataset (现有)
  └── Scene (新增) × N
       └── Instance (多对多，通过 belongs_to_scenes 字段)
```

**Instance 自带默认坐标**（放在本身的 `I3D_Spatial` 接口里），**不为每个 Scene 单独存一份坐标**。

**含义**：同一个 Instance 可以属于多个 Scene，但坐标是一份。如果 Scene A 和 B 想让同一个物体出现在不同位置，需要通过 Scene.placements 里的 `StaticPlacement` 覆盖（第一版暂不做 UI，只留数据结构）。

---

## ADR-008：Placement 不是接口，是 Scene 的字段

**决策**：`I3D_Procedural` 不作为本体接口存在。

**替代**：场景的程序化生成规则（如"沿 Y 轴排列 5 个货架"）作为 Scene 的 `placements` 字段存在。

**理由**：参数化生成是"场景对一组对象的组织方式"，不是"对象自身的能力"。

**第一版 UI 不提供 placements 编辑**，只保留数据结构。

---

## ADR-009：UE 集成选择 Z 路径 + 回写

**决策**：

- UE 不负责 USD 导出（后端统一导出）
- UE 用 USD Stage Actor 加载同一个 USD
- UE 里美术调整位置后，**调用回写 API 更新 Nexus**

**回写范围**：位置 + 旋转 + 缩放。

**不包括**：新增 / 删除 Instance、资产替换。

---

## ADR-010：FBX → USD 惰性转换

**决策**：资产库存 FBX，第一次需要用 USD 时转换并缓存。

**转换工具**：NVIDIA `asset_converter` 优先，Blender 无头模式备选。**M0 阶段可以手动转**。

**缓存失效**：基于 FBX 文件 hash 判断。

---

## ADR-011：customData 追溯标记

**决策**：每个导出的 USD Prim 必须携带 `customData.ontology`：

```python
{
    "instanceId": "...",
    "objectTypeRid": "...",
    "fileNumber": "...",
    "interfaces": [...],
    "sourceScene": "...",
    "datasetId": "...",
    "exportVersion": 1,
    "exportTimestamp": "..."
}
```

**形式**：嵌套 dict（不要用 `ontology:instanceId` 扁平 key）。

---

## ADR-012：后端存储策略

**决策**：本次新增用独立 SQLite 数据库，存在 `backend/lite/db/lite.db`。

**不合并到现有存储**：
- 现有后端是内存 + JSON 文件
- 新需求更适合关系型存储
- 隔离便于维护

**ORM**：SQLAlchemy 或直接用 `sqlite3`（视用户偏好）。

---

## ADR-013：不引入异步任务队列

**决策**：USD 导出同步执行，不用 Celery / Redis / RabbitMQ。

**理由**：一人用，场景小（10 物体级别），同步跑几秒就完。引入队列纯属负担。

---

## ADR-014：不做权限 / 版本 / 审计

**决策**：本项目不做以下"企业级"特性：

- 用户 / 角色 / 权限
- 操作审计日志
- 数据版本管理（USD 文件直接覆盖或手动备份）
- 导出历史的复杂查询

**理由**：一人用。

---

## ADR-015：前端继续用 CDN 模式

**决策**：新增前端页面继续用原生 HTML + CDN 引入 Vue3/Axios/ECharts。

**不做**：
- 不引入 npm / webpack / vite
- 不改成 SPA
- 不引入 TypeScript

**理由**：现有前端就是 MPA，保持一致。

---

## ADR-016：USD 分层策略

**决策**：第一版扁平单文件 USD（一个 `.usda` 搞定所有）。

**未来可升级**：分层（主场景 + SubLayer 结构 + SubLayer 物理）。但 M0/M1 不做。

---

## ADR-017：命名空间

### URL 前缀

- `/api/v3/lite/` — 新增 API（严格隔离，不和现有 `/api/v2` 混）

### 数据库表前缀

- `lite_scenes`
- `lite_scene_instances`
- `lite_assets`
- `lite_exports`

### 前端路径前缀

- `/scenes` — 场景管理入口

---

## ADR-018：Out of Scope 清单

以下明确**不在本项目范围**：

- ❌ UE 现有插件改造（TwinSceneBuilder / PCBWorkerSync / AGVPatrol）
- ❌ 2.6 轮询接口
- ❌ Floor Pulse
- ❌ 多场景管理（第一版一个场景）
- ❌ 命令行导出工具（前端按钮足够）
- ❌ 域随机化的完整实现（只在 USD 留字段）
- ❌ 跨数据集的场景引用
- ❌ 场景克隆 / diff / 回滚
- ❌ Isaac Sim / Isaac Lab 代码（训练侧负责）

---

## ADR-019：开发节奏

**模式**：边做边讨论。

**里程碑**：

| 阶段 | 目标 |
|---|---|
| M0（本周）| 最小闭环：硬编码数据生成 USD，能被 Isaac Sim 加载 |
| M1 | 后端 Scene CRUD + 前端最简编辑 + 导出按钮 |
| M2 | UE 集成（USD Stage 加载）+ 训练剧本 |
| M3 | UE 回写位置 + 联调 |
| M4 | 稳定性与交付 |

详见 `IMPLEMENTATION_PLAN.md`。

---

## 遗留待定事项

以下事项用户暂未最终确定，Claude Code 遇到时询问：

1. **FBX 转换工具选型**（NVIDIA asset_converter vs Blender）— 实际操作时再决定
2. **后端 ORM 选型**（SQLAlchemy vs 原生 sqlite3）— M1 开始时问
3. **UE 版本**（5.3 / 5.4 / 5.5）— M2 开始时问
4. **是否需要 Docker 化**— 第一版不做，M4 可讨论
