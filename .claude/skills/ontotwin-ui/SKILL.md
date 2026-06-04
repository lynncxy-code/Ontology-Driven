---
name: ontotwin-ui
description: OntoTwin Nexus 前端视觉与交互规范（极简黑白灰风格）。当对 2.9 坐标标定工作台（coord_workbench.html）做任何 UI 改动、或需要统一前端样式/组件/交互时使用。定义配色 token、组件配方（按钮/输入/模态/吐司/下拉/提示）、交互约定（可逆性/加载态/确认模式），以及禁止清单（emoji、原生弹窗、滥用颜色）。
---

# OntoTwin UI 规范

> 风格基调：**克制的极简**。参考 typeless 的留白与单色感，但不照搬——更贴近"专业工具软件"的密度。结构层面纯黑白灰，语义色（警示/错误/成功）只在小面积、必要处点到为止。

## 适用范围（重要）

| 范围 | 处理方式 |
| :--- | :--- |
| `frontend/coord_workbench.html`（2.9 / 2.9.1 / 2.9.2） | **主改对象**，全面对齐本规范 |
| 新建的组件 / 弹窗 / 页面 | 必须遵循本规范 |
| `instance.html` / `nexus.html` / `ontology_graph.html` / `scenes.html` | **不大改**。仅在顺手时做"去 emoji、去原生 alert"这类低风险微调；不重写它们的框架或布局 |

> 黄金法则：本规范是给 2.9 立的标尺。其他页面"看到顺手能修就修一点"，但**绝不为了统一去重构它们**。

### 已定决策（用户确认）
- **「数据集」用词保留**，不改名；首次出现处加一句白话注解即可。
- **审核行布局：加宽面板**（不走两行方案）。`coord_workbench` 的 `.panel-area` 适度加宽以容纳审核行的全部字段。

---

## 1. 设计 Token（直接粘进 `:root`）

```css
:root{
  /* ── 灰阶（结构色，全站只用这套）── */
  --ink:#1a1a1a;        /* 主文字 / 主按钮底 */
  --ink-2:#5c5c5c;      /* 次要文字 */
  --ink-3:#8a8a8a;      /* 弱化文字 / placeholder */
  --line:#e8e8e8;       /* 默认边框 / 分隔线 */
  --line-2:#d4d4d4;     /* 强调边框 / 输入框 */
  --bg:#ffffff;         /* 页面底 */
  --bg-2:#fafafa;       /* 次级面板 / 卡片底 */
  --bg-3:#f3f3f3;       /* hover / 选中底 */
  --on-ink:#ffffff;     /* 深底上的文字 */

  /* ── 语义色（仅小面积：徽标点、左边框、文字，禁止整块大色块）── */
  --danger:#b42318;  --danger-bg:#fef3f2;  --danger-line:#fda29b;
  --warn:#b54708;    --warn-bg:#fffaeb;    --warn-line:#fec84b;
  --ok:#067647;      --ok-bg:#ecfdf3;      --ok-line:#a6f4c5;
  --info:#363f72;    --info-bg:#f8f9fc;    --info-line:#b3b8db;

  /* ── 圆角（只用这三档，禁止再造新值）── */
  --r-sm:6px; --r-md:8px; --r-lg:12px;

  /* ── 间距（4 的倍数）── */
  --s1:4px; --s2:8px; --s3:12px; --s4:16px; --s5:20px; --s6:24px; --s8:32px;

  /* ── 字号 ── */
  --t-xs:11px; --t-sm:12px; --t-base:13px; --t-md:14px; --t-lg:16px; --t-xl:20px;

  /* ── 阴影（极克制，只给浮层）── */
  --shadow-pop:0 4px 16px rgba(20,20,20,.08);
  --shadow-modal:0 16px 48px rgba(20,20,20,.18);

  --font:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
}
```

**主色就是黑（`--ink`）。** 过去 2.9 用的蓝 `#2563eb` / `accent-light` 一律替换为灰阶或 `--ink`。

---

## 2. 硬性规则（Do / Don't）

### 禁止
- ❌ **任何 emoji**：`📊 ⛶ 🟢🔵🟡🔴 ✓ ✗ ★ 💡 ⚙ ❌ ✅` 等一律不用
- ❌ **原生 `alert()` / `confirm()` / `prompt()`**：全部改用本规范的 toast / modal / dropdown
- ❌ **大面积语义色块**：不要整行/整卡片铺红绿黄底。语义色只用于：① 6px 的状态点 ② 2px 左边框 ③ 文字色 ④ 浅到几乎白的 `*-bg`
- ❌ **彩色作为主交互色**：主按钮、选中态、链接都用黑/灰，不用蓝
- ❌ **新造圆角/间距值**：只用 token 里定义的
- ❌ **技术黑话进 UI 文案**：`rid` `_object_types` `ObjectType` `INSERT` `block_name` `asset 回写` 等——见第 5 节翻译表

### 允许
- ✅ 单色描边图标（SVG line icon，`stroke=currentColor`），替代 emoji
- ✅ 极少量箭头符号在按钮内（`→`），但能用文字就用文字
- ✅ 语义色小面积点缀（状态点、错误文字、警示左边框）
- ✅ 浅灰底 hover、浅灰底选中

---

## 3. 组件配方

### 3.1 按钮
```css
.btn{font:500 var(--t-base)/1 var(--font);padding:8px 14px;border-radius:var(--r-md);
  border:1px solid var(--line-2);background:var(--bg);color:var(--ink);cursor:pointer;
  transition:background .15s,border-color .15s}
.btn:hover{background:var(--bg-3)}
.btn-primary{background:var(--ink);color:var(--on-ink);border-color:var(--ink)}
.btn-primary:hover{background:#000}
.btn-ghost{border-color:transparent;background:transparent;color:var(--ink-2)}
.btn-ghost:hover{background:var(--bg-3);color:var(--ink)}
.btn-danger{border-color:var(--danger-line);color:var(--danger);background:var(--danger-bg)}
.btn:disabled{opacity:.4;cursor:not-allowed}
.btn-sm{padding:6px 10px;font-size:var(--t-sm)}
```
层级：主操作 `btn-primary`（黑底），次操作 `btn`（白底描边），三级 `btn-ghost`，危险 `btn-danger`。**一个区域只允许一个 primary。**

### 3.2 输入 / 下拉
```css
.field{padding:7px 10px;border:1px solid var(--line-2);border-radius:var(--r-sm);
  font-size:var(--t-sm);background:var(--bg);color:var(--ink);width:100%}
.field:focus{outline:none;border-color:var(--ink);box-shadow:0 0 0 3px rgba(26,26,26,.06)}
.field::placeholder{color:var(--ink-3)}
```
聚焦态用黑色描边 + 极淡灰光晕，不用蓝。

### 3.3 模态（替代 confirm）
统一一个 `openModal({title, body, actions})` helper。结构：
```
.modal-mask{position:fixed;inset:0;background:rgba(20,20,20,.4);display:flex;
  align-items:center;justify-content:center;z-index:1000}
.modal{background:var(--bg);border-radius:var(--r-lg);box-shadow:var(--shadow-modal);
  width:min(520px,92vw);max-height:82vh;overflow:auto;padding:var(--s6)}
.modal h3{font-size:var(--t-lg);font-weight:600;margin-bottom:var(--s3)}
.modal-foot{display:flex;gap:var(--s2);justify-content:flex-end;margin-top:var(--s5)}
```
- 标题左对齐、无 emoji
- 按钮右下：取消（ghost/白）+ 确认（primary/黑或 danger）
- 支持 `Esc` 关闭、点遮罩关闭、回车触发主操作

### 3.4 吐司 Toast（替代 alert）
非阻塞，右上或底部滑入，2.5s 自动消失：
```
.toast{position:fixed;top:16px;right:16px;z-index:1100;display:flex;flex-direction:column;gap:8px}
.toast-item{background:var(--ink);color:var(--on-ink);padding:10px 14px;border-radius:var(--r-md);
  font-size:var(--t-sm);box-shadow:var(--shadow-pop);max-width:360px}
.toast-item.ok{background:var(--bg);color:var(--ink);border-left:2px solid var(--ok)}
.toast-item.err{background:var(--bg);color:var(--ink);border-left:2px solid var(--danger)}
```
用 `toast(msg, type)`：成功/失败用左边框语义色，普通信息用黑底白字。

### 3.5 下拉选择器（替代 prompt 选数据集）
点击触发一个挂在锚点下方的浮层列表，键盘可选，当前项打勾（用 SVG check，非 emoji）：
```
.dropdown{position:absolute;background:var(--bg);border:1px solid var(--line);
  border-radius:var(--r-md);box-shadow:var(--shadow-pop);min-width:200px;padding:4px;z-index:1050}
.dropdown-item{padding:7px 10px;border-radius:var(--r-sm);font-size:var(--t-sm);cursor:pointer;
  display:flex;align-items:center;justify-content:space-between}
.dropdown-item:hover{background:var(--bg-3)}
.dropdown-item[aria-selected=true]{font-weight:600}
```

### 3.6 提示 Tooltip / 行内说明（替代原生 title）
不要再用 `title="..."`。自建 tooltip：hover 立即出、可容纳长文、跟随主题。
对"为什么这个不能创建"这类**因果性提示**，优先用**行内常驻说明**而非 hover——例如审核行下方一条 11px 灰字直接写明原因，比藏在 hover 里清晰。

### 3.7 状态徽标（四态等）
**禁止 `🟢🔵🟡🔴`。** 用 6px 圆点 + 文字：
```
.dot{width:6px;height:6px;border-radius:50%;display:inline-block}
.dot-ok{background:var(--ok)} .dot-warn{background:var(--warn)}
.dot-err{background:var(--danger)} .dot-info{background:var(--info)} .dot-muted{background:var(--ink-3)}
```
用法：`<span class="dot dot-warn"></span> 待确认`。

### 3.8 表格行 / 列表行 hover
hover 用 `--bg-3` 灰底，选中用左 2px `--ink` 边框，不用蓝底高亮。

---

## 4. 交互约定（网页软件规范）

1. **可逆性**：任何"提交/写入"成功后，**不得把编辑区彻底 `display:none` 锁死**。成功提示应与编辑区并存，或提供"继续编辑 / 再次提交"入口。用户永远能退回上一步而不丢数据。
2. **危险操作确认**：删除、覆盖、切换激活集这类有副作用的操作，用模态二次确认（含后果说明），不用原生 confirm。
3. **加载态**：异步操作期间按钮显示 loading 文案并 disable；列表区显示骨架/「加载中」占位，不要空白。
4. **空态**：列表为空时给一句引导文案 + 可能的下一步按钮，不要纯空白。
5. **错误反馈**：就近显示（输入框下红字 / toast），不要打断式 alert。
6. **键盘**：模态支持 Esc/Enter；下拉支持上下键 + Enter；输入支持 Tab 流转。
7. **焦点管理**：模态打开自动聚焦首个输入/主按钮，关闭后焦点回到触发元素。

---

## 5. 文案翻译表（技术词 → 用户语言）

| 代码里的词 | UI 里应写 |
| :--- | :--- |
| ObjectType / rid | 类型 / 设备类型 |
| `_object_types` | 当前生效的类型库 |
| INSERT | 设备块（或直接说"设备"） |
| POLY / POLYLINE | 墙体/地面线 |
| block_name | 块名 |
| asset_id / asset 回写 | 资产路径 / 已记住资产对应关系 |
| dataset / 数据集 | 类型库（"数据集"可保留，但首次出现加一句白话） |
| publish / merge | 新建类型库 / 并入现有类型库 |
| dangling refs | 有 N 个实例正在用这些类型 |
| commit | 提交 / 保存 |

---

## 6. 改造 2.9 时的对照检查清单

改 `coord_workbench.html` 时逐条核对：
- [ ] 蓝色 `#2563eb` / `--accent` / `accent-light` / `bfdbfe` 全部替换为灰阶或 `--ink`
- [ ] 所有 emoji 删除，换 SVG line icon 或纯文字
- [ ] 25× alert → toast；6× confirm → 模态；1× prompt → 下拉
- [ ] 四态 `🟢🔵🟡🔴` → 6px 状态点 + 文字
- [ ] 所有 `title="..."` 原生 tooltip → 自建 tooltip 或行内说明
- [ ] commit 成功后保留可回退入口（解决单向死路）
- [ ] UI 文案过一遍第 5 节翻译表
- [ ] 圆角/间距/字号收敛到第 1 节 token
- [ ] 审核行布局：加宽 `.panel-area` 以容纳全部字段（已定加宽方案）
- [ ] 画布 resize 在模式切换 / 面板变化时重算

> 改完用 `node --check` 验证 JS，并在浏览器实测一遍完整链路（上传→类型审核→标定→实体→导出→投入实例）。

---

## 7. 已落地实现（coord_workbench.html）

首轮 U0–U5 已按本规范完成，后续改动请复用这些既有资产：

- **组件**：`UI.toast(msg,type)` / `UI.modal({title,bodyHTML,actions})` / `UI.confirm({title,bodyHTML,confirmText,danger})` / `UI.dropdown(anchorEl,items)`；tooltip 用元素加 `data-tip="..."` 属性（勿再用原生 `title`）。
- **状态点**：`<span class="dot dot-ok|dot-warn|dot-err|dot-info|dot-muted"></span>`。
- **token**：旧名（`--accent` 等）已重映射为黑白灰，新代码直接用新 token（`--ink` / `--line` / `--r-md` 等）。
- **可逆性**：commit 成功用 `showCommitSuccess` 显示横幅但不隐藏编辑区。
- **画布**：`ResizeObserver` 已挂在画布容器上，布局变化自动重算。
- **面板宽度**：`.panel-area` = `flex:4; min 400 / max 560`。
