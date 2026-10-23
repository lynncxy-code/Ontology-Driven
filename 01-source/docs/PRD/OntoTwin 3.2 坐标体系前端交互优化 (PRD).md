# OntoTwin 3.2 — 坐标体系前端交互优化（PRD）

> 版本：3.2
> 依据：3.1 坐标体系（规范坐标系 + 通用帧 + 变换链）+ /grill-me 决策（2026-06-24）
> 本轮范围：P1 原点 + P2 多坐标联动面板 + P3 标定映射源；P4 多楼层结构顺延。
> 适用：单人开发，不过度工程化。前端改动前过 `ontotwin-ui`。

---

## 1. 背景

3.1 让 ontotwin 成为"空间事实来源"（规范坐标系 mm）。但对客户端，坐标单位仍易混（规范 mm / UE cm / 第三方 mm），且：
- 标定只能 CAD→UE，无法标定其它坐标源；
- 单实例位置调整不直观（散落在 Override，且只改 UE、会被重算覆盖）；
- 坐标原点无 UI、且 origin≠0 时有变换组合 bug。

3.2 把"多帧现实"暴露到前端，并补齐原点。

---

## 2. 名词

| 词 | 含义 |
|---|---|
| 规范坐标系 canonical | 项目级中立系，mm，建筑原点，**唯一事实来源** |
| 帧 / 坐标源 frame | 一个坐标系 + 它与规范系的可逆变换。UE 是内置帧；其余为**自定义源**（不绑定具体厂商，用户自命名） |
| 锚点 anchor | 一个 CAD 点 + 各帧读数：`{cadXY, readings:{frameId:[x,y]}}` |
| 规范原点 | 规范坐标的基准点（CAD 坐标系内的一个点）；全楼一个 |

---

## 3. /grill-me 已决策（2026-06-24）

1. **标定 = "CAD 点 → 选定目标帧"**：会话级「映射目标」选择器（UE 默认 / 自定义源 / + 新建源）；产出 CAD→该帧 变换。
2. **锚点模型升级**：`{cadXY(共享), readings:{frameId:[x,y]}}`。加新帧**继承已打的 CAD 点**，只填新帧那列读数。
3. **原点全局**：一建筑一原点；画布点选 + 数值微调；语义 = 规范坐标基准（cad−origin）；**不改 UE**（组合修正）。
4. **同坐标系多楼层**：各层来自同一张 CAD（按图层拆），坐标系一致 → 原点定义一次全楼通用；**一建筑 = 一 Project，楼层 = 图层标签**（P4 才落地结构，本轮原点先单楼可用）。
5. **多坐标联动面板**：行 = 帧，只显示已标定帧，改任一帧经规范联动，**保存只写规范**。字段含各帧 X/Y + 楼层 + 朝向 + **Z（可改，楼层基准默认，切层重置到新层基准）**。
6. **Override 瘦身**：移除 translation/rotation，只留 材质/动画/特效/显隐。
7. 第三方帧统称**「自定义源」**，不硬编码海康。

---

## 4. 数据结构变更

```jsonc
// 锚点（前端 State，标定用）
anchor = { cadXY:[x,y], readings: { "ue":[x,y], "src_xxx":[x,y] } }

// 构件（新增 canonical_z）
component = { …, canonical_xy:[x,y], canonical_z: <mm，默认楼层 z_base，可改>, floor, ue_xy, ue_z }

// spatial_profile
spatial_profile = {
  unit:"mm",
  canonical_origin:[x,y],          // ★本轮启用 UI；规范坐标 = cad − origin
  ue_transform:{ display:{…}, matrix:<canonical→UE 仿射>, scale_to_cm:0.1, … },
  floor_table:[…],
}

// frames（自定义源；UE 仍在 ue_transform，自定义源在此）
frame = {
  id:"src_xxx", name:"<用户命名>", kind:"custom", unit:"mm",
  from_canonical: <canonical→该源 仿射>,   // 显示该源坐标用；编辑时用其逆
}
```

> 关键修正：**变换一律基于"规范坐标"拟合/应用**。标定时锚点 src 取 `cadXY − origin`（= 规范坐标），故拟合出的矩阵天然是"规范→帧"，应用时 `帧 = M·规范` 无需再补偿，根除 origin≠0 偏移 bug。

---

## 5. 变换与联动（多坐标面板核心）

- 某实例的规范坐标 `(cx, cy, cz)`（来自其绑定构件）。
- 每个已标定帧 F：`F坐标 = M_{规范→F} · (cx,cy)`（UE 还含 z=cz×scale；自定义源多为 2D）。
- **编辑联动**：用户改 F 帧某值 → `规范 = M_{规范→F}⁻¹ · F值` → 再算其余帧。正在输入的栏不回写，其余防抖刷新，显示端 round。
- **保存**：只写 `canonical_xy / canonical_z / rotation / floor`；其余皆派生。

---

## 6. 分步实施（按层 + 文件）

### P1 — 原点 + canonical_z + 组合修正

**后端**
- `coord_transform.py` / `app.py`：标定与 `save_components` 改为**对规范坐标(cad−origin)拟合/应用**；`canonical_to_ue` z 改用 `component.canonical_z`（而非纯楼层查表，楼层只作默认值）。
- `project_store.py`：component 加 `canonical_z`（新建/换楼层默认 = 楼层 z_base）。
- `app.py`：`PUT /spatial/profile` 已触发 `_rederive_components`，确认改 origin 后全场重算正确。

**前端 `coord_workbench.html`**
- 标定页加「设为规范原点」：进入点选模式 → 画布点一下设为 origin（存 CAD 坐标）+ 数值框可微调；画布画原点标记。
- 改 origin → PUT profile → 重绘 + 重算。

### P2 — 多坐标联动面板 + Override 瘦身

**后端 `app.py`**
- `GET /instances/<id>/transform`：返回 `canonical_xy / canonical_z / floor / rotation / ue(xyz) / frames:[{id,name,unit,xy}]`（自定义源坐标 = `M_{规范→源}·规范`）。
- `PUT /instances/<id>/transform`：接收 `canonical_xy / canonical_z / rotation / floor`（前端已折算成规范）→ 重派生。

**前端 `instance.html`**
- 「微调位置」升级为「位置编辑（多坐标）」面板：行=帧（规范 / UE / 各已标定自定义源），X/Y 可编辑，楼层下拉、朝向、Z（规范/UE，可改）。
- 联动换算：前端拉 `/spatial/profile` + `/spatial/frames` 得各矩阵，本地正/逆算（或调 `/spatial/preview`）。
- **Override 面板移除 translation/rotation**，仅留材质/动画/特效/显隐。先核查 batch 流程未依赖 translation override。

### P3 — 标定「映射目标」+ 锚点 readings 模型

**前端 `coord_workbench.html`（动标定主干，最谨慎）**
- 锚点 State：`{cadXY, ueXY}` → `{cadXY, readings:{}}`；存取/恢复/渲染/导出同步改。
- 标定页加「映射目标」选择器：`UE`（默认）/ 各自定义源 / `+ 新建源`（输入名称、单位，建 frame）。
- 当前目标决定锚点编辑哪一列读数；切目标 = CAD 点保留、读数列切换。
- 「计算变换」：用"填了当前目标读数"的锚点（src=cadXY−origin）拟合 → UE 写 `ue_transform.matrix`；自定义源写 `frame.from_canonical`（经 `POST /spatial/frames/<id>/calibrate`）。

**后端 `app.py`**
- `/spatial/frames/<id>/calibrate`：锚点 src 用规范坐标；产出 `from_canonical`（及其逆供编辑）。UE 标定沿用 save_components/ue_transform 一致化。

### 数据兼容
- 旧锚点 `{cadXY, ueXY}` → 迁移读取时归一成 `readings:{ue:ueXY}`。
- 旧构件无 `canonical_z` → 默认楼层 z_base 回填。
- 现状数据可重导，迁移成本低。

### UE 侧
- 无改动（仍 B1：后端派生 UE 绝对坐标）。

### 联调
导入 → 设原点 → 标 UE → 切「新建源」标自定义源（复用 CAD 点）→ 保存构件 → 绑定铸造 → 实例运维「位置编辑」三列联动、改任一列存规范 → UE 正确。

---

## 7. 本轮边界

**做**：P1 + P2 + P3。
**顺延**：P4 多楼层结构（一建筑一 Project / save_components 按楼层合并 / 图层→楼层映射）、外部源实时数据接入、状态模型形式化、UE 根 Actor。

---

## 8. 验收要点

- [ ] 画布点选设原点；origin≠0 时 UE 不偏移（组合修正生效）。
- [ ] 标定页可切「映射目标」：先标 UE，再「新建源」标第二帧，CAD 点继承、只填新读数。
- [ ] 实例运维「位置编辑」显示 规范/UE/已标定源 三列，改任一列其余联动，保存只写规范。
- [ ] Z 可改、切楼层重置到该层基准。
- [ ] Override 仅剩材质/动画/特效/显隐。
- [ ] 全程遵循 `ontotwin-ui`；JS `node --check` 通过。

---

## 9. 风险

- P3 改锚点数据结构，牵动标定保存/恢复/导出多处——最后做、隔离验证。
- 多坐标联动浮点抖动——"只刷新别的栏 + round"规避。
- Override 移除位移——先确认 batch 不依赖。

---

*文档版本 v1 · 待确认后进入开发。*
