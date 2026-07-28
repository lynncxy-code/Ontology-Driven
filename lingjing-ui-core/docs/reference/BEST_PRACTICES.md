# 灵境Core - 常见问题和最佳实践

> **版本**: v2.7.1
> **更新日期**: 2026-02-23
> **说明**: 本文档收集了 AI 工具使用灵境 Core 时的常见问题和实践建议。
> **使用提醒**: 本文更适合作为补充说明与问题排查参考；当前项目接入与生成协议，优先以 `SKILL.md` 为准。

---

## 🎯 目的

通过明确的示例和说明，帮助 AI 工具在生成代码时尽量避开常见问题，显著减少返工。

---

## 🧭 落地前的推荐判断顺序

- 在开始拼装页面前，先读取 `scene_coverage_matrix.yml`，再按“**Level 1 模板轻调 → Level 2 组件编排 → Level 3 规范扩展**”判断：
  1. **Level 1**：现有模板与目标页面主任务流、导航骨架、信息架构都高度接近，可在保留框架层的前提下做轻调；
  2. **Level 2**：没有直达模板，但现有组件与模块骨架足以承载主体页面，应按 `SKILL.md` 与模块骨架重组页面；
  3. **Level 3**：场景较新、跨域或存在新的信息架构时，再依据现有设计令牌、框架层约束和质量检查项扩展页面，并先说明项目级差异点。
- B 端系统顶部栏 + 左侧菜单、网站顶部栏、UE 顶部 HUD 属于框架层，默认必须强一致；项目差异主要发生在主内容区。
- 如果页面要落到独立项目中，通常更稳妥的做法是先把样式资源放入调用方项目，再回写 `<link>` / `import` 路径，而不是直接保留示例中的仓库相对路径。
- `examples/` 更适合作为结构参考；真正交付时，页面能否从目标项目的实际路径访问到样式资源，通常比“是否复用了某个示例文件”更重要。

---

## 📋 常见问题列表

### 问题1: B端侧边栏header中图标和文字错行

**问题描述**:
侧边栏header中的图标和系统名称不在同一行显示

**错误示例**:
```html
<!-- ❌ 错误：使用了额外的容器，导致布局错行 -->
<div class="b-sidebar-header">
    <div class="b-sidebar-brand">
        <i data-lucide="database" class="b-sidebar-logo"></i>
        <span>数据管理</span>
    </div>
</div>
```

**正确示例**:
```html
<!-- ✅ 正确：图标和文字直接放在header中 -->
<div class="b-sidebar-header">
    <i data-lucide="home"></i>
    <span class="b-sidebar-logo">系统名称</span>
</div>
```

**规则**:
- ✅ 图标 `<i>` 和文字 `<span class="b-sidebar-logo">` 应该直接作为 `.b-sidebar-header` 的子元素
- ❌ 不要使用 `.b-sidebar-brand` 等额外的容器包裹
- ✅ logo文字使用 `b-sidebar-logo` 类
- ✅ 图标不需要额外的类名，直接使用 `data-lucide` 属性

---

### 问题2: 网站卡片涟漪效果使用了错误的事件

**问题描述**:
卡片涟漪效果应该在鼠标悬停时触发，而不是点击时触发

**错误示例**:
```javascript
// ❌ 错误：使用click事件，需要点击才触发
cards.forEach(card => {
    card.addEventListener('click', function(e) {
        // 涟漪效果代码...
    });
});
```

**正确示例**:
```javascript
// ✅ 正确：使用mouseenter事件，鼠标悬停即触发
cards.forEach(card => {
    card.addEventListener('mouseenter', function(e) {
        // 涟漪效果代码...
    });
});
```

**规则**:
- ✅ 网站场景卡片的涟漪效果应该使用 `mouseenter` 事件
- ❌ 不要使用 `click` 事件（用户期望悬停就有效果）
- ✅ 适用于：`.website-solution-card`, `.website-product-card`, `.website-tech-card`
- ❌ 不要为B端组件（如 `.b-stat-card`）添加涟漪效果

---

### 问题3: 状态修饰符类单独使用

**问题描述**:
状态修饰符类（如 `.active`, `.positive`, `.negative`）应该与基础类组合使用

**错误示例**:
```html
<!-- ❌ 错误：单独使用active类 -->
<a href="#" class="active">首页</a>

<!-- ❌ 错误：单独使用positive类 -->
<div class="positive">+12.5%</div>
```

**正确示例**:
```html
<!-- ✅ 正确：active与基础类组合 -->
<a href="#" class="website-nav-link active">首页</a>
<a href="#" class="b-sidebar-nav-link active">首页</a>

<!-- ✅ 正确：positive与基础类组合 -->
<div class="b-stat-change positive">
    <i data-lucide="trending-up"></i>
    <span>+12.5%</span>
</div>
```

**规则**:
- ✅ `.active` 应该与导航链接类组合：`.website-nav-link.active` 或 `.b-sidebar-nav-link.active`
- ✅ `.positive` / `.negative` 应该与 `.b-stat-change` 组合
- ❌ 不要单独使用这些修饰符类

---

### 问题4: 按钮尺寸修饰符使用不一致

**问题描述**:
按钮尺寸类在不同版本文档里的口径可能不完全一致；如果直接猜测类名，容易出现与当前版本不匹配的情况。

**高风险写法**:
- 直接臆造尺寸类名（如 `.large`）
- 未确认当前版本可用类名就直接拼接

**推荐做法**:
```html
<!-- 方案1: 使用标准按钮 -->
<button class="btn-primary">确认</button>
<button class="website-btn-primary">立即开始</button>

<!-- 方案2: 需要尺寸变化时，先核对当前版本文档或 dist 产物 -->
<button class="btn-primary btn-sm">保存</button>
```

**规则**:
- ⚠️ 使用尺寸修饰符前，先检查当前版本文档与实际产物是否一致
- ✅ 优先使用当前版本已收录的按钮类
- ✅ 如果确实需要额外尺寸变化，尽量采用最小增量方式处理，避免随意自造类名

---

## ✅ 最佳实践总结

### B端侧边栏开发

```html
<!-- 完整的标准结构 -->
<div class="b-layout-sidebar">
    <aside class="b-sidebar" id="sidebar">
        <!-- Header：图标+文字直接在header中 -->
        <div class="b-sidebar-header">
            <i data-lucide="database"></i>
            <span class="b-sidebar-logo">系统名称</span>
        </div>

        <!-- 导航菜单 -->
        <nav class="b-sidebar-nav">
            <ul class="b-sidebar-nav-list">
                <li class="b-sidebar-nav-item">
                    <a href="#" class="b-sidebar-nav-link active">
                        <i data-lucide="home" class="b-sidebar-nav-icon"></i>
                        <span class="b-sidebar-nav-text">首页</span>
                    </a>
                </li>
            </ul>
        </nav>

        <!-- Footer：折叠按钮 -->
        <div class="b-sidebar-footer">
            <button class="b-sidebar-toggle" onclick="toggleSidebarCollapse()">
                <i data-lucide="chevrons-left" class="b-sidebar-toggle-icon"></i>
                <span class="b-sidebar-toggle-text">收起</span>
            </button>
        </div>
    </aside>

    <!-- 侧边栏遮罩层（移动端） -->
    <div class="b-sidebar-overlay" id="sidebarOverlay" onclick="toggleSidebar()"></div>

    <!-- 主内容区 -->
    <main class="b-main">
        <header class="b-header">
            <div class="b-header-left">
                <h1 class="page-title">页面标题</h1>
            </div>
            <div class="b-header-right">
                <!-- Header中不包含收起侧边栏按钮，该功能已在侧边栏底部提供 -->
                <!-- 其他按钮 -->
            </div>
        </header>
        <div class="b-content">
            <!-- 页面内容 -->
        </div>
    </main>
</div>
```

### 网站卡片涟漪效果

> 说明：下面的代码仅作为历史交互原理示意，**禁止直接复制为新项目默认实现**。当前项目接入时，优先复用仓库已有交互脚本或预定义类；若确实需要补交互，应优先改写为项目 CSS / 官方类扩展，不得通过运行时创建 `<style>` 或大量 `element.style.*` 的方式绕过 `SKILL.md` 的样式约束。

```javascript
// 交互示意代码（鼠标悬停触发）
document.addEventListener('DOMContentLoaded', function() {
    // 只为网站场景的卡片添加涟漪效果
    const cards = document.querySelectorAll('.website-solution-card, .website-product-card, .website-tech-card');

    cards.forEach(card => {
        // 注意：使用mouseenter而不是click
        card.addEventListener('mouseenter', function(e) {
            const ripple = document.createElement('span');
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;

            ripple.style.position = 'absolute';
            ripple.style.left = x + 'px';
            ripple.style.top = y + 'px';
            ripple.style.width = '0';
            ripple.style.height = '0';
            ripple.style.borderRadius = '50%';
            ripple.style.background = 'radial-gradient(circle, rgba(0, 132, 255, 0.3) 0%, transparent 70%)';
            ripple.style.transform = 'translate(-50%, -50%)';
            ripple.style.pointerEvents = 'none';
            ripple.style.animation = 'ripple-effect 0.6s ease-out';

            card.style.position = 'relative';
            card.style.overflow = 'hidden';
            card.appendChild(ripple);

            setTimeout(() => ripple.remove(), 600);
        });
    });

    // 添加涟漪动画样式
    if (!document.getElementById('ripple-animation')) {
        const style = document.createElement('style');
        style.id = 'ripple-animation';
        style.textContent = `
            @keyframes ripple-effect {
                to {
                    width: 500px;
                    height: 500px;
                    opacity: 0;
                }
            }
        `;
        document.head.appendChild(style);
    }
});
```

---

### 问题5: 页面结构正常但几乎没有样式

**问题描述**:
页面加载后，DOM 结构看起来合理，但核心布局/组件几乎没有视觉效果，好像“只剩下裸 HTML”。

**常见原因**:
- 使用了 `components/dist/lingjing-core-*.css` 中根本不存在的类名（如 `.status-badge`、`.modal-dialog`、业务特定的 `.technician-*`、`.parts-*` 等）。
- 未正确接入场景对应的样式入口文件，或 `<link>` / `import` 路径无效。
- 在 UX / 实现层擅自发明了看似“合理”的业务类名，而不是复用现有的通用组件类。

**排查步骤**:
1. 使用全文搜索或工具，在 `components/dist/*.css` 与 `CLASS_NAME_REFERENCE.md` 中检查页面使用的类名是否真实存在；
2. 确认页面已引入正确的场景入口 CSS（如 B 端系统应引入 `lingjing-core-b-system.css`）；
3. 对比 `examples/b-system-complete.html` 等官方示例，检查是否复用了推荐的布局壳和组件类。

**正确做法**:
- 若类名不存在，应改为使用技能包提供的通用组件组合（例如 `.content-card`、`.advanced-data-table`、`.badge`、`.grid-dynamic` 等），并在摘要中明确说明“本需求超出当前技能包样式覆盖范围，仅提供通用组件组合，无专用业务样式”。
- 必要时，将业务特定的视觉需求记录到 UX 侧的 `dev_handoff.edge_cases_zh`，由业务项目在灵境样式之上扩展，而非直接修改技能包。

**错误做法（应避免）**:
- 自造新的 CSS 类名并假设技能包会为其提供样式。
- 通过 `<style>` 块或内联 `style="..."` 大面积重写布局，以“临时补丁”的方式掩盖技能包缺失。

### 问题6: UE5 Overlay 场景中自造类和错误扩展

**错误示例**:
```html
<!-- ❌ 错误：自造 lj-overlay-* 体系，未使用官方骨架 -->
<div class="lj-overlay-root">
  <div class="lj-overlay-panel">...</div>
</div>
```

**正确示例**:
```html
<!-- ✅ 正确：使用官方骨架，并在内部通过项目修饰符扩展 -->
<div class="ue5-overlay-root">
  <div class="ue5-overlay-viewport">
    <div class="ue5-overlay-safe-area">
      <section class="detail-panel detail-panel--alarm">...</section>
    </div>
  </div>
</div>
```

**规则**:
- UE 场景必须使用 `.ue5-overlay-root`、`.ue5-overlay-viewport`、`.ue5-overlay-safe-area` 作为骨架，禁止使用 `.lj-overlay-*` 等新前缀重建一套体系。
- 若需要扩展样式，应优先在官方组件上添加项目修饰符类（如 `detail-panel--alarm`），并将修饰符实现放在项目样式文件中，而不是改写技能包 dist。

### 问题7: B 端和 AI 场景中自造业务组件类

**错误示例**:
```html
<!-- ❌ 错误：在 B 端场景中自造业务组件类 -->
<div class="status-badge error">严重告警</div>

<!-- ❌ 错误：在 AI 工作台中自造聊天气泡类 -->
<div class="chat-message-left">...</div>
```

**正确示例**:
```html
<!-- ✅ 正确：复用官方组件并通过修饰符或内容扩展 -->
<span class="badge badge-error">严重告警</span>

<div class="message-bubble message-bubble--assistant">
  <!-- AI 回复内容 -->
</div>
```

**规则**:
- B 端和 AI 场景中，应优先复用 `.badge`、`.b-stat-change`、`.message-bubble`、`.tool-call-card` 等官方组件表达业务含义。
- 如需扩展样式，只能在官方组件上添加项目修饰符类（如 `b-stat-card--warning`、`message-bubble--assistant`），样式由项目 CSS 提供。
- 确需全新业务组件时，必须使用项目前缀类（如 `.pj-b-system-*`、`.pj-ai-*`），并嵌套在对应官方骨架内部。

### 问题8: 未复用官方模板导致页面与示例相似度过低

**问题描述**:
当用户要求“遵循灵境规范/对齐技能包示例”时，生成的页面结构、区域划分和类名虽然看似合法，但与 `examples/ue5_overlay_dashboard.html` 等官方模板几乎没有相似度，本质上是重新设计了一套页面。

**错误示例（思路层面）**:
- 在未访问技能安装目录（如 `~/.trae-cn/skills/lingjing-ui-core`）的情况下，仅凭记忆和零散文档自创 UE5 Overlay 页面结构；
- 没有读取 `examples/ue5_overlay_dashboard.html`，也没有基于其 DOM 骨架，仅是“参考概念”后自由发挥；
- 未从 `components/dist/lingjing-core-ue5-overlay.css` 复制官方样式文件，而是自己生成 `lingjing-core-ue5-overlay.css` 内容或用 `<style>` 写一大段覆盖样式。

**正确示例（流程层面）**:
1. **先取证技能包安装路径**：确认 UI 技能包实际安装位置，例如：
   - `c:/Users/<用户名>/.trae-cn/skills/lingjing-ui-core`
2. **使用命令复制官方资源**：通过单条命令将官方 dist 与示例复制到项目中（以 Windows 为例）：
   ```powershell
   # 复制 UE5 Overlay 样式
   copy "c:/Users/<用户名>/.trae-cn/skills/lingjing-ui-core/components/dist/lingjing-core-ue5-overlay.css" \
        "项目根路径/styles/lingjing/lingjing-core-ue5-overlay.css"

   # 复制 UE5 Overlay 示例页面骨架
   copy "c:/Users/<用户名>/.trae-cn/skills/lingjing-ui-core/examples/ue5_overlay_dashboard.html" \
        "项目根路径/pages/ue5_overlay_dashboard.html"
   ```
3. **基于官方框架层和骨架做适配**：
   - 保留 `.ue5-overlay-root` → `.ue5-overlay-viewport` → `.ue5-overlay-safe-area` 等骨架结构；
   - 顶部 HUD 必须继续使用 `.topbar-hud` 体系；
   - 在 `.detail-panel`、`.world-marker`、`.layer-switcher`、`.alert-center` 等区域中，可按 Level 1 / 2 / 3 调整数据字段、模块组合和信息架构，但不能推翻框架层；
   - 必要的项目专用元素，通过“组件扩展梯度”（内容扩展 → 修饰符 → 项目前缀组件）嵌入现有骨架中。

**规则**:
- 当用户强调“对齐技能包/对标示例”时，AI 必须先复用官方框架层与最近似模板证据；若整页结构高匹配，可走 Level 1；若主体内容不高匹配，则可直接进入 Level 2 / Level 3，但必须在摘要中说明原因，禁止把“对齐示例”误解为“整页只能换字”。
- 若当前会话因权限或路径限制，**无法访问技能安装目录或读取示例文件**，AI 必须在摘要中说明“本次未能直接复用官方模板，结果仅为近似实现”，并提示存在偏差风险，禁止宣称“与技能包示例完全一致”。
- 超过 2000 行的官方资源（如 UE5 Overlay CSS）禁止通过 `read_file + write_to_file` 分段复制，必须通过 `RunCommand + copy` / `cp` 一次性复制，确保与技能包保持 100% 一致。

## 🔍 检查清单

在生成代码后，AI工具应该自检以下项目：

### B端系统检查清单

- [ ] ✅ 侧边栏header中，图标和logo文字是否直接作为header的子元素？
- [ ] ✅ 是否避免使用 `.b-sidebar-brand` 等额外容器？
- [ ] ✅ logo文字是否使用了 `.b-sidebar-logo` 类？
- [ ] ✅ 导航链接的active状态是否正确组合？（`.b-sidebar-nav-link.active`）
- [ ] ✅ 统计卡片的变化趋势是否正确组合？（`.b-stat-change.positive`）

### 网站场景检查清单

- [ ] ✅ 卡片涟漪效果是否使用了 `mouseenter` 事件而不是 `click`？
- [ ] ✅ 涟漪效果是否只应用于网站卡片，不包括B端组件？
- [ ] ✅ 导航链接的active状态是否正确组合？（`.website-nav-link.active`）
- [ ] ✅ 是否正确使用了修复后的类名？
  - ✅ `website-hero-description` 而不是 `website-hero-subtitle`
  - ✅ `website-hero-actions` 而不是 `website-hero-buttons`
  - ✅ `website-btn-outline` 而不是 `website-btn-secondary`
  - ✅ `website-solution-card` 而不是 `website-card-glass`

### 通用检查清单

- [ ] ✅ 页面当前采用的是 `Level 1 / Level 2 / Level 3` 中哪一级，自己是否已经说明清楚？
- [ ] ✅ 是否避免单独使用状态修饰符类（`.active`, `.positive`, `.negative`）？
- [ ] ✅ 按钮尺寸修饰符是否确认存在于CSS中？
- [ ] ✅ 是否使用了 `website-container` 类包裹网站内容？
- [ ] ✅ 图标是否正确初始化？（`lucide.createIcons()`）
- [ ] ✅ 若页面落在独立项目中，样式资源是否已放入项目内，且从生成文件的实际位置访问时路径仍然成立？

### UE5 HUD / 告警 / 图层观感检查清单（仅 UE5 Web Overlay 场景）

**常见问题**：
- HUD、告警中心、图层切换等区域虽然使用了正确的类名，但整体观感“块状沉重”，遮挡了三维视图核心区域；
- 世界标注样式过小或对比度不足，在真实三维背景上几乎看不清；
- 告警列表和详情面板没有任何加载/错误反馈，导致出现空白卡片。

**错误示例（结构上对，观感上错）**：
```html
<!-- ❌ 错误：HUD 和告警面板遮挡视图中央，面板不透明且没有层次 -->
<div class="ue5-overlay-root">
  <div class="ue5-overlay-viewport">
    <div class="ue5-overlay-safe-area">
      <header class="topbar-hud topbar-hud--solid">
        <!-- HUD 内容，背景为完全不透明深色块 -->
      </header>
      <section class="detail-panel detail-panel--full-screen">
        <!-- 占据视口中央的大块面板 -->
      </section>
      <aside class="alert-center alert-center--solid">
        <!-- 告警列表，背景完全不透明，遮挡右上大面积区域 -->
      </aside>
    </div>
  </div>
</div>
```

**改进方向**：
- 使用技能包提供的玻璃态与边框样式（如 `--ue5-overlay-panel-bg`、`--ue5-overlay-panel-border`）保持通透感；
- 优先将 HUD、告警、图层切换固定在视口四角或边缘，保留中央区域给三维场景；
- 为告警列表、图层切换等异步数据区域添加 loading/错误状态占位。

**检查清单**：
- [ ] ✅ HUD 顶栏是否贴边布局，且背景为半透明/玻璃态而非完全不透明的块？
- [ ] ✅ 告警中心和图层切换是否位于视口边缘区域，避免覆盖三维视图的核心关注区？
- [ ] ✅ `world-marker` 是否具备足够的可见性（尺寸、对比度、hover/active 状态）以适应不同视距？
- [ ] ✅ Overlay 内部的图表/列表是否定义了 loading/错误状态，而不是在加载时直接展示空白区域？

### B 端表格页信息密度与层次检查清单

**常见问题**：
- 表格行距过大，信息密度不足，看起来像“营销官网风格”而不是 B 端系统；
- 所有模块间距类似，缺少“统计区 / 操作区 / 表格区”的层次；
- 关键操作分散在多处按钮上，用户难以判断主操作在哪里。

**错误示例**：
```html
<!-- ❌ 错误：表格行距过大，操作分散，缺少明显层次 -->
<main class="b-main">
  <div class="b-content">
    <section class="content-card" style="margin-bottom: 48px;">
      <!-- 统计区：只有一行文本，留白过多 -->
    </section>
    <section class="content-card" style="margin-bottom: 48px;">
      <div class="table-toolbar">
        <button class="btn-primary">新增</button>
        <button class="btn-secondary">导出</button>
        <button class="btn-secondary">更多操作</button>
      </div>
      <table class="advanced-data-table b-table-lg">
        <!-- 每行高度很高，文本稀疏，看起来像移动端卡片列表 -->
      </table>
    </section>
  </div>
</main>
```

**改进方向**：
- 控制表格行高，使用更紧凑的表格样式（例如去掉多余的上下 padding），同时保留可读性；
- 通过间距与结构划分出“统计区 / 筛选区 / 表格区 / 底部辅助信息”，避免所有模块堆成一列相同卡片；
- 将主操作（如“新增”）放在 `table-toolbar` 左侧或明显位置，其他次要操作收纳到下拉/更多菜单中。

**检查清单**：
- [ ] ✅ 表格行高是否兼顾信息密度与可读性（避免既像表格又像巨型卡片列表）？
- [ ] ✅ 是否通过明确的模块划分和间距，让统计区、筛选区、表格区层次清晰？
- [ ] ✅ 关键操作是否集中在 `table-toolbar` 中，并在视觉上优先于次要操作？

---

## 📚 相关文档

- [SKILL.md](../../SKILL.md) - 主执行协议
- [scene_coverage_matrix.yml](../../scene_coverage_matrix.yml) - Level 判定、框架层强一致与 canonical 真相源
- [CLASS_NAME_REFERENCE.md](./CLASS_NAME_REFERENCE.md) - 完整类名清单

---

## 🔄 版本状态

### v3.1.0+ (2026-03-24)
- 本文档保留为“问题排查 / 实践建议”索引，不再承担主协议职责。
- 页面落地、Level 判定、框架层强一致、类名归一化与验收字段，统一以 `SKILL.md` + `scene_coverage_matrix.yml` 为准。
- 含运行时 `<style>` / `element.style.*` 的历史片段仅作原理示意，不作为新项目默认实现。

---

**最后更新**: 2026-03-24
**适用版本**: v3.1.0+
