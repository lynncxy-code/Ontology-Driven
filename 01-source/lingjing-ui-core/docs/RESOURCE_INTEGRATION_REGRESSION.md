# 资源接入协议与预览方式回归检查（首个业务案例纠偏版）

> 范围：仅围绕 `lingjing-ui-core` 当前版本的 CSS / scripts / assets 接入协议与预览方式进行回归，不改动 router / matrix / Guard / 模板治理逻辑；不直接修改业务案例页面。

---

## 1. 官方资源接入协议（基于现有真值源）

### 1.1 样式入口（CSS）

- **官方入口文件**：
  - `components/dist/lingjing-core-b-system.css`
  - `components/dist/lingjing-core-ue5-overlay.css`
  - `components/dist/lingjing-core-website.css`
  - `components/dist/lingjing-core-presentation.css`
- **场景 → 样式入口映射**（`SKILL.md §1.0`）：
  - `b_system` → `lingjing-core-b-system.css`
  - `ue5_overlay` → `lingjing-core-ue5-overlay.css`
  - `website` → `lingjing-core-website.css`
  - `presentation` → `lingjing-core-presentation.css`
  - `ai_assistant` → `lingjing-core-b-system.css`
- **接入方式原则**：
  - 由调用方项目**复制**或引用上述 dist CSS 文件；
  - 在 HTML 中使用标准的 Web 路径语义（`/` 分隔），通过 `<link rel="stylesheet" href="...">` 接入；
  - `SKILL.md §0.0` 与 `QUICKSTART_FOR_AGENT` 要求：
    - 先对齐 **调用方项目结构**（`package.json` / `index.html` / 页面目录）；
    - 再在项目实际结构下接入 **单文件场景入口 CSS**，而不是重写一套“相似 CSS”。

### 1.2 脚本（scripts）

- **官方运行时脚本与依赖**（`SKILL.md §0.0.6` + `REPO_STRUCTURE_GUIDE`）：
  - 图标库：`scripts/lucide-umd-500.js`
  - 图表库：`scripts/echarts.min.js` + `scripts/echarts-theme-lingjing.js`
  - UE5 桥接：`components/dist/lingjing-core-ue5-bridge.js`（如环境支持）
- **接入方式原则**：
  - 在目标项目中，将上述脚本文件放入可访问的静态资源目录；
  - 用标准 URL 语义的 `<script src="..."></script>` 引用（使用 `/` 分隔），不混用文件系统风格；
  - 示例与工具页（如 `tools/preview-tool.html`）统一使用 `../scripts/...` 或 `../../scripts/...` 相对路径，并未在任何 HTML 中使用 `\\` 作为分隔符。

### 1.3 资产（assets）

- **官方资产路径**（`SKILL.md §0.0.6` + `§4.1`）：
  - B 端 / Website Logo：`assets/logo-flat.png`
  - UE5 HUD 品牌：`.ue5-overlay-system-bar__brand-mark`（CSS 背景图，不额外叠加 `<img>`）
  - UE5 默认背景图：`assets/ue5-bg-scene.png`
- **接入方式原则**：
  - 需要使用官方 Logo / 背景图时，应保证这些文件在项目内对应路径真实存在；
  - HTML / CSS 中使用 `/` 作为路径分隔符，例如：`<img src="assets/logo-flat.png">` 或 `url('assets/ue5-bg-scene.png')`；
  - `assets/legacy-root-copies/` 仅为历史副本归档目录，不作为运行期资源引用目标。

### 1.4 resource_closure 与审计行为

- **SKILL.md §0.0.6** 中定义 `resource_closure_ok`：
  - Step 1：资源目标目录已就位；
  - Step 2：资源文件已成功复制到项目内；
  - Step 3：HTML / CSS / JS 中引用路径与真实文件一致且可达；
  - 任一步失败 → `resource_closure_ok = false`，只能宣称为结构草案/局部实现。
- **skill-audit.js 的实现（当前版本）**：
  - 收集 `<link>` / `<script>` 等标签中的路径，形成 `refs`；
  - 对每个 ref：
    - 跳过 `http/https//data:` 等外部资源；
    - 若路径中包含 `\\`，直接视为 `invalid_separator` 并计入 `broken_resource_refs`；
    - 否则使用 `path.resolve(htmlDir, refPath)` 解析为文件系统路径，再用 `fs.existsSync` 判断目标是否存在；
    - 若文件不存在，则记为 `broken_resource_refs`，导致 `resource_closure_ok = false`。
- **结论**：
  - 协议与审计都基于“**HTML 内写的是 URL 风格路径**”这一前提；
  - “Windows 下 HTML 路径应使用 `\\`” 这一说法与 Web 语义不符，审计层也明确将其视为错误路径。

---

## 2. 首个业务案例项目的路径与预览方式（按当前描述）

> 本节基于首个业务案例项目的结构与 `npm run dev` 配置描述，而不是对该项目仓库的直接扫描。

- **目录结构（简化）**：
  - 根目录：`index.html`、`css/lingjing-core-b-system.css`、`scripts/...`、`pages/*.html`、`package.json`。
  - `package.json` 中：`npm run dev` 使用 `http-server -p 3000 -c-1`，即以当前目录作为站点根，通过 `http://localhost:3000` 访问。
- **当前路径使用方式**：
  - 根目录 `index.html`：
    - 常见写法：`/css/lingjing-core-b-system.css`、`/pages/dashboard.html`（root-relative）。
  - `pages/*.html`：
    - 常见写法：`../css/lingjing-core-b-system.css`、`../scripts/...`（relative）。
- **关键观察**：
  - 在 **Web 路径语义** 下，以上两种写法在 `http-server` 作为站点根时大多可以工作；
  - 问题不在于“路径语法错误”，而在于：
    - **项目在 Web 路径语义下混用了 root-relative 与 relative 两套策略**，但没有在工程层先明确“统一策略”与“默认预览方式”；
    - 在未先澄清 `http-server` vs `file://` 预览假设的前提下，就根据“本机预览有无样式”批量修改 HTML 路径，属于执行判断不稳。

---

## 3. 本次纠偏后的正式问题定义

### 3.1 错误结论（需明确否定）

- “**Windows 下 HTML 资源路径应使用 `\\`**” 这一说法是 **错误的**：
  - 浏览器中的 `href` / `src` / `window.location.href` 使用的是 URL / Web 路径语义，与操作系统无关；
  - 标准分隔符始终是 `/`，`
` 属于文件系统层表达，不是 HTML 路径语法的一部分；
  - skill 仓内所有示例与工具页均使用 `/`，没有任何“因为 Windows 而改用 `\\`” 的官方约定。

### 3.2 正确问题定义

- **问题本质**：
  - 当前案例暴露的是“**Web 路径策略未统一 + 预览方式假设未先澄清**”的问题，而不是模板生成错误或 skill 包本身不适配 Windows；
  - 具体表现为：
    - 项目同时存在 root-relative（如 `/css/...`）与 relative（如 `../css/...`）两种路径策略；
    - 在未先声明“本次验证默认以 `http-server` 视为 Web 根，还是以 `file://` 直接打开”为前提的情况下，就以“页面有没有样式”为依据批量改路径。

### 3.3 责任主次划分

- **Builder 执行判断：主因**
  - 在未澄清预览方式与目标部署根的前提下，就根据“本机预览效果”批量改写路径；
  - 将 HTML 路径问题一度归因为 “Windows 需要 `\\`”，属于对 Web 路径语义的误解。
- **项目工程路径策略未统一：次主因**
  - 工程层没有先统一“本项目到底采用 root-relative 还是 relative 作为主要路径策略”，导致后续任何路径调整都缺乏清晰基准；
  - 根页、子页与内部导航各自使用 convenient 的方式，加大了排查难度。
- **技能包文档 / 审计说明不足：次因**
  - 之前文档虽然强调资源闭环和资源复制，但对“Web 路径语义 + 预览方式需先统一”缺少显式段落；
  - 审计在本轮之前对 `\\` 路径没有单独标记为错误，只是隐含假设 HTML 写的是正常 URL。

---

## 4. 对 Builder 路径修复判断的评估（纠偏视角）

### 4.1 错误判断

- **“Windows 下 HTML 资源路径应使用 `\\`”**
  - 已明确为错误说法（见 §3.1），不再作为后续任何修改的依据。
- **在未查清接入协议与预览方式前批量修改 `pages/*.html`**
  - 在不了解 skill 的资源闭环协议、项目部署根目录与 dev server 配置的前提下，以“当前预览有无样式”为唯一依据批量修改路径，是不稳固的执行方式；
  - 这既可能掩盖“资源未复制到项目内 / 目录层级不匹配”的真实问题，也容易在将来部署环境发生改变时再度翻车。

### 4.2 可能部分正确但前提缺失的判断

- **对相对路径层级的敏感性**
  - 如果业务项目在 `pages/` 子目录中存放 HTML，则正确设置相对路径（如 `../css/...`）确实非常重要；
  - 但这要求先弄清楚：
    - 项目部署根目录在哪里；
    - 资源文件实际复制到哪个目录；
    - dev server 如何映射 Web 根；
  - 在这些前提不明的情况下，单纯“改层级”或“改成 `\\`”都不构成可靠修复。

### 4.3 当前不应继续做的事

- 在本轮纠偏之后，不应继续：
  - 将问题归因为“Windows 需要反斜杠”；
  - 在未统一路径策略与预览方式前，继续批量修改业务页面 HTML；
  - 将这一问题当成“模板生成错误”或“技能包不支持 Windows”；
  - 在 `http-server` vs `file://` 的假设仍然含糊时，继续围绕资源路径做大规模调整。

---

## 5. 最小修正建议（协议层，而非直接改页面）

### 5.1 文档与协议层（已补强）

1. **文档层明确 HTML 使用 Web 路径语义**：
   - 在 `SKILL.md §0.0.6 资源闭环与交付完整性硬约束` 中补充：
     - HTML 中的 `<link>` / `<script>` / `<img>` 路径必须使用 Web URL 语义的 `/` 作为分隔符，禁止使用 `\\` 作为路径分隔符；
   - 在 `QUICKSTART_FOR_AGENT` 的资源落地步骤后，增加提醒：
     - 资源路径必须使用 Web URL 语义，避免将操作系统路径心智带入 HTML。
2. **保留本回归文档作为“资源接入协议”结论**：
   - 本文件作为“资源接入 + 预览方式”层的纠偏记录，供后续业务案例验证与工程评审时引用。

### 5.2 README / QUICKSTART 的最小接入说明

- **README**：
  - 保持现有“实际项目接入”提醒，不过多扩写；
  - 当需要更细节的路径策略讨论时，引导读者阅读本文件与 `QUICKSTART_FOR_AGENT`。  
- **QUICKSTART_FOR_AGENT**：
  - 已在“4. 框架层先行 + 资源落地”中补充：资源路径必须使用 `/`，不要写成 Windows 风格 `\\`；
  - 不直接规定“必须统一为 relative”，而是：
    - 提醒 AI 和开发者先对齐项目结构与预览方式；
    - 再选择一套与目录结构和审计行为更容易对齐的路径策略。

> 换句话说，文档层只强调“必须是 Web URL 语义 + 先统一路径策略与预览方式”，**不会**把“相对路径是唯一官方策略”写死为硬规则。

### 5.3 audit 层（已做最小兜底，不再扩展）

- `skill-audit.js` 在本轮已增加：
  - 对 HTML 引用路径中包含 `\\` 的情况，直接记为 `invalid_separator` 并纳入 `broken_resource_refs`；
  - 确保这种明显错误的路径不会被误判为 `resource_closure_ok = true`。
- 当前 **没有** 增加对“root-relative 与 relative 混用”的自动 WARN：
  - 原因是：是否允许混用取决于具体部署模型（如挂在子路径时 root-relative 可能天然不可用），
  - 审计层难以在不了解部署根与预览方式的前提下给出“哪一种才是错误”的自动判断。
- 路径策略统一与预览方式选择，仍然视为 **工程项目层面的责任**，不由 audit 单方面决定。

---

## 6. 是否构成发版前 blocker 及恢复条件

### 6.1 Blocker 判断（纠偏后）

- **对于 `lingjing-ui-core` 作为独立技能包的稳定发版**：
  - 文档（`SKILL.md` / `QUICKSTART_FOR_AGENT` / 本文档）已明确强调 Web 路径语义与资源闭环要求；
  - `skill-audit.js` 对明显错误的 `\\` 路径已有兜底拦截；
  - 因此，就“技能包自身是否可以作为 v3.0.0 稳定版发布”这一问题而言，
    - 本案例暴露的风险已 **降级为可控风险**，不再单独阻塞 skill 仓本身的发版。
- **对于“携带首个业务案例验证一起对外宣称稳定可用”的整体发布**：
  - 在业务项目尚未统一路径策略、澄清预览方式并通过新的 audit 检查之前，
    - 这一问题仍应视为整体交付层面的 **blocker**：
      - 很难证明“真实接入场景下资源闭环稳定可复现”。

### 6.2 恢复业务案例验证的必要条件

在恢复后续业务案例验证之前，至少应满足：

1. **预览方式已明确并约定**：
   - 明确当前业务项目默认通过 `npm run dev` / `http-server` 等 dev server 访问，还是通过其他方式（如 file://）预览；
   - 若采用 dev server，则以其站点根为 Web 根来设计路径策略，不再混用 file:// 心智。
2. **项目已统一 Web 路径策略**：
   - 在 `index.html`、`pages/*.html`、页面内部导航 `<a href>` 与 `window.location.href` 中统一选择一种策略：
     - 要么以 root-relative 为主（`/css/...`、`/pages/...`），并清楚声明站点根；
     - 要么以 relative 为主（`./css/...`、`../css/...`），并保证与实际目录结构和 audit 行为一致；
   - 避免在同一项目中无注释地混用 root-relative 与 relative，让问题难以归因。
3. **Builder 执行判断已纠偏**：
   - 不再沿用“Windows 反斜杠”这一错误前提；
   - 在批量修改页面前，先确认预览方式与路径策略，而不是仅以“本机有无样式”作为唯一依据。
4. **技能包侧接入说明已足够防误解**：
   - 本文档与 `SKILL.md` / `QUICKSTART_FOR_AGENT` 已给出“Web 路径语义 + 预览方式需先统一”的提醒；
   - 团队在评审和接入时，会主动参考这些说明，而不是凭个人平台经验改路径。
5. **首个业务案例在约定预览方式下资源加载稳定**：
   - 在统一路径策略后，通过 dev server 或约定的预览方式访问代表性页面；
   - 使用最新的 `skill-audit.js` 进行检查，确认：
     - 无资源相关 ERROR（包括 `invalid_separator` 与文件缺失）；
     - `resource_closure_ok = true`，且整体审计结果可接受。

---

## 7. 一句话总结

纠偏后，这个案例的问题被正式界定为“**Web 路径策略 + 预览假设 + Builder 判断**”的工程接入问题：对于 `lingjing-ui-core` 作为独立技能包的发版来说，经过本轮最小协议补强后已降级为可控风险；但在业务项目尚未统一预览方式与路径策略并通过新的 audit 之前，它仍然是“携带首个业务案例验证一起对外宣称稳定可用”的 blocker，后续业务案例验证应暂缓至上述条件满足后再恢复。