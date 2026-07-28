# 灵境Core - 演示文稿使用指南

## 概述

演示文稿场景是lingjing-core的第三大核心应用场景，用于创建符合灵境品牌视觉规范的HTML演示文稿。

**版本**: 2.7.1  
**更新日期**: 2026-02-23
**文档状态**: 历史文档（待迁移至 v3.0 口径）

---

## 快速开始

### 1. 先判断实现层级

- 演示文稿任务应先读取 `scene_coverage_matrix.yml`，再按“**Level 1 模板轻调 → Level 2 组件编排 → Level 3 规范扩展**”选择路径；
- 若已有高匹配模板，优先沿用其叙事节奏、页面骨架和组件组合；
- 若没有直达模板，则按本指南的页型与组件规则组织内容；
- 若场景较新或混合度较高，再依据现有规范补充生成缺失页面。

### 2. 选择模板

| 模板文件 | 用途 |
|---------|------|
| `examples/presentation-product.html` | 产品展示模板（首选） |
| `examples/presentation-business.html` | 商务汇报模板 |
| `examples/presentation-planning.html` | 项目规划模板 |
| `examples/presentation-minimal.html` | 极简模板 |
| `examples/presentation-work-report.html` | 工作总结 / 阶段汇报模板 |

> 这些模板更适合作为结构参考；若演示文稿将落到独立项目或单独目录中，通常可先确定资源落点，再回写页面引用路径。

### 3. 引入CSS

```html
<!-- 以下路径示意调用方项目内的样式落点 -->
<link rel="stylesheet" href="./styles/lingjing/lingjing-core-presentation.css">
```

### 4. 引入交互脚本

```html
<!-- 以下路径示意调用方项目内的脚本落点 -->
<script src="./scripts/lingjing/presentation-template.js"></script>
```

### 5. 引入图标

```html
<script src="https://unpkg.com/lucide@latest"></script>
<script>
  lucide.createIcons();
</script>
```

---

## 页面类型

### 1. 封面页

```html
<div class="presentation-slide slide-cover active">
  <div class="slide-content">
    <div class="slide-content-inner">
      <h1 class="slide-cover-title">演示文稿标题</h1>
      <p class="slide-cover-subtitle">副标题</p>
    </div>
  </div>
</div>
```

### 2. 目录页

```html
<div class="presentation-slide slide-toc">
  <div class="slide-content">
    <div class="slide-content-inner">
      <h2 class="slide-toc-title">目录</h2>
      <ul class="slide-toc-list">
        <li class="slide-toc-item">
          <span class="slide-toc-number">01</span>
          <span class="slide-toc-text">第一章</span>
        </li>
      </ul>
    </div>
  </div>
</div>
```

### 3. 内容页

```html
<div class="presentation-slide">
  <div class="slide-content">
    <div class="slide-content-inner">
      <div class="slide-header">
        <h2 class="slide-title">章节标题</h2>
      </div>
      <div class="slide-body">
        <p>内容...</p>
      </div>
    </div>
  </div>
</div>
```

### 4. 结束页

```html
<div class="presentation-slide slide-closing">
  <div class="slide-content">
    <div class="slide-content-inner">
      <h2 class="slide-closing-title">谢谢</h2>
      <p class="slide-closing-subtitle">Q&A</p>
    </div>
  </div>
</div>
```

---

## 组件库

### 渐变文字

```html
<h2 class="presentation-gradient-text">渐变文字</h2>
```

### 时间线

```html
<div class="presentation-timeline">
  <div class="presentation-timeline-item">
    <div class="presentation-timeline-dot"></div>
    <div class="presentation-timeline-content">
      <h4 class="presentation-timeline-title">标题</h4>
      <p class="presentation-timeline-content">内容</p>
    </div>
  </div>
</div>
```

### 特性列表

```html
<ul class="presentation-feature-list">
  <li class="presentation-feature-item">
    <div class="presentation-feature-icon">
      <i data-lucide="zap"></i>
    </div>
    <div class="presentation-feature-content">
      <h4 class="presentation-feature-title">特性标题</h4>
      <p class="presentation-feature-desc">特性描述</p>
    </div>
  </li>
</ul>
```

### 要点列表

```html
<ul class="presentation-bullets">
  <li class="presentation-bullet-item">
    <div class="presentation-bullet-icon">
      <i data-lucide="check" width="14" height="14"></i>
    </div>
    <span class="presentation-bullet-text">要点</span>
  </li>
</ul>
```

### 引用块

```html
<div class="presentation-quote">
  <p class="presentation-quote-text">引用文字</p>
  <p class="presentation-quote-author">— 作者</p>
</div>
```

---

## 动画效果

| 动画类名 | 效果 |
|---------|------|
| `.presentation-animate-fadeIn` | 淡入 |
| `.presentation-animate-slideInUp` | 上滑进入 |
| `.presentation-animate-slideInLeft` | 左滑进入 |
| `.presentation-animate-slideInRight` | 右滑进入 |
| `.presentation-animate-scaleIn` | 缩放进入 |
| `.presentation-animate-bounceIn` | 弹跳进入 |
| `.presentation-animate-pulse` | 脉冲 |
| `.presentation-animate-float` | 悬浮 |
| `.presentation-animate-gradient` | 渐变位移 |

---

## 导航控制

### 键盘快捷键

| 按键 | 功能 |
|------|------|
| → / ↓ / 空格 | 下一页 |
| ← / ↑ | 上一页 |
| Home | 第一页 |
| End | 最后一页 |

### 触摸滑动

- 左滑：下一页
- 右滑：上一页

---

## 主题切换

演示文稿支持浅色/深色主题切换，使用与网站和B端系统相同的主题机制。

```html
<button id="themeToggle">
  <i data-lucide="sun" class="icon-light"></i>
  <i data-lucide="moon" class="icon-dark"></i>
</button>
```

---

## 复用现有组件

演示文稿场景可以完全复用以下现有组件：

- `.glass-card` - 玻璃卡片
- `.btn-primary` / `.btn-outline` - 按钮
- `.stat-card` - 统计卡片
- `.modal` - 模态框
- `flex` / `grid` / `gap-md` 等工具类

---

## 完整HTML结构

```html
<!DOCTYPE html>
<html lang="zh-CN" data-theme="light">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>演示文稿</title>
  <!-- 以下路径示意调用方项目内的样式落点 -->
  <link rel="stylesheet" href="./styles/lingjing/lingjing-core-presentation.css">
  <script src="https://unpkg.com/lucide@latest"></script>
</head>
<body>
  <div class="presentation-container">
    <div class="presentation-wrapper">
      
      <!-- 幻灯片1 -->
      <div class="presentation-slide slide-cover active">
        <div class="slide-content">
          <div class="slide-content-inner">
            <h1 class="slide-cover-title">标题</h1>
          </div>
        </div>
      </div>
      
      <!-- 更多幻灯片... -->
      
    </div>
    
    <!-- 主题切换 -->
    <div class="presentation-theme-toggle">
      <button class="glass-card p-md" id="themeToggle" style="cursor: pointer;">
        <i data-lucide="sun" class="icon-light"></i>
        <i data-lucide="moon" class="icon-dark"></i>
      </button>
    </div>
    
    <!-- 导航栏 -->
    <div class="presentation-nav">
      <button class="presentation-nav-btn" id="prevSlide">
        <i data-lucide="chevron-left" width="20" height="20"></i>
      </button>
      <div class="presentation-progress">
        <span class="presentation-progress-text">1 / 4</span>
        <div class="presentation-progress-bar">
          <div class="presentation-progress-fill" style="width: 25%;"></div>
        </div>
      </div>
      <div class="presentation-indicators"></div>
      <button class="presentation-nav-btn" id="nextSlide">
        <i data-lucide="chevron-right" width="20" height="20"></i>
      </button>
    </div>
  </div>
  
  <!-- 以下路径示意调用方项目内的脚本落点 -->
  <script src="./scripts/lingjing/presentation-template.js"></script>
  <script>
    lucide.createIcons();
  </script>
</body>
</html>
```
