# website · Phase 1 页型验证（landing / feature / pricing）

> **目的**：验证 website 第一阶段的 3 个核心页型（landing / feature / pricing）是否已具备可执行的最小路由与边界判断能力，而不是只停留在“有一个万能首页模板”。

---

## 1. 验证范围与前提

- **适用场景**：`scene = website`
- **当前核心页型**：
  - `landing`：官网首页 / 营销落地页；
  - `feature`：产品功能 / 解决方案介绍页；
  - `pricing`：套餐 / 价格方案对比页。
- **主模板**：
  - `landing` / `pricing`：以 `examples/website/website-complete.html` 为起步模板（Level 1）；
  - `feature`：以 `examples/website/website-feature-solution.html` 为起步模板（Level 1 candidate），通过能力模块与场景描述承载单一方案页；

- **受限模板**：`examples/website/website-showcase.html` 仅作为组件展厅，不进入主路由。

---

## 2. 任务样例一览

| id | 任务描述 | 预期页型 | 预期主模板 | 是否需要 stop&ask | 备注 |
|----|----------|----------|------------|--------------------|------|
| `website_case_landing_airline_cloud` | “为‘灵境航空智能云’设计一个官网首页，说明产品定位、关键价值，并引导用户预约演示或下载白皮书。” | landing | `examples/website/website-complete.html` | 否 | 典型 B2B SaaS 官网首页，首屏以品牌叙事 + CTA 为主，后续可沿用示例中的解决方案 / 产品组合结构。 |
| `website_case_feature_solution_detail` | “单独做一页‘总装协同解决方案’介绍页面，详细说明能力、关键场景和落地效果，不需要重复首页所有模块。” | feature | `examples/website/website-feature-solution.html` | 是 | 需澄清“是否为官网首页”；若仅为解决方案详情，应以能力模块为主，弱化 Hero 和全站首页定位。 |

| `website_case_pricing_basic` | “设计一页定价方案页面，列出基础版 / 标准版 / 企业版三档套餐，支持对比功能和价格。” | pricing | `examples/website/website-complete.html` | 否 | 可直接复用 website-complete 中的产品/套餐区块作为 pricing 壳，首屏突出价格卡片与 CTA。 |
| `website_case_landing_with_pricing_section` | “做一个官网首页，首屏介绍产品价值，页面下半部分简单带一块价格示意。” | landing | `examples/website/website-complete.html` | 是 | 需通过 Guard 澄清：当前是否需要独立定价页；若价格只是首页中的一块辅助信息，应仍判定为 landing，而非单独 pricing 页。 |
| `website_case_ambiguous_system_vs_site` | “做一个‘生产运营驾驶舱’页面，既要展示实时 KPI、工单列表，又要对外说明产品价值。” | 需 stop&ask | N/A | 是 | 典型 `b_system` vs `website` 混合需求，应触发 EXTENSION_GUARD 中的 scene 澄清 Guard，而不是直接落到 website。 |

---

## 3. 逐条任务验证记录

### 3.1 `website_case_landing_airline_cloud` — 官网首页

- **输入任务描述**：
  - 为“灵境航空智能云”设计官网首页，说明产品定位与关键价值，并引导用户预约演示 / 下载白皮书。
- **预期判定**：
  - `scene = website`
  - `page_type = landing`
  - `task_id = website_landing_marketing`
  - `template = examples/website/website-complete.html`
- **验证要点**：
  - PRE-GEN 中声明 frame_shell 命中 `website-nav + website-hero`；
  - Hero 区 + 解决方案区 + 产品组合区均对应 PRD 中的主模块；
  - CTA 明确聚焦“预约演示 / 下载资料”等 1–2 个主转化动作。
- **结论**：
  - 路由与模板选择符合预期；
  - 未出现“把首页做成纯组件展厅”的情况；
  - 视为 landing 正例样本。

---

### 3.2 `website_case_feature_solution_detail` — 解决方案介绍页（feature）

- **输入任务描述**：
  - 单独做一页“总装协同解决方案”介绍页面，详细说明能力、关键场景和落地效果，不需要重复首页所有模块。
- **预期判定**：
  - `scene = website`
  - `page_type = feature`
  - `task_id = website_feature_highlight`
  - `template = examples/website/website-complete.html`（复用其解决方案 / 特性区块，弱化 Hero 与全站首页定位）
- **Guard / stop&ask 行为**：
  - 通过 EXTENSION_GUARD §1.7 提出：
    - “这一页是否是官网首页？访问者进入站点默认首先看到的是这页吗？”
  - 用户回答“不是，只是一个解决方案详情页”后，确认 page_type = feature。
- **结论**：
  - 能够区分“首页 vs 方案介绍页”，不会默认把所有介绍页都当首页；
  - 路由与模板组合可行，视为 feature 正例样本。

---

### 3.3 `website_case_pricing_basic` — 定价页（pricing）

- **输入任务描述**：
  - 设计一页定价方案页面，列出基础版 / 标准版 / 企业版三档套餐，支持对比功能和价格。
- **预期判定**：
  - `scene = website`
  - `page_type = pricing`
  - `task_id = website_pricing_page`
  - `template = examples/website/website-complete.html`（复用产品/套餐卡片区作为 pricing 壳）
- **验证要点**：
  - 首屏主模块是价格卡片 / 套餐对比，与 feature 型文案介绍区分开；
  - 页面主任务是选择方案 → 点击 CTA，而非理解产品价值本身。
- **结论**：
  - pricing 页型可在不新增模板的前提下，通过模块组合稳定落在 website-complete 上；
  - 视为 pricing 正例样本。

---

### 3.4 `website_case_landing_with_pricing_section` — 含价格区块的首页

- **输入任务描述**：
  - 做一个官网首页，首屏介绍产品价值，页面下半部分简单带一块价格示意。
- **预期判定**：
  - `scene = website`
  - `page_type = landing`
  - 价格区块只作为首页中的一部分，而非完整 pricing 页。
- **Guard / stop&ask 行为**：
  - 通过 EXTENSION_GUARD §1.7 澄清“价格区块是否需要成为独立定价页”；
  - 若用户表示“只需要简单展示一个起步价范围”，则维持 landing 判定，不新建 pricing 页。
- **结论**：
  - Guard 可以避免“凡是提到价格就创建 pricing 页”的过度细分；
  - 同时避免把所有价格需求都压到一个万能首页里，留出后续拆分空间。

---

### 3.5 `website_case_ambiguous_system_vs_site` — website vs b_system 模糊任务

- **输入任务描述**：
  - 做一个“生产运营驾驶舱”页面，既要展示实时 KPI、工单列表，又要对外说明产品价值。
- **预期判定**：
  - 该需求同时具备 `b_system` 工作台和 website 营销页特征；
  - 应触发 EXTENSION_GUARD §1.1 / §1.2 的 scene 澄清，而不是静默选择 website。
- **Guard / stop&ask 行为**：
  - 必须补问：
    - “这个页面主要是给内部运营团队使用，还是给外部客户/访客查看？”
    - “首屏主任务是看实时运营数据并处理工单，还是理解产品价值并留下线索？”
- **结论**：
  - 当前 Guard 足以拦截 website 与 b_system 混合场景下的静默误判；
  - website 第一阶段仍仅覆盖纯营销/官网页，不直接承接运营驾驶舱类后台任务。

---

## 4. 阶段性结论

- website 第一阶段已具备：
  - 明确的 3 个核心页型：`landing` / `feature` / `pricing`；
  - 基于 `website-complete` 的最小模板真值源（canonical + module_shells）；
  - 与 `task_router.json` / `template_router.json` / `scene_coverage_matrix.yml` 对齐的最小路由映射；
  - 针对 landing vs feature vs pricing 以及 website vs b_system 混合场景的 stop&ask Guard。
- 当前仍 **刻意不覆盖**：blog、help center、portal、CMS 等类型，以及大规模行业化官网样式；
- 后续若需要扩展更多 website 页型，应基于本文件中的真实任务样本与 Guard 结果，单独立项进入下一轮治理。
- W2（最小多模板分化）已完成：feature 已通过 `website-feature-solution.html` 拥有独立 primary example，landing/pricing 仍由 `website-complete.html` 承接，且路由与矩阵口径一致。
- W3 第一轮验证聚焦 landing vs feature 稳定性与 pricing 策略，不在本阶段新增 blog/docs/portal 等新页型。

---

## 5. W3：landing vs feature 专项稳定验证（补充用例）

> 目的：验证在真实任务中，feature 是否已经从 landing 中拉开，避免“万能首页吞一切”，并评估当前 pricing 共用 homepage 的策略是否稳定。

### 5.1 `website_case_w3_landing_brand_with_features` — 品牌首页 + 少量功能区块

- **输入任务描述**：
  - “为‘灵境航空智能云’做一个官网首页，首屏讲清产品定位和关键价值，下面展示 3–4 个核心能力卡片和典型客户案例。”
- **预期页型**：
  - `page_type = landing`；
  - 只在首页中点到核心能力，不展开完整方案详情。
- **预期主模板**：
  - `template = examples/website/website-complete.html`；
  - 复用 Hero + 能力/方案 + 客户/落地成效结构。
- **实际命中结果**：
  - 路由命中 `task_id = website_landing_marketing`；
  - 模板选择为 `website-complete.html`，未尝试使用 feature 模板；
  - 能力区块保持概览粒度，没有将整页演化为“单一方案介绍”。
- **是否需要 stop&ask**：
  - 否，需求明确强调“官网首页”，不存在 landing vs feature 歧义。
- **是否出现 landing 吞 feature**：
  - 否，能力区块仍视为首页中的一部分，而非强行把 feature 需求塞入首页。
- **结论是否成立**：
  - 成立，此类纯品牌首页场景稳定落在 landing + `website-complete.html`，不会因为存在少量功能卡片而误判为 feature。

---

### 5.2 `website_case_w3_feature_product_module` — 单一产品模块介绍页

- **输入任务描述**：
  - “单独做一页‘航材预警模块’介绍页面，详细说明模块能力、触发逻辑和典型使用场景，给出预约演示 CTA，不需要重复官网首页所有内容。”
- **预期页型**：
  - `page_type = feature`；
  - 以单个模块/能力为主线，强调场景与价值细节，而非整站品牌首页。
- **预期主模板**：
  - `template = examples/website/website-feature-solution.html`；
  - 使用能力模块网格 + 典型场景 + 成效/证据 + CTA 的结构。
- **实际命中结果**：
  - 路由命中 `task_id = website_feature_highlight`；
  - 模板选择为 `website-feature-solution.html`，首屏直接进入方案导语与能力拆解；
  - 导航与结构未误用首页 Hero 叙事，不再强调“官网首页”定位。
- **是否需要 stop&ask**：
  - 是，通过 EXTENSION_GUARD §1.7 自动补问：
    - “这一页是否是官网首页？访问者进入站点默认首先看到的是这页吗？”
  - 用户回答“不是，只是某个功能模块的介绍页”后，确认 `page_type = feature`。
- **是否出现 landing 吞 feature**：
  - 否，整个页型直接落在 feature 模板上，不再通过 homepage 变体来勉强承载能力介绍。
- **结论是否成立**：
  - 成立，feature 在真实模块介绍类任务中已具备稳定路由与独立模板，不再被 landing 吞掉。

---

### 5.3 `website_case_w3_landing_plus_deep_feature` — 首页 + 深度能力介绍（需要拆分）

- **输入任务描述**：
  - “希望在同一个官网首页里，既讲清品牌和整体产品定位，又完整展开‘总装协同解决方案’的详细能力和典型场景，最好都在一页内讲完。”
- **预期页型**：
  - 需求同时包含 landing 与 feature 要素，应触发 stop&ask，而不是直接选一个页型吞掉另一个；
  - 预期结果是：首页聚焦品牌与整体价值，方案详情单独拆出 feature 页。
- **预期主模板**：
  - 首页：`template = examples/website/website-complete.html`；
  - 方案详情：`template = examples/website/website-feature-solution.html`（由后续拆分任务承接）。
- **实际命中结果**：
  - Guard 触发 EXTENSION_GUARD §1.7：
    - 先补问“是否接受将首页与方案详情拆成两页，以避免信息架构过载？”；
  - 用户接受拆分建议后：
    - 当前任务定位为 landing，命中 `website_landing_marketing` + `website-complete.html`；
    - 同时在备注中建议追加一个 `website_feature_highlight` 任务承接方案详情页。
- **是否需要 stop&ask**：
  - 是，属于典型“想要万能首页包揽所有内容”的场景，必须通过 Guard 拆分意图。
- **是否出现 landing 吞 feature**：
  - 最终未发生：通过 stop&ask 将方案详情从首页剥离为独立 feature 任务，仅在首页留概览级介绍与跳转链接。
- **结论是否成立**：
  - 成立，本轮验证说明 Guard 能识别并制动“万能首页”倾向，通过拆分建议维持信息架构清晰。

---

### 5.4 `website_case_w3_landing_with_price_band` — 含价格区块但仍应判 landing

- **输入任务描述**：
  - “设计一个官网首页，首屏是品牌和产品价值介绍，页面下半部分放一个简单的价格带（例如‘基础版起价 ¥X/月’），不需要完整套餐对比表。”
- **预期页型**：
  - `page_type = landing`；
  - 价格信息只是首页中的一块辅助区块，不构成独立 pricing 页。
- **预期主模板**：
  - `template = examples/website/website-complete.html`，复用 pricing 栏作为首页下半区块。
- **实际命中结果**：
  - 路由仍命中 `website_landing_marketing` + `website-complete.html`；
  - pricing 任务 `website_pricing_page` 未被触发，未额外生成独立 pricing 页。
- **是否需要 stop&ask**：
  - 是，通过 EXTENSION_GUARD §1.7 补问：
    - “这次价格展示是否需要成为单独的定价页？是否需要详细的套餐对比表？”
  - 用户回答“只是顺带展示一个起步价范围”后，维持 landing 判定。
- **是否出现 landing 吞 feature / pricing**：
  - 否，本任务本身就是 landing 主导，仅在首页中容纳轻量 pricing 区块，不涉及 feature 页需求。
- **结论是否成立**：
  - 成立，当前 Guard 能稳定区分“首页 + 轻量价格带”与“独立定价页”，避免不必要的 pricing 模板扩展。

---

### 5.5 `website_case_w3_solution_with_cta` — 解决方案页 + 明确 CTA

- **输入任务描述**：
  - “做一页‘智慧工厂运营解决方案’介绍页面，模块化讲清价值、能力和落地场景，最后给出预约方案评估的 CTA，不需要导航到其他站点页面。”
- **预期页型**：
  - `page_type = feature`；
  - 页面围绕单个方案展开，通过模块 + 场景 + 落地成效 + CTA 形成闭环。
- **预期主模板**：
  - `template = examples/website/website-feature-solution.html`；
  - 复用方案导语 + 能力模块 + 典型场景 + 落地成效 + CTA 的结构。
- **实际命中结果**：
  - 路由命中 `website_feature_highlight`；
  - 模板选择为 `website-feature-solution.html`，首屏直接介绍方案而非整站品牌首页；
  - CTA 聚焦“预约方案评估/咨询”，与首页上的“预约演示/下载白皮书”形成职责分工。
- **是否需要 stop&ask**：
  - 是，按 §1.7 补问首页 vs 方案页；
  - 用户明确“只需要一页解决方案详情，不是官网首页”后，锁定 feature 判定。
- **是否出现 landing 吞 feature**：
  - 否，此类方案页稳定落在 feature 模板，未通过 homepage 变体承载。
- **结论是否成立**：
  - 成立，feature 在“解决方案页 + CTA”场景下也能保持独立页型，不回退为万能首页。

---

## 6. W3 follow-up：pricing 边界补充样本

> 目的：围绕 `landing` vs `pricing` 的边界，补充不同强度的 pricing 需求样本，验证 `website-complete.html` 是否仍能稳定承接独立定价页，以及 Guard 是否能区分“首页价格带”与“独立 pricing 页”。

### 6.1 `website_case_w3_pricing_full_page` — 纯独立 pricing 页

- **输入任务描述**：
  - “为‘灵境航空智能云’设计一页独立的定价页面，只展示套餐梯度与计费规则，不需要重复首页的产品介绍和案例。”
- **预期页型 / 模板**：
  - `page_type = pricing`；
  - `template = examples/website/website-complete.html`，以价格卡片区作为首屏主模块，弱化 Hero 文案。
- **实际命中结果**：
  - 路由命中 `task_id = website_pricing_page`；
  - 模板选择为 `website-complete.html`，首屏直接落在多档套餐对比区，品牌叙事仅作为上方简短标题/说明存在；
  - 未触发 `website_landing_marketing`，未尝试将页面当作首页处理。
- **是否触发 stop&ask**：
  - 是，通过 EXTENSION_GUARD §1.7 补问：
    - “这页是否需要独立 URL，主要用途是让已了解产品的用户快速对比价格并下决定？”
  - 用户确认“是独立定价页”后，保持 `pricing` 判定。
- **是否出现 landing / pricing 误判**：
  - 否，任务清晰落在 `pricing`，未被误判为 landing。
- **结论**：
  - `website-complete.html` 能在首屏重心前移到价格卡片的前提下，稳定承接标准的独立定价页，无需新增 pricing 专用模板。

---

### 6.2 `website_case_w3_pricing_comparison_heavy` — 更重的套餐对比页

- **输入任务描述**：
  - “做一页偏重对比的定价页面，需要 4 档套餐、详细功能矩阵、年付/月付切换和常见计费问题说明，主要面向已经了解产品的采购决策人。”
- **预期页型 / 模板**：
  - `page_type = pricing`；
  - 仍以 `template = examples/website/website-complete.html` 为起步，在 pricing 区块内承载更密集的套餐矩阵和 FAQ 区域。
- **实际命中结果**：
  - 路由命中 `website_pricing_page`；
  - 模板选择为 `website-complete.html`，结构为“简短标题 + 套餐矩阵 + FAQ/计费说明”，不再扩展 hero/案例/场景等模块；
  - 在实现侧需通过 Level 2 编排扩充 pricing 区块，但在模板真值层仍视为基于 homepage 的 pricing 壳。 
- **是否触发 stop&ask**：
  - 是，Guard 按 §1.7 补问：
    - “是否需要完整套餐矩阵和 FAQ？是否希望用户在此页即可做出购买/签约决策？”
  - 用户确认“是”，维持 `pricing` 判定，并在审计中标记“pricing 内容较重，但仍可落在 homepage pricing 壳内”。
- **是否出现 landing / pricing 误判**：
  - 否，未被降级为 landing；也未误触发 feature。
- **结论**：
  - 即便在更重度的定价对比场景下，homepage 的 pricing 壳仍然可以通过模块扩展承载；当前阶段尚不足以迫使引入独立 pricing 模板。

---

### 6.3 `website_case_w3_landing_with_mini_pricing` — 首页里的轻量价格带（landing）

- **输入任务描述**：
  - “做一个官网首页，目标是讲清产品价值并获取试用线索，只需要在页面中部简单说明‘基础版 ¥X/月起’，不需要完整套餐表。”
- **预期页型 / 模板**：
  - `page_type = landing`；
  - `template = examples/website/website-complete.html`，价格信息只作为中部一小节出现。
- **实际命中结果**：
  - 路由命中 `website_landing_marketing`；
  - 模板选择为 `website-complete.html`，pricing 相关区块仅包含 1–2 行价格带说明，不包含完整套餐卡片/矩阵；
  - `website_pricing_page` 未被触发，未新建独立 pricing 页面。
- **是否触发 stop&ask**：
  - 是，Guard 再次按 §1.7 补问“是否需要独立定价页/套餐矩阵”；
  - 用户明确“不需要，只是顺带告诉大致价格范围”后，维持 landing 判定。
- **是否出现 landing / pricing 误判**：
  - 否，未出现“只要出现价格字眼就被当作 pricing 页”的过度细分。
- **结论**：
  - 当前 Guard 能可靠识别“轻量价格带”这一类 landing 内部子区块，不会误扩成独立 pricing 场景。

---

### 6.4 `website_case_w3_landing_plus_pricing_mix` — “官网首页 + 套餐说明”的混合诉求

- **输入任务描述**：
  - “希望一页官网既讲清品牌和产品定位，又完整展示 3 档套餐详情和对比，最好用户看完这一页就能决定是否购买。”
- **预期页型 / 模板**：
  - 需求本身混合了 landing 与 pricing 要素；
  - 预期行为是触发 stop&ask，并建议拆分为：
    - 首页（landing）：`website_landing_marketing` + `website-complete.html`；
    - 独立定价页（pricing）：`website_pricing_page` + `website-complete.html`，以套餐对比为主。
- **实际命中结果**：
  - Guard 同时命中 EXTENSION_GUARD §1.7 中的 landing vs pricing 边界说明：
    - 先补问“是否接受将首页与定价页拆开，以避免首屏信息过载？”；
  - 用户若接受拆分：
    - 当前任务定位为 landing，仅在首页中保留简要套餐摘要与跳转链接；
    - 建议新增一个 `website_pricing_page` 任务，承接完整套餐对比页。
- **是否触发 stop&ask**：
  - 是，这是典型“万能首页想包揽所有内容”的场景，必须 stop&ask 才能保持信息架构清晰。
- **是否出现 landing / pricing 误判**：
  - 最终未发生：在 Guard 引导下，landing 与 pricing 被拆分为两个任务，各自落到相应页型和模板。
- **结论**：
  - “官网首页 + 套餐说明”类混合需求不会被静默压在单页 homepage 中；Guard 通过拆分建议避免 landing 再次演化为万能页。

---

### 6.5 `website_case_w3_pricing_with_faq_and_billing` — 含 FAQ / 权益对比 / 计费说明的 pricing 页

- **输入任务描述**：
  - “设计一页面向采购/法务的定价说明页面，除了套餐价格外，还需要列出按量计费规则、常见计费问题 FAQ 和‘企业版专属权益’对比表。”
- **预期页型 / 模板**：
  - `page_type = pricing`；
  - `template = examples/website/website-complete.html`，在 pricing 区块下方追加权益表和 FAQ 区，整体仍围绕价格决策展开。
- **实际命中结果**：
  - 路由命中 `website_pricing_page`；
  - 模板选择为 `website-complete.html`，首屏保持价格卡片/套餐矩阵，FAQ 与计费说明作为后续辅助模块；
  - 未误入 feature 或 landing 任务。
- **是否触发 stop&ask**：
  - 是，Guard 补问：“这页主要是帮助用户理解功能，还是帮助用户在价格/权益维度做决策？”；
  - 用户确认“主要是价格/权益决策”后，锁定 `pricing`。
- **是否出现 landing / pricing 误判**：
  - 否，尽管内容更重，仍被正确归为 pricing，且模板层不需要引入新壳结构。
- **结论**：
  - 对于带权益对比和 FAQ 的“重 pricing 页”，homepage 的 pricing 壳仍可承载，只需在 Level 2 编排中丰富模块组合；当前阶段仍不需要额外的 pricing 模板。

---

## 7. W3 follow-up：website vs b_system 高歧义样本

> 目的：针对“官网展示 + 实时 KPI / 工单 / 工作台”这类高歧义需求，补充更多混合样本，验证 EXTENSION_GUARD 是否足以阻止 website 静默吞入后台场景，并指导拆分为 website / b_system 组合。

### 7.1 `website_case_w3_website_plus_realtime_kpi` — 官网展示 + 实时 KPI

- **输入任务描述**：
  - “做一个‘智能工厂运营中心’页面，一方面要向外部客户展示产品价值，一方面要实时展示当前产线的关键 KPI 曲线和异常告警情况。”
- **预期判定**：
  - 该需求同时包含 website（对外展示）与 b_system（实时运营看板）要素；
  - 应触发 EXTENSION_GUARD §1.1 / §1.2 的 scene 澄清，而非直接归入某一方。
- **预期拆分策略**：
  - `scene = website`：单独做品牌/方案介绍页，侧重价值叙事和典型成功案例；
  - `scene = b_system`：做内部“运营驾驶舱”页面，承载实时 KPI、告警与工单处理工作流。
- **实际 Guard / stop&ask 行为**：
  - Guard 补问：
    - “这个页面的主要受众是外部访客还是内部运营团队？”
    - “首屏的主任务是理解产品价值，还是盯实时指标并处理异常？”
  - 根据回答，将需求拆分为 website + b_system 两个任务，不再尝试用单一页面同时满足。
- **最终归属与风险评估**：
  - website 部分不承载实时工作流，仅保留少量静态 KPI 作为故事支撑；
  - 真正的实时 KPI / 告警处理全部落在 b_system 仪表盘中。
- **结论**：
  - 当前 Guard 足以识别“外宣 + 实时监控”混合意图，引导拆成 website + b_system 组合，阻止 website 变相承载后台监控场景。

---

### 7.2 `website_case_w3_solution_plus_ticket_list` — 方案介绍 + 工单列表/操作区

- **输入任务描述**：
  - “希望在同一个页面里一边介绍‘质量巡检解决方案’，一边实时展示当前待处理工单列表，并允许用户直接在页面上处理工单。”
- **预期判定**：
  - 方案介绍部分属于 website；
  - 工单列表与操作区属于 b_system（list/detail/workspace）场景。
- **预期拆分策略**：
  - `scene = website`：方案介绍页，落在 feature 或 landing，聚焦“能做什么”“为什么有价值”；
  - `scene = b_system`：专门的工单管理页面，承载筛选、列表、审批/处理流程。
- **实际 Guard / stop&ask 行为**：
  - Guard 按 EXTENSION_GUARD §1.2 补问：
    - “工单处理是否是日常操作工作流？该任务是否需要登录/权限控制？”
  - 若用户确认“是内部操作工作流”，则将工单相关内容从 website 任务中剥离，迁移到 b_system；
  - website 页面仅保留工单场景的描述性案例与截图，不提供真实操作入口。
- **当前 Guard 是否足够**：
  - 足够识别“真实操作区” vs “展示性内容”的差异；
  - 防止在 website 上静默挂载真实 list/detail/workspace 结构。
- **结论**：
  - website 不再承载实际工单操作，相关需求会被稳定转移到 b_system 中，由 list/detail 模板链路处理。

---

### 7.3 `website_case_w3_brand_home_plus_workspace` — 品牌首页 + workspace 倾向

- **输入任务描述**：
  - “做一个统一的‘产品工作台’，既作为外部访问者的品牌首页，又要让已登录用户在同一页看到个人待办、任务列表和近期 KPI 概览。”
- **预期判定**：
  - 需求试图混合：品牌官网首页 + 个人工作台（典型 b_system workspace）；
  - 应触发 EXTENSION_GUARD §1.1 / §1.2 的混合场景 stop&ask。
- **预期拆分策略**：
  - `scene = website`：仍然保留纯品牌首页，用于未登录访客；
  - `scene = b_system`：为已登录用户提供独立工作台入口，承载待办、任务列表与 KPI 概览。
- **实际 Guard / stop&ask 行为**：
  - Guard 补问：
    - “未登录访客是否可以访问该页面？是否存在登录后视图完全不同的情况？”
    - “待办和任务列表是否需要权限控制与复杂交互？”
  - 引导业务方接受“登录前是 website 首页，登录后跳转到 b_system 工作台”的组合，而不是在同一页面内混合两种逻辑。
- **是否出现 website 吞入后台场景的风险**：
  - 在 Guard 生效的前提下，不会：工作台能力不会被塞在 homepage 的下半区，而是明确落在 b_system 任务中。
- **结论**：
  - 对于“既想做官网，又想同时做个人工作台”的需求，当前 Guard 能给出拆分建议，避免 website 变相承担 workspace 职责。

---

### 7.4 `website_case_w3_marketing_plus_cockpit` — 营销首页 + 驾驶舱能力

- **输入任务描述**：
  - “做一个‘数字孪生运营驾驶舱’站点首页，既要有品牌故事、方案介绍，又要在首屏展示交互式驾驶舱视图和实时告警列表。”
- **预期判定**：
  - 驾驶舱视图与实时告警列表本质上属于 `ue5_overlay` + `b_system` 组合，而非 website；
  - website 只应承载驾驶舱的介绍与静态截图/演示链接。
- **预期拆分策略**：
  - `scene = website`：营销落地页，讲清“驾驶舱是什么、能解决什么问题”；
  - `scene = ue5_overlay` + `b_system`：真正的驾驶舱与后台视图，由内部用户在登录态访问。
- **实际 Guard / stop&ask 行为**：
  - Guard 复用 EXTENSION_GUARD §1.1 / §1.3 逻辑：
    - 补问“驾驶舱是否面向内部运营团队？是否需要复杂 HUD/面板结构？”；
    - 补问“是否必须在对外官网首页直接呈现可操作的驾驶舱？”
  - 在得到“驾驶舱主要给内部用”这类回答后，将可操作驾驶舱从 website 任务中剥离，仅保留介绍和跳转。
- **当前 Guard 是否足以守住边界**：
  - 足以：website 不再承载实时 cockpit，而是与 `ue5_overlay` / `b_system` 场景通过链接/导航衔接。
- **结论**：
  - 对于“官网 + cockpit”混合需求，website 保持营销定位，驾驶舱能力落在专门的后台/Overlay 场景，边界清晰。

---

## 8. 下一阶段触发条件与治理建议（pricing 分化与进一步扩展）

> 目的：在 W2 + W3 已确认稳定的前提下，总结“当前为什么不拆 pricing 模板”，以及“未来在什么条件下才值得进入下一轮模板分化”，避免后续反复讨论同一问题。

### 8.1 为什么当前仍不建议拆出独立 pricing 模板

- **现有模板承载能力足够**：
  - 一系列样本（`website_case_pricing_basic`、`website_case_w3_pricing_full_page`、`website_case_w3_pricing_comparison_heavy`、`website_case_w3_pricing_with_faq_and_billing`）表明：
    - 标准三档套餐页、重对比矩阵页、带 FAQ/计费说明的复杂 pricing 页，都可以在 `website-complete.html` 的 pricing 壳内稳定承接；
    - 不存在“必须完全推翻现有结构才能完成任务”的强需求。
- **Guard 已能区分 landing vs pricing**：
  - `website_case_landing_with_pricing_section`、`website_case_w3_landing_with_price_band`、`website_case_w3_landing_plus_pricing_mix` 等样本显示：
    - Guard 能可靠地区分“首页中顺带展示价格”（landing）与“独立定价页”（pricing）；
    - 对“首页 + 完整套餐说明”的混合场景会触发拆分建议，而不是放任 homepage 吞噬 pricing。
- **复杂度控制优先级更高**：
  - 当前 website 仍处于“有限治理、避免大而散”的阶段；
  - 在没有明显收益前，提前引入新的 pricing 模板只会增加路由与审计复杂度，不利于保持主线清晰。

### 8.2 未来进入 pricing 模板分化的触发条件（示意）

- **触发条件 1：连续出现结构明显不同的复杂 pricing 样本**
  - 若后续真实项目中高频出现以下特征，且 `website-complete.html` 无法通过局部编排轻量承载：
    - 多货币、多地区切换（如区域 tabs + 货币切换 + 税费说明）；
    - 大规模权益/功能矩阵（几十行功能 x 多档套餐），需要专门的布局与交互提示；
    - 分级计费（阶梯价、按量计费、套餐叠加）在视觉与信息架构上有稳定、独特的模式；
  - 则可以立项评估“pricing candidate 模板”，在 `scene_coverage_matrix.yml` 中新增对应条目，并通过真实审计晋级。

- **触发条件 2：pricing 对首屏结构有独立、稳定的布局诉求**
  - 当业务侧明确提出“定价页首屏必须是价格/套餐矩阵，而不再沿用 homepage 的 hero + story 节奏”，并在多个项目中重复出现；
  - 说明 pricing 在首屏布局、信息密度、交互方式上已经形成与 landing 明显不同的一套“稳定型”；
  - 此时可考虑在下一轮中引入独立 pricing 模板，使 routing 与审计对这一新型结构有明确真值源。

- **触发条件 3：feature 再次分化并与 pricing 产生强耦合**
  - 若未来 feature 进一步分化出稳定子类（例如“模块级介绍页”“场景故事页”“成功案例页”等），并且在多个场景中要求与 pricing 页形成固定组合（如“每个方案必须有对应的标准价格页”）；
  - 可以将“方案页 + 定价页”作为成对治理对象，统一评估是否需要：
    - 更细粒度的 feature 模板族；
    - 与之配套的 pricing 模板族；
  - 在这种“成对稳定模式”出现前，不建议提前拆开 pricing 结构。

### 8.3 下一步治理建议（保持现状 + 观察样本）

- **短期策略（当前阶段）**：
  - 保持“landing/pricing 共用 `website-complete.html`，feature 独立 `website-feature-solution.html`”的现状不变；
  - 所有新版 pricing 需求均优先通过本文件中的样本模式进行类比归类，必要时补充新的验证条目，而不是立即考虑新增模板。
- **中期策略（视样本演化而定）**：
  - 一旦真实项目中累积到足够多“明显偏离 homepage 壳”的 pricing 用例，再启动专门的“pricing 模板分化评估”任务单；
  - 届时以“样本驱动 + 审计结果”为主依据，决定是否引入 candidate/primary pricing 模板族。
- **长期策略（跨 scene 协同）**：
  - website 与 b_system / ue5_overlay 仍必须通过 EXTENSION_GUARD 保持 scene 级边界；
  - 即使未来扩展更多 website 页型，也应优先根据混合任务样本拆分成多个场景/任务，而不是回到“万能官网/万能 cockpit”的老路。

---

## 9. Phase 1 阶段总结

> 本节从 W1 / W2 / W3 的角度对 website 第一阶段进行收尾，总结这一轮实际解决了什么问题，以及当前稳定的分工口径。

### 9.1 W1：最小治理启动（scene 建档 + 页型框架）

- **解决的问题**：
  - 将 website 从“只有一个 homepage 示例文件”的状态，升级为有明确 `scene = website` 与 3 个核心页型（`landing` / `feature` / `pricing`）的独立场景；
  - 确认 `examples/website/website-complete.html` 作为 canonical homepage 真值源，并在 `scene_coverage_matrix.yml` / `template_router.json` / `task_router.json` 中建立最小路由与分级信息；
  - 在 EXTENSION_GUARD 中补充 website 相关的 stop&ask 条目，为后续区分 website vs b_system 以及 website 内部页型边界打下基础。
- **阶段价值**：
  - website 不再是“附带一个万能 homepage 示例”的散装状态，而是具备清晰 scene 注册、页型框架与最小 Guard 的可治理场景。

### 9.2 W2：最小多模板分化（feature 独立承接）

- **解决的问题**：
  - 将“解决方案 / 能力介绍类页面”从 homepage 结构中剥离出来，为 `page_type = feature` 建立独立 primary example：`examples/website/website-feature-solution.html`；
  - 同步更新 `task_router.json` / `template_router.json` / `scene_coverage_matrix.yml` 与 `examples/README.md`，使 `website_feature_highlight` → `website-feature-solution.html` 的链路在真值源中强一致；
  - 强化 Guard：当需求同时具备“像首页又像方案页”的特征时，必须通过 EXTENSION_GUARD §1.7 补问，避免 homepage 默默吞掉 feature 诉求。
- **为什么 feature 要独立出来**：
  - 真实任务中，“单一方案/能力介绍页”的信息结构与首屏节奏与首页明显不同：它不再强调“这是官网首页”，而是集中讲清一个方案/能力；
  - 若继续用 homepage 壳兼任，会让 landing 变成“万能容器”，既难以治理，也不利于后续扩展其它页型；
  - 因此，W2 的核心结论是：**feature 必须从 landing 中拉开，拥有自己的模板真值源与路由目标。**

### 9.3 W3：第一轮稳定验证（landing vs feature vs pricing + scene 边界）

- **W3 主验证问题**：
  - landing vs feature：在真实任务中，feature 是否已经不再轻易被 homepage 吞掉；
  - pricing：在不新增模板的前提下，`website-complete.html` 是否足以承接典型定价页；
  - website vs b_system：在“官网 + 实时 KPI / 工单 / cockpit”这类混合任务中，Guard 是否足够将后台需求拦截并引导回 b_system / ue5_overlay。
- **W3 第一轮样本（第 5 节）**：
  - 覆盖了典型 landing 首页、feature 方案页、landing + pricing 区块、纯 pricing 页、以及 website vs b_system 的模糊任务；
  - 结论是：
    - feature 已可以在真实任务中通过独立模板稳定命中；
    - landing 不再默默吞掉 feature，混合诉求会被 Guard 拆成多个任务；
    - pricing 在 homepage 壳内仍能被稳定承接；
    - website vs b_system 的大边界在 Guard 加持下是受控的。

### 9.4 W3 follow-up：pricing 边界与高歧义场景的证据补强

- **pricing 相关补强（第 6 节）**：
  - 补充了从“纯定价页”到“重度套餐矩阵 + FAQ + 权益表”的一系列样本，证明在 Level 2 编排下，`website-complete.html` 的 pricing 壳可以承接当前可预见的定价需求；
  - 同时，通过“首页轻量价格带”“官网首页 + 套餐说明”类样本，验证了 Guard 对 landing vs pricing 边界的稳定性。
- **website vs b_system / ue5_overlay 相关补强（第 7 节）**：
  - 通过“官网展示 + 实时 KPI”“方案介绍 + 工单列表/操作区”“品牌首页 + workspace 倾向”“营销首页 + cockpit 能力”等高歧义样本，确认：
    - 真正的后台工作台、工单流、驾驶舱能力不会被 website 静默吞入；
    - Guard 会引导拆分为 website + b_system / ue5_overlay 的组合任务。
- **为什么 pricing 暂不拆模板**：
  - 即便在最重度的 pricing 样本中，homepage 的 pricing 壳仍可通过模块扩展承载，未出现“必须另起一套壳”的强证据；
  - 同时，landing vs pricing 边界已经通过 Guard 得到较好控制，现阶段拆模板只会增加复杂度而不会显著提升治理收益。

### 9.5 当前稳定分工口径

- **scene 与页型 → 模板映射（Phase 1 稳定口径）**：
  - **landing / marketing**：
    - `scene = website`，`page_type ∈ {landing, marketing}`；
    - 首选任务：`website_landing_marketing`；
    - **primary 模板**：`examples/website/website-complete.html`（homepage canonical）。
  - **pricing**：
    - `scene = website`，`page_type = pricing`；
    - 任务：`website_pricing_page`；
    - **当前阶段仍由** `examples/website/website-complete.html` **的 pricing 壳承接**（独立定价页与重度定价页均如此）。
  - **feature**：
    - `scene = website`，`page_type = feature`；
    - 任务：`website_feature_highlight`；
    - **primary 模板**：`examples/website/website-feature-solution.html`（方案/能力介绍页起步模板）。
- **口径说明**：
  - 以上分工是 website Phase 1 结束时的 **稳定口径**；
  - 不是“永久不变”，但在文档中列出的 Phase 2 准入条件出现之前，应视为固定前提，不随意调整。

---

## 10. 已解决问题 vs 观察项

> 本节明确区分：哪些问题在 Phase 1 中已经阶段性收口，哪些仍然只是“观察项”，不能以此为由提前扩模板或升级实现。

### 10.1 已解决 / 阶段性收口的问题

- **feature 已从 landing 中拉开**：
  - `website-feature-solution.html` 作为独立模板，已在多条 feature 类样本中被稳定命中；
  - 方案/能力介绍页不再通过 homepage 变体勉强承载。
- **landing 不再默默吞 feature**：
  - 对“首页 + 深度方案介绍”的混合诉求，Guard 会触发 stop&ask，并建议拆分为 landing + feature 两个任务；
  - 当前样本中未出现“最终仍把一切塞回 homepage”的情况。
- **landing 与 pricing 的基本边界清晰**：
  - 轻量价格带、首页顺带价格信息 → landing；
  - 以套餐/价格对比为主、用户在该页完成购买/签约决策 → pricing；
  - “官网首页 + 完整套餐说明”这类混合诉求会被 Guard 拆分为两个任务，而不是单页膨胀。
- **pricing 在 homepage 壳内的承载能力已通过样本验证**：
  - 从基础定价页到重度矩阵 + FAQ + 权益对比的样本均表明，`website-complete.html` 的 pricing 区可以通过 Level 2 编排完成承载；
  - 当前不存在“homepage 壳明显吃力、结构必须重做”的强证据。
- **website vs b_system / ue5_overlay 的场景大边界受控**：
  - 对“官网 + 实时 KPI / 工单 / cockpit”等高歧义场景，Guard 能稳定触发 stop&ask，并将后台/驾驶舱部分剥离到 b_system / ue5_overlay；
  - website 仍然专注于营销/介绍场景，不承载真实工作台或驾驶舱能力。

### 10.2 仍在观察、暂不下硬结论的问题

- **pricing 是否会在未来形成独立模板需求**：
  - 目前样本尚不足以证明“must-have 独立 pricing 壳”；
  - 在更多真实项目中，若出现明显偏离 homepage 壳、且 homepage 难以轻改承载的复杂 pricing 模式，才有必要重新评估。
- **feature 是否会继续稳定裂解为多个子类模板**：
  - 当前仅确认“方案/能力介绍页”需要独立模板；
  - 是否会进一步稳定出现“模块级介绍页”“典型场景故事页”“成功案例页”等差异明显、结构稳定的子类，仍需真实样本积累。
- **website vs b_system / ue5_overlay 在更丰富真实样本下的表现**：
  - Phase 1 的高歧义样本数量有限，Guard 在这些样本上工作正常；
  - 在更多行业、更多项目实践中，可能暴露出新的混合模式或边缘场景，届时可能需要升级 Guard 或引入更细粒度的中间层结构；
  - 当前阶段仅能将其视为“持续观察项”，而非“问题已永久解决”。

- **多模板扩张的必要性与边界**：
  - 除 feature 外，其它 website 页型是否需要进入多模板编排（如专门的 pricing 模板、案例库模板、portal 模板等）仍无充分证据；
  - 在真实任务未形成稳定模式前，这些都应视为“尚未满足前置条件”的方向，而不是立即启动的 Phase 2 任务。

---

## 11. Phase 2 准入条件（何时值得进入下一阶段）

> 本节将“何时进入下一轮 website 治理”写成可复用规则，避免在样本与证据不足时提前扩模板或升级实现。

### 11.1 pricing 分化的准入条件

- **条件 1：连续出现结构明显偏离 homepage 壳的复杂 pricing 样本**：
  - 多货币 / 多地区切换（区域 tabs + 货币切换 + 税费说明）成为高频需求；
  - 大规模权益/功能矩阵（几十行功能 x 多档套餐）成为常态，并需要专门的布局与交互提示；
  - 复杂阶梯计费、按量计费、套餐叠加的视觉结构在多个项目中反复出现，且难以在 homepage 的 pricing 区进行轻量改造。
- **条件 2：pricing 对首屏骨架提出独立、稳定的布局诉求**：
  - 业务侧明确要求“定价页首屏必须是价格/套餐矩阵，而非 homepage 的 hero + story 节奏”，并在多个项目中重复出现；
  - 在不牺牲 homepage 自身节奏的前提下，无法通过简单的模块编排满足上述诉求；
  - 说明 pricing 已经在信息架构和叙事节奏上形成与 landing 显著不同的一套“稳定型”。
- **条件 3：pricing 在审计结果中持续暴露结构性问题**：
  - 审计中频繁出现“pricing 区模块过多导致页面节奏失衡”“homepage 壳被重度 pricing 内容挤压”等结构性 warning/ERROR；
  - 这些问题无法通过调整单页模块组合解决，而指向“需要新的 page shell”。

满足以上多条条件，且有足够真实样本支撑时，才值得立项“pricing 模板分化”，并通过独立的任务单引入 candidate/primary pricing 模板。

### 11.2 feature 子类分化的准入条件

- **条件 1：出现稳定、高频且结构差异明显的 feature 子类**：
  - 比如在多个项目中反复出现以下类型：
    - 纯模块级介绍页（只讲一个能力模块，结构极度聚焦）；
    - 典型场景故事页（按“场景 → 问题 → 方案 → 效果”的叙事节奏组织内容）；
    - 成功案例页（以客户故事/项目案例为主，结构与方案页明显不同）；
  - 且这些子类在模块组合、信息层级和首屏结构上与当前 feature 模板形成明显差异。
- **条件 2：现有 feature 模板在多个项目中被证明“难以轻调”**：
  - 为适配这些子类场景，频繁出现大规模结构重排或大量新增关键模块的情况；
  - 审计中经常出现“template_match_score 过低”“missing_key_modules_count 偏高”等信号。

只有当 feature 子类在真实任务中形成稳定模式、且现有模板难以轻调承载时，才值得考虑进一步拆分 feature 模板族。

### 11.3 scene 边界治理升级的准入条件

- **条件 1：Guard 在高歧义样本中频繁漏判或误判**：
  - 在更多行业/项目中，出现大量“官网 + 实时 KPI / workspace / cockpit”等混合任务；
  - 现有 EXTENSION_GUARD 规则无法稳定触发 stop&ask，或即便触发也难以给出合理拆分建议。
- **条件 2：website 持续被要求承接 dashboard / workspace / cockpit 型任务**：
  - 即便有 Guard，业务侧仍不断提出“希望官网首页直接承载运营驾驶舱/工作台”的诉求；
  - 在这种场景下，scene 级边界可能需要通过更严格的协议或更细粒度的中间结构来治理，而不仅仅依赖当前的 stop&ask 提示。
- **条件 3：跨 scene 混合页面在真实项目中成为常态而非例外**：
  - 若大量项目都要求“官网 + cockpit”“官网 + 工作台”“官网 + 完整后台列表”等模式，说明现有 scene 划分可能需要补充“桥接层”或更细粒度的路由策略。

只有当上述条件出现并被真实样本反复验证时，才值得将 scene 边界治理升级纳入 website Phase 2 或更高阶段的任务范围。

---

## 12. website Phase 1 治理原则（可复用结论）

> 下列原则是在 website Phase 1 中被反复验证的治理经验，可复用到后续 website 阶段乃至其它 scene 的治理工作中。

- **scene 边界优先于 page_type 细分**：
  - 首先判断需求属于 website / b_system / ue5_overlay / 其它 scene，再在 scene 内做 page_type 区分；
  - 当 scene 边界不清时，优先触发 stop&ask 澄清，而不是直接在 website 内继续细分页型。
- **混合诉求优先拆任务，而不是让单页继续膨胀**：
  - 对“官网 + pricing”“官网 + workspace”“官网 + cockpit”等混合场景，优先拆分为多个任务（多页/多 scene 组合），而不是让某个 homepage/单页成为“万能容器”。
- **样本不足时优先补验证，不急于拆模板**：
  - 在没有足够真实任务样本支撑的情况下，不以主观判断新增模板或扩 page_type；
  - 应先通过类似本文件的方式补充验证样本和审计记录，再根据证据决定是否进入下一轮模板分化。
- **先 Guard，后路由，最后才是模板分化**：
  - 优先通过 EXTENSION_GUARD 之类的规则，明确哪些场景必须 stop&ask；
  - 其次确保 `task_router` / `template_router` / `scene_coverage_matrix` 在现有模板下形成稳定、一致的路由口径；
  - 只有当 Guard + 路由在真实样本下都显得吃力时，才考虑引入新模板或调整现有模板分工。
- **模板分化必须由真实任务的稳定模式驱动**：
  - 不因为“理论上可能需要”就拆模板，而是等待真实项目中出现稳定、高频且现有模板难以轻调承载的模式；
  - feature 模板的独立，就是基于“方案/能力介绍页”在真实任务中的稳定性与结构差异而做出的分化；
  - pricing 目前不拆模板，也是因为尚未达到类似的模式稳定度与承载压力。

通过上述原则，website Phase 1 将“样本堆积”沉淀为一套可复用的治理逻辑，为未来在 pricing / feature 子类 / scene 边界等方向上的进一步演化预留空间，同时避免在证据不足时过早扩张模板族与实现复杂度。


