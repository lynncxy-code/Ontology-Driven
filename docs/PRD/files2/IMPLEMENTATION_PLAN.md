# IMPLEMENTATION_PLAN.md — 落地计划

> 本文档把项目拆成**可执行的任务块**，每个任务块独立、可验证、可暂停。
> Claude Code 按顺序推进，每完成一块等用户确认后再进下一块。

---

## 总览

```
M0（1-2 天）  → 后端硬编码闭环验证     [先跑通，验证 USD 格式可用]
M1（2-3 天）  → 数据库 + API + 前端    [让场景配置可视化]  
M2（2-3 天）  → UE 工程 + USD 加载      [可视化验证]
M3（1-2 天）  → 回写功能                [美术闭环]
M4（1 天）     → 训练剧本文档 + 交付    [对接训练同事]
```

总工期预估：**1-2 周**（单人开发，边做边调）。

---

## M0：硬编码闭环（最先做）

### 目标

不动前端、不建数据库，用一个 Python 脚本把硬编码的几个物体导出为 USD，验证：
1. `usd-core` 环境正常
2. 生成的 USD 结构符合预期
3. 训练同事能加载

### Task M0-1：创建目录结构

```bash
mkdir -p backend/lite/services
mkdir -p backend/lite/tests
mkdir -p assets/fbx assets/usd_cache
mkdir -p exports
mkdir -p docs
```

### Task M0-2：写一个独立导出脚本

**文件**：`backend/lite/services/usd_exporter.py`

**要求**：
- 不依赖数据库
- 接受硬编码的 dict 描述
- 生成 `.usda` 文件到 `exports/`
- 包含：1 个机器人 + 2 个货架 + 3 个箱子（1 大 1 中 1 小）
- 正确应用物理 Schema（static / graspable）
- 正确写入 customData

**示例调用**：

```python
scene_data = {
    "id": "hardcoded_demo",
    "display_name": "硬编码演示场景",
    "bounds": {"x": [-3, 3], "y": [-3, 3], "z": [0, 3]},
    "instances": [
        {
            "id": "franka_001",
            "object_type_rid": "ri.obj.robot",
            "file_number": "franka",
            "translation": [0, 0, 0],
            "rotation": [0, 0, 0],
            "collision_type": "static",
        },
        {
            "id": "shelf_001",
            "object_type_rid": "ri.obj.shelf",
            "file_number": "shelf",
            "translation": [1.5, 0, 0],
            "rotation": [0, 0, 90],
            "collision_type": "static",
        },
        {
            "id": "box_large_001",
            "object_type_rid": "ri.obj.box",
            "file_number": "box_large",
            "translation": [-1, 0.5, 0.15],
            "collision_type": "graspable",
            "mass": 2.0,
        },
        # ... 更多
    ]
}

export_scene_to_usd(scene_data, "exports/hardcoded_demo.usda")
```

### Task M0-3：资产 USD 准备

**M0 简化**：不做 FBX 转换，手动准备几个最简单的占位 USD 资产。

**方式**：用 `pxr` 生成 3 个简单的 Cube 作为占位资产：

```python
def create_placeholder_asset(name: str, size: tuple, output_path: str):
    """生成一个 Cube 作为占位资产。"""
    stage = Usd.Stage.CreateNew(output_path)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    
    xform = UsdGeom.Xform.Define(stage, f"/{name}")
    stage.SetDefaultPrim(xform.GetPrim())
    
    cube = UsdGeom.Cube.Define(stage, f"/{name}/mesh")
    cube.CreateSizeAttr(1.0)
    
    xform_op = xform.AddScaleOp()
    xform_op.Set(Gf.Vec3f(*size))
    
    stage.Save()

# 生成占位资产
create_placeholder_asset("shelf", (0.8, 2.0, 2.0), "assets/usd_cache/shelf.usd")
create_placeholder_asset("box_large", (0.3, 0.3, 0.3), "assets/usd_cache/box_large.usd")
create_placeholder_asset("franka", (0.3, 0.3, 1.2), "assets/usd_cache/franka.usd")
```

**后续替换**：M1 之后用真实的 FBX 转 USD。

### Task M0-4：测试脚本

**文件**：`backend/lite/tests/test_hardcoded_export.py`

跑一遍导出流程，确认：
- 无报错
- `exports/hardcoded_demo.usda` 生成
- 文件大小 > 0
- 打开文件，肉眼确认结构正确

### Task M0-5：交付给训练同事验证

- 把 `exports/hardcoded_demo.usda` 和 `assets/usd_cache/*.usd` 打包发给训练同事
- 请他在 Isaac Sim 里加载确认
- 如果有问题，修正

**M0 完成标准**：训练同事在 Isaac Sim 里能看到场景，物理属性应用正确。

---

## M1：数据库 + API + 最简前端

### 目标

把 M0 的硬编码数据变成可配置的。前端能管理场景、点击导出。

### Task M1-1：搭建 SQLite 数据库

**文件**：`backend/lite/models/db.py` + `backend/lite/models/schemas.py`

**要做**：
- 决定用 SQLAlchemy ORM 还是原生 sqlite3（**问用户**）
- 创建 `TECH_SPEC.md` 里定义的 5 张表
- 提供 `get_db_connection()` 工具函数
- 初始化脚本：首次启动自动建表

### Task M1-2：Flask Blueprint 初始化

**文件**：`backend/lite/api/__init__.py`

按 `TECH_SPEC.md` 第六节组织。

### Task M1-3：资产管理 API

**文件**：`backend/lite/api/assets.py`

- GET /api/v3/lite/assets
- POST /api/v3/lite/assets
- DELETE /api/v3/lite/assets/{file_number}

**手动数据注入**：M1 阶段不做 FBX 上传 UI，资产通过 API 或 SQL 手动插入几条：
- franka, shelf, box_large, box_medium, box_small

### Task M1-4：实例管理 API

**文件**：`backend/lite/api/instances.py`

标准 CRUD。

### Task M1-5：场景管理 API

**文件**：`backend/lite/api/scenes.py`

- GET/POST /api/v3/lite/scenes
- GET /api/v3/lite/scenes/{id}
- POST /api/v3/lite/scenes/{id}/instances (批量加)
- DELETE /api/v3/lite/scenes/{id}/instances/{instance_id}

### Task M1-6：导出 API

**文件**：`backend/lite/api/export.py`

- POST /api/v3/lite/scenes/{id}/export
- GET /api/v3/lite/exports/{id}/download

复用 M0 的 `usd_exporter.py`，但数据从数据库读。

### Task M1-7：在 `app.py` 末尾注册路由

**这是唯一修改现有文件的地方**。

```python
# 末尾追加
try:
    from lite.api import register_lite_routes
    register_lite_routes(app)
except Exception as e:
    print(f"[Lite] 加载失败: {e}")
```

### Task M1-8：前端页面

**文件**：`frontend/scenes/scenes.html` + `scenes.js`

单页搞定：
- 左侧：场景列表 + 新建按钮
- 中间：当前场景的实例列表（可增删、改坐标）
- 右侧：资产库（可拖拽或点击添加到场景）
- 顶部：导出 USD 按钮

**不做**：美观设计、动画、复杂交互。能用即可。

### Task M1-9：端到端测试

- 打开 `http://localhost:5000/scenes`
- 新建场景
- 添加几个实例
- 配置坐标
- 点击导出
- 下载 USD
- 用 usdview 打开验证

**M1 完成标准**：前端能驱动后端生成正确的 USD。

---

## M2：UE 工程 + USD 加载

### 目标

新建 UE 项目，通过 USD Stage Actor 加载 Nexus 导出的 USD，验证视觉效果。

### Task M2-1：新建 UE 项目

**手动操作**（Claude Code 指导）：
- 下载 UE 5.x（具体版本由用户决定）
- 新建 Blank 项目，命名 `OntoTwinLite`
- 路径：`d:\tmp\digital_twin_aircraft\ue_project\`

### Task M2-2：启用 USD 插件

- `Edit → Plugins → Universal Scene Description`
- 重启 UE

### Task M2-3：导入 USD

- 把 `exports/warehouse_demo_01_v1.usda` 拖进 UE Content Browser
- 或者在 Level 中添加 USD Stage Actor，指向该文件

### Task M2-4：编写拉取 Nexus 数据的脚本

**UE Python 脚本**：`ue_project/Scripts/fetch_nexus_scene.py`

- 调用 `GET /api/v3/lite/scenes/{id}/ue_data`
- 解析响应
- 在当前 Level 中 spawn 对应的 Actor
- 每个 Actor 挂 Tag，记录 `instance_id`

（本任务是 UE 端核心代码，细节在实施时和 Claude Code 讨论）

### Task M2-5：坐标系转换工具

**文件**：`ue_project/Scripts/coord_utils.py`

```python
def nexus_to_ue_location(loc_m):
    """米 + 右手系 → cm + 左手系"""
    x, y, z = loc_m
    return (x * 100, -y * 100, z * 100)

def ue_to_nexus_location(loc_cm):
    """cm + 左手系 → 米 + 右手系"""
    x, y, z = loc_cm
    return (x / 100, -y / 100, z / 100)
```

### Task M2-6：UE 菜单入口

加一个"OntoTwin"菜单，包含：
- 加载场景（触发 M2-4）
- 导出 USD（调用后端 API，下载到本地）

**M2 完成标准**：在 UE 里能看到场景正确渲染，坐标与 Isaac Sim 一致。

---

## M3：回写功能

### 目标

美术在 UE 里调整物体位置后，能写回 Nexus。

### Task M3-1：变更检测

扫描 Level 中带 `ontology_instance_id` Tag 的 Actor，对比当前位置和 Tag 里记录的原始位置。

### Task M3-2：回写 UI

UE 菜单加"回写位置修改"按钮：
- 弹窗展示变更列表
- 用户确认后调用 `POST /api/v3/lite/scenes/{id}/placements/update`

### Task M3-3：后端响应

后端更新 `lite_instances` 表的 translation / rotation / scale 字段。

**M3 完成标准**：UE 里拖一个箱子 → 回写 → Nexus 里坐标更新 → 重新导出 USD → 新位置生效。

---

## M4：训练剧本 + 交付

### Task M4-1：写训练剧本

**文件**：`docs/TRAINING_BRIEF.md`

内容参考 `PROJECT_BRIEF.md` 第四节的"业务场景"。

### Task M4-2：整理交付包

给训练同事一个 zip：
- `warehouse_demo_v1.usda`
- 所有引用的 `*.usd`（资产库）
- `TRAINING_BRIEF.md`
- `README.md`（如何加载、注意事项）

### Task M4-3：联调

与训练同事一起试跑一次 Isaac Lab 训练，确认：
- USD 加载成功
- 物理行为合理（箱子不穿模、不爆炸）
- 分拣规则能实现
- 有问题的话，快速迭代 USD

**M4 完成标准**：训练同事能独立跑通一次抓取训练。

---

## 每个任务块的推进方式

### 1. 开始任务前

Claude Code 要：
1. 明确当前任务编号（如 "现在做 Task M1-3"）
2. 陈述即将产出的文件列表
3. 如果有疑问（接口细节、命名、选型），**先问清楚再开工**

### 2. 任务进行中

- 小步快跑：一次写 1-2 个文件，不要一次写 10 个
- 关键点停下来等用户验证

### 3. 任务完成

- 给出验证命令（如"运行 `python test_xxx.py` 看输出"）
- 列出下一步候选任务，让用户决定走哪个

---

## 里程碑检查点

每个 M 阶段完成时，用户要做一次验证：

### M0 验证清单

- [ ] `python backend/lite/tests/test_hardcoded_export.py` 无报错
- [ ] `exports/hardcoded_demo.usda` 文件存在且大小 > 0
- [ ] 用 `type exports/hardcoded_demo.usda`（Windows）或任意文本编辑器打开，能看到 USD 文本
- [ ] 结构包含：1 机器人 + 2 货架 + 3 箱子
- [ ] 训练同事反馈：Isaac Sim 能加载

### M1 验证清单

- [ ] 数据库 `lite.db` 创建成功
- [ ] 5 张表结构正确
- [ ] 所有 API 能 curl 调用成功
- [ ] 前端 `/scenes` 页面打开无报错
- [ ] 端到端：前端点导出 → 下载 → usdview 打开 OK

### M2 验证清单

- [ ] UE 项目能启动
- [ ] 导入 USD 无报错
- [ ] 通过脚本能从 Nexus 拉数据并摆放 Actor
- [ ] 坐标位置和 Isaac Sim 一致

### M3 验证清单

- [ ] UE 里拖动物体 → 回写 → 数据库更新
- [ ] 重新导出 USD → 新位置生效

### M4 验证清单

- [ ] 训练同事能独立跑通一次训练
- [ ] 训练剧本清晰完整

---

## 紧急止损规则

如果某个任务卡住超过 1 小时（调试 bug、API 不通等），按以下顺序操作：

1. 记录卡点，暂停当前任务
2. 退一步：跳过该任务，做下一个不依赖它的
3. 汇总问题向用户求助
4. 如果是方向性问题（比如发现方案不通），立刻开 "架构调整" 讨论

**绝对不要**在一个 bug 上死磕超过 2 小时而不汇报。
