# OntoTwin 3.4.3.1 UE 关卡字段清理补丁（PRD）

> 版本：3.4.3.1（小功能补充）
> 编号：OPT-10
> 日期：2026-11-26（第 2 版：吸收代码评审意见，见第 4 节）
> 状态：需求已和产品确认，**未开发**
> 前置版本：3.4 UE同步数据库与场景管理升级、3.4.3 分区目录与新建交互、3.2.1 楼层空间高度配置补丁、CAD空间底图草稿与发布补丁
> 来源：4.7 场景演出 grill 讨论（决定 D8）。总体编号与顺序见 `OntoTwin 4.7 场景演出：关卡切换·环境灯光·摆放的灯·天气 (PRD).md` 第 0.1 节
> 改动范围：前端、后台、UE 插件（一处比对规则）；不改数据库结构

---

## 1. 背景

3.4 引入了场景级绑定以后，一个数据集只能绑一张 UE 地图，一张地图也只能绑一个数据集（`db/schema.sql` 中 `project_scene_binding` 的两条唯一约束）。但网页上还有三处让人手填"UE 关卡路径"，其中一处还是硬门槛：

| 字段 | 位置 | 现状 |
|---|---|---|
| 区域「UE Level」 | `frontend/instance.html` 约 L722-737，新建/编辑区域 →「高级设置」，界面自注"当前仅登记路径，不自动启用关卡流送" | 不生效。只存进数据库 `zone.ue_level`，没有任何地方读取 |
| 底图「绑定的 UE 场景地图」 | `frontend/coord_workbench.html` L531（CAD 底图）、L694（图片底图） | **生效且是硬门槛**：`backend/spatial_assets/service.py` 约 L521 不填不让发布；`backend/scene_interaction/routes.py` 约 L202 校验；UE 端 `TwinInteractionManagerComponent.cpp` 的 `IsRuntimeRouteForCurrentLevel`（约 L1299）要求它和当前地图路径**一字不差、大小写相同**，否则漫游路线不出现，而且不报错 |
| 楼层表 `ue_level` | `backend/floor_profile_service.py` L111、L283，`backend/project_store.py` L349 | 不生效。界面上没有入口，只是写一个空的默认值 |

数据集本来就知道自己绑在哪张地图上，让人再手填一遍既多余又容易填错。

## 2. 要做的

### 2.1 先说清楚"地图"存的是什么

UE 告诉后台"我是哪张地图"时，发的是**场景编号**（请求头 `X-OntoTwin-UE-Scene-Id`），默认等于地图包路径（如 `/Game/StandardScenes/Maps/Factory`），也可以在关卡里手动指定成别的（如 `standard.factory`）。后台把它存在 `ue_scene.stable_key`。

`ue_scene.level_path` **不可靠，本条不用它**：网页绑定弹窗（`frontend/scene_binding.js` 约 L49）把场景编号原样写进了 `level_path`，旧的绑定代码（`app.py` 约 L4262）插入时根本没写。

### 2.2 UE 端：路线的地图"两种都认"（产品决定 2026-11-26）

`TwinInteractionManagerComponent.cpp` 的 `IsRuntimeRouteForCurrentLevel`（约 L1299）现在只认"和当前地图包路径一字不差"。改为：路线记录的地图等于**当前地图包路径**，或者等于**当前关卡的场景编号**（`ATwinSceneManager` 的 `EnsureSceneId()` 结果），任一相同就算对上。两边都先经过现有的 `NormalizeLevelPackageName` 规范化（处理 `/Game/A.A` 和 `/Game/A` 这类写法差异）。

这样老底图里手填的地图路径照样能用，新底图自动填的场景编号也能用，已有数据不需要迁移。

### 2.3 区域

- 「高级设置」折叠栏里只有「UE Level」一个字段，**整个折叠栏一起隐藏**，不留空框。
- 数据库 `zone.ue_level`、`zone.streaming` **保留**，已存的值不删。
- **防止旧值被抹掉**：`zone_management/service.py` 的 `save_catalog` 是整份覆写，现在前端不传 `ue_level` 时会存成空串（约 L161）。改为：请求里**没有**这两个键时，沿用库里这个区域原来的值；新建区域为空。

### 2.4 底图

- 「绑定的 UE 场景地图」输入框改为**只读显示**（`coord_workbench.html` L531 CAD 底图、L694 图片底图）。
- 后台**不再接受前端传来的 `ue_level`**，统一按下面的规则填写（`spatial_assets/service.py` 新建 L150、L199，修改 L329、L412）：
  - 底图的 `ue_level` 为空（新建的底图，或历史上没填过）→ 填当前数据集生效绑定的场景编号（`project_scene_binding` 中 `status='active'` 那条对应的 `ue_scene.stable_key`）。
  - 底图已经有值 → **保持原值不动**。原因：`ue_level` 算在底图的标定指纹（`calibration_fingerprint`，约 L524-533）里，改了它，已关联的漫游路线会全部变成"待复核"停用。有了 2.2 的"两种都认"，老值不用改也能用。
- 发布（约 L521）：数据集没有生效的绑定时，提示"当前数据集尚未绑定 UE 关卡，请先绑定"，替换现在的"发布前必须填写绑定的 UE Level"。
- 换绑到另一张地图后的处理，沿用 NEW-06 已定的规则：换绑时加新底图，旧路线停用、待复核。本条不改这部分。
- `scene_interaction/routes.py` 约 L202 的一致性检查（"空间底图缺少运行关卡绑定"）保留。按上面的规则发布过的底图一定有值。

### 2.5 楼层表

`floor_table[].ue_level` 界面上没有入口，也没有地方读取。以下写入点都去掉，已存的数据不动：

- `floor_profile_service.py` L111、L283，`project_store.py` L349（写空的默认值）；
- `spatial_assets/service.py` L569（图片底图发布时抄写）、L655-656（CAD 底图发布时抄写）。

## 3. 验收清单

- [ ] 新建、编辑区域时看不到「高级设置」；改一个已有区域的名称后保存，数据库里它的 `ue_level`、`streaming` 不变。
- [ ] 坐标工作台的底图上，「绑定的 UE 场景地图」显示为只读；新建底图后显示当前绑定的场景编号。
- [ ] 不填任何关卡路径也能发布底图；发布后在 UE 里漫游路线正常出现。**分别用默认场景编号（地图路径）的工程和自定义场景编号（如标准工程 `standard.factory`）的工程各验一次。**
- [ ] 升级前已发布的底图：升级后原 `ue_level` 和标定指纹都不变，已有漫游路线照常出现，没有变成"待复核"。
- [ ] 未绑定 UE 关卡的数据集发布底图时，给出明确提示。
- [ ] 发布底图后，楼层表里不再新写 `ue_level`。
- [ ] 后台全量测试通过；新增测试覆盖：自动带出、忽略前端传值、已有值不被覆盖、未绑定时拒绝、区域保存时继承旧值。
- [ ] 网页部分发布到 5501（`python 01-source/tools/publish_5501.py --task OPT-10`），由产品验收；UE 端"两种都认"在 5501 上看不出来，用打包好的 UE 程序验收。

## 4. 评审修订记录（2026-11-26，第 2 版）

| 评审意见 | 处理 |
|---|---|
| 自动填 `ue_scene.level_path` 不可行：里面存的可能是场景编号或空值，UE 端一字不差比对会让自定义场景编号工程的漫游路线全部消失、且不报错 | 改用场景编号（`stable_key`）；UE 端改为"地图路径或场景编号任一相同"（2.1、2.2） |
| 楼层表漏了底图发布时的两处写入 | 补上（2.5） |
| 隐藏输入框后，区域整份覆写会抹掉旧的 `ue_level` | 后台缺键时继承旧值；整个折叠栏隐藏（2.3） |
| 自动替换会改变标定指纹，让漫游路线变成"待复核" | 已有值一律不动，只填空值（2.4） |
