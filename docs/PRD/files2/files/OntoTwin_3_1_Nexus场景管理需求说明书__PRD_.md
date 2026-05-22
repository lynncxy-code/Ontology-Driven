# OntoTwin 3.1 Nexus 场景管理需求说明书（PRD）

| 字段 | 内容 |
|---|---|
| **文档版本** | v3.1-r1 |
| **日期** | 2026-04-17 |
| **状态** | 草稿（待审阅） |
| **模块代号** | SceneManagement |
| **归属** | 前端（Nexus Web）+ 后端（Python）|
| **依赖** | 2.1 本体接口 / 2.2 资产中台 / 2.3 数据集管理 / 3.0 USD 导出 |

---

## 一、产品背景

### 1.1 背景

2.x 系列里，本体实例（Instance）是"飘"在数据集下的——每个实例自带坐标但不归属任何"场景"。这在单一演示场景下是可行的，但一旦涉及到：

- 需要导出 USD 给训练侧使用（3.0）
- 一个数据集下有多个独立的三维场景（如"仓库演示"和"训练场景"）
- 需要做场景级别的版本管理和导出历史

就必须引入"场景（Scene）"这一层组织单元。

### 1.2 目标

在 Nexus 现有数据集 → 本体 → 实例的结构上，新增一层"场景"管理能力，作为 USD 导出的组织边界。

### 1.3 参考界面

当前 Nexus 左侧导航（已有模块）：
- 数据定义 → 语义图谱总览
- 模型工坊 → CAD 一键成模
- 接口治理 → 本体配置中心
- 运行守护 → 实例运维与监控 / 实时数据监控台

**本次新增一个模块**：数据定义 → **场景管理**（在"语义图谱总览"下方）

---

## 二、核心功能概述

### 2.1 功能清单

| 功能 ID | 功能名称 | 前端 | 后端 | 优先级 |
|---|---|---|---|---|
| S1 | 场景 CRUD | ✅ | ✅ | P0 |
| S2 | 场景-实例归属管理 | ✅ | ✅ | P0 |
| S3 | 场景概览信息卡片 | ✅ | ✅ | P0 |
| S4 | "导出 USD"入口按钮 | ✅ | ✅ | P0 |
| S5 | 导出历史查看 | ✅ | ✅ | P1 |
| S6 | 场景 DXF 结构文件上传与关联 | ✅ | ✅ | P1 |
| S7 | 场景下实例坐标校验 | ✅ | ✅ | P1 |
| S8 | Scene Placement（程序化摆放规则） | ⚠️ 数据结构预留，UI 不做 | ✅ | P2 |

---

## 三、数据模型

### 3.1 Scene 实体

```typescript
interface Scene {
    id: string                        // "warehouse_demo_01"，全局唯一
    dataset_id: string                // 所属数据集
    display_name: string              // "仓库演示场景"
    description: string | null        // 可选描述
    
    // 空间边界
    bounds: {
        x: [number, number]           // 米
        y: [number, number]
        z: [number, number]
    }
    up_axis: "Z"                      // 固定值
    unit: "meter"                     // 固定值
    
    // 结构数据源（DXF 图纸，可选）
    structure_dxf_path: string | null
    structure_dxf_uploaded_at: string | null
    
    // 摆放规则（第一版仅数据结构，无 UI）
    placements: Placement[]
    
    // 元数据
    created_at: string
    updated_at: string
    created_by: string
    
    // 统计信息（GET 时由后端计算返回）
    stats?: {
        instance_count: number
        static_count: number
        dynamic_count: number
        graspable_count: number
    }
    
    // 最近导出信息（GET 时由后端计算返回）
    latest_export?: {
        version: number
        exported_at: string
        file_size_bytes: number
    } | null
}
```

### 3.2 Instance 字段修订

Instance 在 3.0 中已新增：

```typescript
interface Instance {
    // ... 原有字段 ...
    belongs_to_scenes: string[]       // Scene ID 列表（多对多）
    interfaces: {
        // ... 原有接口 ...
        I3D_PhysicsHint?: {
            collision_type: "static" | "dynamic" | "graspable"
            mass?: number
            friction?: number
        }
    }
}
```

### 3.3 Placement 结构（数据预留）

```typescript
type Placement = StaticPlacement | ProceduralGroup

interface StaticPlacement {
    type: "static"
    instance_id: string
    translation: [number, number, number]
    rotation: [number, number, number]
    scale: [number, number, number]
}

interface ProceduralGroup {
    type: "procedural_group"
    pattern: "linear_repeat" | "grid" | "random_in_region"
    template_instance_id: string
    count: number
    start_translation: [number, number, number]
    step?: [number, number, number]
    rotation?: [number, number, number]
    randomization?: {
        enabled: boolean
        translation_jitter?: [number, number, number]
        rotation_jitter?: number
    }
}
```

---

## 四、前端需求

### 4.1 导航与入口

在左侧导航的 **"数据定义"** 分组下，**"语义图谱总览"** 下方新增：

```
数据定义
 ├── 语义图谱总览
 └── 场景管理   ← 新增
```

### 4.2 场景列表页

**路由**：`/nexus/scenes`

**页面结构**：

```
顶部：
  [当前数据集：标准实践（内置 Demo）▼]  [+ 新建场景]

场景列表（卡片式）：
  ┌───────────────────────────────────────┐
  │ 仓库演示场景                           │
  │ warehouse_demo_01                      │
  │                                        │
  │ 实例数：35   静态：23  动态：8  可抓取：4│
  │ 边界：60m × 40m × 5m                   │
  │ 最近导出：v3  (2026-04-15 14:30)       │
  │                                        │
  │ [查看详情] [导出 USD] [在 UE 打开]     │
  └───────────────────────────────────────┘
  ┌───────────────────────────────────────┐
  │ 训练场景 A                             │
  │ ...                                    │
  └───────────────────────────────────────┘
```

**交互细节**：
- 支持搜索（按名称、ID）
- 支持排序（最近更新、名称、实例数）
- 空状态：展示"还没有场景，点击上方按钮新建"

### 4.3 新建场景抽屉

点击"+ 新建场景"弹出抽屉：

```
字段：
  * 场景 ID（英文，如 warehouse_demo_01）
  * 显示名称（中文，如 仓库演示场景）
    描述（多行文本，可选）
  * 边界：X Y Z 各两个数字输入框（米）

[取消]  [创建]
```

**校验规则**：
- ID 只能包含英文字母、数字、下划线、短横线
- ID 在同一数据集下唯一
- 边界值合法（max > min）

创建成功后跳转到场景详情页。

### 4.4 场景详情页

**路由**：`/nexus/scenes/:scene_id`

**页面标签（Tab）结构**：

```
场景：仓库演示场景 (warehouse_demo_01)                  [导出 USD]

┌ 基本信息 ┬ 实例管理 ┬ 结构文件 ┬ 导出历史 ┐

─────────────────────────────────────────────
```

#### 4.4.1 Tab: 基本信息

- 显示所有 Scene 字段（可编辑）
- 场景边界的可视化：用一个简单的 2D 俯视图画出 bounds 矩形（第一版可不做）
- 场景统计信息

#### 4.4.2 Tab: 实例管理

**核心功能**：管理哪些 Instance 归属于当前 Scene。

```
顶部：
  [+ 添加已有实例到本场景]  [批量配置坐标]

实例列表（表格）：
  ┌──────┬──────────┬──────────────┬──────────┬─────────────┬──────┐
  │ 选择 │ 实例 ID  │ 类型          │ 坐标      │ 物理类型    │ 操作 │
  ├──────┼──────────┼──────────────┼──────────┼─────────────┼──────┤
  │ □    │ shelf_001│ 仓储货架      │(1.5,2,0) │ static      │ 移出 │
  │ □    │ shelf_002│ 仓储货架      │(1.5,4,0) │ static      │ 移出 │
  │ □    │ box_001  │ 木箱          │(3.0,2,1) │ graspable   │ 移出 │
  └──────┴──────────┴──────────────┴──────────┴─────────────┴──────┘
```

**"添加已有实例"弹窗**：
- 列出当前数据集下**尚未属于本场景**的所有 Instance
- 按 ObjectType 过滤
- 多选后批量添加（写入 Instance.belongs_to_scenes）

**"批量配置坐标"**：
- 复用 2.3.1 的批量配置表格
- 区别：只列出本场景下的 Instance

**"移出"**：
- 从 Instance.belongs_to_scenes 中删除当前 scene_id
- 不删除 Instance 本身（Instance 可能属于其他场景）

#### 4.4.3 Tab: 结构文件

```
当前结构文件：
  [无]  →  [上传 DXF]

或：

  warehouse_layout.dxf  (上传于 2026-04-10)
  [预览][替换][删除]
```

**DXF 上传**：
- 支持 .dxf 文件
- 上传后后端立即调用 3.0 F3 做一次校验解析（检查图层命名规范）
- 解析失败时返回详细错误（哪个图层缺失、哪个实体格式错误）

#### 4.4.4 Tab: 导出历史

```
┌ 版本 ┬ 导出时间           ┬ 大小    ┬ 文件名              ┬ 操作         ┐
│ v3   │ 2026-04-15 14:30   │ 245 KB  │ warehouse_v3.usda   │ 下载｜查看报告│
│ v2   │ 2026-04-14 10:20   │ 238 KB  │ warehouse_v2.usda   │ 下载｜查看报告│
│ v1   │ 2026-04-13 16:05   │ 210 KB  │ warehouse_v1.usda   │ 下载｜查看报告│
└─────┴────────────────────┴─────────┴─────────────────────┴──────────────┘
```

**"查看报告"**：弹出 Modal 展示 JSON 格式的导出报告（警告、错误、统计）。

### 4.5 "导出 USD" 交互流程

从场景列表或场景详情页的"导出 USD"按钮触发：

```
用户点击 [导出 USD]
    ↓
前端校验：
  - 场景下至少有 1 个 Instance
  - 所有 Instance 的坐标都在 bounds 内
  - graspable 物体的资产 USD 已存在（调用后端检查）
  ↓
展示"导出选项"Modal：
  □ 输出格式  ◉ usda (文本，可读)  ○ usdc (二进制，小)
  □ 包含物理 Schema（默认勾选）
  □ 强制重建资产 USD 缓存（默认不勾选）
  ↓
点击 [确认导出]
  ↓
调用 POST /api/v3/scenes/{scene_id}/export
  → 返回 job_id
  ↓
前端展示进度面板：
  "正在转换资产（3/15）..."
  "正在组装场景..."
  "正在生成 USD..."
  ↓
后端完成 → 推送 job 状态 → 自动下载
  ↓
成功提示：
  "warehouse_v4.usda 已下载。查看导出报告？"
```

---

## 五、后端需求

### 5.1 数据库变更

**新增表**：

```sql
CREATE TABLE scenes (
    id VARCHAR(128) PRIMARY KEY,
    dataset_id VARCHAR(128) NOT NULL,
    display_name VARCHAR(256) NOT NULL,
    description TEXT,
    bounds JSONB NOT NULL,           -- {x:[a,b], y:[a,b], z:[a,b]}
    up_axis VARCHAR(8) DEFAULT 'Z',
    unit VARCHAR(16) DEFAULT 'meter',
    structure_dxf_path TEXT,
    structure_dxf_uploaded_at TIMESTAMP,
    placements JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(128),
    
    UNIQUE(dataset_id, id),
    FOREIGN KEY (dataset_id) REFERENCES datasets(id)
);

CREATE TABLE scene_exports (
    id SERIAL PRIMARY KEY,
    scene_id VARCHAR(128) NOT NULL,
    version INT NOT NULL,
    exported_at TIMESTAMP DEFAULT NOW(),
    file_path TEXT NOT NULL,
    file_size_bytes BIGINT,
    file_hash VARCHAR(128),
    export_report JSONB,
    
    FOREIGN KEY (scene_id) REFERENCES scenes(id),
    UNIQUE(scene_id, version)
);
```

**现有表修改**：

```sql
-- instances 表新增字段
ALTER TABLE instances ADD COLUMN belongs_to_scenes JSONB DEFAULT '[]'::jsonb;
-- interfaces 字段内新增 I3D_PhysicsHint 支持（JSONB 字段无需改表结构）

-- 索引：快速按 scene 查 instance
CREATE INDEX idx_instances_scenes ON instances USING GIN (belongs_to_scenes);
```

### 5.2 API 接口清单

详见 `3.3_USD导出与场景管理API规范 (API)` 文档。本节仅列出清单：

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/v3/datasets/{dataset_id}/scenes` | 列出数据集下的场景 |
| POST | `/api/v3/datasets/{dataset_id}/scenes` | 创建场景 |
| GET | `/api/v3/scenes/{scene_id}` | 获取场景详情（带统计信息）|
| PUT | `/api/v3/scenes/{scene_id}` | 更新场景基本信息 |
| DELETE | `/api/v3/scenes/{scene_id}` | 删除场景（不删除归属的 Instance） |
| POST | `/api/v3/scenes/{scene_id}/instances` | 添加 Instance 到场景 |
| DELETE | `/api/v3/scenes/{scene_id}/instances/{instance_id}` | 从场景移除 Instance |
| POST | `/api/v3/scenes/{scene_id}/structure/dxf` | 上传 DXF 结构文件 |
| DELETE | `/api/v3/scenes/{scene_id}/structure/dxf` | 删除 DXF 关联 |
| POST | `/api/v3/scenes/{scene_id}/export` | 触发 USD 导出（见 3.0 文档）|
| GET | `/api/v3/scenes/{scene_id}/exports` | 获取场景导出历史 |
| POST | `/api/v3/scenes/{scene_id}/validate` | 预校验：检查导出前是否有问题 |

### 5.3 校验逻辑

**预校验 API** (`POST /api/v3/scenes/{scene_id}/validate`) 的规则：

| 检查项 | 级别 | 触发条件 |
|---|---|---|
| 场景下无 Instance | error | belongs_to_scenes 反查为空 |
| Instance 坐标超出 bounds | error | translation 任一轴超出 Scene.bounds |
| graspable 物体无质量 | warning | collision_type=graspable 但 mass 未填 |
| graspable 物体资产缺失 physics_proxy | warning | 可能影响抓取精度 |
| 同一位置多个 Instance | warning | 两个实例坐标距离 < 1cm |
| DXF 文件格式错误 | error | ezdxf 解析失败 |
| FBX 源文件不存在 | error | Instance 的 file_number 找不到 FBX |

### 5.4 权限模型（简化）

第一版权限设计：

- **查看场景**：数据集成员均可
- **创建/修改场景**：数据集管理员
- **导出 USD**：数据集成员均可（但导出次数限流）
- **删除场景**：数据集管理员

---

## 六、非功能需求

### 6.1 性能

| 指标 | 要求 |
|---|---|
| 场景列表加载（20 个场景） | ≤ 500ms |
| 场景详情加载（含 100 个 Instance） | ≤ 1s |
| 添加 Instance 到场景（单个） | ≤ 200ms |
| 批量添加 Instance（50 个） | ≤ 2s |
| 预校验 | ≤ 2s |

### 6.2 兼容性

- 不破坏 2.3.1 的批量投产功能（批量投产继续可用于为 Instance 填写默认坐标）
- 不影响 2.6 的轮询接口
- 旧数据（无 Scene 归属的 Instance）不会凭空消失，但也不会自动归入任何 Scene（需管理员手动整理）

---

## 七、验收标准

| 场景 | 通过条件 |
|---|---|
| 创建场景 | 正常创建，列表中可见 |
| 添加 Instance 到场景 | Instance.belongs_to_scenes 正确更新 |
| 从场景移除 Instance | 只修改归属关系，不删除 Instance |
| 一个 Instance 属于多个场景 | 两个场景查询时都能看到该 Instance |
| 删除场景 | 场景被删，但归属的 Instance 保留，belongs_to_scenes 中移除该 scene_id |
| 预校验失败的场景尝试导出 | 前端拦截，给出具体错误原因 |
| 成功导出 | 生成 USD 文件 + 写入 exports 表 + 前端可下载 |
| 导出历史 | 每次导出都有新版本号（自增） |
| 上传 DXF 结构文件 | 文件被保存，场景详情可展示 |
| 上传格式错误的 DXF | 返回详细错误，不保存 |

---

## 八、风险与注意事项

### 8.1 历史数据迁移

2.x 里已有的 Instance 在 3.0 之后 `belongs_to_scenes` 为空数组，不会出现在任何 Scene 里。

**两种处理方案**：
1. **推荐**：提供一个"默认场景"创建引导，首次进入 3.0 的数据集时提示"您有 X 个未归属场景的实例，是否创建默认场景'全部实例'并将它们归入？"
2. **备选**：完全手动，用户自己决定如何组织

### 8.2 "一个 Instance 属于多个场景"的坐标冲突

场景 A 里 shelf_001 在 (1,2,0)，场景 B 里希望它在 (5,6,0) —— 怎么办？

**3.0 的方案**：
- Instance 只有一个默认坐标
- 场景 B 如果要不同坐标，需要在 Scene.placements 里加一个 `StaticPlacement` 覆盖
- 第一版 UI 不暴露 placements 编辑（由 API 或 UE 回写触发）

**用户提示**：当用户在场景 B 里想修改一个已属于多个场景的实例坐标时，弹窗提示：
> "shelf_001 也被其他场景使用。修改默认坐标会影响所有场景，是否仅对本场景生效？"
> 
> [影响所有场景]  [仅本场景]  [取消]

### 8.3 场景数量膨胀

如果团队习惯频繁创建场景（每次实验一个），很快就会有几十个场景。需要：
- 归档功能（软删除 + 筛选）
- 标签/分组功能

这些**不在 3.0 范围内**，但数据库设计时预留 `tags JSONB` 字段。

---

## 九、范围外（Out of Scope）

- ❌ 场景 2D/3D 可视化编辑器（第一版纯表单）
- ❌ Placement 的 UI 配置（程序化摆放规则）
- ❌ 场景克隆/复制
- ❌ 场景版本对比（diff）
- ❌ 跨数据集的场景引用
- ❌ 场景分组/标签
- ❌ 权限细粒度控制（行级）
