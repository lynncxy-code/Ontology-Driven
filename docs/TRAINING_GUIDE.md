# 训练剧本：仓库箱体抓取分拣

> **交付物**：本文档 + USD 场景文件（`exports/warehouse_demo_01.usda`）+ 资产目录（`assets/usd_cache/`）
> **范围**：M4 阶段任务为打通"场景生成 → USD → 训练"链路，sim-to-real 不在本阶段范围内。

---

## 1. 任务定义

| 项 | 内容 |
|---|---|
| **场景** | 单个房间（6×6×3 m），地板 + 货架 + 若干箱子 |
| **机器人** | 默认 Unitree H1（待定，训练侧可替换；本项目不提供机器人 USD） |
| **目标动作** | 拾取箱子 → 按规则放置 |
| **分拣规则** | 大箱子放货架底层（并排）、中箱子放货架上方两层（不限具体层位）、小箱子扔进筐 |
| **训练算法** | PPO（Isaac Lab 默认）|

### 任务分阶段（产品侧拆解，节奏请训练侧自行判断）

| 阶段 | 任务 |
|---|---|
| **Stage-1** | 抓起任意一个箱子放到指定区域 |
| **Stage-2** | 按类型分到不同区域 |
| **Stage-3** | 完整规则（大箱并排放货架底层、中箱放货架上方两层、小箱入筐）|

---

## 2. 环境准备

### 2.1 安装 Isaac Lab

本项目按 **Isaac Lab** 框架交付，官方安装：<https://isaac-sim.github.io/IsaacLab/main/source/setup/installation/index.html>

如需切换其他框架（OmniIsaacGym / 裸 Isaac Sim 等），本项目只交付 USD，不影响。

### 2.2 拷贝本项目资产

主场景 USD 内部用 **相对路径** `../assets/usd_cache/xxx.usda` 引用资产，所以 `exports/` 和 `assets/` **必须保持同级**目录结构：

```
ontotwin_export/                       ← 任意根目录
├── exports/
│   └── warehouse_demo_01.usda          ← 主场景
└── assets/
    └── usd_cache/
        ├── shelf.usda
        ├── box_large.usda
        ├── box_medium.usda
        ├── box_small.usda
        ├── plasticbasket.usda
        └── Textures/                   ← 贴图（货架/箱子需要）
```

> ⚠️ **不能**只拷主场景文件，也不能把场景文件拷到 `assets/scenes/`——相对引用会断。
> 整个 `exports/` 和 `assets/` 一起打包传给训练同事即可。

---

## 3. USD 场景说明

### 3.1 场景结构

打开 `warehouse_demo_01.usda`（usdview 或 Isaac Sim Stage 面板）会看到：

```
/World
├── /Environment
│   ├── /Ground       (灰色地板，带 CollisionAPI)
│   ├── /WallNorth    (浅灰色薄墙，仅视觉，无 collision)
│   ├── /WallSouth
│   ├── /WallEast
│   └── /WallWest
└── /Misc
    ├── /shelf_xxx              (静态货架，CollisionAPI)
    ├── /plasticbasket_xxx      (静态筐，CollisionAPI；小箱目标容器)
    ├── /box_large_xxx          (graspable，RigidBody + CollisionAPI)
    ├── /box_medium_xxx         (graspable)
    └── /box_small_xxx          (graspable)
```

> 当前所有实例都在 `/Misc` 下（M0 阶段实例的 `object_type_rid` 没分类）。
> 训练时按 prim 名称前缀（`shelf_*` / `plasticbasket_*` / `box_*_*`）筛选即可。

### 3.2 物理属性约定

| `collision_type` | USD Schema | 用途 |
|---|---|---|
| `static` | `CollisionAPI` 仅 | 货架、墙、地板（不动）|
| `dynamic` | `CollisionAPI` + `RigidBodyAPI` + `MassAPI` | 受重力的物体 |
| `graspable` | 同 dynamic，但 collision approx = `none`（精确凸壳）| 需要被夹爪精确抓取的箱子 |

每个 prim 的 `customData["ontology"]` 含追溯信息（场景 ID、资产 file_number 等），仅用于回写到 Nexus 时识别身份。

### 3.3 单位与坐标系

- **单位**：USD 内部 cm（`metersPerUnit = 0.01`）
- **上轴**：Z-up
- **手系**：右手系（与 Isaac Sim 默认一致）

Isaac Lab 加载时不需要做坐标变换。

### 3.4 语义锚点（产品侧定义）

> 训练侧据此编写 reward / 终止条件 / observation。
> 机器人选型与可达性约束本节不涉及，由训练侧自行评估。

**默认机器人**：Unitree H1（如训练侧需要更换，本项目场景设计兼容大多数双臂人形）。

#### 3.4.1 空间分区

房间 6×6 m（X[-3, 3] × Y[-3, 3] × Z[0, 3]，Z 向上），地面 z = 0，划分 4 个语义区：

| 区域 | XY 范围（m）| 用途 |
|---|---|---|
| 初始散落区 | X ∈ [0, 3], Y ∈ [-3, 0] | 每 episode reset 时所有箱子随机掉落于此 |
| 货架（大箱+中箱目标）| `shelf_*` prim 的 AABB | 底层 2 大箱并排，上方两层放中箱 |
| 筐（小箱目标）| `plasticbasket_*` prim 的 AABB | 3 个小箱投入筐内 |

#### 3.4.2 货架层位定义

货架共 3 层，每层顶面 z 高度（米）：

| 层位 | z (m) | 目标 |
|---|---|---|
| 下层 | 0.9 | 2 个 box_large 并排 |
| 中层 | 1.8 | box_medium（不限层位，3 个中箱可任意分布在中/上层）|
| 上层 | 2.7 | box_medium（同上）|

> "上 / 中 / 下层"为产品侧术语，训练侧请按此 z 值识别。
> 中箱放中层还是上层不强制，单层物理上能放 ~6 个中箱，3 个中箱怎么分配训练侧自定。

#### 3.4.3 初始化规则

每次 episode reset：

| 物体 | 数量 | 初始 XY | 初始 z (m) | 初始 yaw |
|---|---|---|---|---|
| box_large | 2 | 散落区随机 | 0.3（自由落体）| [-90°, 90°] |
| box_medium | 3 | 散落区随机 | 0.3 | [-90°, 90°] |
| box_small | 3 | 散落区随机 | 0.3 | [-90°, 90°] |

约束：物体间最小水平距离 ≥ 0.4 m，避免初始穿插。

#### 3.4.4 目标判定语义

| 物体 | 完成条件（语义层）|
|---|---|
| 2 × box_large | 都在货架底层（z 接近 0.9），XY 在货架 AABB 内，并排放置（不重叠）|
| 3 × box_medium | 每个 box_medium 的 z 接近中层或上层（1.8 或 2.7），且 XY 在货架 AABB 内 |
| 3 × box_small | 每个 box_small 的 XY 在筐口 AABB 内，且 z 低于筐顶 |

具体判定阈值（"接近"、"上方"等的 ε）由训练侧根据 reward shaping 决定。

---

## 4. 域随机化（Domain Randomization）

本项目**不预生成多个 USD 变体**，只交付 1 个 base USD（`warehouse_demo_01.usda`）。
变体生成由训练侧在 episode reset 时按需随机化。

### 4.1 产品侧期望的随机化维度

| 维度 | 范围 | 备注 |
|---|---|---|
| 箱子初始位置 | 散落区内随机（见 §3.4.3）| 保证不穿墙、物体间距 ≥ 0.4 m |
| 箱子初始朝向 | yaw ∈ [-90°, 90°] | 限制范围避免长条小箱竖起来 |
| 箱子数量 | 固定 2 大 + 3 中 + 3 小（见 §3.4.3）| 验证阶段可放宽 |
| 箱子质量 | base ±20% | 提高鲁棒性 |
| 摩擦系数 | [0.4, 0.7] | 模拟不同表面 |
| 光照 | 强度 / 角度随机 | 视觉训练才需要 |

具体实现交训练侧自定。

---

## 5. 任务约束与产品侧期望

| 项 | 期望 |
|---|---|
| 机器人 | 默认 Unitree H1（待定，训练侧可替换；本项目不交付机器人 USD）|
| 夹取对象 | `box_*` 命名的 prim（graspable，RigidBody + CollisionAPI）|
| 终点判定 | 由训练侧自定，语义参考 §3.4.4 |
| 失败判定 | 由训练侧自定（参考：箱子掉出 bounds、超时等）|

奖励函数、observation/action 空间、并行规模均由训练侧自定。

---

## 6. 场景修改与回流

如果训练发现场景需要调整（比如货架位置不合理）：

1. 在 Nexus Lite 前端修改坐标：<http://localhost:5000/scenes>
2. 点"保存并预览"，会重新生成 `exports/warehouse_demo_01.usda`
3. 把新文件覆盖到训练侧的 `exports/warehouse_demo_01.usda`（保持目录结构）
4. 重启训练即可

> 不要直接在 Isaac Sim 里手动改 USD，改了不会回流到 Nexus。

---

## 7. 资产/场景问题反馈

- USD 引用断链、prim 缺失、坐标错误等 → 反馈给本项目维护者（Nexus Lite）
- 需要新增资产、调整 bounds、修改物理参数 → 同上，由产品侧在 Nexus 前端修改后重新导出

