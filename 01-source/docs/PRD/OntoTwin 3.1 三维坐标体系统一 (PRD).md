# OntoTwin 3.1 — 三维坐标体系统一（PRD）

> 版本：3.1
> 依据：同目录《3.1 三维坐标体系统一（设计草案）》+ /grill-me 决策（2026-06-23）
> 适用：单人开发，不过度工程化。前端走 CDN、改动前过 `ontotwin-ui`。
> 本 PRD 重点：细化各功能点 + 按「后端 / 前端 / 数据 / 联调」拆分到具体文件函数。

---

## 1. 概述

让 ontotwin 持有中立的**规范坐标系（mm）**作为空间事实来源；CAD 等源经"源→规范"变换汇入；UE 坐标由"规范→UE"变换派生。解决：顶视朝向对不上（打点脑内旋转）、原点不可定义、多源无统一汇合、坐标映射裸奔。

模型与变换链见设计草案 §2。本 PRD 不重复，直接进功能点与实施。

---

## 2. 名词

| 词 | 含义 |
|---|---|
| 规范坐标系 (canonical frame) | 项目级中立坐标系，mm，2D + 楼层 Z，原点由 ontotwin 声明 |
| 帧 (frame) | 一个外部坐标源 + 它到规范系的仿射变换。CAD 是第一个具体帧 |
| 空间剖面 (spatial_profile) | 项目的规范系定义 + 规范→UE 声明 + 楼层表 |
| 源→规范 / 规范→UE | 两段仿射变换；前者每帧一个，后者每项目一个 |
| 派生缓存 | UE 厘米坐标，由规范坐标算出，存入 component.ue_xy / instance.raw_state.translation |

---

## 3. 功能点清单（细化）

### FR-1 项目空间剖面
- **描述**：每个项目声明 `unit=mm`、规范原点、规范→UE 变换、楼层表。
- **行为**：新建项目时给默认剖面（恒等朝向、原点 0、单层）；可读可改；改动后触发 FR-8 全场重算。
- **验收**：剖面持久化进项目文件；重启不丢；切项目隔离。

### FR-2 通用帧注册表
- **描述**：项目维护一组帧；CAD 帧由标定生成；预留 `kind=external`（海康等本版不写实现）。
- **行为**：列帧 / 建帧 / 标定帧（FR-?）。每帧存 `to_canonical` 仿射 + unit + floor + map_code(可空)。
- **验收**：CAD 标定后能在帧列表看到 `frame_cad` 及其矩阵。

### FR-3 规范坐标存储（事实来源）
- **描述**：component 存 `canonical_xy(mm)` + `frame_id` + `floor` + `source_xy`(留痕)；`ue_xy` 降为派生缓存。instance 的 `raw_state.translation_*` 同为派生缓存。
- **行为**：标定保存构件时，先 `源→规范` 得 canonical，再 `规范→UE` 派生 ue。
- **验收**：改规范→UE 后，重算出的 ue 与新朝向一致；canonical 不变。

### FR-4 规范→UE 朝向显式声明 + 实时预览
- **描述**：剖面里以 `axis_map / flip / rotation_deg / ue_origin_cm / scale_to_cm` 显式声明朝向，不靠锚点撞。
- **行为**：UI 改任一参数 → 调 `/spatial/preview` → 画布/坐标实时刷新。支持先粗选(90°/翻转)再精调。
- **验收**：同一组 canonical 坐标，改 rotation 90° 后导出的 UE 坐标按预期旋转。

### FR-5 标定画布按朝向自动转向（核心 UX，消"打点脑内旋转"）
- **描述**：标定画布按当前 `ue_transform` 把 CAD 显示**转到与 UE 顶视图一致的朝向**（纯显示变换，不改 canonical 数据）。
- **行为**：声明朝向后，画布即时转向；打点所见即所得，无需脑内旋转。
- **验收**：声明"转90°+翻转"后，画布上设备的相对方位与 UE 顶视图一致。

### FR-6 楼层 → Z 映射表
- **描述**：剖面 `floor_table`：`楼层 ↔ z_base_mm ↔ ue_level ↔ map_codes[]`。
- **行为**：构件/实例带 `floor`；派生 UE 时 `z = z_base_mm × 0.1`。
- **验收**：2 层构件的 UE Z 等于其层高换算值。

### FR-7 单实例微调入口
- **描述**：对已铸造实例，可在 ontotwin 改其规范坐标/朝向数值（UE 端手动拖是临时的，会被轮询覆盖）。
- **行为**：实例运维（或绑定台）提供一个"位置微调"小弹窗，改 canonical_xy / rotation → 重派生 → 下一轮快照生效。
- **验收**：改某实例坐标后，UE 中该实例移动到新位置且持久。

### FR-8 改一处，全场重算
- **描述**：`spatial_profile.ue_transform` 或 `floor_table` 变更后，重算所有 component/instance 的派生 UE 坐标。
- **行为**：profile 写入后触发批量重派生 + 重新对齐 instances。
- **验收**：改朝向一次，全场实例在 UE 下一轮轮询整体转正。

### FR-9（留接口，不实现）外部帧 / 反算
- **描述**：通用帧抽象支持 `kind=external` 与"填参标定"；变换矩阵保留求逆能力（将来向外部系反下发坐标）。
- **行为**：本版仅保证数据结构与变换层能容纳，不接任何实时外部源。

---

## 4. 数据结构变更（ProjectStore）

> 涉及存储结构变更，已获用户同意。向后兼容：缺字段按默认；旧数据靠重导 CAD 迁移。

```jsonc
Project {
  "spatial_profile": {
    "unit": "mm",
    "canonical_origin": [0,0],
    "ue_transform": { "axis_map": {"x":"+x","y":"-y"}, "flip": false,
                      "rotation_deg": 0, "ue_origin_cm": [0,0], "scale_to_cm": 0.1 },
    "floor_table": [ {"floor":1,"z_base_mm":0,"ue_level":"",  "map_codes":[]} ]
  },
  "frames": [ {"id":"frame_cad","name":"CAD 图纸","kind":"cad","unit":"mm",
               "to_canonical":{"method":"anchor","matrix":[[a,b,tx],[c,d,ty]]},
               "floor":1,"map_code":null} ],
  "components": { "cmp_x": {
      "frame_id":"frame_cad","canonical_xy":[x,y],"floor":1,
      "source_xy":[..],"ue_xy":[..],   // ue_xy 现为派生缓存
      /* …object_type_rid/attribs/asset_path/bound_instance_id… */ } }
  // instances.raw_state.translation_* 为派生缓存
}
```

---

## 5. 变换规格

- **源→规范**（每帧）：`p_canon = M_src→canon · p_src`。CAD 情形下，规范系即 CAD mm 帧，`M` 可退化为原点平移（canonical_xy = source_xy − canonical_origin）。
- **规范→UE**（每项目）：`R(axis_map,flip,rotation)` 构成 2×2 朝向阵；`p_ue_cm = R · p_canon_mm × scale_to_cm + ue_origin_cm`；`z_ue = floor.z_base_mm × scale_to_cm`。
- **求逆**：各矩阵可逆，供 FR-9 反算（本版仅保留能力）。

> ✅ 标定 UX（已定）：**锚点仍承担精确拟合**。分工 = 显式声明定**粗朝向 + 画布转向**（解打点脑内旋转），锚点拟合定**精确旋转/平移/尺度**。即：声明给出 90°/翻转级的粗对齐并驱动画布显示；锚点最小二乘在此基础上拟合出"规范→UE"的精确仿射。两者叠加为最终 `ue_transform`。

---

## 6. 分步实施计划（按层 + 具体文件函数）

### 阶段 A — 后端：数据结构与变换层

**A1. `backend/project_store.py`**
- Project 默认结构新增 `spatial_profile`、`frames`（`create_project` / `_default_*` 补默认值）。
- 新增方法：`get/set_spatial_profile()`、`list_frames/upsert_frame()`。
- `component` 记录新增 `canonical_xy / frame_id / floor`（`set_components` 接收）。
- `mint_instances()`（现 L426）：实例初始 `pos` 改为「派生 UE」+ `z = floor.z_base × 0.1`，不再直接用 `comp.ue_xy`（或令 ue_xy 始终是最新派生值）。
- 新增 `rederive_ue()`：遍历 components，按 `spatial_profile` 重算 `ue_xy`（FR-8）。

**A2. `backend/coord_transform.py`**
- 新增 `build_ue_matrix(profile)`：由 axis_map/flip/rotation/scale/origin 构 2×3 矩阵。
- 新增 `canonical_to_ue(profile, xy, floor)` → `[x_cm, y_cm, z_cm]`。
- 新增 `invert_affine(m)`（FR-9 备用）。
- 保留现有 `calibrate / apply_transform`（用于"源→规范"锚点拟合）。

**A3. `backend/app.py`**
- 新路由：`GET/PUT /api/v2/spatial/profile`、`GET/POST /api/v2/spatial/frames`、`POST /api/v2/spatial/frames/<id>/calibrate`、`POST /api/v2/spatial/preview`。
- `coord_save_components`（现 L761）：先存 `canonical_xy`（CAD→规范），再 `canonical_to_ue` 派生 `ue_xy`；写 `frame_id/floor`。
- `_build_snapshot`（现 L1558）I3D_Spatial：`translation_z` 取楼层派生值（现恒 0）。
- PUT profile 后调用 `project_store.rederive_ue()` + `mint_instances()`（FR-8）。
- 路由注册 `/spatial`（若需页面，另加 serve 路由）。

### 阶段 B — 前端：标定画布 + 空间剖面

**B1. `frontend/coord_workbench.html`（主改）**
- 标定步骤新增**「朝向/原点」声明面板**：axis_map 下拉、翻转开关、旋转 0/90/180/270 + 微调、UE 原点。
- **画布按声明自动转向显示**（FR-5）：`draw()` 前对显示坐标套一层"规范→UE 朝向"显示变换；改参数即时重绘。
- 改参数 → 调 `/spatial/preview` 实时预览（或前端本地同算）。
- 锚点语义按 §5 待确认项落定后微调。
- 过 `ontotwin-ui`：面板用既有 token / 控件，无 emoji。

**B2. 单实例微调入口（FR-7）**
- 落点（已定）：`frontend/instance.html` 实例行加"微调位置"小弹窗。
- 改 canonical_xy / rotation → `PUT /api/v2/instances/<id>/transform` → 重派生 → 下一轮快照生效。

**B3. 空间剖面落点**
- 剖面声明 UI 建议内嵌在 coord_workbench 标定步骤（就近预览），不另起页面；楼层表作为剖面里的小表格。

### 阶段 C — 数据迁移
- 现场若无不可重导数据：**重导一次 CAD** 即完成迁移（零脚本）。
- 若有：写一次性 `backfill` 脚本，把旧 instance 的 UE 坐标按现矩阵反算成 canonical 回填。

### 阶段 D — UE 侧
- **无改动**（B1）。仅确认快照 `translation_z` 带楼层值后，UE 落点正确。

### 阶段 E — 联调验收
导入 → 声明朝向（画布转正、打点 1:1）→ 标定 → 保存构件（canonical+派生 ue）→ 绑定铸造 → UE 朝向正确 → 改朝向一次确认全场重算 → 单实例微调确认持久。

---

## 7. API 详表

| 方法 | 路径 | 入/出 |
|---|---|---|
| GET | `/api/v2/spatial/profile` | 出：当前项目 spatial_profile |
| PUT | `/api/v2/spatial/profile` | 入：profile；副作用：rederive + remint |
| GET | `/api/v2/spatial/frames` | 出：frames[] |
| POST | `/api/v2/spatial/frames` | 入：帧定义 |
| POST | `/api/v2/spatial/frames/<id>/calibrate` | 入：anchors[] 或 params；出：to_canonical 矩阵 |
| POST | `/api/v2/spatial/preview` | 入：源/规范坐标 + profile；出：规范 + UE 坐标 |
| PUT | `/api/v2/instances/<id>/transform` | 入：canonical_xy/rotation（FR-7）|

---

## 8. 本版边界

**做**：FR-1 ~ FR-8。
**不做（留接口）**：FR-9 外部源实时接入/专属逻辑、状态模型形式化、UE 根 Actor(B2)、白皮书/Skill。

---

## 9. 待确认 / 现场核实

- ~~§5 标定 UX：锚点新角色~~ ✅ 已定：锚点仍承担精确拟合（声明定粗朝向+画布转向，锚点定精确旋转/平移）。
- ~~FR-7 微调入口落点~~ ✅ 已定：`instance.html`。
- CAD↔UE 确切轴对应（每项目声明值，现场比一次）。
- 外部源（海康为例）尺度/mapCode 粒度/原点/朝向 → `docs/坐标体系 - 海康等外部源待核实项.md`。
- 现场是否有不可重导数据（决定阶段 C 是否需脚本）。

---

## 10. 验收清单

- [ ] 空间剖面可声明、持久化、切项目隔离。
- [ ] 标定画布按朝向声明自动转向，打点无需脑内旋转。
- [ ] 改朝向参数实时预览；改一次全场实例在 UE 整体转正。
- [ ] 构件存 canonical 坐标，UE 坐标为派生；重算朝向后 canonical 不变。
- [ ] 楼层 Z 生效（多层构件 UE Z 正确）。
- [ ] 单实例微调持久（不被轮询覆盖）。
- [ ] UE 侧零改动即正确显示。
- [ ] 全程遵循 `ontotwin-ui`。

---

*文档版本 v1 · 待确认（尤其 §9 标定 UX）后进入开发。*
