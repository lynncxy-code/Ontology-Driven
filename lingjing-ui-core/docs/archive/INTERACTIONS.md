# 🎭 LingJing Core - 交互效果指南

> **面向**: AI开发工具、前端开发者
> **用途**: 实现卡片涟漪、悬停高亮等交互效果
> **更新**: 2026-02-13
> **版本**: v1.8.1
> **文档状态**: 历史文档（待迁移至 v3.0 口径）
> **使用提醒**: 若当前任务属于实际项目接入或全局技能验证，请优先参考仓库根目录 `SKILL.md`、`README.md` 与 `docs/DOCS_STATUS_SUMMARY.md`；本文中的脚本与样式路径示例应视为资源组织方式说明，落地时应先适配到调用方项目。


---

## 📋 目录

- [交互效果概述](#交互效果概述)
- [卡片涟漪效果](#卡片涟漪效果)
- [卡片悬停描边](#卡片悬停描边)
- [按钮交互效果](#按钮交互效果)
- [快速集成](#快速集成)

---

## 交互效果概述

LingJing Core 提供了一套完整的交互效果系统，包括：

| 效果类型 | 触发方式 | 需要JS | 自动生效 |
|---------|---------|--------|---------|
| **卡片涟漪** | 鼠标进入 | ✅ 是 | ❌ 需引入 |
| **卡片悬停描边** | 鼠标悬停 | ❌ 否 | ✅ 是 |
| **按钮光泽效果** | 鼠标悬停 | ❌ 否 | ✅ 是 |
| **表单焦点高亮** | 键盘焦点 | ❌ 否 | ✅ 是 |

---

## 卡片涟漪效果

### 效果演示

鼠标进入卡片时，会在鼠标位置产生一个**蓝色波纹扩散动画**，增强用户交互反馈。

**视觉特征**:
- 🎯 从鼠标位置开始扩散
- ⏱️ 持续 0.6 秒
- 🎨 浅色模式：`rgba(0, 132, 255, 0.3)`
- 🌙 深色模式：`rgba(0, 229, 255, 0.3)`
- 📐 从 100px 扩散至 400px (scale 4倍)

---

### 使用方法

#### **步骤 1: 引入 JavaScript**

在 HTML 底部引入交互脚本：

```html
<!-- 以下路径示意调用方项目内的脚本落点 -->
<script src="./scripts/lingjing/interactions.js"></script>
```


#### **步骤 2: 使用标准卡片类**

涟漪效果会自动应用到以下卡片类：

```html
<!-- 玻璃拟态卡片 -->
<div class="card-glass">
  <h3>卡片标题</h3>
  <p>卡片内容</p>
</div>

<!-- 流动玻璃卡片 -->
<div class="glass-flowing">
  <h3>卡片标题</h3>
  <p>卡片内容</p>
</div>

<!-- 磨砂玻璃卡片 -->
<div class="glass-frosted">
  <h3>卡片标题</h3>
  <p>卡片内容</p>
</div>
```

**支持的卡片类**:
- `.card-glass` - 标准玻璃拟态卡片
- `.glass-card` - 玻璃卡片别名
- `.glass-flowing` - 流动玻璃效果
- `.glass-frosted` - 磨砂玻璃效果
- `.glass-colored` - 彩色玻璃效果

**⚠️ 不支持涟漪效果的卡片** (B端系统专用):
- `.content-card` - B端内容卡片（表单、数据展示）
- `.b-stat-card` - B端统计卡片（KPI卡片）
- `.b-chart-card` - B端图表容器卡片
- `.card-solid` - 实心卡片（设置面板）

**设计原则**:
- ✅ **营销网站、官网**: 使用玻璃拟态卡片 + 涟漪效果，增强互动感
- ✅ **B端管理系统**: 使用实心卡片/内容卡片，**不使用涟漪效果**，保持专业简洁
- ✅ **移动端应用**: 根据场景选择，避免过度动效

---

### 技术实现细节

#### **CSS 动画关键帧**

涟漪效果已内置在 `interactions.js` 中，会自动注入以下样式：

```css
@keyframes lingjing-ripple {
  from {
    transform: translate(-50%, -50%) scale(0);
    opacity: 1;
  }
  to {
    transform: translate(-50%, -50%) scale(4);
    opacity: 0;
  }
}

.lingjing-ripple {
  position: absolute;
  border-radius: 50%;
  pointer-events: none;
  animation: lingjing-ripple 0.6s ease-out;
}
```

#### **JavaScript 实现原理**

```javascript
// 1. 监听鼠标进入事件
card.addEventListener('mouseenter', (e) => {
  // 2. 计算鼠标相对卡片的位置
  const rect = card.getBoundingClientRect();
  const x = e.clientX - rect.left;
  const y = e.clientY - rect.top;

  // 3. 创建涟漪元素
  const ripple = document.createElement('div');
  ripple.className = 'lingjing-ripple';
  ripple.style.left = `${x}px`;
  ripple.style.top = `${y}px`;

  // 4. 添加到卡片中
  card.appendChild(ripple);

  // 5. 600ms 后自动清理
  setTimeout(() => ripple.remove(), 600);
});
```

---

### 自定义涟漪效果

#### **自定义颜色**

```javascript
// 在引入 interactions.js 后，可以自定义涟漪颜色
document.querySelectorAll('.my-custom-card').forEach(card => {
  card.addEventListener('mouseenter', (e) => {
    const ripple = createCustomRipple(e, card);
    ripple.style.background = 'radial-gradient(circle, rgba(0, 163, 131, 0.3), transparent)';
  });
});
```

#### **自定义动画时长**

```css
/* 在你的 CSS 中覆盖 */
.lingjing-ripple {
  animation-duration: 0.4s; /* 从默认 0.6s 改为 0.4s */
}
```

---

## 卡片悬停描边

### 效果演示

鼠标悬停在卡片上时，**自动显示蓝色描边高亮** + 阴影增强 + 向上浮起。

**视觉特征**:
- 🔵 蓝色描边：`var(--glass-border-hover)`
  - 浅色: `rgba(0, 102, 204, 0.3)`
  - 深色: `rgba(0, 132, 255, 0.4)`
- ⬆️ 向上浮起：`translateY(-4px)`
- ✨ 增强阴影：`var(--shadow-hover)`
- 💡 蓝色光晕：`var(--glow-primary)`

---

### 使用方法

#### **无需额外代码**

只要使用标准卡片类，悬停效果会自动生效：

```html
<div class="card-glass">
  <h3>鼠标悬停试试</h3>
  <p>会自动显示蓝色描边和阴影增强效果</p>
</div>
```

#### **CSS 实现**

```css
/* 默认状态 */
.card-glass {
  background: var(--bg-glass);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(28, 102, 196, 0.15);
  border-radius: var(--radius-lg);
  box-shadow: var(--glass-shadow);
  transition: all 0.3s cubic-bezier(0.2, 0, 0, 1);
}

/* 悬停状态 - 自动生效 */
.card-glass:hover {
  transform: translateY(-4px);                          /* 向上浮起 */
  border-color: var(--glass-border-hover);              /* 蓝色描边 */
  box-shadow: var(--shadow-hover), var(--glow-primary); /* 阴影 + 光晕 */
}
```

---

### 深色模式适配

悬停效果在深色模式下自动调整：

```css
[data-theme="dark"] .card-glass:hover {
  border-color: rgba(0, 132, 255, 0.4);  /* 更亮的蓝色描边 */
  box-shadow:
    0 12px 40px rgba(0, 132, 255, 0.3),  /* 蓝色阴影 */
    0 2px 4px rgba(0, 0, 0, 0.4),        /* 深色投影 */
    inset 0 1px 0 rgba(255, 255, 255, 0.15); /* 内发光 */
}
```

---

### 禁用悬停效果

如果某些卡片不需要悬停效果：

```css
/* 方法1: 禁用特定卡片 */
.card-glass.no-hover:hover {
  transform: none;
  border-color: var(--glass-border);
  box-shadow: var(--glass-shadow);
}

/* 方法2: 使用其他卡片类 */
.card-solid {
  /* card-solid 有更简单的悬停效果 */
}
```

---

## 按钮交互效果

### 主按钮光泽效果

主按钮 (`.btn-primary`) 悬停时会显示**从左到右的光泽扫过动画**：

```html
<button class="btn-primary">
  <i data-lucide="check"></i>
  <span>确认</span>
</button>
```

**CSS 实现**:

```css
.btn-primary::before {
  content: '';
  position: absolute;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  left: -100%;
  transition: left 0.5s ease;
}

.btn-primary:hover::before {
  left: 100%; /* 光泽从左扫到右 */
}
```

---

### 按钮涟漪点击效果

点击按钮时会产生**白色涟漪扩散**：

```css
.btn-primary:active::after {
  width: 100px;
  height: 100px;
  opacity: 0;
  /* 白色涟漪从点击位置扩散 */
}
```

---

## 快速集成

### 方法 1: 完整集成（推荐）

引入完整的 LingJing Core 样式 + 交互脚本：

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <title>My Project</title>

  <!-- 引入 LingJing Core 样式 -->
  <link rel="stylesheet" href="assets/css/lingjing-core/index.css">
</head>
<body>

  <!-- 你的内容 -->
  <div class="card-glass">
    <h3>卡片标题</h3>
    <p>自动支持涟漪和悬停效果</p>
  </div>

  <!-- 引入交互脚本 -->
  <script src="assets/js/lingjing-core/interactions.js"></script>
</body>
</html>
```

---

### 方法 2: 仅引入涟漪效果

如果只需要涟漪效果，最小化引入：

```html
<head>
  <!-- 以下路径示意调用方项目内的样式落点 -->
  <link rel="stylesheet" href="./styles/lingjing/lingjing-core-website.css">

</head>
<body>
  <!-- 你的卡片 -->
  <div class="card-glass">内容</div>

  <!-- 以下路径示意调用方项目内的脚本落点 -->
  <script src="./scripts/lingjing/interactions.js"></script>
</body>
```


---

### 方法 3: 自定义集成

若不直接复用脚本文件，可将等效的涟漪逻辑迁入你的项目：

```javascript
// 迁移与 LingjingCardEffects 等效的涟漪逻辑
class LingjingCardEffects {

  constructor() {
    this.init();
  }

  init() {
    this.injectRippleStyles();
    this.setupCardHoverEffects();
  }

  // ... 完整代码见 interactions.js
}

// 初始化
new LingjingCardEffects();
```

---

## 浏览器兼容性

| 浏览器 | 最低版本 | 涟漪效果 | 悬停描边 |
|--------|---------|---------|---------|
| **Chrome** | 90+ | ✅ | ✅ |
| **Firefox** | 88+ | ✅ | ✅ |
| **Safari** | 14+ | ✅ | ✅ |
| **Edge** | 90+ | ✅ | ✅ |
| **Opera** | 76+ | ✅ | ✅ |

---

## 性能优化

### ✅ 已优化

- ✅ 使用 `transform` 和 `opacity` 实现动画（GPU 加速）
- ✅ 涟漪元素在动画结束后自动清理（防止内存泄漏）
- ✅ 使用 `mouseenter` 而非 `mousemove`（避免频繁触发）
- ✅ 涟漪元素设置 `pointer-events: none`（不阻挡交互）

### 📊 性能指标

- **FPS**: 60fps 流畅动画
- **内存**: 每次涟漪约 50 bytes，自动回收
- **CPU**: 小于 1% 占用

---

## 常见问题

### Q1: 涟漪效果不显示？

**原因**: 未引入 `interactions.js`

**解决**:
```html
<!-- 以下路径示意调用方项目内的脚本落点 -->
<script src="./scripts/lingjing/interactions.js"></script>
```


---

### Q2: 卡片没有悬停描边？

**原因**: 未使用标准卡片类或CSS未引入

**解决**:
1. 确保卡片使用 `.card-glass` 类
2. 确保引入了 `components.css` 或 `index.css`

---

### Q3: 涟漪颜色和我的主题不搭配？

**解决**: 自定义涟漪颜色

```javascript
// 在你的 JS 中覆盖
document.querySelectorAll('.card-glass').forEach(card => {
  card.addEventListener('mouseenter', (e) => {
    // 自定义涟漪颜色为绿色
    const ripple = createRipple(e, card);
    ripple.style.background = 'radial-gradient(circle, rgba(0, 163, 131, 0.3), transparent)';
  });
});
```

---

### Q4: 移动端需要涟漪效果吗？

**建议**: 移动端无鼠标，涟漪效果不会触发，但不影响使用。

如需在移动端禁用（减小文件大小）：

```javascript
if (!('ontouchstart' in window)) {
  // 仅在桌面端加载
  const script = document.createElement('script');
  script.src = 'interactions.js';
  document.body.appendChild(script);
}
```

---

## 相关资源

- [组件目录](./COMPONENT_CATALOG.md) - 查看所有可用组件
- [代码片段](./CODE_SNIPPETS.md) - 复制粘贴即用的代码
- [变量索引](../components/src/styles/01-foundation/variables.css) - 查看所有设计令牌
- [GitHub Issues](https://github.com/lingjing-core/issues) - 报告问题和建议

---

## 更新日志

### v1.8.1 (2026-02-13)
- ✅ 正式发布交互效果文档
- ✅ 补充颜色变量别名 (`--color-blue` 等)
- ✅ 完善涟漪效果说明
- ✅ 添加快速集成指南

---

**© 2026 LingJing Core. 灵境核心设计系统.**
