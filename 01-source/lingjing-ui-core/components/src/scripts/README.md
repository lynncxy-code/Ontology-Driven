# Lingjing Core 交互效果使用指南

## 概述

Lingjing Core 提供了一套默认的交互效果，为玻璃拟态卡片组件增添动态视觉反馈，提升用户体验。

> 使用说明：下面的样式与脚本路径均应视为调用方项目内的资源落点示意；若在外部项目中接入，请先将相关资源放入项目自己的目录，再回写引用路径。

## 快速开始

### 1. 引入脚本

在 HTML 文件的 `</body>` 标签之前引入交互脚本：

```html
<!-- 以下路径示意调用方项目内的资源落点 -->
<link rel="stylesheet" href="./styles/lingjing/lingjing-core-website.css">

<!-- 页面内容 -->
<div class="card-glass">
    <h3>玻璃卡片</h3>
    <p>鼠标悬停查看涟漪效果</p>
</div>

<!-- 以下路径示意调用方项目内的脚本落点 -->
<script src="./scripts/lingjing/interactions.js"></script>
```

### 2. 自动初始化

脚本会在 DOM 加载完成后自动初始化，无需额外配置。所有支持的卡片组件会自动获得以下效果：

- **涟漪效果（Ripple Effect）**：鼠标悬停时在鼠标位置产生扩散涟漪动画
- **滚动动画（Scroll Animation）**：卡片进入视口时淡入并上移
- **主题管理（Theme Management）**：自动适配浅色/深色主题

## 支持的组件

### 常规卡片组件（推荐日常使用）

以下组件适合用于内容卡片、产品卡片、新闻卡片等常规业务场景：

- **`.card-glass`** - 标准玻璃卡片（Lingjing Core 规范）
  - 适用场景：所有常规卡片需求
  - 特点：标准模糊效果、简洁 hover 动画、顶部 1px 高光
  - 使用率：⭐⭐⭐⭐⭐ 最常用

- **`.glass-card`** - 玻璃卡片变体（项目自定义）
  - 适用场景：与 `.card-glass` 相同，项目特定样式
  - 特点：与 `.card-glass` 类似，可能有项目级定制
  - 使用率：⭐⭐⭐⭐⭐ 最常用

### 特殊场景组件（装饰性视觉效果）

⚠️ **注意：以下组件包含持续动画效果，不适合用于承载文字内容的常规卡片。**

它们专为特定视觉场景设计，应谨慎使用：

- **`.glass-flowing`** - 流动玻璃效果
  - ⚠️ 适用场景：Hero 区域背景装饰、大型视觉区块、落地页头图
  - ⚠️ 不适用：新闻卡片、产品卡片、表单容器等需要阅读的内容
  - 特点：15s 无限旋转渐变动画
  - 使用建议：仅用于纯装饰性区块，避免放置大量文字

- **`.glass-frosted`** - 磨砂玻璃效果
  - ⚠️ 适用场景：模态框背景、遮罩层、对话框背景
  - ⚠️ 不适用：常规内容卡片（模糊过强影响可读性）
  - 特点：24px 超强模糊、多层阴影
  - 使用建议：用于背景层，上层需要有清晰内容

- **`.glass-colored`** - 彩色玻璃效果
  - ⚠️ 适用场景：营销落地页特殊区块、品牌展示区、创意视觉区域
  - ⚠️ 不适用：常规业务卡片（视觉冲击力过强）
  - 特点：彩色渐变背景 + 12s 旋转动画
  - 使用建议：仅用于需要强视觉吸引力的特殊场景

### 使用建议总结

| 使用场景 | 推荐组件 | 避免使用 |
|---------|---------|---------|
| 新闻/文章卡片 | `.card-glass` / `.glass-card` | `.glass-flowing` `.glass-colored` |
| 产品展示卡片 | `.card-glass` / `.glass-card` | `.glass-flowing` `.glass-colored` |
| 表单容器 | `.card-glass` / `.glass-card` | 所有特殊场景组件 |
| Hero 背景装饰 | `.glass-flowing` | - |
| 模态框背景 | `.glass-frosted` | `.glass-flowing` `.glass-colored` |
| 营销落地页视觉区 | `.glass-colored` `.glass-flowing` | - |

## 功能详解

### 涟漪效果（Ripple Effect）

当鼠标进入卡片时，在鼠标位置创建一个蓝色扩散涟漪动画。

**特性：**
- 自动适配深色/浅色主题
- 主题色为 `#0084FF`（深色主题透明度 25%，浅色主题 30%）
- 动画时长：600ms
- 自动处理 `position` 和 `overflow` 样式

### 滚动动画（Scroll Animation）

卡片首次进入视口时执行淡入和上移动画。

**参数：**
- 初始状态：`opacity: 0; transform: translateY(20px)`
- 触发阈值：元素 10% 进入视口
- 动画时长：600ms
- 缓动函数：`cubic-bezier(0.2, 0, 0, 1)`
- 延迟：每个元素延迟 50ms（避免同时触发）

### 主题管理（Theme Management）

自动检测并应用系统主题偏好，支持主题切换。

**API：**

```javascript
// 切换主题（浅色 ↔ 深色）
window.Lingjing.toggleTheme();

// 设置特定主题
window.Lingjing.setTheme('dark');  // 或 'light'

// 获取当前主题
const currentTheme = window.Lingjing.getTheme();
```

**示例：添加主题切换按钮**

```html
<button onclick="window.Lingjing.toggleTheme()">
    切换主题
</button>
```

## 动态元素支持

脚本使用 `MutationObserver` 监听 DOM 变化，动态添加的卡片元素会自动获得交互效果，无需手动初始化。

**示例：**

```javascript
// 动态添加的卡片会自动获得涟漪效果
const newCard = document.createElement('div');
newCard.className = 'card-glass';
newCard.innerHTML = '<h3>动态卡片</h3>';
document.body.appendChild(newCard);
```

## 禁用特定效果

### 禁用涟漪效果

为卡片添加 `data-lingjing-ripple="disabled"` 属性：

```html
<div class="card-glass" data-lingjing-ripple="disabled">
    <p>此卡片没有涟漪效果</p>
</div>
```

### 禁用滚动动画

为卡片添加 `data-lingjing-animated="true"` 属性：

```html
<div class="card-glass" data-lingjing-animated="true">
    <p>此卡片没有滚动动画</p>
</div>
```

## 自定义配置

如果需要自定义行为，可以直接访问类实例：

```javascript
// 等待 Lingjing Core 初始化完成
document.addEventListener('DOMContentLoaded', () => {
    // 访问卡片效果管理器
    const cardEffects = window.Lingjing.cardEffects;

    // 访问滚动动画管理器
    const scrollAnimations = window.Lingjing.scrollAnimations;

    // 访问主题管理器
    const themeManager = window.Lingjing.themeManager;
});
```

## 性能考虑

- 涟漪元素在动画结束后自动移除（600ms）
- 滚动动画使用 `IntersectionObserver`，性能开销小
- 仅在元素首次进入视口时执行滚动动画
- MutationObserver 使用节流，避免性能问题

## 浏览器兼容性

- **现代浏览器**：Chrome 60+、Firefox 60+、Safari 12+、Edge 79+
- **所需特性**：
  - CSS `backdrop-filter`（主要样式特性）
  - `IntersectionObserver`（滚动动画）
  - `MutationObserver`（动态元素支持）
  - CSS Grid（布局系统）

## 常见问题

### Q: 涟漪效果不显示？

**A:** 检查以下事项：
1. 确保引入了交互脚本
2. 检查元素是否使用了支持的类名
3. 确认浏览器支持所需特性
4. 查看控制台是否有错误信息

### Q: 如何修改涟漪颜色？

**A:** 修改 `interactions.js` 中的 `createRipple` 方法：

```javascript
// 修改这两个颜色值
const rippleColor = isDarkTheme
  ? 'rgba(0, 132, 255, 0.25)'  // 深色主题
  : 'rgba(0, 132, 255, 0.3)';  // 浅色主题
```

### Q: 可以移除某个功能吗？

**A:** 可以注释掉 `initLingjingCore()` 函数中对应的初始化代码：

```javascript
function initLingjingCore() {
  window.Lingjing = window.Lingjing || {};

  window.Lingjing.cardEffects = new LingjingCardEffects();  // 涟漪效果
  // window.Lingjing.scrollAnimations = new LingjingScrollAnimations();  // 注释掉滚动动画
  window.Lingjing.themeManager = new LingjingThemeManager();  // 主题管理

  // ...
}
```

## 示例项目

参考以下示例项目查看完整用法：

- [网站完整演示](../examples/website-complete.html)
- [B端系统完整演示](../examples/b-system-complete.html)
- [网站展示案例](../examples/website-showcase.html)
- [B端系统展示案例](../examples/b-system-showcase.html)

## 更新日志

### v1.0.0 (2026-02-10)

- ✨ 新增卡片涟漪悬停效果
- ✨ 新增滚动动画效果
- ✨ 新增主题管理功能
- ✨ 支持动态添加元素
- ✨ 自动初始化机制

