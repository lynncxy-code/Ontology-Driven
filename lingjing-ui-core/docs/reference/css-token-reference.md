# 灵境 UI Core — CSS Token 参考手册

> 版本：v3.1.6 · 最后更新：2026-03-25
> 本文档是 `SKILL.md §3.0.c Step 4` 与 `§4.0 Token 与资源速查` 的完整参考，用于在自定义组件中保持与品牌的视觉一致性。
> **规则：自定义 HTML 元素的任何颜色、间距、字号、阴影，必须使用本文档中的 CSS 变量，禁止硬编码。**

---

## 一、跨场景通用 Token

这些变量在所有 4 个场景的 CSS 文件中均已定义，且根据主题（`data-theme="light/dark"`）自动切换，**可安全用于任意场景的自定义组件**。

### 1.1 品牌色

| CSS 变量 | 语义 | 典型用途 |
|----------|------|----------|
| `--theme-primary` | 主品牌色（B端浅色：`#0066CC`，UE5深色：`#0084FF`） | 主按钮、激活边框、主要高亮 |
| `--theme-secondary` | 次品牌色（B端：`#0099AA`，UE5：`#00E5FF`） | 辅助操作色、次要高亮 |
| `--theme-accent` | 强调色（B端：`#00A383`，UE5：`#00FFC8`） | 成功状态、正向反馈 |
| `--theme-border-base` | 品牌边框色（含透明度） | 强调边框、选中态 |

### 1.2 文字色

| CSS 变量 | 语义 | 典型用途 |
|----------|------|----------|
| `--theme-text-primary` | 主文字（B端浅色：`#0F172A`，深色：`#F8FAFC`） | 标题、正文、数值 |
| `--theme-text-secondary` | 次文字（B端：`#475569`，深色：`#94A3B8`） | 描述文字、元信息、标签 |

### 1.3 背景色

| CSS 变量 | 语义 | 典型用途 |
|----------|------|----------|
| `--bg-base` | 页面底色 | body/根容器 |
| `--bg-card` | 卡片/面板背景 | 内容容器、自定义卡片 |
| `--bg-glass` | 玻璃拟态背景（高层级） | 浮层、对话框 |
| `--bg-elevated` | 提升层背景 | 工具提示、弹出层 |
| `--bg-secondary` | 次要背景 | 侧边栏、辅助区域 |
| `--bg-input` | 输入框背景 | 表单控件 |

### 1.4 边框与分隔线

| CSS 变量 | 语义 | 典型用途 |
|----------|------|----------|
| `--glass-border` | 玻璃边框（完整 `border` 值） | 容器边框，直接赋值给 `border` 属性 |
| `--border-glass` | 同上（别名） | 同上 |

> 用法示例：`border: var(--glass-border);`

### 1.5 阴影

| CSS 变量 | 语义 | 典型用途 |
|----------|------|----------|
| `--shadow-sm` | 小阴影 | 卡片轻浮层次 |
| `--shadow-md` | 中阴影 | 下拉菜单、弹出层 |
| `--shadow-lg` | 大阴影 | 对话框、侧边栏 |
| `--shadow-hover` | 悬停阴影（品牌色） | 可交互卡片的 hover 态 |
| `--glass-shadow` | 玻璃感阴影 | 半透明容器 |

### 1.6 状态色

| CSS 变量 | 语义 | 颜色参考 |
|----------|------|----------|
| `--success-base` | 成功 / 正常运行 | 绿色系 |
| `--warning-base` | 警告 / 待确认 | 琥珀色系 |
| `--error-base` | 错误 / 严重异常 | 红色系 |
| `--danger-base` | 危险（同 error） | 红色系 |
| `--info-base` | 信息 / 提示 | 靛蓝色系 |

### 1.7 间距（8px 节奏）

| CSS 变量 | 值 | 用途 |
|----------|----|------|
| `--spacing-xs` | `4px` | 图标与文字间距、小徽章内边距 |
| `--spacing-sm` | `8px` | 行内元素间距、输入框内边距 |
| `--spacing-md` | `16px` | 卡片内边距（默认） |
| `--spacing-lg` | `24px` | 区块间距、较宽内边距 |
| `--spacing-xl` | `32px` | 大区块间距 |
| `--spacing-2xl` | `40px` | 页面级间距 |
| `--spacing-3xl` | `48px` | 最大间距 |

### 1.8 圆角

| CSS 变量 | 值 | 用途 |
|----------|----|------|
| `--radius-xs` | `4px` | 小徽章、小按钮 |
| `--radius-sm` | `6px` | 输入框、小卡片 |
| `--radius-md` | `8px` | 标准卡片（默认） |
| `--radius-lg` | `12px` | 大卡片、面板 |
| `--radius-xl` | `16px` | 对话框、大型容器 |

### 1.9 字号

| CSS 变量 | 值 | 用途 |
|----------|----|------|
| `--font-size-xs` | `12px` | 辅助标注、元信息 |
| `--font-size-sm` | `14px` | 正文、表格内容 |
| `--font-size-base` | `16px` | 标准正文 |
| `--font-size-lg` | `20px` | 小标题 |
| `--font-size-xl` | `24px` | 中标题 |
| `--font-size-2xl` | `32px` | 大数字、KPI 值 |
| `--font-size-3xl` | `40px` | 超大数字、主标题 |

### 1.10 字重

| CSS 变量 | 值 |
|----------|----|
| `--font-weight-normal` | `400` |
| `--font-weight-medium` | `500` |
| `--font-weight-semibold` | `600` |
| `--font-weight-bold` | `700` |

---

## 二、UE5 Overlay 场景专属 Token

> 仅在 `lingjing-core-ue5-overlay.css` 加载且 `data-theme="dark"` 时有效。
> 这些变量有针对深色 HUD 场景调优的透明度和颜色值。

### 2.1 文字色（UE5 专用分级）

| CSS 变量 | 值 | 用途 |
|----------|----|------|
| `--ue5-overlay-text-strong` | `#f2f7ff` | 最强调文字（数值、告警标题） |
| `--ue5-overlay-text-base` | `rgba(221,230,242,0.88)` | 正文（标签、列表内容） |
| `--ue5-overlay-text-muted` | `rgba(185,201,220,0.72)` | 次要文字（元信息、时间戳） |
| `--ue5-overlay-text-dim` | `rgba(148,165,188,0.58)` | 最弱文字（占位符、禁用态） |

### 2.2 状态色（UE5 霓虹调色版本）

| CSS 变量 | 值 | 用途 |
|----------|----|------|
| `--ue5-overlay-brand` | `#4f8df5` | 品牌蓝（信息高亮、选中态） |
| `--ue5-overlay-success` | `#02c39a` | 成功 / 正常状态 |
| `--ue5-overlay-warning` | `#ffb547` | 警告 / 待确认 |
| `--ue5-overlay-danger` | `#ff4a5b` | 错误 / P1 告警 |
| `--ue5-overlay-info` | `#37c3ff` | 信息蓝（一般提示） |

> UE5 状态色比通用 `--success-base/--error-base` 具有更强的发光感，自定义组件在 UE5 场景优先使用上述专属变量。

### 2.3 面板 / 容器背景

| CSS 变量 | 语义 |
|----------|------|
| `--ue5-overlay-panel-bg` | 面板半透明渐变背景（主面板） |
| `--ue5-overlay-panel-border` | 面板边框（低对比白半透明） |
| `--ue5-overlay-panel-sub-bg` | 子面板更深背景（嵌套层） |
| `--ue5-overlay-sub-border` | 子边框（更淡） |
| `--ue5-overlay-card-bg` | 卡片背景（深色半透明渐变） |
| `--ue5-overlay-card-border` | 卡片边框 |
| `--ue5-overlay-card-active-bg` | 激活卡片背景（更深） |
| `--ue5-overlay-card-active-border` | 激活卡片边框（品牌色） |

### 2.4 尺寸常量（不要覆盖！）

| CSS 变量 | 值 | 说明 |
|----------|----|------|
| `--ue5-overlay-system-bar-height` | `56px` | 系统栏高度 |
| `--ue5-overlay-safe-top` | `168px` | 安全区顶部偏移 |
| `--ue5-overlay-left-width` | `332px` | 左侧面板宽度 |
| `--ue5-overlay-right-width` | `360px` | 右侧面板宽度 |

> ⚠️ 尺寸常量仅供读取参考（如计算定位），**禁止在自定义组件中覆盖这些变量**。

---

## 三、B 端管理系统专属 Token

> 仅在 `lingjing-core-b-system.css` 加载且 `data-theme="light"`（默认）时有效。

### 3.1 品牌固定色板

| CSS 变量 | 值 | 用途 |
|----------|----|------|
| `--color-aero-blue` | `#0066CC` | 航空蓝，主操作色 |
| `--color-pulse-cyan` | `#0099AA` | 脉冲青，次操作色 |
| `--color-signal-green` | `#00A383` | 信号绿，正向状态 |
| `--color-warning-amber` | `#D97706` | 警告琥珀 |
| `--color-error-red` | `#DC2626` | 错误红 |
| `--color-info-indigo` | `#4338CA` | 信息靛蓝 |

### 3.2 中性色阶（Slate 系列）

| CSS 变量 | 值 | 用途 |
|----------|----|------|
| `--neutral-50` | `#F8FAFC` | 最浅，表格表头、次要背景 |
| `--neutral-100` | `#F1F5F9` | 悬停背景 |
| `--neutral-200` | `#E2E8F0` | 禁用背景、分割线 |
| `--neutral-300` | `#CBD5E1` | 边框、图标 |
| `--neutral-400` | `#94A3B8` | 占位符文字 |
| `--neutral-500` | `#64748B` | 次要文字 |
| `--neutral-600` | `#475569` | 正文 |
| `--neutral-700` | `#334155` | 标题 |
| `--neutral-800` | `#1E293B` | 强调标题 |
| `--neutral-900` | `#0F172A` | 主标题、重要文字 |

### 3.3 玻璃拟态（B 端特色）

| CSS 变量 | 值/语义 |
|----------|---------|
| `--glass-border` | `1px solid rgba(28,102,196,0.15)` 品牌蓝极浅边框 |
| `--glass-shadow` | `0 8px 32px rgba(28,102,196,0.08)` 品牌蓝浅阴影 |
| `--bg-glass-accent` | `rgba(0,102,204,0.05)` 品牌蓝极浅填充（active/hover 态） |

---

## 四、自定义组件 Token 用法示例

以下示例展示「在不同场景中如何用 Token 创建一个自定义卡片，让它自动融入当前场景的视觉语言」：

```html
<!-- 跨场景通用：自定义信息卡片（Light/Dark 主题自动切换） -->
<div class="pj-b-system-custom-card" style="
  background: var(--bg-card);
  border: var(--glass-border);
  box-shadow: var(--shadow-sm);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
">
  <span style="
    color: var(--theme-text-secondary);
    font-size: var(--font-size-xs);
    font-weight: var(--font-weight-medium);
  ">自定义标签</span>
  <div style="
    color: var(--theme-text-primary);
    font-size: var(--font-size-xl);
    font-weight: var(--font-weight-bold);
    margin-top: var(--spacing-xs);
  ">核心数值</div>
</div>
```

```html
<!-- UE5 专属：自定义告警条目（使用 UE5 专属变量） -->
<div class="pj-ue5-custom-alert" style="
  background: var(--ue5-overlay-card-bg);
  border: 1px solid var(--ue5-overlay-card-border);
  border-radius: var(--radius-sm);
  padding: var(--spacing-sm) var(--spacing-md);
">
  <span style="color: var(--ue5-overlay-danger); font-weight: var(--font-weight-semibold);">
    告警标题
  </span>
  <span style="color: var(--ue5-overlay-text-muted); font-size: var(--font-size-xs);">
    时间戳
  </span>
</div>
```

---

## 五、扩展说明

- **新增场景**：新场景的 CSS 文件只需在 `:root` 中注册同名变量（`--theme-primary` 等），即可自动兼容基于通用 Token 的自定义组件。
- **深色模式**：所有通用 Token 在 `[data-theme="dark"]` 中均有对应覆盖值，无需为深色模式单独写自定义样式。
- **Token 来源验证**：如需确认某个变量是否真实存在于 CSS 文件中，运行：
  ```bash
  grep "变量名" components/dist/lingjing-core-{scene}.css
  ```
