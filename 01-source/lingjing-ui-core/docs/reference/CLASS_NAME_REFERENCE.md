# 灵境 Core - 类名参考索引

> **版本**: v3.1.6
> **更新日期**: 2026-03-25
> **重要说明**: 本文件自 v3.1.6 起仅作为**索引与说明文档**。
> **机器可读真值源**：`data/class_registry.json`（1878 条记录，含 canonical / utility / alias / deprecated / demo_only 分级）

---

## 真值源：`data/class_registry.json`

所有类名的**权威来源**已迁移至 [`data/class_registry.json`](../../data/class_registry.json)，由 `scripts/build-registry.js` 从 dist CSS 自动提取生成。

### 查询方式

```bash
# 查询某个类名是否存在及其类型
node -e "const r=require('./data/class_registry.json').classes; console.log(r['data-table-container'])"

# 列出所有 deprecated 类名
node -e "const r=require('./data/class_registry.json').classes; Object.entries(r).filter(([,v])=>v.type==='deprecated').forEach(([k])=>console.log(k))"

# 重新生成注册表（从 dist CSS 提取）
node scripts/build-registry.js
```

### 类名分级说明

| 类型 | 数量 | 含义 | 可用于业务交付 |
|------|------|------|----------------|
| `canonical` | 1394 | 官方正式类名，完整 CSS 支持 | ✅ 是 |
| `utility` | 448 | 工具类（间距、颜色、显示等） | ✅ 是 |
| `alias` | 18 | 历史别名，已映射至 canonical | ⚠️ 改用 canonical |
| `deprecated` | 13 | 已废弃，下个主版本移除 | ⚠️ 禁止新增使用 |
| `demo_only` | 5 | 仅用于展示示例，禁止业务引用 | ❌ 否 |
| **合计** | **1878** | | |

---

## 场景分布概览

以下为各场景类名分布的**高层概览**，详细类名列表请查阅 `data/class_registry.json`。

### B 端管理系统（b_system）— `lingjing-core-b-system.css`

**骨架层**：`b-layout-*`、`b-header`、`b-sidebar`、`b-content`、`b-footer`

**组件类**（partial list）：

| 分类 | 核心类名 |
|------|---------|
| 数据表格 | `data-table-container`、`data-table`、`table-toolbar`、`filter-bar` |
| 卡片 | `content-card`、`card-header`、`card-title`、`stat-card`、`chart-card` |
| 状态与徽章 | `status-dot`、`badge`、`badge--success/warning/error/info` |
| 时间线 | `status-timeline`、`status-timeline-item`、`status-timeline-dot` |
| 表单 | `form-group`、`form-label`、`form-input`、`search-bar`、`filter-select` |
| 导航 | `b-breadcrumb`、`b-header-left`、`b-header-right` |
| 抽屉/模态 | `drawer`、`drawer-header`、`drawer-body`、`modal`、`modal-header` |

> 完整食谱见 [`b-system-composition-recipes.md`](./b-system-composition-recipes.md)
> 布局决策见 [`../operations/b-system-layout-playbook.md`](../operations/b-system-layout-playbook.md)

---

### UE5 Web Overlay（ue5_overlay）— `lingjing-core-ue5-overlay.css`

**必须骨架**：`ue5-overlay-root` → `ue5-overlay-background` + `ue5-overlay-viewport` + `ue5-overlay-safe-area`

**核心组件类**：

| 分类 | 核心类名 |
|------|---------|
| HUD | `topbar-hud`、`hud-left/right`、`hud-metric`、`hud-metric-value` |
| 告警 | `alert-center`、`alert-item`、`alert-item--critical/warning/info` |
| 面板 | `detail-panel`、`detail-panel--alarm`、`panel-header`、`panel-body` |
| 世界标注 | `world-marker`、`world-marker--critical/warning/success/info` |
| 图层切换 | `layer-switcher`、`layer-item`、`layer-item--active` |

> 布局决策见 [`../operations/ue5-overlay-layout-playbook.md`](../operations/ue5-overlay-layout-playbook.md)

---

### 营销/企业门户（website）— `lingjing-core-website.css`

**核心类名**（partial list）：

`website-container`、`website-section`、`website-nav`、`website-nav-glass`、
`website-hero`、`website-hero-title`、`website-feature-card`、`website-footer`

---

### 专业演示（presentation）— `lingjing-core-presentation.css`

**核心类名**（partial list）：

`slide-container`、`slide-title`、`slide-subtitle`、`slide-content`、
`slide-section`、`slide-highlight`、`slide-chart-placeholder`

---

## 工具类速查

所有工具类（`utility` 类型）均适用于所有场景。常用工具类：

| 类别 | 典型类名 |
|------|---------|
| 显示/隐藏 | `hidden`、`visible`、`opacity-30`、`opacity-50`、`opacity-70` |
| 文本对齐 | `text-left`、`text-center`、`text-right` |
| 间距 | `mt-*`、`mb-*`、`ml-*`、`mr-*`、`p-*`、`gap-*` |
| 颜色 | `text-primary`、`text-secondary`、`text-tertiary`、`text-success/warning/error` |
| 边框 | `border-*`、`rounded-*` |

---

## 已知 Alias（历史别名）

在 `ux_spec` 中使用以下类名时，lint 工具将提示改用 canonical 名称：

| alias（旧名） | canonical（当前正确名） |
|--------------|----------------------|
| `activity-timeline` | `status-timeline` |
| `timeline-item` | `status-timeline-item` |
| `b-main-content` | `b-content` |
| `stats-card` | `stat-card` |
| *(其余见 class_registry.json)* | |

---

## 已废弃类名（deprecated）

以下类名在当前版本仍可用，但将在下个主版本移除，禁止新代码引入：

> 完整列表见 `data/class_registry.json`（type: "deprecated"）

---

## 相关工具

| 工具 | 命令 | 用途 |
|------|------|------|
| **skill-audit.js** | `node scripts/skill-audit.js <html>` | HTML 产物 7 项规范审计 |
| **ux-spec-lint.js** | `node ../lingjing-ux-core/scripts/ux-spec-lint.js <yml>` | ux_spec 类名校验 |
| **build-registry.js** | `node scripts/build-registry.js` | 从 dist CSS 重建注册表 |

---

*本索引文件由人工维护，版本与 `SKILL.md` 同步。详细数据以 `data/class_registry.json` 为准。*
