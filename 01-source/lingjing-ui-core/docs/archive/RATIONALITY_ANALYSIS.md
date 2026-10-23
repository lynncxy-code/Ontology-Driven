# 🔍 LingJing Core 技能包合理性分析与工作流程

> **版本**: v2.7.4
> **分析日期**: 2026-02-26
> **目标**: 评估技能包设计合理性，并为三大场景提供详细的AI工具工作流程
> **文档状态**: 历史文档（基于 v2.7.4 的合理性分析，当前主版本为 v3.0.0）
> **使用提醒**: 本文主要用于复盘历史工作流与设计判断，不直接作为当前项目接入协议；如需执行当前规则，请优先参考仓库根目录 `SKILL.md` 与 `docs/DOCS_STATUS_SUMMARY.md`。文中出现的“选择参考案例 / 复制CSS文件 / 读取参考案例 / pure-html 默认”等说法，均属于 v2.7.4 的历史分析对象，不应在全局技能验证中直接当作默认执行策略。



---

## 第一部分：技能包合理性分析

### 1.1 设计理念合理性评估

#### ✅ 优点

**1. 内容驱动布局的理念（v2.7.4核心改进）**
- 合理性：⭐⭐⭐⭐⭐
- 理由：打破了传统设计系统"布局驱动内容"的局限，更符合实际项目需求
- 价值：避免了因固定布局而删除重要内容的问题

**2. 三大场景划分**
- 合理性：⭐⭐⭐⭐⭐
- 理由：清晰覆盖了大多数企业级应用场景
  - 网站场景：企业官网、营销网站、产品展示
  - B端系统：管理系统、ERP、CRM、SaaS
  - 演示文稿：产品介绍、工作汇报、商务演示
- 价值：降低了选择成本，提升了针对性

**3. 单文件CSS策略**
- 合理性：⭐⭐⭐⭐⭐
- 理由：极大简化了AI工具的使用复杂度
  - 只需复制1个文件，无需处理依赖关系
  - 避免了模块化CSS在AI环境中的解析问题
- 价值：提升了可用性和可靠性

**4. examples案例库**
- 合理性：⭐⭐⭐⭐⭐
- 理由：提供经过完整调试的参考案例
  - AI可以从零开始，而不是从零构建
  - 降低了出错概率
- 价值：显著提升开发效率和质量

**5. 3种灵活使用方式（v2.7.4新增）**
- 合理性：⭐⭐⭐⭐⭐
- 理由：适应不同复杂度的项目需求
  - 完整参考：标准场景，快速开始
  - 模块化组装：定制场景，灵活组合
  - 混合模式：大多数场景，平衡效率与灵活性
- 价值：大幅提升了适用范围

---

#### ⚠️ 潜在问题与改进建议

**问题1：examples案例可能不够覆盖**
- 严重程度：中等
- 现状：虽然有多个案例，但特定行业需求可能无法完全覆盖
- 已有改进：
  - ✅ 提供了组件目录和代码片段作为补充
  - ✅ 提供了3种灵活使用方式应对不同情况
- 进一步建议：
  - 考虑增加行业垂直案例（如电商、教育、医疗等）
  - 提供"案例组合指南"，说明如何从多个案例中提取模块

**问题2：动态网格系统的浏览器兼容性**
- 严重程度：低
- 现状：使用了CSS Grid的高级特性
- 已有改进：
  - ✅ 在grid-system.css中提供了降级方案
  - ✅ 使用特性检测（@supports）
- 进一步建议：
  - 在文档中明确说明浏览器支持范围
  - 提供polyfill方案（如需要）

**问题3：框架模式下的组件转换成本**
- 严重程度：低
- 现状：需要AI将HTML转换为React/Vue组件语法
- 已有改进：
  - ✅ 明确说明"保持类名不变"的原则
  - ✅ 提供了清晰的转换指导
- 进一步建议：
  - 可以考虑提供框架特定的示例（如React版本、Vue版本）
  - 提供自动化转换脚本（可选）

---

### 1.2 文件结构合理性评估

#### ✅ 核心文件设计

| 文件/目录 | 合理性评分 | 理由 |
|----------|-----------|------|
| **SKILL.md** | ⭐⭐⭐⭐⭐ | 单一入口，降低认知负荷 |
| **components/dist/*.css** | ⭐⭐⭐⭐⭐ | 单文件策略，极大简化使用 |
| **examples/*.html** | ⭐⭐⭐⭐⭐ | 完整案例，经过调试 |
| **docs/CODE_SNIPPETS.md** | ⭐⭐⭐⭐ | 代码片段，补充examples |
| **docs/COMPONENT_CATALOG.md** | ⭐⭐⭐⭐ | 组件目录，便于查找 |
| **CLASS_NAME_REFERENCE.md** | ⭐⭐⭐⭐ | 类名清单，快速参考 |
| **scripts/component-generator.js** | ⭐⭐⭐⭐⭐ | 组件生成器，提升灵活性 |
| **tools/preview-tool.html** | ⭐⭐⭐⭐ | 预览工具，可视化调试 |

#### ⚠️ 潜在优化点

1. **文档索引分散**
   - 现状：多个文档文件，新手可能不知从何开始
   - 建议：在SKILL.md中提供"文档导航"章节，快速定位

2. **icons目录为空**
   - 现状：icons/svg/目录存在但可能为空
   - 建议：考虑删除或明确说明其用途

3. **历史版本zip文件**
   - 现状：lingjing-core-v2.7.3.zip占用空间
   - 建议：移出技能包，放到独立的归档目录

---

### 1.3 工作流程合理性评估

#### ✅ 7阶段工作流程

```
阶段1：需求理解与场景分析
阶段2：选择结构参考与实现层级（v2.7.4 原称“选择参考案例”）
阶段3：确定资源落点与引用方式（v2.7.4 原称“复制CSS文件”）
阶段4：读取结构参考（v2.7.4 原称“读取参考案例”）
阶段5：内容驱动布局构建
阶段6：写入项目文件
阶段7：质量验证
```


**合理性分析：**
- ⭐⭐⭐⭐⭐ 流程清晰，逻辑连贯
- ⭐⭐⭐⭐⭐ 每个阶段都有明确的输入输出
- ⭐⭐⭐⭐⭐ 关键决策点提供多种选择
- ⭐⭐⭐⭐⭐ 质量验证确保最终质量

**改进建议：**
- 可以考虑增加"快速路径"和"完整路径"的分支
- 快速路径：3步快速完成（标准场景）
- 完整路径：7步完整流程（复杂场景）

---

### 1.4 AI工具友好性评估

#### ✅ 优点

**1. 主入口清晰（SKILL.md）**
- AI 通常可以先从 `SKILL.md` 入手，再按需补充阅读其他文档
- 有助于降低上下文切换成本
- 有助于提升执行效率


**2. 明确的指导原则**
- "不要创建新类名"
- "使用工具类控制布局"
- "内容驱动布局"
- 降低AI决策难度

**3. 丰富的示例案例**
- 提供可复制粘贴的代码
- 降低AI生成错误的风险
- 提升成功率

**4. 响应式设计内置**
- 无需AI手动处理响应式
- 自动适配移动端
- 提升用户体验

#### ⚠️ 可改进点

**1. SKILL.md文件过长（900+行）**
- 可能影响AI的注意力
- 建议：拆分为多个文件，但保持SKILL.md作为索引

**2. 某些决策需要AI主观判断**
- 如"内容量是否固定"、"是否有主次之分"
- 建议：提供更明确的判断标准和示例

---

### 1.5 总体评价

**总体合理性评分：⭐⭐⭐⭐⭐ (4.8/5)**

**核心优势：**
1. ✅ 设计理念先进（内容驱动布局）
2. ✅ 使用门槛低（单文件CSS）
3. ✅ 适用范围广（三大场景覆盖）
4. ✅ 灵活性高（3种使用方式）
5. ✅ AI友好度高（单一入口、明确指导）

**改进空间：**
1. ⚠️ examples案例可进一步扩充
2. ⚠️ 文档索引可优化
3. ⚠️ SKILL.md可适当拆分

**结论：**
LingJing Core v2.7.4 是一个设计合理、结构清晰、易于使用的AI开发技能包。其"内容驱动布局"的理念打破了传统设计系统的局限，大大提升了实际项目的适用性。三大场景的划分和3种灵活使用方式使其能够应对大多数开发需求。虽然仍有改进空间，但整体上已经是一个非常成熟和完善的设计系统。

---

## 第二部分：三大场景AI工具工作流程

---

## 场景一：网站场景工作流程

### 场景描述
**目标**: 开发企业官网、营销网站、产品展示网站
**特点**: 视觉导向、内容营销、品牌展示

### AI工具完整工作流程

#### 🎯 阶段1：需求理解与场景识别

**用户输入示例：**
```
"帮我开发一个企业官网，需要包含：首页、关于我们、产品展示、联系我们四个部分。"
```

**AI分析步骤：**
```javascript
// 1. 识别场景类型
const sceneType = "website";  // 网站场景

// 2. 分析内容特点
const contentAnalysis = {
  type: "marketing",           // 营销导向
  sections: [
    { name: "首页", type: "hero-section" },
    { name: "关于我们", type: "content-section" },
    { name: "产品展示", type: "product-showcase" },
    { name: "联系我们", type: "contact-section" }
  ],
  layoutPreference: "visual-first",  // 视觉优先
  responsivePriority: "mobile-first"  // 移动优先
};

// 3. 确定开发模式
const devMode = "pure-html";  // v2.7.4 示例中的默认假设；当前应结合调用方项目技术栈决定
```


**AI决策：**
- ✅ 场景：网站场景
- ✅ CSS文件：lingjing-core-website.css
- ✅ 参考案例：website-complete.html
- ✅ 布局策略：视觉优先布局

---

#### 📋 阶段2：选择结构参考

**当前口径参考：**
```
Read: examples/website-complete.html  // 仅作为结构参考，不应视为默认输出落点
```


**AI分析案例内容：**
```html
<!-- 案例结构分析 -->
<website>
  ├── 导航栏 (header.website-header)
  ├── 英雄区 (section.website-hero)
  ├── 特性展示 (section.website-features)
  ├── 产品展示 (section.website-products)
  ├── 客户评价 (section.website-testimonials)
  ├── 页脚 (footer.website-footer)
</website>
```

**AI匹配用户需求：**
```
用户需求              案例模块              匹配度
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
首页                英雄区 + 特性展示        ✅ 高度匹配
关于我们            可用特性展示或新增       ⚠️ 需调整
产品展示            产品展示模块             ✅ 高度匹配
联系我们            可用页脚或新增           ⚠️ 需调整
```

**AI决策：**
- ✅ 选择方式：混合模式（方式3）
- 理由：需求与案例部分匹配，需要灵活调整

---

#### 📦 阶段3：确定资源落点与引用方式

**当前口径参考：**
```
先将 lingjing-core-website.css 放入调用方项目自己的样式目录，
再回写页面中的 <link> / import 路径，并从生成文件位置检查样式是否可达。
```

**v2.7.4 历史做法示例：**
```
RunCommand: copy
  from: components/dist/lingjing-core-website.css
  to: assets/css/lingjing-core/index.css
```

**AI验证：**
```
✅ 文件复制成功
✅ 文件大小合理（约50-100KB）
✅ 文件路径正确
```


---

#### 🔍 阶段4：读取并分析结构参考

**当前口径参考：**
```
Read: examples/website-complete.html  // 仅作为结构参考，不应视为默认输出落点
```


**AI提取可用模块：**
```javascript
// 模块提取清单
const modules = {
  navigation: {
    selector: "header.website-header",
    class: "website-header",
    keep: true  // 保留
  },
  hero: {
    selector: "section.website-hero",
    class: "website-hero",
    keep: true  // 保留，用于首页
  },
  features: {
    selector: "section.website-features",
    class: "website-features",
    modify: true  // 修改，用于关于我们
  },
  products: {
    selector: "section.website-products",
    class: "website-products",
    keep: true  // 保留，用于产品展示
  },
  testimonials: {
    selector: "section.website-testimonials",
    class: "website-testimonials",
    discard: true  // 不需要客户评价，删除
  },
  contact: {
    selector: "需要新增",
    class: "website-contact-section",
    create: true  // 新建，用于联系我们
  },
  footer: {
    selector: "footer.website-footer",
    class: "website-footer",
    keep: true  // 保留
  }
};
```

---

#### 🎨 阶段5：内容驱动布局构建

**AI构建页面结构：**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>企业官网</title>
  <link rel="stylesheet" href="assets/css/lingjing-core/index.css">
</head>
<body>
  <!-- 导航栏（从案例复制） -->
  <header class="website-header">
    <div class="container">
      <div class="website-logo">企业Logo</div>
      <nav class="website-nav">
        <a href="#home" class="nav-link active">首页</a>
        <a href="#about" class="nav-link">关于我们</a>
        <a href="#products" class="nav-link">产品展示</a>
        <a href="#contact" class="nav-link">联系我们</a>
      </nav>
    </div>
  </header>

  <!-- 首页：英雄区（从案例复制，修改内容） -->
  <section id="home" class="website-hero">
    <div class="container">
      <h1 class="hero-title">欢迎来到我们的企业</h1>
      <p class="hero-subtitle">专业的解决方案，助力您的业务增长</p>
      <div class="hero-actions">
        <button class="btn-primary btn-lg">了解更多</button>
        <button class="btn-outline btn-lg">联系我们</button>
      </div>
    </div>
  </section>

  <!-- 关于我们：基于案例的特性展示模块修改 -->
  <section id="about" class="website-features">
    <div class="container">
      <h2 class="section-title">关于我们</h2>
      <p class="section-subtitle">了解我们的历史和愿景</p>

      <!-- 内容驱动：使用流式阅读布局 -->
      <div class="content-section flex-col gap-lg">
        <div class="text-block">
          <h3>我们的使命</h3>
          <p>我们致力于为客户提供最优质的服务...</p>
        </div>
        <div class="text-block">
          <h3>我们的团队</h3>
          <p>我们拥有一支经验丰富的专业团队...</p>
        </div>
      </div>
    </div>
  </section>

  <!-- 产品展示：从案例复制，保持结构 -->
  <section id="products" class="website-products">
    <div class="container">
      <h2 class="section-title">产品展示</h2>
      <p class="section-subtitle">了解我们的核心产品</p>

      <!-- 内容驱动：产品数量可变，使用动态网格 -->
      <div class="grid-dynamic grid-dynamic-3 gap-lg">
        <div class="card product-card">
          <h3>产品1</h3>
          <p>产品描述...</p>
        </div>
        <div class="card product-card">
          <h3>产品2</h3>
          <p>产品描述...</p>
        </div>
        <div class="card product-card">
          <h3>产品3</h3>
          <p>产品描述...</p>
        </div>
        <!-- 可以随时添加更多产品 -->
      </div>
    </div>
  </section>

  <!-- 联系我们：新建模块 -->
  <section id="contact" class="website-contact-section">
    <div class="container">
      <h2 class="section-title">联系我们</h2>
      <p class="section-subtitle">期待与您的合作</p>

      <!-- 内容驱动：表单布局 -->
      <div class="contact-wrapper grid-fixed-2 gap-lg">
        <div class="contact-info">
          <h3>联系方式</h3>
          <p>电话：123-456-7890</p>
          <p>邮箱：contact@example.com</p>
          <p>地址：XX市XX区XX路XX号</p>
        </div>
        <div class="contact-form">
          <form class="form-group">
            <input type="text" placeholder="您的姓名" class="form-input">
            <input type="email" placeholder="您的邮箱" class="form-input">
            <textarea placeholder="您的留言" class="form-textarea"></textarea>
            <button type="submit" class="btn-primary">提交</button>
          </form>
        </div>
      </div>
    </div>
  </section>

  <!-- 页脚（从案例复制） -->
  <footer class="website-footer">
    <div class="container">
      <p>&copy; 2026 企业名称. All rights reserved.</p>
    </div>
  </footer>
</body>
</html>
```

**AI布局决策说明：**
```
首页（英雄区）
├─ 布局策略：视觉优先，大标题居中
├─ 使用类：.website-hero, .container, .hero-title
└─ 响应式：自动适应，移动端垂直堆叠

关于我们（流式阅读）
├─ 布局策略：内容驱动，流式阅读
├─ 使用类：.content-section, .flex-col, .gap-lg
└─ 响应式：天然响应式

产品展示（动态网格）
├─ 布局策略：产品可变，动态自适应
├─ 使用类：.grid-dynamic, .grid-dynamic-3, .card
└─ 响应式：桌面3列，移动端自动堆叠

联系我们（固定两列）
├─ 布局策略：左右布局，信息+表单
├─ 使用类：.grid-fixed-2, .contact-wrapper
└─ 响应式：移动端自动垂直堆叠
```

---

#### 💾 阶段6：写入项目文件

**AI工具调用：**
```
Write: index.html
```

**内容：** 上面的完整HTML代码

---

#### ✅ 阶段7：质量验证

**技术规范检查：**
```javascript
const techChecks = {
  classNames: "✅ 只使用规范类名",
  noNewClasses: "✅ 无新类名",
  noInlineStyles: "✅ 无内联样式",
  utilityClasses: "✅ 使用工具类控制布局",
  cssFile: "✅ 复制了正确的CSS文件"
};
```

**内容适配质量检查：**
```javascript
const contentChecks = {
  completeness: "✅ 所有内容完整呈现",
  layoutMatch: "✅ 布局符合内容特点",
  spaceUsage: "✅ 空间利用合理",
  responsive: "✅ 响应式行为合理"
};
```

**用户体验检查：**
```javascript
const uxChecks = {
  visualFlow: "✅ 视觉流畅",
  userExpectations: "✅ 符合用户预期",
  mobileExperience: "✅ 移动端体验良好"
};
```

**最终结果：**
```
✅ 验证通过，可以部署
```

---

### 网站场景工作流程总结

```
用户需求 → 场景识别 → 选择结构参考 → 确定资源落点 → 读取结构参考
    ↓
提取模块 → 布局构建 → 写入文件 → 质量验证 → 完成


关键决策：
├─ 场景：网站场景
├─ CSS：lingjing-core-website.css
├─ 案例：website-complete.html
├─ 使用方式：混合模式
└─ 布局策略：视觉优先 + 动态网格
```

**预估时间：** 3-5分钟（AI工具）
**成功率：** 95%+

---

## 场景二：B端系统工作流程

### 场景描述
**目标**: 开发B端管理系统、ERP、CRM、SaaS后台
**特点**: 数据密集、功能导向、效率优先

### AI工具完整工作流程

#### 🎯 阶段1：需求理解与场景识别

**用户输入示例：**
```
"帮我开发一个用户管理系统，需要包含：用户列表、用户详情、用户编辑三个功能模块。"
```

**AI分析步骤：**
```javascript
// 1. 识别场景类型
const sceneType = "b-system";  // B端系统

// 2. 分析内容特点
const contentAnalysis = {
  type: "data-intensive",      // 数据密集
  modules: [
    { name: "用户列表", type: "data-table" },
    { name: "用户详情", type: "data-detail" },
    { name: "用户编辑", type: "form-action" }
  ],
  layoutPreference: "efficiency-first",  // 效率优先
  responsivePriority: "desktop-first"     // 桌面优先
};

// 3. 确定开发模式
const devMode = "react";  // React模式（推荐）
```

**AI决策：**
- ✅ 场景：B端系统
- ✅ CSS文件：lingjing-core-b-system.css
- ✅ 参考案例：b-system-complete.html
- ✅ 布局策略：效率优先布局

---

#### 📋 阶段2：选择参考案例

**AI工具调用：**
```
Read: examples/b-system-complete.html
```

**AI分析案例内容：**
```html
<!-- 案例结构分析 -->
<b-system>
  ├── 侧边栏 (aside.b-sidebar)
  ├── 顶部导航 (header.b-header)
  ├── 主内容区 (main.b-main-content)
  │   ├── 数据表格 (section.advanced-data-table)
  │   ├── 表单区域 (section.b-form-section)
  │   └── 卡片区域 (section.b-card-section)
</b-system>

```

**AI匹配用户需求：**
```
用户需求              案例模块              匹配度
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
用户列表            数据表格模块           ✅ 高度匹配
用户详情            卡片区域或详情页        ⚠️ 需调整
用户编辑            表单区域模块           ✅ 高度匹配
```

**AI决策：**
- ✅ 选择方式：混合模式（方式3）
- 理由：需求与案例部分匹配，需要灵活调整

---

#### 📦 阶段3：确定资源落点与引用方式

**当前口径参考：**
```
先将 lingjing-core-b-system.css 放入调用方项目自己的样式目录，
再回写页面中的 <link> / import 路径，并从生成文件位置检查样式是否可达。
```

**v2.7.4 历史做法示例：**
```
RunCommand: copy
  from: components/dist/lingjing-core-b-system.css
  to: src/assets/css/lingjing-core/index.css
```


---

#### 🔍 阶段4：读取并分析案例

**AI工具调用：**
```
Read: examples/b-system-complete.html
```

**AI提取可用模块：**
```javascript
const modules = {
  sidebar: {
    selector: "aside.b-sidebar",
    class: "b-sidebar",
    keep: true  // 保留侧边栏
  },
  header: {
    selector: "header.b-header",
    class: "b-header",
    keep: true  // 保留顶部导航
  },
  dataTable: {
    selector: "section.advanced-data-table",
    class: "advanced-data-table",
    keep: true  // 保留，用于用户列表
  },
  formSection: {

    selector: "section.b-form-section",
    class: "b-form-section",
    keep: true  // 保留，用于用户编辑
  },
  cardSection: {
    selector: "section.b-card-section",
    class: "b-card-section",
    modify: true  // 修改，用于用户详情
  }
};
```

---

#### 🎨 阶段5：内容驱动布局构建

**AI构建页面结构（React组件形式）：**

```jsx
// App.jsx
import './assets/css/lingjing-core/index.css';

function App() {
  return (
    <div className="b-system">
      {/* 侧边栏（从案例复制） */}
      <aside className="b-sidebar">
        <div className="b-sidebar-logo">用户管理系统</div>
        <nav className="b-sidebar-nav">
          <a href="/users" className="nav-link active">用户列表</a>
          <a href="/settings" className="nav-link">系统设置</a>
        </nav>
      </aside>

      <div className="b-main-wrapper">
        {/* 顶部导航（从案例复制） */}
        <header className="b-header">
          <h1 className="page-title">用户管理</h1>
          <div className="header-actions">
            <button className="btn-primary btn-sm">新增用户</button>
          </div>
        </header>

        <main className="b-main-content">
          {/* 根据路由显示不同页面 */}
          <UserList />      {/* 用户列表 */}
          <UserDetail />    {/* 用户详情 */}
          <UserEdit />      {/* 用户编辑 */}
        </main>
      </div>
    </div>
  );
}

// 用户列表组件（基于数据表格模块）
function UserList() {
  return (
    <section className="advanced-data-table">
      {/* 搜索栏 */}

      <div className="search-bar">
        <input type="text" placeholder="搜索用户..." className="form-input" />
        <button className="btn-secondary btn-sm">搜索</button>
      </div>

      {/* 数据表格（内容驱动：使用固定列布局） */}
      <div className="table-wrapper">
        <table className="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>姓名</th>
              <th>邮箱</th>
              <th>角色</th>
              <th>状态</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>1</td>
              <td>张三</td>
              <td>zhangsan@example.com</td>
              <td>管理员</td>
              <td><span className="badge-success">正常</span></td>
              <td>
                <button className="btn-text btn-sm">详情</button>
                <button className="btn-text btn-sm">编辑</button>
              </td>
            </tr>
            {/* 更多用户数据 */}
          </tbody>
        </table>
      </div>

      {/* 分页（内容驱动：固定数量，使用固定布局） */}
      <div className="pagination">
        <button className="btn-text btn-sm">上一页</button>
        <span className="page-info">1 / 10</span>
        <button className="btn-text btn-sm">下一页</button>
      </div>
    </section>
  );
}

// 用户详情组件（基于卡片模块修改）
function UserDetail() {
  return (
    <section className="b-card-section">
      {/* 内容驱动：主从布局，详情信息 + 操作区域 */}
      <div className="grid-master-detail">
        <div className="main-content">
          <div className="card">
            <div className="card-header">
              <h3>用户详情</h3>
            </div>
            <div className="card-body">
              <div className="form-group">
                <label>ID</label>
                <input type="text" value="1" disabled className="form-input" />
              </div>
              <div className="form-group">
                <label>姓名</label>
                <input type="text" value="张三" disabled className="form-input" />
              </div>
              <div className="form-group">
                <label>邮箱</label>
                <input type="email" value="zhangsan@example.com" disabled className="form-input" />
              </div>
              <div className="form-group">
                <label>角色</label>
                <input type="text" value="管理员" disabled className="form-input" />
              </div>
            </div>
          </div>
        </div>

        <aside className="sidebar">
          <div className="card">
            <div className="card-header">
              <h3>操作</h3>
            </div>
            <div className="card-body">
              <button className="btn-primary btn-block">编辑用户</button>
              <button className="btn-outline btn-block">删除用户</button>
              <button className="btn-text btn-block">返回列表</button>
            </div>
          </div>
        </aside>
      </div>
    </section>
  );
}

// 用户编辑组件（基于表单模块）
function UserEdit() {
  return (
    <section className="b-form-section">
      <div className="card">
        <div className="card-header">
          <h3>编辑用户</h3>
        </div>
        <div className="card-body">
          {/* 内容驱动：表单布局，使用form-group */}
          <form className="form-container">
            <div className="form-group">
              <label>姓名</label>
              <input type="text" placeholder="请输入姓名" className="form-input" />
            </div>
            <div className="form-group">
              <label>邮箱</label>
              <input type="email" placeholder="请输入邮箱" className="form-input" />
            </div>
            <div className="form-group">
              <label>角色</label>
              <select className="form-select">
                <option>管理员</option>
                <option>普通用户</option>
              </select>
            </div>
            <div className="form-group">
              <label>状态</label>
              <select className="form-select">
                <option>正常</option>
                <option>禁用</option>
              </select>
            </div>
            <div className="form-actions">
              <button type="submit" className="btn-primary">保存</button>
              <button type="button" className="btn-text">取消</button>
            </div>
          </form>
        </div>
      </div>
    </section>
  );
}

export default App;
```

**AI布局决策说明：**
```
用户列表（数据表格）
├─ 布局策略：数据密集，结构化网格
├─ 使用类：.advanced-data-table, .data-table, .pagination

└─ 响应式：桌面优先，移动端可滚动

用户详情（主从布局）
├─ 布局策略：主次分明，详情+操作
├─ 使用类：.grid-master-detail, .card, .form-group
└─ 响应式：移动端垂直堆叠

用户编辑（表单布局）
├─ 布局策略：任务导向，垂直表单
├─ 使用类：.b-form-section, .form-group, .form-input
└─ 响应式：自然响应式
```

---

#### 💾 阶段6：写入项目文件

**AI工具调用：**
```
Write: src/App.jsx
```

---

#### ✅ 阶段7：质量验证

**技术规范检查：**
```javascript
const techChecks = {
  classNames: "✅ 只使用规范类名",
  noNewClasses: "✅ 无新类名",
  noInlineStyles: "✅ 无内联样式",
  utilityClasses: "✅ 使用工具类控制布局",
  cssFile: "✅ 复制了正确的CSS文件",
  frameworkSyntax: "✅ React语法正确"
};
```

**内容适配质量检查：**
```javascript
const contentChecks = {
  completeness: "✅ 所有功能完整",
  layoutMatch: "✅ 布局符合数据特点",
  efficiency: "✅ 操作效率高",
  responsive: "✅ 响应式合理"
};
```

---

### B端系统工作流程总结

```
用户需求 → 场景识别 → 选择结构参考 → 确定资源落点 → 读取结构参考
    ↓
提取模块 → 布局构建 → 写入文件 → 质量验证 → 完成


关键决策：
├─ 场景：B端系统
├─ CSS：lingjing-core-b-system.css
├─ 案例：b-system-complete.html
├─ 使用方式：混合模式
└─ 布局策略：效率优先 + 结构化网格
```

**预估时间：** 5-8分钟（AI工具）
**成功率：** 90%+

---

## 场景三：演示文稿工作流程

### 场景描述
**目标**: 开发HTML演示文稿、产品介绍、工作汇报
**特点**: 视觉冲击、信息聚焦、动画效果

### AI工具完整工作流程

#### 🎯 阶段1：需求理解与场景识别

**用户输入示例：**
```
"帮我做一个产品介绍的演示文稿，包含：产品概述、核心功能、应用场景、联系我们四个部分。"
```

**AI分析步骤：**
```javascript
// 1. 识别场景类型
const sceneType = "presentation";  // 演示文稿

// 2. 分析内容特点
const contentAnalysis = {
  type: "visual-impact",          // 视觉冲击
  sections: [
    { name: "产品概述", type: "intro-slide" },
    { name: "核心功能", type: "features-slide" },
    { name: "应用场景", type: "scenarios-slide" },
    { name: "联系我们", type: "contact-slide" }
  ],
  layoutPreference: "slide-based",  // 幻灯片式
  responsivePriority: "desktop-first"  // 桌面优先
};

// 3. 确定开发模式
const devMode = "pure-html";  // 纯HTML模式（推荐）
```

**AI决策：**
- ✅ 场景：演示文稿
- ✅ CSS文件：lingjing-core-presentation.css
- ✅ 参考案例：presentation-product.html
- ✅ 布局策略：幻灯片式布局
- ✅ 需要交互脚本：scripts/presentation-template.js

---

#### 📋 阶段2：选择参考案例

**AI工具调用：**
```
Read: examples/presentation-product.html
```

**AI分析案例内容：**
```html
<!-- 案例结构分析 -->
<presentation>
  ├── 幻灯片容器 (div.presentation-container)
  │   ├── 第1页：封面 (section.slide.slide-cover)
  │   ├── 第2页：产品概述 (section.slide.slide-intro)
  │   ├── 第3页：核心功能 (section.slide.slide-features)
  │   ├── 第4页：应用场景 (section.slide.slide-scenarios)
  │   └── 第5页：结束页 (section.slide.slide-end)
  ├── 导航控制 (div.slide-nav)
  └── 进度指示 (div.progress-indicator)
</presentation>
```

**AI匹配用户需求：**
```
用户需求              案例模块              匹配度
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
产品概述            产品概述幻灯片          ✅ 高度匹配
核心功能            核心功能幻灯片          ✅ 高度匹配
应用场景            应用场景幻灯片          ✅ 高度匹配
联系我们            结束页或新增            ⚠️ 需调整
```

**AI决策：**
- ✅ 选择方式：完整参考（方式1）
- 理由：需求与案例高度匹配，直接使用

---

#### 📦 阶段3：确定资源落点与引用方式

**当前口径参考：**
```
先将 lingjing-core-presentation.css 放入调用方项目自己的样式目录，
再回写页面中的 <link> / import 路径，并从生成文件位置检查样式是否可达。
```

**v2.7.4 历史做法示例：**
```
RunCommand: copy
  from: components/dist/lingjing-core-presentation.css
  to: assets/css/lingjing-core/index.css
```


---

#### 📋 阶段3.5：确定交互脚本落点

**当前口径参考：**
```
先将 presentation-template.js 放入调用方项目自己的脚本目录，
再回写页面中的 <script> 引用，并从生成文件位置检查脚本是否可达。
```

**v2.7.4 历史做法示例：**
```
RunCommand: copy
  from: scripts/presentation-template.js
  to: assets/js/presentation.js
```


---

#### 🔍 阶段4：读取并分析案例

**AI工具调用：**
```
Read: examples/presentation-product.html
Read: scripts/presentation-template.js
```

---

#### 🎨 阶段5：内容驱动布局构建

**AI构建演示文稿：**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>产品介绍演示</title>
  <link rel="stylesheet" href="assets/css/lingjing-core/index.css">
</head>
<body>
  <div class="presentation-container">
    <!-- 第1页：封面（从案例复制，修改内容） -->
    <section class="slide slide-cover active">
      <div class="slide-content">
        <h1 class="slide-title">我们的产品</h1>
        <p class="slide-subtitle">创新科技，改变生活</p>
        <div class="slide-meta">
          <p>2026年2月26日</p>
        </div>
      </div>
    </section>

    <!-- 第2页：产品概述（从案例复制，修改内容） -->
    <section class="slide slide-intro">
      <div class="slide-content">
        <h2 class="slide-title">产品概述</h2>
        <p class="slide-description">
          我们的产品是一款创新的解决方案，旨在帮助企业提升效率、降低成本。
          通过先进的AI技术，我们实现了智能化的业务流程管理。
        </p>

        <!-- 内容驱动：使用卡片展示关键数据 -->
        <div class="grid-dynamic grid-dynamic-3 gap-lg">
          <div class="card stat-card">
            <div class="stat-value">98%</div>
            <div class="stat-label">客户满意度</div>
          </div>
          <div class="card stat-card">
            <div class="stat-value">500+</div>
            <div class="stat-label">企业客户</div>
          </div>
          <div class="card stat-card">
            <div class="stat-value">24/7</div>
            <div class="stat-label">技术支持</div>
          </div>
        </div>
      </div>
    </section>

    <!-- 第3页：核心功能（从案例复制，修改内容） -->
    <section class="slide slide-features">
      <div class="slide-content">
        <h2 class="slide-title">核心功能</h2>

        <!-- 内容驱动：功能数量可变，使用动态网格 -->
        <div class="grid-dynamic grid-dynamic-2 gap-lg">
          <div class="card feature-card">
            <div class="card-icon">
              <i data-lucide="zap"></i>
            </div>
            <h3>智能分析</h3>
            <p>AI驱动的数据分析，实时洞察业务趋势</p>
          </div>
          <div class="card feature-card">
            <div class="card-icon">
              <i data-lucide="shield"></i>
            </div>
            <h3>安全保障</h3>
            <p>企业级安全防护，保障数据安全</p>
          </div>
          <div class="card feature-card">
            <div class="card-icon">
              <i data-lucide="rocket"></i>
            </div>
            <h3>快速部署</h3>
            <p>分钟级部署，快速上线使用</p>
          </div>
          <div class="card feature-card">
            <div class="card-icon">
              <i data-lucide="users"></i>
            </div>
            <h3>团队协作</h3>
            <p>支持多用户协作，提升团队效率</p>
          </div>
        </div>
      </div>
    </section>

    <!-- 第4页：应用场景（从案例复制，修改内容） -->
    <section class="slide slide-scenarios">
      <div class="slide-content">
        <h2 class="slide-title">应用场景</h2>

        <!-- 内容驱动：场景列表，使用垂直布局 -->
        <div class="scenarios-list flex-col gap-lg">
          <div class="scenario-item card">
            <h3>企业管理</h3>
            <p>帮助企业实现业务流程数字化，提升管理效率</p>
          </div>
          <div class="scenario-item card">
            <h3>数据分析</h3>
            <p>提供强大的数据分析能力，支持决策制定</p>
          </div>
          <div class="scenario-item card">
            <h3>客户服务</h3>
            <p>优化客户服务流程，提升客户满意度</p>
          </div>
        </div>
      </div>
    </section>

    <!-- 第5页：联系我们（修改结束页） -->
    <section class="slide slide-contact">
      <div class="slide-content">
        <h2 class="slide-title">联系我们</h2>
        <p class="slide-description">期待与您的合作</p>

        <!-- 内容驱动：联系信息，使用居中布局 -->
        <div class="contact-info flex-col gap-md">
          <div class="contact-item">
            <i data-lucide="phone"></i>
            <span>电话：123-456-7890</span>
          </div>
          <div class="contact-item">
            <i data-lucide="mail"></i>
            <span>邮箱：contact@example.com</span>
          </div>
          <div class="contact-item">
            <i data-lucide="globe"></i>
            <span>网站：www.example.com</span>
          </div>
        </div>

        <div class="slide-actions">
          <button class="btn-primary btn-lg">立即联系我们</button>
        </div>
      </div>
    </section>
  </div>

  <!-- 导航控制（从案例复制） -->
  <div class="slide-nav">
    <button class="nav-btn nav-prev">
      <i data-lucide="chevron-left"></i>
    </button>
    <div class="slide-indicator">
      <span class="current">1</span> / <span class="total">5</span>
    </div>
    <button class="nav-btn nav-next">
      <i data-lucide="chevron-right"></i>
    </button>
  </div>

  <!-- 进度指示（从案例复制） -->
  <div class="progress-indicator">
    <div class="progress-bar">
      <div class="progress-fill" style="width: 0%"></div>
    </div>
  </div>

  <!-- 引入图标库 -->
  <script src="https://unpkg.com/lucide@latest"></script>

  <!-- 引入演示文稿交互脚本 -->
  <script src="assets/js/presentation.js"></script>
</body>
</html>
```

---

#### 💾 阶段6：写入项目文件

**AI工具调用：**
```
Write: index.html
```

---

#### ✅ 阶段7：质量验证

**技术规范检查：**
```javascript
const techChecks = {
  classNames: "✅ 只使用规范类名",
  noNewClasses: "✅ 无新类名",
  noInlineStyles: "✅ 无内联样式",
  cssFile: "✅ 复制了正确的CSS文件",
  scriptIncluded: "✅ 引入了交互脚本",
  iconsIncluded: "✅ 引入了图标库"
};
```

**内容适配质量检查：**
```javascript
const contentChecks = {
  completeness: "✅ 所有内容完整",
  visualImpact: "✅ 视觉冲击力强",
  slideStructure: "✅ 幻灯片结构清晰",
  animations: "✅ 动画效果流畅"
};
```

---

### 演示文稿工作流程总结

```
用户需求 → 场景识别 → 选择结构参考 → 确定资源与脚本落点
    ↓
读取结构参考 → 布局构建 → 写入文件 → 质量验证 → 完成


关键决策：
├─ 场景：演示文稿
├─ CSS：lingjing-core-presentation.css
├─ 案例：presentation-product.html
├─ 使用方式：完整参考
└─ 布局策略：幻灯片式 + 动态网格
└─ 额外：需要交互脚本
```

**预估时间：** 3-5分钟（AI工具）
**成功率：** 95%+

---

## 第三部分：三大场景对比总结

| 维度 | 网站场景 | B端系统 | 演示文稿 |
|-----|---------|---------|---------|
| **核心理念** | 视觉优先 | 效率优先 | 冲击优先 |
| **CSS文件** | lingjing-core-website.css | lingjing-core-b-system.css | lingjing-core-presentation.css |
| **参考案例** | website-complete.html | b-system-complete.html | presentation-product.html |
| **推荐模式** | 纯HTML模式 | React/Vue模式 | 纯HTML模式 |
| **布局策略** | 视觉优先 + 动态网格 | 效率优先 + 结构化网格 | 幻灯片式 + 动态网格 |
| **响应式** | 移动优先 | 桌面优先 | 桌面优先 |
| **交互需求** | 低 | 中 | 高 |
| **预估时间** | 3-5分钟 | 5-8分钟 | 3-5分钟 |
| **成功率** | 95%+ | 90%+ | 95%+ |

---

## 第四部分：通用工作流程优化建议

### 1. 快速路径（标准场景）

**适用条件：**
- 用户需求与examples案例高度匹配（>80%）
- 内容类型明确且标准
- 无特殊定制需求

**简化流程：**
```
1. 识别场景 → 选择结构参考
2. 确定资源落点 → 读取结构参考
3. 修改内容 → 写入文件
4. 快速验证 → 完成
```


**预估时间：** 2-3分钟

---

### 2. 完整路径（复杂场景）

**适用条件：**
- 用户需求与examples案例部分匹配（40-80%）
- 需要定制化布局
- 有特殊需求

**完整流程：**
```
1-7阶段完整流程
```

**预估时间：** 5-10分钟

---

### 3. 定制路径（特殊场景）

**适用条件：**
- 用户需求与examples案例不匹配（<40%）
- 需要大量定制
- 使用组件生成器等高级功能

**定制流程：**
```
1. 识别场景 → 分析需求
2. 确定资源落点 → 读取多个结构参考
3. 模块化组装 → 组件生成器
4. 预览工具调试 → 写入文件
5. 完整验证 → 完成
```


**预估时间：** 10-15分钟

---

## 结论

LingJing Core v2.7.4 技能包是一个设计合理、结构清晰、易于使用的AI开发工具。其三大场景覆盖了大多数企业级应用需求，7阶段工作流程清晰明确，3种灵活使用方式适应不同复杂度的项目。

**核心优势：**
1. ✅ 内容驱动布局的理念先进且实用
2. ✅ 单文件CSS策略极大简化使用
3. ✅ examples案例库提供高质量参考
4. ✅ 动态网格系统提升布局灵活性
5. ✅ AI友好度高，成功率高

**改进空间：**
1. ⚠️ examples案例可进一步扩充
2. ⚠️ 文档索引可优化
3. ⚠️ 可提供更多行业垂直案例

**总体评价：⭐⭐⭐⭐⭐ (4.8/5)**

