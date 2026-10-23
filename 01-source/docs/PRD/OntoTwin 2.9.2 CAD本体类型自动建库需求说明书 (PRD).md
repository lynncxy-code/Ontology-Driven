# OntoTwin 2.9.2 CAD 本体类型自动建库需求说明书 (PRD)

> **文档定位：** 在 PRD 2.9 坐标标定工作台基础上，扩展"从 DXF 自动识别并建立本体 ObjectType"的能力。
>
> **开发顺序：** 本模块（2.9.2）**先于** 2.9.1 实施。2.9.1 依赖本模块产出的 ObjectType 才能进行实例 Spawn。

---

## 1. 产品背景

当前 2.9 坐标标定工作台已能从 DXF 中解析出 INSERT 实体（设备块引用），但**这些块名（block_name）只是 DXF 内部标识，与 Nexus 本体体系（ObjectType / 数据集）完全脱节**。要把 CAD 中的设备真正变成数字孪生实例（PRD 2.9.1），必须先在本体库里有对应的 ObjectType，并且该 ObjectType 所属的数据集必须处于激活状态。

人工逐个建类型不现实——一张真实 DXF 可能有 260+ 个 block_name，其中很多是 AutoCAD 自动生成的匿名块、XREF 外参子块或系统辅助块，需要自动过滤；剩下的"真实设备块"也需要批量入库。同时，新建的 ObjectType 不应直接污染 `_object_types` 全局表，而应**作为一个独立的数据集发布**，参与现有的数据集激活/合并体系。

**2.9.2 提供的能力：**

```
上传 DXF
  → 自动过滤系统块
  → 候选类型审核列表
  → 用户确认（含资产路径预填）
  → 批量创建为一个新数据集（默认激活）
  → 可选：合并到现有工作数据集
```

---

## 2. 核心功能概览

| 功能模块 | 说明 |
| :--- | :--- |
| **图元扫描** | 复用 2.9 的 DXF 解析能力，统计每个 block_name 的出现次数、所在图层 |
| **自动过滤** | 双层过滤：图层黑名单 + block_name 前缀黑名单 |
| **候选类型审核** | UI 列出所有未过滤的 (block_name, layer) 组合，用户勾选、改名、确认 |
| **资产路径预填** | 复用 `block_asset_mapping.json`，已映射的块自动填 `asset_id` |
| **数据集发布** | 一键将勾选条目打包为新数据集，**默认发布并激活** |
| **合并到工作数据集** | 把当前 CAD 数据集 ObjectType 追加到一个非 Demo 的工作数据集 |
| **冲突检测** | rid 重复时弹窗让用户选择"跳过 / 覆盖 / 逐个确认" |

---

## 3. 前置依赖：语义图谱总览扩展

2.9.2 的"合并到工作数据集"功能要求系统中存在**非 Demo 的可写数据集**。当前 `ontology_graph.html` 只能通过 CSV 导入或 API 拉取产生数据集，缺少"凭空新建空白工作集"的入口。

**因此本 PRD 同步要求扩展语义图谱总览：**

### 3.1 新增接口

| 路由 | 方法 | 说明 |
| :--- | :--- | :--- |
| `/api/v2/ontology/datasets` | POST | 创建空数据集。Body: `{ "name": "我的工厂工作集" }`，返回 `{ "id": "...", "name": "..." }` |

### 3.2 新增 UI

在 `ontology_graph.html` 的"我的数据集"列表顶部，"标准实践"（Demo）旁边，加一个 **`+ 新建空数据集`** 按钮：

- 点击弹出输入框 → 用户填写数据集名称 → 调用上述 POST 接口
- 新数据集为空（无 nodes、无 links），创建后可选择立即激活
- 该数据集后续可被 2.9.2 的"合并到工作数据集"作为目标，也可被其他途径（CSV 导入合并、本体注入中心手动添加）扩充

**实施代价**：后端 ~15 行，前端 ~30 行；不属于 2.9.2 范围但必须先于 2.9.2 上线。

---

## 4. 系统架构

### 4.1 四个核心数据载体

理解 2.9.2 与 2.9.1 必须先理解 Nexus 本体/实例体系中四个数据载体的角色：

| 载体 | 角色 | 持久化 | 写者 | 读者 |
| :--- | :--- | :--- | :--- | :--- |
| `block_asset_mapping.json` | 块名 → 资产路径 种子字典 | ✅ JSON 文件 | 2.9 工作台 / 2.9.2 commit | 2.9 工作台 / 2.9.2 scan |
| `_datasets`（数据集列表） | 本体类型集合容器 | ❌ 内存 | 2.9.2 / 语义图谱导入 / 新建空集 | 语义图谱 / 激活操作 |
| `_object_types` | **当前激活数据集的投影** | ❌ 内存 | 激活操作触发，被动同步 | 实例运维 / 2.9.1 / 本体注入 |
| `InstanceStore` | 实例集合 | ❌ 内存 | 实例运维 / 2.3.1 / 2.9.1 | 实例运维 / UE 同步 |

**关键认识：`_object_types` 不是权威源，它是数据集激活的副产物。** 任何要影响 `_object_types` 的操作（包括 2.9.2）都必须通过数据集体系来做。

### 4.2 技术栈

延续 2.9 的栈，不引入新依赖：

| 层 | 技术 |
| :--- | :--- |
| 前端 | 在 `coord_workbench.html` 内新增一个步骤面板 |
| 后端 | Flask `/api/v2/coord/types/*` 路由族 |
| 解析 | 复用 `parser_dxf.py` |
| 存储 | 写入 `_datasets`，激活时按现有机制同步至 `_object_types` |

### 4.3 文件清单

| 文件路径 | 职责 |
| :--- | :--- |
| `backend/app.py` | 新增 `/api/v2/coord/types/*` 路由（4 个）+ `POST /api/v2/ontology/datasets`（1 个，属于前置改造） |
| `backend/parser_dxf.py` | 扩展 `extract_block_candidates(file)` 函数，按规则分类 block_name |
| `backend/coord_filter_rules.py` | **新增**：过滤规则定义（图层/前缀黑名单），独立成模块便于维护 |
| `frontend/coord_workbench.html` | CAD 模式步骤条新增"② 类型审核"步骤 |
| `frontend/ontology_graph.html` | 新增"+ 新建空数据集"按钮（属于前置改造） |

### 4.4 API 路由

| 路由 | 方法 | 说明 |
| :--- | :--- | :--- |
| `/api/v2/coord/types/scan` | POST | 上传 DXF，返回候选类型列表（已过滤 + 待审核 + 灰色地带） |
| `/api/v2/coord/types/check_conflicts` | POST | 提交勾选列表，扫描所有数据集查找同 rid 的位置（仅用于 merge 模式或信息提示） |
| `/api/v2/coord/types/check_coverage` | POST | 给定 DXF 中的 block_name 列表，返回"当前激活数据集中覆盖了哪些 / 缺失哪些"，用于"跳过此步"的覆盖率检查 |
| `/api/v2/coord/types/commit` | POST | 提交审核通过的列表，**创建新数据集 + 默认激活**，或**合并到指定工作数据集** |
| `/api/v2/coord/mapping` | GET/POST | **复用 2.9 已有接口**，2.9.2 审核时填写的 asset_id 反向回写至同一份 `block_asset_mapping.json` |
| `/api/v2/ontology/datasets` | POST | **前置改造**：新建空数据集 |

---

## 5. 端到端数据流时序图

```
[用户]          [前端 coord_workbench]      [后端 app.py]                [数据载体]

上传DXF  ─────► ─── POST /scan ────────►  parser_dxf 解析
                                          + filter_rules 过滤
                                          + 读 mapping 预填 asset_id    block_asset_mapping.json
              ◄── 候选列表 ──────────

审核确认 ─────► ─ POST /check_conflicts ─► 扫描所有数据集中的 rid
              ◄── 冲突清单 ──────────

策略确认 ─────► ── POST /commit ──────►  ① 新建数据集 ds_id           _datasets[ds_id]
                  (mode=publish)         ② 写入 nodes/links
                                         ③ 默认激活该数据集            _datasets, _active_dataset_id
                                         ④ 投影至 _object_types       _object_types  ← 同步！
                                         ⑤ 回写 asset_id 到 mapping   block_asset_mapping.json
              ◄── {ds_id, 摘要} ──────

[或：]
策略确认 ─────► ── POST /commit ──────►  ① 找到目标 ds_target
                  (mode=merge,           ② 合并 nodes/links（同名以 CAD 优先）
                   target_ds_id=...)     ③ 若 ds_target 已激活 → 同步至 _object_types
                                         ④ 回写 asset_id 到 mapping
              ◄── {ds_id, 摘要} ──────

[继续 2.9 标定流程 → 2.9.1 投入实例]

投入实例 ─────► ─ POST /spawn_instances ► 按 block_name 查 _object_types  _object_types
                                         三态校验（详见 2.9.1）
                                         写入 InstanceStore            InstanceStore
              ◄── 结果摘要 ──────────
```

---

## 6. 过滤规则详细设计

过滤分两层：先按图层，再按 block_name 前缀。两条规则任一命中即视为系统块，**默认不入候选列表**。

### 6.1 图层黑名单（建筑/标注/外参）

| 规则类型 | 匹配模式 | 说明 |
| :--- | :--- | :--- |
| 前缀 | `A-` | AIA 标准图层（A-DOOR, A-WIN, A-WALL-*, A-ANNO-*, A-AXIS, A-FLOR-*） |
| 包含 | `$0$` 或 `$AZ$` | XREF 外参子图层（如 `X_18_A_Plan$0$A-DOOR`） |
| 精确 | `Defpoints` | AutoCAD 系统层 |
| 前缀 | `PUB_`, `DIM_` | 公共图层、尺寸标注 |

### 6.2 block_name 前缀黑名单

| 规则类型 | 匹配模式 | 说明 |
| :--- | :--- | :--- |
| 前缀 | `A$C`, `A$c` | AutoCAD 匿名块 |
| 前缀 | `*U` | AutoCAD 匿名块 |
| 前缀 | `G$C` | 匿名块 |
| 前缀 | `zw$` | 中望 CAD 内部块 |
| 包含 | `$0$`, `$AZ$` | XREF 外参子块 |
| 精确 | `_AXISO` | 坐标轴标记 |
| 前缀 | `template_`, `AE_A0` | 图框/模板 |

### 6.3 灰色地带（特殊处理）

| 图层名 | 处理方式 |
| :--- | :--- |
| `0`, `00` | **不过滤**，进入候选列表，UI 标红警告"未分图层，请仔细确认"，默认不勾选 |
| `0土建*`, `000家具`, `000卫生间洁具`, `000平面文字`, `弱电图层` 等 | 进入候选列表，UI 标黄警告"图层归属可疑"，默认勾选 |

灰色地带规则定义在 `coord_filter_rules.py`，便于后期根据用户实践增删。

---

## 7. 候选类型数据结构

`/api/v2/coord/types/scan` 响应示例：

```json
{
  "summary": {
    "total_inserts": 7239,
    "unique_block_names": 260,
    "filtered_system_blocks": 87,
    "filtered_xref_blocks": 53,
    "candidates": 120
  },
  "candidates": [
    {
      "block_name": "SDT-0200-甲-3",
      "layers": ["一期生产设备", "二期生产设备"],
      "primary_layer": "一期生产设备",
      "count": 64,
      "suggested_name": "SDT-0200-甲-3",
      "suggested_rid": "SDT-0200-甲-3",
      "preset_asset_id": "SM_SDT_0200",
      "warning": null,
      "default_checked": true
    },
    {
      "block_name": "GDFGHFDHJHJ",
      "layers": ["生产设备"],
      "primary_layer": "生产设备",
      "count": 237,
      "suggested_name": "GDFGHFDHJHJ",
      "suggested_rid": "GDFGHFDHJHJ",
      "preset_asset_id": null,
      "warning": "block_name 不规范，建议改名",
      "default_checked": true
    },
    {
      "block_name": "AGV",
      "layers": ["0"],
      "primary_layer": "0",
      "count": 2,
      "suggested_name": "AGV",
      "suggested_rid": "AGV",
      "preset_asset_id": null,
      "warning": "位于 0 图层（未分图层）",
      "default_checked": false
    }
  ],
  "filtered_log": [
    {"block_name": "A$C718A3FEA", "reason": "AutoCAD 匿名块", "count": 44},
    {"block_name": "X_18_A_Plan$0$$DorLib2D$00000001", "reason": "XREF 外参子块", "count": 32}
  ]
}
```

`primary_layer` 为该 block 出现次数最多的图层，作为最终写入 ObjectType 的 `category`。

---

## 8. UI 设计：CAD 模式新增"② 类型审核"步骤

原 2.9 CAD 模式步骤条：① 上传 → ② 标定 → ③ 实体 → ④ 导出

**2.9.2 后调整为：** ① 上传 → **② 类型审核** → ③ 标定 → ④ 实体 → ⑤ 导出

### 8.0 全局：工作台 Header 显示当前激活数据集

工作台顶部 header 在原"CAD MODE"badge 旁加一个"当前激活数据集"指示条，让用户随时知道"我现在做的操作会写入哪个数据集"：

```
[CAD MODE]  📊 当前激活：我的工厂本体  [切换 ▼]
```

- 点击"切换 ▼"展开下拉，列出所有数据集（含 Demo），点击即调 `/api/v2/ontology/datasets/activate`
- 切换前若触发副作用（见 § 8.5），同样弹警告
- header 上的状态由 GET `/api/v2/ontology/datasets` 在工作台初始化时拉取一次，commit 成功后刷新

### 8.1 类型审核面板布局

```
┌──────────────────────────────────────────────────────┐
│ 候选 ObjectType（120 个）  [全选] [全不选] [仅勾选灰色]   │
├──────────────────────────────────────────────────────┤
│ ☑ SDT-0200-甲-3      [一期生产设备 x64]                │
│     name: [SDT-0200-甲-3____]   asset: [SM_SDT_0200__]│
│ ☑ GDFGHFDHJHJ ⚠       [生产设备 x237]                  │
│     name: [____________]        asset: [_____________]│
│ ☐ AGV 🟥             [0 x2]                            │
│     name: [____________]        asset: [_____________]│
│ ...                                                   │
├──────────────────────────────────────────────────────┤
│ 系统已过滤 140 个块（点击展开查看明细）                  │
├──────────────────────────────────────────────────────┤
│ ⚙ 写入策略                                            │
│   ◉ 发布为新数据集并激活  名称: [cad:新块_20260522___] │
│   ○ 合并到现有工作数据集   [▼ 选择数据集...]           │
│                                                       │
│  [跳过此步]            [批量创建 / 合并]                │
└──────────────────────────────────────────────────────┘
```

### 8.2 写入策略选择

按"漏洞 6"约定的规则，UI 智能决定可选项：

| 当前激活数据集 | "发布并激活"可选 | "合并到工作集"可选 | 默认选中 |
| :--- | :---: | :---: | :--- |
| Demo（只读） | ✅ | ❌（禁用） | 发布并激活 |
| 用户创建的工作集 | ✅ | ✅ | 合并到该工作集 |

"合并到现有工作数据集"下拉列表：**排除 Demo**，列出所有用户创建/导入/发布的数据集。

**当 active = Demo 时的特殊引导（漏洞 10 修正）：**

为避免用户被迫离开工作台去语义图谱总览建空集，在写入策略区直接给出快捷入口：

```
⚠ 当前激活的是只读 Demo 数据集，无可合并目标

  ◉ 发布为新数据集并激活
      名称: [我的工厂本体______]
  ○ 合并到现有工作数据集  （禁用）

  💡 推荐操作：
    [立即新建空数据集"我的工厂本体"并激活]   ← 一键按钮
       建好后界面自动切到 merge 模式
```

按钮内嵌调 `POST /api/v2/ontology/datasets` 创建空集 + `POST /datasets/activate` 激活，全程不离开工作台。

### 8.3 交互细节

| 元素 | 行为 |
| :--- | :--- |
| 复选框 | 默认勾选状态由后端 `default_checked` 决定（灰色地带默认不勾） |
| name 输入框 | 默认 = block_name，可改，作为 `ObjectType.name`（显示用） |
| rid | 不可改，保持 block_name 不变，作为内部唯一标识 |
| asset 输入框 | 默认 = `preset_asset_id`（来自 mapping），可改 |
| 警告标识 | 🟥 红：未分图层；⚠ 黄：命名不规范/图层可疑；无标识 = 正常 |
| 跳过此步按钮 | 触发覆盖率检查（见 § 8.3.1）后再决定是否跳到 ③ 标定 |
| 批量创建按钮 | 触发冲突检查 → 弹窗确认 → 提交 commit |

### 8.3.1 "跳过此步"的覆盖率检查（漏洞 9 修正）

用户跳过类型审核可能意味着"我已经在别处建好类型了"，但必须确认**当前激活数据集真的覆盖了 DXF 中的 block_name**，否则到 ⑤ 导出投实例时才报错就太晚。

点击"跳过此步"时前端调 `POST /api/v2/coord/types/check_coverage`：

```
请求: { "block_names": ["SDT-0200-甲-3", "AGV", "焊接头", ...] }
响应: {
  "total": 120,
  "covered": 80,           // 激活数据集中存在的
  "missing": 40,           // 激活数据集中没有的
  "missing_samples": ["GDFGHFDHJHJ", "AGV", "UNKNOWN_BLK"]  // 最多 10 个示例
}
```

前端三态处理：

| 覆盖情况 | 处理 |
| :--- | :--- |
| `missing == 0` | 直接放行，跳到 ③ 标定 |
| `0 < missing < total` | 弹窗"激活数据集中只覆盖了 80/120 个类型，缺失：[GDFGHFDHJHJ, AGV...]。仍要跳过吗？" `[继续跳过] [返回审核]` |
| `missing == total` | 弹窗"激活数据集中找不到任何对应类型，强烈建议先做类型审核。" `[仍要跳过] [返回审核]`，且第一个按钮置灰 1 秒防误点 |

### 8.4 冲突弹窗（按 mode 区分语义，漏洞 7 修正）

调用 `/api/v2/coord/types/check_conflicts` 后，**publish 与 merge 两种模式的"冲突"含义完全不同**，UI 必须分开处理。

#### 8.4.1 publish 模式：仅做"信息提示"，无需用户决策

publish 模式下，目标是**新建的空数据集**，里面一定没有任何 rid——"其他数据集里也有同名 rid"**不算冲突**，只是重名。多个数据集可以各自存在同名 rid，互不影响。

```
ℹ 信息：以下 rid 在系统中其他数据集里也存在

  - SDT-0200-甲-3   也存在于: 我的工厂工作集
  - AGV             也存在于: 标准实践(Demo)、cad:旧块.dxf

新数据集允许有同名 rid，互不干扰。
激活新数据集后，_object_types 会以新定义为准。

[知道了，继续提交]
```

只有"知道了"一个按钮，不要求用户做选择。

#### 8.4.2 merge 模式：真正的冲突，三选一

merge 模式下目标是**已有内容的工作集**，同 rid 写入会真覆盖该集中的老 node。这才是真冲突：

```
检测到 3 个 ObjectType 已在目标数据集"我的工厂本体"中存在：

  - SDT-0200-甲-3
  - CCD检测站
  - AGV

请选择处理方式：
  ( ) 全部跳过（保留目标集中的老定义）
  ( ) 全部覆盖（用 CAD 新定义替换目标集中的老定义）
  ( ) 逐个确认（弹出每个的对比详情）

[取消]  [确认]
```

"覆盖"仅作用于**目标数据集**，不会跨数据集影响其他集中的同名条目。

#### 8.4.3 check_conflicts 接口的返回结构

```json
{
  "in_target_dataset": [          // 目标集中已存在的 rid（仅 merge 模式有意义）
    {"rid": "SDT-0200-甲-3", "old": {...}, "new": {...}}
  ],
  "in_other_datasets": [          // 其他集中存在的 rid（仅作信息展示）
    {"rid": "AGV", "datasets": [{"id": "demo", "name": "标准实践"}]}
  ]
}
```

前端按 mode 决定渲染哪部分：publish 只渲染 `in_other_datasets`，merge 只渲染 `in_target_dataset`。

### 8.5 副作用警告（漏洞 1 + 漏洞 8 修正）

**触发条件：所有会刷新 `_object_types` 的写入操作**，不分 publish/merge：

| 操作 | 是否触发检测 |
| :--- | :---: |
| publish 模式 + 默认激活 | ✅（切换激活数据集会全量替换 `_object_types`） |
| merge 模式 + target == 当前激活数据集 | ✅（直接修改激活集中的 node，会同步刷新 `_object_types`） |
| merge 模式 + target ≠ 当前激活数据集 | ❌（只动未激活集的内容，对运行时无影响） |
| 直接在 header 切换激活数据集 | ✅ |

**检测内容**：

```
比较"操作前 _object_types 的 rid 集合"与"操作后 _object_types 的 rid 集合"，
找出"将被删除或被新定义覆盖的 rid"，再查这些 rid 是否被 InstanceStore 中的实例引用。
```

**警告弹窗（publish 案例）**：

```
⚠ 切换激活数据集会有副作用

当前数据集"标准实践"中有 5 个 ObjectType 正在被
InstanceStore 中的 23 个实例引用。切换后这些实例的
类型引用将悬空，可能在实例运维中心显示异常。

建议改用"合并到现有工作数据集"模式。

  [仍要发布并激活]  [改为合并模式]  [取消]
```

**警告弹窗（merge 覆盖案例）**：

```
⚠ 合并到当前激活数据集会覆盖部分定义

以下 ObjectType 将被新定义替换，且正在被实例引用：
  - SDT-0200-甲-3  （被 12 个实例引用）
  - AGV            （被 3 个实例引用）

若新定义改动了 properties 或 injected_interfaces，
现有实例的对应字段可能失效。

  [仍要合并]  [改用'跳过冲突项'策略]  [取消]
```

### 8.6 commit 成功后的提示（改进 2）

写入成功后，前端展示双出口提示，不强制自动跳到下一步：

```
✓ 已成功写入 60 个 ObjectType 到"我的工厂本体"

  本次新增: 50    覆盖: 10    跳过: 0
  asset_id 已预填: 35 项（来自历史映射）

  💡 提示：如其他标签页正在浏览语义图谱总览，请刷新查看新数据

  [前往语义图谱总览查看]    [继续标定 →]
```

默认聚焦"继续标定"按钮（回车快速进入下一步），但用户可点击另一个出口跳走。

---

## 9. ObjectType 默认结构

**严格沿用现有 `OBJECT_TYPES` 平铺结构**（见 `backend/mapping_store.py:132`），只新增一个 `source` 字段用于追溯：

```json
{
  "rid": "SDT-0200-甲-3",
  "name": "SDT-0200-甲-3",
  "category": "一期生产设备",
  "description": "由 CAD 解析自动创建（来源：新块.dxf）",
  "color": "#0891b2",
  "properties": [
    {"name": "EQUIP_ID", "label": "设备编号", "type": "string"},
    {"name": "MODEL",    "label": "型号",     "type": "string"}
  ],
  "injected_interfaces": ["I3D_Representable", "I3D_Spatial"],
  "mock_instances": [],
  "asset_id": "SM_SDT_0200",
  "source": "cad_auto:新块.dxf",
  "created_at": 1716345600
}
```

### 9.1 字段说明

| 字段 | 来源 / 默认值 |
| :--- | :--- |
| `rid` | INSERT 的 `block_name`（不可改） |
| `name` | 用户在审核面板填写，默认 = `block_name` |
| `category` | `primary_layer`（该 block 出现次数最多的图层） |
| `description` | 自动拼接：`"由 CAD 解析自动创建（来源：<文件名>）"` |
| `color` | 取所在图层的颜色（来自 DXF 图层 ACI） |
| `properties` | 从该 block 所有 INSERT 的 `attribs` keys 中并集提取，全部按 string 类型 |
| `injected_interfaces` | **固定** = `["I3D_Representable", "I3D_Spatial"]` |
| `mock_instances` | 空数组（实际实例由 2.9.1 创建） |
| `asset_id` | 用户填或来自 mapping，可为 `null` |
| `source` | **2.9.2 新增字段**：`"cad_auto:<文件名>"` |
| `created_at` | 服务端 `time.time()` |

### 9.2 关键约定（漏洞 3）

**`asset_id` 双轨同步规则：**

- `block_asset_mapping.json` 是 **种子字典**，仅在创建新 ObjectType 时被 2.9.2 读取用于预填
- ObjectType.asset_id 一旦写入即为**权威值**
- mapping 后续被改动（用户在 2.9 工作台保存新映射）**不会反向更新已存在的 ObjectType**
- 2.9.2 commit 时，会将新填写的 asset_id 回写至 mapping（同名块覆盖），形成正反馈

### 9.3 接口属性默认值的获取（保持现有机制）

ObjectType 自身**不存接口属性默认值**（如 translation_x、scale_x 等）。这些默认值统一由 `INTERFACES` 表（`mapping_store.py:69`）提供。实例 spawn 时（2.9.1）按 `injected_interfaces` 字段从 `INTERFACES` 拉默认值，再用 CAD 仿射变换结果覆盖坐标字段。

---

## 10. 与数据集体系的集成（核心章节）

### 10.1 commit 接口的两种 mode

```
POST /api/v2/coord/types/commit
Body: {
  "source_file": "新块.dxf",
  "items": [ ... 候选条目 ... ],
  "conflict_strategy": "skip" | "overwrite" | "per_item",
  "mode": "publish" | "merge",
  "publish_options": { "name": "cad:新块_20260522" },        // mode=publish 时
  "merge_options":   { "target_dataset_id": "ds_user_01" }   // mode=merge 时
}
```

### 10.2 mode = publish 的处理流程

1. **重名检测（漏洞 11 修正）**：扫描 `_datasets`，若已存在同 `name` 的数据集，返回 409 `{"error": "name_duplicated", "existing_id": "ds_xxx"}`，前端弹窗"已存在同名数据集 X，是否：[改名 / 合并到 X / 取消]"
2. 创建新数据集，name 由 `publish_options.name` 提供
3. 把所有 items 转换为 ObjectType（结构见第 9 节），存入新数据集的 `nodes`
4. **默认调用 `/api/v2/ontology/datasets/activate`**，让 `_object_types` 立刻可用
5. 激活前若触发"副作用警告"（§ 8.5），由前端弹窗拦截，用户确认后再 commit
6. 响应中带 `hint: "请在其他打开的语义图谱总览页面手动刷新查看新数据集"`（改进 3）

### 10.3 mode = merge 的处理流程

1. 校验 `target_dataset_id`：
   - 不能是 Demo（Demo 只读）
   - 必须已存在
2. **副作用预检（漏洞 8 修正）**：若 `target_dataset_id == _active_dataset_id`，扫描会被新定义覆盖的 rid 是否被 InstanceStore 引用；若有则返回 200 但带 `pending_warnings`，由前端弹 § 8.5 警告弹窗，用户确认后再次提交（带 `force=true`）才真正执行
3. 把所有 items 追加到目标数据集的 `nodes`
4. 同名 ObjectType 按 `conflict_strategy` 处理：
   - `skip`：保留目标中的原条目
   - `overwrite`：用 CAD 新条目替换（**CAD 优先**）
5. 原 CAD 文件不再单独发布数据集（避免冗余）
6. 若 `target_dataset_id == _active_dataset_id`，同步刷新 `_object_types`；否则仅写入 `_datasets`，等用户后续手动激活
7. 响应中带 `hint: "请在其他打开的语义图谱总览页面手动刷新查看更新"`（改进 3）

### 10.4 多张 CAD 累积的推荐做法（漏洞 5）

| 场景 | 推荐操作 |
| :--- | :--- |
| 第一次跑 2.9.2，没有工作集 | 先去语义图谱总览"+ 新建空数据集"建一个 `我的工厂工作集` 并激活，然后回 2.9.2 选"合并到 我的工厂工作集" |
| 已有工作集，传入新 CAD | 默认选"合并到该工作集"，所有 CAD 类型累积到同一处 |
| 想给某张 CAD 单独建库（如临时实验） | 选"发布为新数据集"，名称区分 |

UI 在 commit 面板根据当前状态自动**预选默认 mode**：当前激活的不是 Demo → 默认 merge；否则默认 publish。

### 10.5 asset_id 反向回写（保留原约定）

`commit` 接口在写入 ObjectType 的同时，将所有非空 `asset_id` 合并写回 `block_asset_mapping.json`：

```python
existing = load_mapping()
for item in committed:
    if item['asset_id']:
        existing[item['block_name']] = item['asset_id']
save_mapping(existing)
```

---

## 11. 编码与字符集

DXF 文件的中文编码（GBK / CP936）由 `ezdxf` 自动处理（`doc.encoding` 字段可见），返回的 Python 字符串本身就是 unicode，**无需任何转码逻辑**。

需要确保：
1. Flask `jsonify` 需设置 `app.config['JSON_AS_ASCII'] = False`（若尚未设置），保证中文字符不被转义为 `\uXXXX`
2. 调试脚本若在 Windows 控制台运行，需 `sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')`

---

## 12. 与其他模块的关系

| 模块 | 关系 |
| :--- | :--- |
| **PRD 2.9 坐标标定工作台** | 在 CAD 模式步骤条中插入一个新步骤；复用其 DXF 解析与 mapping 接口 |
| **PRD 2.9.1 实体投入实例库** | **下游依赖**：2.9.1 spawn 实例时需要 2.9.2 已建好的 ObjectType 且所在数据集已激活 |
| **PRD 2.2 Nexus 资产中台** | `asset_id` 字段最终指向资产库中的 SM_* 资产；2.9.2 不主动校验资产是否存在 |
| **PRD 2.3 实例运维监控中心** | 通过 `_object_types` 间接关联：ObjectType 必须在激活数据集中，实例运维才能识别 |
| **PRD 2.3.1 数据集批量投产** | 2.9.2 创建的 ObjectType 同时供 2.3.1 的"按类型筛选实例"使用，两个流程共享同一份本体库 |
| **语义图谱总览（ontology_graph.html）** | 2.9.2 产出的数据集在此页面可见、可激活、可删除；新增"+ 新建空数据集"按钮亦在此页面 |

---

## 13. 已知限制与约束

1. **仅支持 INSERT 实体**：POLYLINE/LINE/CIRCLE 等几何体不参与 ObjectType 创建（它们走 PROCEDURAL_WALL/FLOOR 路线，不属于设备本体）。
2. **图片模式不适用**：图片模式没有 block 概念，2.9.2 仅在 CAD 模式生效。图片模式下用户继续使用现有的"从下拉框选已有 type"方式。
3. **过滤规则硬编码**：当前规则写在 `coord_filter_rules.py`，修改需改代码并重启；不提供运行时配置 UI。
4. **同名跨图层合并**：一个 block_name 出现在多个图层时，合并为一个候选条目，`category` 取 `primary_layer`。
5. **不持久化**：与现有 `_datasets` / `_object_types` 一致，重启后丢失；后续如需持久化，统一改造。
6. **跨数据集 rid 全局唯一性不保证**：不同数据集可以有同名 rid，但激活时会以激活数据集为准。冲突弹窗（8.4）会列出所有同名条目所在的数据集名称。

---

## 14. 未来演进路线

1. **持久化 ObjectType 与数据集**：与现有本体体系一并迁移到 JSON/SQLite 存储。
2. **过滤规则可视化配置**：UI 允许用户增删黑名单规则，存为 JSON。
3. **block 缩略图预览**：审核面板每行显示该 block 在画布中的小图，辅助判断。
4. **跨 DXF 增量识别**：检测新 DXF 中已存在的 ObjectType（rid 匹配），仅展示新增项。
5. **基于命名 LLM 建议**：对 `GDFGHFDHJHJ` 这类乱名，结合所在图层和形状特征，提示"建议改名为：XXX"。
6. **多数据集同时激活**：当前激活为单选，未来可扩展为多选叠加（按优先级解决 rid 冲突）。
