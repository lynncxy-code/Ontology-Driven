# OntoTwin 2.8 / 2.8.1 AGV 小车巡逻组件需求与技术说明 (PRD)

> **文档版本说明：**
> - **2.8** — 初始版本，描述基础的本地算法驱动巡逻模式
> - **2.8.1** — 深化版本（本次迭代），增加仿真日志驱动模式与路网 CSV 规范

## 1. 产品背景

在"数字孪生飞机"车间场景中，除了固定的流水线和移动的工人外，还需要呈现自动化导引车（AGV）的动态物流作业过程。当前版本的 AGV 尚未接入后端中间层的实时寻路调度系统（如 `APCBWorkerManager` 的轮询架构），因此引入了 `UAGVPatrolComponent` 作为一个**基于纯前端算法驱动的模拟巡逻组件**，用以在场景中展示 AGV 沿固定轨道往返运动的视觉效果。

---

## 2. 核心功能及应用场景

`AGVPatrolComponent` 是一个轻量级的 Actor 组件（`UActorComponent`），可挂载到任何表示 AGV 的三维模型（Actor）上。

**主要职责：**
1. **自动往返巡逻：** 记录小车在场景中放置的初始坐标，并在此基础上沿指定轴向进行往返运动。
2. **非线性平滑过渡：** 弃用生硬的匀速折返（Ping-Pong），采用**三角函数缓动（Cosine Easing）**算法，模拟车辆启动时的加速和首尾到达时的减速（Ease-in-out）效果。
3. **完全参数化控制：** 巡逻距离、运动轴向、往返周期均向编辑器（Details 面板）及蓝图暴露，支持在同一个场景中部署多个具有不同运动特性的 AGV。

---

## 3. 详细逻辑与技术实现（2.8 基础版）

### 3.1 核心驱动算法 (Tick 位移计算)

- **时间累加器：** 在 `TickComponent` 中累加 `DeltaTime` 为 `RunningTime`。
- **平滑缓动曲线计算：**
  - 公式：`OffsetScale = (1.0f - cos((RunningTime / CycleTime) * PI * 2.0f)) * 0.5f`
  - 将时间映射到 $0 \sim 2\pi$ 的余弦波周期，利用 $1 - \cos(\theta)$ 特性归一化到 `[0, 1]`
  - 保证 AGV 从起点加速启动，临近掉头点平滑衰减至 0 并反向，消除"瞬停掉头"
- **位移更新：**
  `NewLocation = InitialLocation + (NormalizedPatrolAxis * PatrolDistance * OffsetScale)`

### 3.2 暴露的配置参数

| 参数 | 默认值 | 说明 |
| :--- | :--- | :--- |
| `PatrolDistance` | 3000.0f (30m) | AGV 距初始点的单边最远距离 |
| `CycleTime` | 10.0f 秒 | 完整来回一次所需时间；为 0 时自动跳过防除零 |
| `PatrolAxis` | `(0, 1, 0)` (+Y 轴) | 可改为任意轴向实现多方向运动 |

---

## 4. 与 PCBWorkerSyncComponent 的差异对比

| 维度 | `PCBWorkerSyncComponent`（工人） | `AGVPatrolComponent`（AGV 车） |
| :--- | :--- | :--- |
| **驱动模式** | 后端数据驱动（被动接受快照和指令） | 2.8: 本地算法模拟 / **2.8.1: CSV日志驱动** |
| **移动轨迹** | 点到点直线插值（A → B 随时改变） | 2.8: 固定轴往返 / **2.8.1: 遵循日志全场调度** |
| **状态机** | 有复杂业务状态（工作/站立/行走） | 无状态机，纯粹的持续空间位移 |
| **组件依赖** | 强依赖 `ITwinEntitySync` 与总控中台 | 本期轻量级挂载 Actor，下期并入孪生网络 |
| **朝向控制** | 有 `RotationInterpSpeed` 自动看向前方 | 2.8版无朝向控制 / **2.8.1改版后强同步 CSV 的四元数朝向** |

---

## 5. 2.8.1 深化需求：仿真日志驱动模式

### 5.1 背景与目标

在 2.8 纯本地算法驱动的基础上，接入真实仿真系统产生的运行日志（CSV 格式），使 AGV 在 UE5 场景中能回放真实的调度轨迹，为产线评审与仿真验证提供依据。

### 5.2 两种接入模式对比

| 模式 | 说明 | 本期实现？ |
| :--- | :--- | :--- |
| **离线 CSV 导入** | 一次性完整导入仿真日志，UE 端按时间戳顺序插值回放 | ✅ 本期实现 |
| **实时推流接口** | 仿真软件实时推送给中间层，UE 按 `/api/ue/events` 消费 | 🔜 下期规划 |

### 5.3 C++ 组件改造方案

#### 新增：`UAGVSimLogLoader`（数据加载器）

独立 `UActorComponent`，职责与 `AGVPatrolComponent` 完全解耦：

| 职责 | 实现方式 |
| :--- | :--- |
| 读取 CSV 路径 | `UPROPERTY(EditAnywhere)` 暴露 `FFilePath CsvPath` |
| 按 `serial` 分组 | `BeginPlay` 时解析，建立 `TMap<FString, TArray<FAgvFrame>>` |
| 注入帧序列 | 通过 `serial` 检索 Actor 上的 `AGVPatrolComponent` 并注入 |

#### 新增帧结构体 `FAgvFrame`

```cpp
USTRUCT(BlueprintType)
struct FAgvFrame {
    GENERATED_BODY()
    UPROPERTY() float   Time;         // 相对时间（秒）
    UPROPERTY() FVector Position;     // positionX/Y/Z
    UPROPERTY() FQuat   Orientation;  // orientationX/Y/Z/W
    UPROPERTY() float   Yaw;          // 已解算偏航角（弧度）
    UPROPERTY() bool    HasCargo;     // cargo_status != "[0]"
};
```

#### `AGVPatrolComponent` 回放逻辑

- `TickComponent` 根据 `World->GetTimeSeconds()` 二分查找帧索引
- 相邻帧做**线性插值（位置）+ Slerp（四元数朝向）**
- 直接调用 `Owner->SetActorLocationAndRotation(...)`
- **帧序列注入后自动禁用余弦缓动算法**，切换为 CSV 回放模式

#### 坐标系策略（本期）

本期不做坐标系映射，CSV 坐标直接使用 UE cm 单位。后续可在组件中暴露 `CoordScale`（缩放）和 `CoordOffset`（偏置）供项目自定义对齐。

### 5.4 AGV Actor 对应策略（本期：静态预埋）

每台 AGV 在 UE 编辑器预先放好 Actor，Details 面板填写 `AgvSerial`（与 CSV `serial` 字段对应）。`UAGVSimLogLoader` 在 `BeginPlay` 时扫描全场景匹配并注入。

| 方案 | 优点 | 缺点 | 阶段 |
| :--- | :--- | :--- | :--- |
| **静态预埋** | 快速配置、可视化调试 | 须提前知道 AGV 数量 | 本期 |
| **动态 Spawn** | CSV 数据决定小车数量 | 需额外 SpawnManager | 下期 |

### 5.5 组件可迁移性设计

- **纯 C++**，无蓝图代码、无项目特定资产引用
- 迁移至新项目只需 copy 并重新编译：
  - `AGVPatrolComponent.h / .cpp`
  - `AGVSimLogLoader.h / .cpp`（新增）
- 在新项目 Details 面板重新填 `CsvPath` 与 `AgvSerial` 即可运行，无需修改任何代码
- **后续打包为 `.uplugin`**：代码稳定后增加描述文件即可一键跨项目安装

---

## 6. 路网设计（test0316 工厂）

### 6.1 工厂坐标边界

| 坐标轴 | 范围 | 说明 |
| :--- | :--- | :--- |
| X | -2990 ~ +2990 | 纵深长轴（5980 cm ≈ 60 m） |
| Y | -2000 ~ +2000 | 横向短轴（4000 cm ≈ 40 m） |
| Z | 0 | 地面层 |

### 6.2 禁入区域（对照平面图）

| 区域 | X 范围 | Y 范围 |
| :--- | :--- | :--- |
| 产线 A | -2500 ~ +2500 | -800 ~ -200 |
| 产线 B | -2500 ~ +2500 | +200 ~ +800 |
| 仓库（顶端两侧） | +1500 ~ +2990 | ±900 ~ ±2000 |
| 设备区（侧部） | -1500 ~ +1500 | ±800 ~ ±2000 |
| 办公室（底左） | -2990 ~ -1500 | -2000 ~ 0 |
| 休息区（底右） | -2990 ~ -1500 | 0 ~ +2000 |

### 6.3 AGV 走廊（可通行区域）

```
Y 轴
+2000 |  仓库(左)                        仓库(右)
+1200 |──────────── C5 外侧辅道 R ────────────────
 +800 |  [设备区]  [═══ 产线 B ═══]  [设备区]
    0 |────────────── C1 中央主道 ─────────────────
 -800 |  [设备区]  [═══ 产线 A ═══]  [设备区]
-1200 |──────────── C4 外侧辅道 L ────────────────
-2000 |  办公室                          休息区
      +------------------------------------------------ X 轴
      -2990  -1500    0   +1500   +2700  +2990
                                    ↑
                               C2 纵向横道
                              (Y: -700~+700)
```

| 走廊 ID | 描述 | X 范围 | Y 固定值 |
| :--- | :--- | :--- | :--- |
| **C1** | 中央主道（两产线之间） | -2800 ~ +2800 | Y = 0 |
| **C2** | 仓库端纵向横道 | Y: -700 ~ +700 | X = +2700 |
| **C4** | 外侧辅道 L（设备区外沿南） | -2000 ~ +2500 | Y = -1200 |
| **C5** | 外侧辅道 R（设备区外沿北） | -2000 ~ +2500 | Y = +1200 |

### 6.4 仿真 CSV 格式规范

字段与原始仿真日志（`仿真运行日志.csv`）完全兼容：

| 字段名 | 类型 | 说明 |
| :--- | :--- | :--- |
| `id` | int | 全局记录流水号（按时间排序） |
| `serial` | string | AGV 唯一 ID（如 `agvfac000000001n01`） |
| `power` | int | 电量 %，模拟固定 `99` |
| `charging` | int | 充电标志 `0`/`1` |
| `cargo_status` | string | `[0]` 空载，`[1]` 有货 |
| `positionX/Y/Z` | float | 坐标（UE cm，直接使用） |
| `orientationX/Y/Z/W` | float | 方向四元数（X/Y 恒为 0，仅用 Z/W） |
| `yaw_x`, `yaw_y` | float | cos(yaw) / sin(yaw) |
| `yaw` | float | 偏航角（弧度）：`0`=+X，`π/2`=+Y，`±π`=-X |
| `dispatch_recv_timestamp` | int | Unix 时间戳（秒） |
| `dispatch_recv_time` | string | `MM/DD/YYYY HH:MM:SS` |
| `time` | int | 相对秒数，从 0 起 |

### 6.5 已规划 AGV 路线（test0316 工厂）

| AGV Serial | 走廊 | 运动方向 | 速度 | 载货周期 |
| :--- | :--- | :--- | :--- | :--- |
| `agvfac000000001n01` | C1 中央主道 | 左 → 右往返 | 300 cm/s | 95 s |
| `agvfac000000001n02` | C1 中央主道 | 右 → 左往返（与 n01 错相防碰） | 280 cm/s | 110 s |
| `agvfac000000001n03` | C2 仓库端横道 | 南 ↔ 北往返 | 220 cm/s | 80 s |
| `agvfac000000001n04` | C4 外侧辅道 L | 西 → 东往返 | 320 cm/s | 130 s |
| `agvfac000000001n05` | C5 外侧辅道 R | 东 → 西往返 | 310 cm/s | 115 s |

**CSV 生成脚本（本地运行）：** [`gen_agv_csv.py`](file:///d:/tmp/mock_data/gen_agv_csv.py)

```bash
cd d:\tmp\mock_data
python gen_agv_csv.py
# 输出: agv_route_test0316.csv
# 约 3500 条记录，5 台 AGV × 700 秒，格式与原始仿真日志完全兼容
```

---

## 7. 未来演进路线

1. **坐标系对齐工具：** 暴露 `CoordScale`（缩放）与 `CoordOffset`（偏置），实现"一套组件适配多个仿真坐标系"的跨项目迁移目标。
2. **实时推流模式：** AGV 并入中间层 `/api/ue/events` 体系，`UAGVSimLogLoader` 改为事件侦听模式，彻底与数字孪生中台并轨。
3. **打包为 UE 插件：** C++ 验证稳定后，添加 `.uplugin` 描述文件，跨项目一键安装。
4. **动态 Spawn：** 引入 `UAGVSpawnManager`，CSV 中每个新 `serial` 自动 Spawn AGV Actor，无需手动预埋。
5. **碰撞避障：** 基于 Raycast 的前向障碍检测，与 `PCBWorkerSyncComponent` 路径冲突进行协同感应与停车让行。
