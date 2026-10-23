# UE5 Overlay 布局决策卡

> **适用场景**：`ue5_overlay`（UE5 Web Overlay / 数字孪生叠加层）
> **样式入口**：`lingjing-core-ue5-overlay.css`
> **使用方法**：先读末尾"快速决策树"确定布局模式编号，再按下表选取参考文件，禁止绕过决策树直接套 quality_tracking。
>
> | 布局模式 | 参考文件 |
> |---|---|
> | 模式 1 — 单 HUD | `examples/ue5-overlay/ue5_overlay_data_viz.html` |
> | 模式 2 — HUD + 侧边详情面板 | `examples/ue5-overlay/ue5_overlay_quality_tracking.html` |
> | 模式 3 — HUD + 告警中心 | `examples/ue5-overlay/ue5_overlay_dashboard.html` |
> | 模式 4 — 紧急横幅（叠加） | 无独立文件，见本文 §布局模式4 骨架代码 |
> | 模式 5 — 双侧面板 + 底部 Dock | `examples/ue5-overlay/ue5_overlay_sidepanel_dock_layout.html` |

---

## 核心设计原则

1. **透明优先**：所有面板必须有玻璃拟态透明度，禁止大面积实色块遮挡三维视口
2. **层级分离**：通过 `ue5-overlay-layer--*` 控制 z-index，HUD → Marker → Detail → Critical 逐层递增
3. **框架强一致**：`ue5-overlay-root` 骨架禁止自建替代，面板必须在骨架内排布
4. **低干扰**：世界标注 / 告警信息不得覆盖三维中央视野核心区域

---

## 必须骨架（顶层结构）

所有 UE5 Overlay 页面必须以此为根：

```html
<!DOCTYPE html>
<html lang="zh-CN" data-theme="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link rel="stylesheet" href="[路径]/lingjing-core-ue5-overlay.css">
</head>
<body>
  <main class="ue5-overlay-root">
    <!-- 背景层 -->
    <div class="ue5-overlay-background"></div>
    <!-- 三维视口（可放 img 占位或 UE5 视口容器） -->
    <div class="ue5-overlay-viewport">
      <img class="ue5-overlay-scene-image" src="[背景图]" alt="三维场景">
    </div>
    <!-- 网格线装饰（可选） -->
    <div class="ue5-overlay-grid"></div>
    <!-- 中央保护区（防止内容挡住核心视野） -->
    <div class="ue5-overlay-center-guard"></div>

    <!-- 系统栏（默认必须保留；仅 PRD 明确"无顶部导航"时才省略） -->
    <header class="ue5-overlay-system-bar">…</header>

    <!-- 安全区：所有 HUD / 面板必须在此内 -->
    <section class="ue5-overlay-safe-area">
      <!-- 在此放 topbar-hud / world-marker / detail-panel 等 -->
    </section>
  </main>
</body>
</html>
```

**层级类对应关系**：

| 类名 | 用途 | z-index 语义 |
|------|------|-------------|
| `ue5-overlay-layer--ambient` | 环境装饰层（网格、背景效果） | 最底层 |
| `ue5-overlay-layer--marker` | 世界标注层 | 中间层 |
| `ue5-overlay-layer--hud` | HUD 顶部信息层 | 较高层 |
| `ue5-overlay-layer--detail` | 详情面板层 | 高层 |
| `ue5-overlay-layer--critical` | 紧急告警层 | 最高层 |

---

## 布局模式 1 — 单 HUD 模式（监控大屏）

**典型需求**：顶部状态栏 + 三维场景全屏 + 少量关键指标

```
┌─────────────────────────────────────────────────────────────┐
│ topbar-hud（顶部 HUD：标题 + KPI 信号条 + 操作按钮）       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│              三维场景（ue5-overlay-viewport）               │
│                                                             │
│  world-marker  world-marker  world-marker                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**骨架代码**：

```html
<section class="ue5-overlay-safe-area">
  <!-- HUD 顶部区 -->
  <div class="topbar-hud ue5-overlay-panel ue5-overlay-layer ue5-overlay-layer--hud">
    <div class="topbar-hud__headline">
      <h1 class="topbar-hud__title">系统标题</h1>
      <p class="topbar-hud__subtitle">副标题描述</p>
    </div>
    <!-- 信号指标条 -->
    <div class="topbar-hud__signal-strip">
      <div class="topbar-hud__stat topbar-hud__stat--info">
        <span class="topbar-hud__stat-label">任务数</span>
        <span class="topbar-hud__stat-value">128</span>
      </div>
      <div class="topbar-hud__stat topbar-hud__stat--success">
        <span class="topbar-hud__stat-label">完成率</span>
        <span class="topbar-hud__stat-value">94%</span>
      </div>
      <div class="topbar-hud__stat topbar-hud__stat--warning">
        <span class="topbar-hud__stat-label">预警</span>
        <span class="topbar-hud__stat-value">3</span>
      </div>
    </div>
    <div class="topbar-hud__actions">
      <div class="topbar-hud__button-group">
        <button class="topbar-hud__button">刷新</button>
        <button class="topbar-hud__button">导出</button>
      </div>
    </div>
  </div>

  <!-- 世界标注（叠加在三维场景上） -->
  <div class="world-marker ue5-overlay-layer ue5-overlay-layer--marker" data-status="warning">
    <div class="world-marker__label">
      <span class="world-marker__title">S4 对接工位</span>
      <span class="world-marker__status">预警</span>
    </div>
  </div>
</section>
```

**推荐 Level**：Level 1（模板直用）。

---

## 布局模式 2 — HUD + 侧边详情面板（双区模式）

**典型需求**：顶部 HUD + 右侧详情面板 + 世界标注

```
┌─────────────────────────────────────────────────────────────┐
│ topbar-hud--with-sidepanel（顶部 HUD）                     │
├────────────────────────────────────┬────────────────────────┤
│                                    │  detail-panel          │
│  三维场景 + world-marker           │  （右侧详情面板）      │
│                                    │                        │
└────────────────────────────────────┴────────────────────────┘
```

**骨架代码**：

```html
<section class="ue5-overlay-safe-area">
  <!-- 顶部 HUD：叠加 --with-sidepanel 修饰，为侧边面板留出空间 -->
  <div class="topbar-hud topbar-hud--with-sidepanel ue5-overlay-panel ue5-overlay-layer ue5-overlay-layer--hud">
    <div class="topbar-hud__headline">
      <h1 class="topbar-hud__title">页面标题</h1>
    </div>
    <div class="topbar-hud__signal-strip">…</div>
    <div class="topbar-hud__actions">…</div>
  </div>

  <!-- 世界标注 -->
  <div class="world-marker ue5-overlay-layer ue5-overlay-layer--marker" data-status="critical">
    <div class="world-marker__label world-marker__label-top">
      <span class="world-marker__icon"><i data-lucide="alert-triangle"></i></span>
      <span class="world-marker__title">问题工位</span>
    </div>
  </div>

  <!-- 右侧详情面板 -->
  <aside class="detail-panel ue5-overlay-panel ue5-overlay-layer ue5-overlay-layer--detail">
    <div class="detail-panel-header">
      <span class="detail-panel-title">详情标题</span>
    </div>
    <!-- 子卡片 -->
    <div class="ue5-overlay-subcard">
      <div class="ue5-overlay-section-title">基本信息</div>
      <!-- 内容 -->
    </div>
    <!-- 状态指示 -->
    <div class="ue5-overlay-status ue5-overlay-status--warning">预警状态</div>
    <div class="detail-panel-footer">
      <button class="topbar-hud__button">确认</button>
    </div>
  </aside>
</section>
```

**推荐 Level**：Level 1~2。

---

## 布局模式 3 — HUD + 告警中心（多面板模式）

**典型需求**：顶部 HUD + 左侧或底部告警面板 + 多个世界标注

```
┌─────────────────────────────────────────────────────────────┐
│ topbar-hud                                                  │
├─────────────────────────────────────────────────────────────┤
│  alert-center（告警列表）        │  三维场景 + markers     │
└─────────────────────────────────────────────────────────────┘
```

**骨架代码**：

```html
<section class="ue5-overlay-safe-area">
  <div class="topbar-hud ue5-overlay-panel ue5-overlay-layer ue5-overlay-layer--hud">…</div>

  <!-- 告警中心面板 -->
  <div class="alert-center ue5-overlay-panel ue5-overlay-layer ue5-overlay-layer--detail">
    <div class="alert-center__header">
      <span class="alert-center__title">实时告警</span>
    </div>
    <ul class="alert-center-list">
      <li class="alert-center-item">
        <!-- 告警条目内容 -->
        <span>告警描述</span>
      </li>
    </ul>
  </div>

  <!-- 世界标注（可多个） -->
  <div class="world-marker ue5-overlay-layer ue5-overlay-layer--marker" data-status="critical">…</div>
  <div class="world-marker ue5-overlay-layer ue5-overlay-layer--marker" data-status="success">…</div>
</section>
```

**推荐 Level**：Level 2。

---

## 布局模式 4 — 紧急告警模式（Critical Banner）

**典型需求**：触发紧急状态时，全屏叠加关键信息条

```
┌─────────────────────────────────────────────────────────────┐
│  ue5-critical-banner（红色紧急横幅，最高层）                │
├─────────────────────────────────────────────────────────────┤
│  正常布局（模式 1~3）                                       │
└─────────────────────────────────────────────────────────────┘
```

**骨架代码**：

```html
<!-- 紧急横幅：放在 ue5-overlay-safe-area 内顶层 -->
<div class="ue5-critical-banner ue5-overlay-layer ue5-overlay-layer--critical">
  <div class="topbar-hud__critical-strip">
    <div class="topbar-hud__critical-main">
      <span class="topbar-hud__critical-title">⚠ P1 紧急：S4 工位冻结</span>
      <span class="topbar-hud__critical-meta">触发时间：22:18 · 影响范围：3 工位</span>
    </div>
    <div class="topbar-hud__critical-actions">
      <button class="topbar-hud__critical-action topbar-hud__critical-action--primary">立即处置</button>
      <button class="topbar-hud__critical-action">查看详情</button>
    </div>
  </div>
</div>

<!-- 底部 Dock 操作区（可选） -->
<div class="ue5-overlay-bottom-dock">
  <div class="ue5-overlay-dock-group">
    <button class="ue5-overlay-dock-button"><i data-lucide="layers"></i> 图层</button>
    <button class="ue5-overlay-dock-button"><i data-lucide="map"></i> 视角</button>
  </div>
  <span class="ue5-overlay-dock-status">系统正常</span>
  <span class="ue5-overlay-dock-time">22:18:34</span>
</div>
```

**推荐 Level**：Level 2~3（需与业务告警逻辑联动）。

---

## 布局模式 5 — 双侧面板 + 底部时间轴（数字孪生监控全布局）

**典型需求**：左侧数据面板 + 中央三维场景 + 右侧详情/告警面板 + 底部时间轴，无或有顶部系统栏。最大化三维场景可视区域的同时提供完整的监控信息层。

```
┌─────────────────────────────────────────────────────────────────┐
│ ue5-overlay-system-bar（系统顶部导航栏，默认必须保留）           │
├──────────────────┬──────────────────────────┬───────────────────┤
│  detail-panel    │  三维场景中央区域         │  detail-panel     │
│  （左侧面板）    │  ue5-overlay-viewport     │  （右侧面板）     │
│                  │  world-marker × N         │                   │
│                  │  ue5-overlay-center-guard │                   │
├──────────────────┴──────────────────────────┴───────────────────┤
│  ue5-overlay-bottom-dock（底部时间轴/快捷操作，高度约 100-140px）│
└─────────────────────────────────────────────────────────────────┘
```

**布局关键规则**：

1. `ue5-overlay-safe-area` 需设置 `display:flex; flex-direction:column`，内部分为"面板行"和"底部 dock"两层
2. "面板行"设置 `display:flex; flex-direction:row; flex:1`，左右 `detail-panel` 固定宽度，中央区域 `flex:1` 自适应
3. `ue5-overlay-bottom-dock` 固定高度（建议 `100px`–`140px`），`flex-shrink:0`，不参与自适应
4. 左右 `detail-panel` 设置 `display:flex; flex-direction:column`，`detail-panel__body` 设 `flex:1; overflow-y:auto`
5. `ue5-critical-banner` 是条件组件，**无告警时 `display:none`**，`detail-panel__body` 会自动填满

**骨架代码**：

```html
<!-- 系统顶部导航栏（默认必须保留） -->
<header class="ue5-overlay-system-bar">
  <!-- brand-mark 显示 logo（background-image: assets/logo_3d.png），禁止替换为 Lucide 图标 -->
  <div class="ue5-overlay-system-bar__brand">
    <span class="ue5-overlay-system-bar__brand-mark" aria-hidden="true"></span>
    <div class="ue5-overlay-system-bar__brand-copy">
      <span class="ue5-overlay-system-bar__brand-name">系统名称</span>
      <span class="ue5-overlay-system-bar__brand-subtitle">副标题</span>
    </div>
  </div>
  <nav class="ue5-overlay-system-bar__nav">
    <a class="ue5-overlay-system-bar__nav-item">模块一</a>
    <a class="ue5-overlay-system-bar__nav-item">模块二</a>
  </nav>
  <div class="ue5-overlay-system-bar__meta">
    <span class="ue5-overlay-system-bar__meta-item">
      <i class="ue5-overlay-system-bar__meta-dot"></i>系统正常
    </span>
    <span class="ue5-overlay-system-bar__meta-item" id="sysTime">00:00:00</span>
  </div>
</header>

<section class="ue5-overlay-safe-area" style="display:flex; flex-direction:column; flex:1;">

  <!-- 面板行：左面板 + 中央场景 + 右面板 -->
  <div style="display:flex; flex-direction:row; flex:1; overflow:hidden;">

    <!-- 左侧面板 -->
    <aside class="detail-panel detail-panel--pinned ue5-overlay-panel ue5-overlay-layer ue5-overlay-layer--detail"
           style="width:var(--ue5-overlay-left-width,332px); display:flex; flex-direction:column;">
      <div class="detail-panel__header">
        <div class="detail-panel__title-group">
          <h1 class="detail-panel__title">面板标题</h1>
          <span class="detail-panel__eyebrow">标识徽章</span>
        </div>
        <div class="detail-panel__meta">说明文字</div>
      </div>
      <!-- body 填满剩余高度 -->
      <div class="detail-panel__body" style="flex:1; overflow-y:auto;">
        <div class="detail-panel__section">
          <h2 class="detail-panel__section-title">数据分区一</h2>
          <!-- detail-panel__metrics / __list / charts-grid--single ... -->
        </div>
      </div>
    </aside>

    <!-- 中央三维场景区（透明，UE5 视口穿透） -->
    <div style="flex:1; position:relative;">
      <!-- world-marker 叠加在三维场景上 -->
      <div class="world-marker ue5-overlay-layer ue5-overlay-layer--marker world-marker--info">
        <div class="world-marker__card">
          <span class="world-marker__title">标注点</span>
          <span class="world-marker__status">状态</span>
        </div>
      </div>
    </div>

    <!-- 右侧面板 -->
    <aside class="detail-panel detail-panel--pinned ue5-overlay-panel ue5-overlay-layer ue5-overlay-layer--detail"
           style="width:var(--ue5-overlay-right-width,360px); display:flex; flex-direction:column;">
      <!-- 条件告警横幅：无告警时 display:none -->
      <div class="ue5-critical-banner" style="display:none;">
        <span class="ue5-critical-banner__pill">告警</span>
        <strong class="ue5-critical-banner__title">告警标题</strong>
        <p class="ue5-critical-banner__copy">告警详情</p>
        <div class="ue5-critical-banner__actions">
          <button class="ue5-critical-banner__action ue5-critical-banner__action--primary">处置</button>
        </div>
      </div>
      <!-- body 填满剩余高度（banner display:none 后自动顶上） -->
      <div class="detail-panel__body" style="flex:1; overflow-y:auto;">
        <div class="detail-panel__section">
          <h2 class="detail-panel__section-title">数据分区一</h2>
        </div>
      </div>
    </aside>

  </div>

  <!-- 底部时间轴 / 停靠区（固定高度，不参与 flex 伸缩） -->
  <div class="ue5-overlay-bottom-dock" style="flex-shrink:0; height:120px;">
    <div class="ue5-overlay-dock-group">
      <button class="ue5-overlay-dock-button">操作一</button>
    </div>
    <span class="ue5-overlay-dock-status">系统正常</span>
    <span class="ue5-overlay-dock-time" id="dockTime">00:00</span>
    <!-- pj-ue5-timeline 项目扩展时间轴放在此处 -->
  </div>

</section>
```

> **内联 `style` 说明**：骨架中的 `display:flex`、`flex:1`、`overflow` 等布局属性为框架层必需属性，应在调用方项目 CSS 中对对应类名统一定义，此处仅以内联形式标示意图。

**推荐 Level**：Level 2~3（双侧面板为高度定制布局，通常需要项目级扩展）。

---

## world-marker 状态规范

`data-status` 属性驱动世界标注颜色，无需额外类：

| `data-status` 值 | 视觉含义 | 典型场景 |
|---------|---------|---------|
| `critical` | 红色 / 紧急 | P1 故障、工位冻结 |
| `warning` | 黄色 / 预警 | 待确认问题、参数偏差 |
| `success` | 绿色 / 正常 | 工位正常运行 |
| `info` | 蓝色 / 信息 | 一般状态标注 |
| _(不设)_ | 默认白色 | 中性信息 |

---

## topbar-hud 变体修饰类

| 修饰类 | 含义 |
|--------|------|
| `topbar-hud--with-sidepanel` | 为右侧详情面板留出空间 |
| `topbar-hud--compact` | 紧凑模式，减小 HUD 高度 |
| `topbar-hud--context-locked` | 上下文锁定状态（视角已固定某工位） |
| `topbar-hud--degraded` | 降级模式（数据链路中断） |
| `topbar-hud--quality` | 质量场景专用样式 |

---

## 通用禁止做法

| 类型 | 禁止行为 | 正确替代 |
|------|---------|---------|
| 根容器替换 | `<div class="lj-overlay-root">` | 必须 `<main class="ue5-overlay-root">` |
| 骨架绕过 | 面板直接放在 `body` 下 | 必须在 `ue5-overlay-safe-area` 内 |
| 内联定位 | `style="top:200px; left:300px"` | 通过 `ue5-overlay-layer--*` + CSS 变量定位 |
| 实色块遮挡 | 大面积 `background:#000` 面板 | 使用 `ue5-overlay-panel`（含玻璃拟态透明度） |
| demo_only 类 | `world-marker--demo-a/b` | 用业务语义修饰符 + `data-status` |
| 替换 HUD 体系 | 自建 `.my-hud / .custom-topbar` | 必须用 `topbar-hud` 及其子类 |
| **critical-strip 多余包裹** | 在 `topbar-hud__critical-strip` 外再套一层 `<div class="critical-wrapper">` 等容器 | `topbar-hud__critical-strip` 本身即为横幅容器，直接放置内容；多余包裹会破坏宽度和定位 |
| **底部 Dock 直接使用** | 仅写 `<div class="ue5-overlay-bottom-dock">` 不做 CSS 覆写 | 库默认样式为胶囊形 `inline-flex`，必须在页面 `<style>` 中覆写（见下方说明） |

### 底部 Dock 必要 CSS 覆写

库的 `.ue5-overlay-bottom-dock` 默认是 **胶囊按钮组**（`inline-flex; align-items:center; justify-self:center; border-radius:full`），用作布局容器时必须全部覆写，否则：
- `justify-self:center` → dock 宽度缩为内容宽，时间轴宽度塌缩为 **0px**（绝对定位子元素全部不可见）
- `align-items:center` → 子项不能撑满全宽

**必须添加的覆写：**

```css
.ue5-overlay-bottom-dock {
  /* Grid 放置 */
  grid-column: 1 / 4;
  grid-row: 2;
  justify-self: stretch;    /* ⚠️ 覆写库的 justify-self:center，否则宽度塌缩 */
  align-self: stretch;      /* 覆写库的 align-self:end */

  /* 容器布局 */
  display: flex !important; /* 覆写库的 inline-flex */
  flex-direction: column;
  align-items: stretch;     /* 覆写库的 align-items:center，子项填满全宽 */

  /* 外观 */
  border-radius: 0;         /* 覆写库的 pill 圆角 */
  padding: 0;
  overflow: hidden;         /* 防止时间轴标签溢出 dock 上边界 */
}
```

> 若时间轴内含 `transform: translateX(-50%)` 的绝对定位子元素，还需在时间轴容器上加 `contain: layout paint`，防止 CSS Transform 绕过 `overflow:hidden` 的裁切范围。

---

## 快速决策树

```
新 UE5 Overlay 页面
│
├─ 第一步：有没有顶部系统导航？
│   ├─ 有（默认）→ 保留 ue5-overlay-system-bar
│   └─ PRD 明确说"全屏无 UI 框架" → 才可省略
│
├─ 只需顶部 HUD + 世界标注，无侧边面板？
│   └─ 布局模式 1（单 HUD）
│
├─ 需要一侧详情面板（单侧）？
│   └─ 布局模式 2（HUD + 单侧详情面板）
│
├─ 需要多条告警列表？
│   └─ 布局模式 3（HUD + 告警中心）
│
├─ 需要左右双侧面板 + 底部时间轴？
│   └─ 布局模式 5（双侧面板 + 底部 dock，数字孪生监控全布局）
│
└─ 需要响应紧急状态 / P1 告警？
    └─ 在已有布局上叠加 布局模式 4（Critical Banner）
```
