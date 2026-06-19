# OntoTwin 2.9.2.1 画布标定精准对齐辅助需求说明书 (PRD)

> **文档定位：** 在 PRD 2.9 坐标标定工作台基础上，增强画布标定/标注操作的精准对齐能力。
>
> **开发顺序：** 本模块为独立增量优化，不改变 2.9 / 2.9.1 / 2.9.2 的数据结构和 API，仅改动 `coord_workbench.html` 前端。

---

## 1. 产品背景

### 1.1 问题描述

当前坐标标定工作台的画布操作中，用户需要在三个场景下进行**精确点击定位**：

| 场景 | 模式 | 步骤 | 操作描述 |
| :--- | :--- | :--- | :--- |
| **CAD 锚点标定** | CAD 模式 | ③ 标定 | 点击 DXF 图纸上已知坐标的位置，放置锚点 |
| **图片锚点标定** | 图片模式 | ① 标定 | 点击图片上已知位置，放置锚点 |
| **图片设备标注** | 图片模式 | ② 标注 | 点击图片上的设备位置，放置标注点 |

**用户反馈的核心痛点：**

1. **网格粒度太粗** — 当前网格最小间距 100 单位（世界坐标），缩放后屏幕上仍然间距较大，无法精确定位到图元交叉点或建筑拐角
2. **无正交约束** — 在同一行/列放置多个标定点时，全靠肉眼对齐，很容易出现微小偏移（Y 不一致导致 RMSE 劣化）
3. **缺少参考线** — 放置第 2+ 个锚点时，没有任何与已有锚点对齐的视觉提示，无法快速判断「是否在同一条线上」

### 1.2 解决方案概述

引入三个互补的精准对齐辅助功能：

```
┌────────────────────────────────────────────────────────────┐
│ ① 细化网格           → 解决"网格太粗，没有可参考的刻度"   │
│ ② 强制正交（Ortho）  → 解决"多个点无法保证水平/垂直对齐"  │
│ ③ 智能对齐线（Snap） → 解决"新点无法快速对齐已有点"       │
│    + 网格吸附                                              │
└────────────────────────────────────────────────────────────┘
```

三者可同时启用，在工作台画布顶部提供**辅助工具栏**统一控制。

---

## 2. 核心功能详细设计

### 2.1 功能①：细化网格

#### 2.1.1 当前实现分析

现有 `drawGrid()` 函数（[coord_workbench.html:L933](file:///d:/tmp/digital_twin_aircraft/frontend/coord_workbench.html#L933)）的网格间距候选表为：

```javascript
const STEPS = [100, 500, 1000, 2000, 5000, 10000, 20000, 50000, 100000];
```

选择算法为：找到第一个使 `step * camScale >= 60` 的间距。这意味着：
- 屏幕上网格行间距永远 ≥ 60px
- 最小世界坐标间距为 100 单位，无法进一步细分

#### 2.1.2 改进方案

**扩展间距候选表，增加更细粒度的选项：**

```javascript
const STEPS = [10, 25, 50, 100, 250, 500, 1000, 2000, 5000, 10000, 20000, 50000, 100000];
```

**调整选择阈值，允许更密的网格：**

将阈值从 60px 降至 **40px**（网格可以更密但不至于过密）：

```javascript
let step = STEPS.find(s => s * camScale >= 40) || STEPS[STEPS.length - 1];
```

**视觉层次增强**：

| 网格层级 | 条件 | 线条样式 | 标注 |
| :--- | :--- | :--- | :--- |
| **主网格线** | `wx % (step * 5) === 0` | `rgba(120,130,150, 0.22)` 1px | 显示坐标值 |
| **次网格线** | 其余 | `rgba(120,130,150, 0.10)` 0.5px | 不显示 |
| **细分网格线**（新增） | 当 `step <= 50` 且缩放 > 0.5 时，在两条次网格线之间画 `step/5` 间距的点状虚线 | `rgba(120,130,150, 0.06)` 0.5px dotted | 不显示 |

> **性能保护**：当屏幕上可见网格线超过 200 条时，自动跳到更大的间距，避免渲染卡顿。

#### 2.1.3 交互效果

- 用户放大到局部区域时（如 camScale > 0.5），网格自动细化到 10~25 的间距
- 配合网格吸附（§2.4），用户可以将标定点精确放置在 10 单位整数倍坐标上
- 缩小到全图时，自动退回到 1000~5000 的间距，不影响全局预览

---

### 2.2 功能②：强制正交（Ortho Lock）

#### 2.2.1 概念

类似 AutoCAD 的 `ORTHO` 模式。启用后，**新放置的点被约束为与上一个点水平或垂直对齐**。

具体规则：当画布中已存在至少 1 个锚点/标注点时，鼠标点击放置新点的坐标将被修正：

```
设上一个点为 P_last = (x0, y0)
鼠标点击位置为 P_click = (mx, my)

如果 |mx - x0| >= |my - y0|:
    → 水平约束: 实际放置 (mx, y0)     // Y 对齐上一点
否则:
    → 垂直约束: 实际放置 (x0, my)     // X 对齐上一点
```

#### 2.2.2 视觉反馈

当 Ortho 模式启用且画布中已有锚点时，**实时**显示约束预览线：

| 元素 | 样式 |
| :--- | :--- |
| 正交引导线 | 从 P_last 到修正后落点的蓝色虚线，`1px dashed #4f7df7` |
| 修正后落点预览 | 蓝色空心圆，`r=6px, stroke=#4f7df7, 1.5px` |
| 约束方向标签 | 在预览圆旁显示 `H` (水平) 或 `V` (垂直)，`10px monospace, #4f7df7` |

#### 2.2.3 触发方式

**双重触发**：
- **全局开关**：画布顶部辅助工具栏的 `Ortho` 按钮（toggle），默认关闭
- **Shift 快捷键**：按住 Shift 临时启用正交（不管开关状态）；如果开关已开，按 Shift 则临时**禁用**（反转逻辑）

| 开关状态 | Shift 未按 | Shift 按下 |
| :--- | :---: | :---: |
| OFF | 自由放置 | **临时正交** |
| ON | 正交约束 | **临时自由** |

#### 2.2.4 "上一个点"的定义

| 模式 | "上一个点"来源 |
| :--- | :--- |
| CAD 模式 ③ 标定 | `State.anchors` 数组最后一个元素的 `cadXY` |
| 图片模式 ① 标定 | `imgState.anchors` 数组最后一个元素的 `pixelXY` |
| 图片模式 ② 标注 | `imgState.markers` 数组最后一个元素的 `pixelXY` |
| 数组为空（第一个点） | 不约束，等同于自由放置 |

---

### 2.3 功能③：智能对齐线（Smart Guides）

#### 2.3.1 概念

当鼠标在画布上移动时，如果当前位置的 X 或 Y 接近已有锚点/标注点的 X 或 Y，则显示一条贯穿画布的对齐参考线，并将坐标吸附到对齐位置。

#### 2.3.2 对齐源

对齐线会参考两类目标：

| 对齐源类型 | 来源 | 颜色 |
| :--- | :--- | :--- |
| **已有锚点/标注点** | 当前步骤对应的点集（`State.anchors` / `imgState.anchors` / `imgState.markers`） | 品红色 `#e040a0` |
| **网格线** | 当前可见的主/次网格线 | 蓝色 `#4f7df7`（仅在网格吸附开启时） |

#### 2.3.3 吸附判定

```
吸附阈值 = 8px (屏幕坐标)

对于鼠标当前屏幕坐标 (sx, sy)：
  遍历所有对齐源的屏幕 X 坐标：
    如果 |sx - sourceX| < 阈值 → X 吸附到 sourceX
  遍历所有对齐源的屏幕 Y 坐标：
    如果 |sy - sourceY| < 阈值 → Y 吸附到 sourceY
```

X 和 Y 独立吸附——可以同时吸附（表现为"十字星"对齐）。

#### 2.3.4 视觉反馈

| 元素 | 样式 | 说明 |
| :--- | :--- | :--- |
| **X 对齐线**（竖线） | 贯穿画布高度，`1px dashed`，颜色取决于对齐源类型 | 表示"X 坐标与某个已有点一致" |
| **Y 对齐线**（横线） | 贯穿画布宽度，`1px dashed`，颜色取决于对齐源类型 | 表示"Y 坐标与某个已有点一致" |
| **吸附圆环** | 在被参考的源点位置画一个高亮外环，`r=12px, stroke=对应颜色, 1px` | 提示"正在对齐到这个点" |
| **距离标注**（可选） | 吸附线上显示两点间距离值，`9px monospace` | 辅助判断间距 |

#### 2.3.5 网格吸附（Snap to Grid）

当网格吸附功能开启时：

```
对于鼠标点击的世界坐标 (wx, wy):
  snapX = round(wx / gridStep) * gridStep
  snapY = round(wy / gridStep) * gridStep
  实际放置坐标 = (snapX, snapY)
```

- `gridStep` 为当前自适应选择的网格间距
- 网格吸附与智能对齐线同时生效时，**对齐线优先级更高**（距离更近时优先吸附到已有点而非网格）

#### 2.3.6 优先级规则

当多个吸附目标同时满足阈值时，按以下优先级选择：

1. **已有锚点/标注点** — 最高优先级（精确对齐已有标定比对齐网格更重要）
2. **主网格线** (step * 5) — 次优先级
3. **次网格线** (step) — 最低优先级

---

### 2.4 辅助工具栏

#### 2.4.1 位置与布局

在画布区域（`.canvas-area`）**顶部**新增一条浮动工具栏，**仅在进入需要打点的步骤时显示**：

```
┌────────────────────────────────────────────────────────────────────┐
│  [⊞ Grid ✓]  [⊕ Snap ✓]  [⟂ Ortho]  │  网格间距: 100  │  吸附: 8px  │
└────────────────────────────────────────────────────────────────────┘
```

#### 2.4.2 工具栏元素

| 按钮/元素 | 功能 | 默认状态 | 快捷键 |
| :--- | :--- | :--- | :--- |
| **Grid** | 显示/隐藏网格 | ✅ 开启 | `G` |
| **Snap** | 网格吸附 + 智能对齐线 | ✅ 开启 | `S` |
| **Ortho** | 正交约束 | ❌ 关闭 | `O` / Shift(临时) |
| 网格间距显示 | 只读，显示当前自适应选出的网格间距值 | — | — |
| 吸附距离显示 | 只读，显示当前吸附阈值（屏幕像素） | — | — |

#### 2.4.3 显示条件

| 模式/步骤 | 是否显示工具栏 |
| :--- | :--- |
| CAD 模式 Step③ 标定 | ✅ |
| 图片模式 Step① 标定 | ✅ |
| 图片模式 Step② 标注 | ✅ |
| 其他步骤 | ❌ 隐藏 |

#### 2.4.4 视觉设计

```css
.canvas-toolbar {
  position: absolute;
  top: 8px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 2px;
  background: rgba(255,255,255,0.92);
  backdrop-filter: blur(6px);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 3px 6px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  z-index: 10;
  font-size: 11px;
  user-select: none;
}

.toolbar-btn {
  padding: 4px 8px;
  border-radius: 5px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
  color: var(--ink-2);
  border: 1px solid transparent;
  background: transparent;
  font-size: 11px;
  font-weight: 500;
  transition: all 0.15s;
}

.toolbar-btn.active {
  background: var(--ink);
  color: var(--on-ink);
  border-color: var(--ink);
}

.toolbar-btn:hover:not(.active) {
  background: var(--bg-3);
  color: var(--ink);
}

.toolbar-sep {
  width: 1px;
  height: 18px;
  background: var(--line-2);
  margin: 0 4px;
}

.toolbar-info {
  font-size: 10px;
  color: var(--ink-3);
  font-family: monospace;
  padding: 0 4px;
}
```

---

## 3. 交互流程详解

### 3.1 典型使用场景：CAD 模式标定

```
用户进入 Step③ 标定
  → 画布顶部出现辅助工具栏（Grid✓ Snap✓ Ortho○）
  → 默认 Snap 开启，网格吸附生效

点击画布放置第 1 个锚点：
  → Snap 生效：坐标吸附到最近的网格交叉点
  → 锚点放置在整数坐标（如 3000, 5000）
  → 状态栏显示 "已吸附: (3000, 5000)"

移动鼠标准备放第 2 个锚点：
  → Smart Guide 生效：
     当鼠标 Y ≈ 5000 时，画出一条品红色水平虚线
     提示"Y 与 #1 锚点对齐"
  → 如果此时按住 Shift 或开启 Ortho：
     坐标被约束为 (mx, 5000) 或 (3000, my)

点击放置第 2 个锚点：
  → 坐标经过吸附 + 正交修正后确定最终位置
  → 状态栏确认最终坐标
```

### 3.2 状态栏增强

底部状态栏（`#canvasInfo`）在启用辅助功能时追加吸附状态显示：

```
缩放: 250% | CAD: (3000, 5010) → 吸附: (3000, 5000) [Y 对齐 #1]
```

| 显示内容 | 条件 |
| :--- | :--- |
| `→ 吸附: (x, y)` | 当 Snap 生效且坐标被修正时 |
| `[Y 对齐 #1]` | 当智能对齐线命中已有锚点时 |
| `[Ortho H]` / `[Ortho V]` | 当正交约束生效时 |
| 不显示额外信息 | Snap/Ortho 均未生效时 |

---

## 4. 鼠标指针（Cursor）增强

### 4.1 十字准星指针

在标定/标注步骤中，将默认的 `crosshair` 光标替换为自定义 Canvas 绘制的**精确十字准星**：

| 状态 | 指针样式 |
| :--- | :--- |
| 默认 | 细线十字准星，中心 3px 间隙，臂长 12px，`1px #333` |
| 吸附生效 | 十字准星变色为蓝色/品红色（取决于吸附源），中心填充小圆点 |
| 正交约束中 | 十字准星 + 在约束方向上绘制延长线 |

> **实现方式**：不使用 CSS cursor，而是通过 `canvas.style.cursor = 'none'` 隐藏原生光标，在 `draw()` 中绘制自定义十字准星。这样可以实现颜色变化和与辅助线的视觉融合。

---

## 5. 系统架构

### 5.1 技术栈

| 层 | 说明 |
| :--- | :--- |
| 前端 | 纯 Canvas + JS，在现有 `coord_workbench.html` 中增改 |
| 后端 | **无改动** — 全部为纯前端视觉与交互优化 |

### 5.2 文件清单

| 文件路径 | 改动类型 | 职责 |
| :--- | :--- | :--- |
| `frontend/coord_workbench.html` | ✏️ 修改 | 新增辅助工具栏 HTML/CSS + 吸附/正交/对齐线 JS 逻辑 |

### 5.3 代码结构新增

```javascript
// ═══ 辅助对齐系统（2.9.2.1） ═══

const AlignAssist = {
  // 开关状态
  gridVisible: true,      // 网格是否显示
  snapEnabled: true,       // 吸附 + 对齐线是否启用
  orthoEnabled: false,     // 正交约束是否启用

  // 配置
  SNAP_THRESHOLD_PX: 8,   // 吸附阈值（屏幕像素）

  // 运行时状态（每帧重算）
  snapResult: null,        // { snappedWX, snappedWY, guides:[], snapInfo:'' }
  orthoResult: null,       // { constrainedWX, constrainedWY, direction:'H'|'V' }

  // 核心方法
  computeSnap(mouseWX, mouseWY, existingPoints, gridStep) { ... },
  computeOrtho(mouseWX, mouseWY, lastPoint) { ... },
  drawGuides(ctx, cw, ch) { ... },
  drawCrosshair(ctx, sx, sy, state) { ... },
  getAdjustedCoord(mouseWX, mouseWY) { ... },  // 综合 snap + ortho 的最终坐标
};
```

### 5.4 改动点索引

| 现有代码位置 | 改动内容 |
| :--- | :--- |
| [drawGrid()](file:///d:/tmp/digital_twin_aircraft/frontend/coord_workbench.html#L933) | 扩展 STEPS 候选表，增加细分网格渲染逻辑 |
| [addAnchor()](file:///d:/tmp/digital_twin_aircraft/frontend/coord_workbench.html#L1937) | 调用 `AlignAssist.getAdjustedCoord()` 修正坐标 |
| [imgAddAnchor()](file:///d:/tmp/digital_twin_aircraft/frontend/coord_workbench.html#L2274) | 同上 |
| [imgAddMarker()](file:///d:/tmp/digital_twin_aircraft/frontend/coord_workbench.html#L2352) | 同上 |
| [canvas mousedown](file:///d:/tmp/digital_twin_aircraft/frontend/coord_workbench.html#L2404) | 在点击时应用最终修正坐标 |
| [canvas mousemove](file:///d:/tmp/digital_twin_aircraft/frontend/coord_workbench.html#L824) | 增加对齐线/正交预览的实时计算与绘制 |
| [draw()](file:///d:/tmp/digital_twin_aircraft/frontend/coord_workbench.html#L1023) | 在绘制尾部增加 `AlignAssist.drawGuides()` + `drawCrosshair()` |
| [_applyStep()](file:///d:/tmp/digital_twin_aircraft/frontend/coord_workbench.html#L1127) | 根据步骤控制工具栏显隐 |
| [updateCanvasInfo()](file:///d:/tmp/digital_twin_aircraft/frontend/coord_workbench.html#L897) | 增加吸附状态文字 |
| [saveSession() / restoreSession()](file:///d:/tmp/digital_twin_aircraft/frontend/coord_workbench.html#L597) | 持久化辅助工具开关状态 |
| HTML body | 在 `.canvas-area` 内新增 `.canvas-toolbar` DOM |
| CSS `<style>` | 新增工具栏 + 按钮样式 |

---

## 6. 详细算法

### 6.1 吸附坐标计算（`computeSnap`）

```javascript
computeSnap(mouseWX, mouseWY, existingPoints, gridStep) {
  const threshold = this.SNAP_THRESHOLD_PX / camScale;  // 转为世界坐标阈值
  let resultX = mouseWX, resultY = mouseWY;
  let guideX = null, guideY = null;
  let snapInfoParts = [];

  // 第一优先级：已有锚点/标注点
  let bestDx = Infinity, bestDy = Infinity;
  for (const [idx, pt] of existingPoints.entries()) {
    const dx = Math.abs(mouseWX - pt[0]);
    const dy = Math.abs(mouseWY - pt[1]);
    if (dx < threshold && dx < bestDx) {
      bestDx = dx;
      resultX = pt[0];
      guideX = { wx: pt[0], color: '#e040a0', label: `X 对齐 #${idx+1}` };
    }
    if (dy < threshold && dy < bestDy) {
      bestDy = dy;
      resultY = pt[1];
      guideY = { wy: pt[1], color: '#e040a0', label: `Y 对齐 #${idx+1}` };
    }
  }

  // 第二优先级：网格线（仅在未被锚点吸附时）
  if (!guideX && gridStep) {
    const nearestGridX = Math.round(mouseWX / gridStep) * gridStep;
    if (Math.abs(mouseWX - nearestGridX) < threshold) {
      resultX = nearestGridX;
      guideX = { wx: nearestGridX, color: '#4f7df7', label: '' };
    }
  }
  if (!guideY && gridStep) {
    const nearestGridY = Math.round(mouseWY / gridStep) * gridStep;
    if (Math.abs(mouseWY - nearestGridY) < threshold) {
      resultY = nearestGridY;
      guideY = { wy: nearestGridY, color: '#4f7df7', label: '' };
    }
  }

  return {
    snappedWX: resultX, snappedWY: resultY,
    guideX, guideY,
    snapInfo: [guideX?.label, guideY?.label].filter(Boolean).join(' ')
  };
}
```

### 6.2 正交约束计算（`computeOrtho`）

```javascript
computeOrtho(mouseWX, mouseWY, lastPoint) {
  if (!lastPoint) return null;
  const [x0, y0] = lastPoint;
  const dx = Math.abs(mouseWX - x0);
  const dy = Math.abs(mouseWY - y0);
  if (dx >= dy) {
    // 水平约束
    return { constrainedWX: mouseWX, constrainedWY: y0, direction: 'H' };
  } else {
    // 垂直约束
    return { constrainedWX: x0, constrainedWY: mouseWY, direction: 'V' };
  }
}
```

### 6.3 综合坐标（`getAdjustedCoord`）

吸附和正交的组合规则：

```javascript
getAdjustedCoord(mouseWX, mouseWY) {
  let wx = mouseWX, wy = mouseWY;
  const isOrthoActive = this.orthoEnabled !== isShiftDown;  // XOR

  // Step 1: 先算吸附
  if (this.snapEnabled) {
    const points = getCurrentPointsList();
    const snap = this.computeSnap(wx, wy, points, getCurrentGridStep());
    wx = snap.snappedWX;
    wy = snap.snappedWY;
    this.snapResult = snap;
  }

  // Step 2: 在吸附结果上叠加正交
  if (isOrthoActive) {
    const last = getLastPoint();
    const ortho = this.computeOrtho(wx, wy, last);
    if (ortho) {
      wx = ortho.constrainedWX;
      wy = ortho.constrainedWY;
      this.orthoResult = ortho;
    }
  } else {
    this.orthoResult = null;
  }

  return [wx, wy];
}
```

---

## 7. 键盘快捷键

| 快捷键 | 功能 | 说明 |
| :--- | :--- | :--- |
| `G` | 切换网格显隐 | toggle `AlignAssist.gridVisible` |
| `S` | 切换吸附/对齐线 | toggle `AlignAssist.snapEnabled` |
| `O` | 切换正交约束 | toggle `AlignAssist.orthoEnabled` |
| `Shift`（按住） | 临时切换正交 | 反转当前 ortho 状态 |
| `Esc` | 取消所有辅助 | 全部关闭（不影响网格显示） |

> **注意**：快捷键仅在画布获得焦点且不在输入框中时生效，避免与 UE 坐标输入框冲突。

---

## 8. 状态持久化

辅助工具的开关状态纳入现有的 `SessionDB` 会话缓存体系（[coord_workbench.html:L573](file:///d:/tmp/digital_twin_aircraft/frontend/coord_workbench.html#L573)）：

```javascript
// saveSession() 中追加
SessionDB.save({
  ...existing,
  alignAssist: {
    gridVisible: AlignAssist.gridVisible,
    snapEnabled: AlignAssist.snapEnabled,
    orthoEnabled: AlignAssist.orthoEnabled,
  }
});

// restoreSession() 中恢复
if (snap.alignAssist) {
  AlignAssist.gridVisible = snap.alignAssist.gridVisible ?? true;
  AlignAssist.snapEnabled = snap.alignAssist.snapEnabled ?? true;
  AlignAssist.orthoEnabled = snap.alignAssist.orthoEnabled ?? false;
  syncToolbarUI();  // 同步按钮状态
}
```

---

## 9. 性能考量

| 关注点 | 策略 |
| :--- | :--- |
| 吸附计算频率 | mousemove 事件中计算，但使用 `requestAnimationFrame` 节流，保证每帧只算一次 |
| 对齐源数量 | 通常 < 20 个锚点/标注点，O(n) 遍历无性能问题 |
| 网格细分渲染 | 当可见网格线 > 200 条时自动退到更大间距 |
| 辅助线绘制 | 最多 2 条辅助线 + 2 个高亮环 + 1 个十字准星，开销可忽略 |

---

## 10. 与其他模块的关系

| 模块 | 关系 |
| :--- | :--- |
| **PRD 2.9 坐标标定工作台** | 在其画布交互设计（§7）基础上增强 |
| **PRD 2.9.1 实体投入** | 无直接关系，标定精度提升可间接减少 RMSE |
| **PRD 2.9.2 类型审核** | 无直接关系 |

---

## 11. 已知限制与约束

1. **仅前端改动**：不涉及后端 API 和数据结构变更
2. **不改变坐标语义**：吸附和正交仅修正用户点击位置，不改变仿射变换算法
3. **图片模式坐标系**：图片模式的坐标为像素坐标（Y 不翻转），吸附和正交逻辑相同，仅坐标系不同
4. **不支持角度约束**：当前正交仅支持 0°/90°，不支持 45° 等角度约束（可作为后续演进）
5. **触屏设备**：辅助工具栏适配触屏点击，但 Shift 快捷键在触屏上不可用

---

## 12. 未来演进路线

1. **角度约束扩展**：支持 15°/30°/45° 等可配置角度约束
2. **对象吸附**：除了锚点外，还能吸附到 DXF 图元的顶点、端点、中点
3. **距离测量工具**：在两个锚点间显示实时测距，辅助判断标定精度
4. **坐标微调面板**：点击已放置的锚点，弹出微调面板可用方向键 ±1 单位移动
5. **辅助工具偏好设置**：吸附阈值、对齐线颜色等可在设置中自定义
