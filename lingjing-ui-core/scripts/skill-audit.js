#!/usr/bin/env node
/**
 * skill-audit.js  —  灵境UI规范 HTML 审计器 v1.0.0
 *
 * 用途：AI 完成 HTML 生成后，在"完工自检"步骤中强制执行此脚本。
 *       发现 FAIL 项时，AI 禁止输出最终交付结论，必须先修复再重跑。
 *
 * 用法：
 *   node scripts/skill-audit.js <html文件路径> [--scene b_system|website|ue5_overlay|presentation]
 *   node scripts/skill-audit.js pages/dashboard.html --scene b_system
 *
 * 输出：
 *   - 控制台：彩色摘要
 *   - audit-report.json：结构化报告（写在 HTML 文件同目录）
 */

const fs = require('fs');
const path = require('path');

// ── CLI 参数 ──────────────────────────────────────────────────────────────
const args = process.argv.slice(2);
if (args.length === 0 || args[0] === '--help') {
  console.log('Usage: node scripts/skill-audit.js <html-file> [--scene b_system|website|ue5_overlay|presentation] [--task <task_id>]');
  process.exit(0);
}

const htmlPath = args[0];
let scene = 'auto';
let taskId = null;
const sceneIdx = args.indexOf('--scene');
if (sceneIdx >= 0 && args[sceneIdx + 1]) scene = args[sceneIdx + 1];
const taskIdx = args.indexOf('--task');
if (taskIdx >= 0 && args[taskIdx + 1]) taskId = args[taskIdx + 1];

if (!fs.existsSync(htmlPath)) {
  console.error('[ERROR] File not found:', htmlPath);
  process.exit(1);
}

const htmlContent = fs.readFileSync(htmlPath, 'utf8');

// ── 加载 class_registry / skill_version ────────────────────────────────────
const SKILL_ROOT = path.resolve(__dirname, '..');
const registryPath = path.join(SKILL_ROOT, 'data/class_registry.json');
if (!fs.existsSync(registryPath)) {
  console.error('[ERROR] class_registry.json not found. Run: node scripts/build-registry.js first.');
  process.exit(1);
}
const registry = JSON.parse(fs.readFileSync(registryPath, 'utf8')).classes;

const skillVersionPath = path.join(SKILL_ROOT, 'skill_version.json');
let skillVersion = null;
if (fs.existsSync(skillVersionPath)) {
  try {
    skillVersion = JSON.parse(fs.readFileSync(skillVersionPath, 'utf8'));
  } catch (e) {
    console.warn('[WARN] Failed to parse skill_version.json, 模板分级审计将被跳过:', e.message);
  }
}

// ── 模板分级索引与策略检查（基于 skill_version.json）───────────────────────────
function normalizePathToSkillRoot(absPath) {
  const rel = path.relative(SKILL_ROOT, path.resolve(absPath));
  // 统一使用正斜杠，确保与 skill_version.json / template_router.json 中路径一致
  return rel.replace(/\\/g, '/');
}

function buildTemplateIndexFromSkillVersion(meta) {
  const index = {};
  if (!meta || !meta.examples) return index;

  const buckets = ['canonical', 'candidate', 'demo', 'blacklist', 'limited'];
  for (const bucket of buckets) {
    const group = meta.examples[bucket];
    if (!group) continue;

    Object.keys(group).forEach(sceneId => {
      const list = group[sceneId];
      if (!Array.isArray(list)) return;
      list.forEach(p => {
        if (!p) return;
        const normalized = p.replace(/^\.\/?/, '').replace(/\\/g, '/');
        if (!index[normalized]) {
          index[normalized] = { categories: new Set(), scenes: new Set() };
        }
        index[normalized].categories.add(bucket);
        index[normalized].scenes.add(sceneId);
      });
    });
  }

  return index;
}

function computeGradeFromCategories(categoriesSet) {
  if (!categoriesSet || categoriesSet.size === 0) return 'unknown';
  if (categoriesSet.has('blacklist')) return 'blacklist';
  if (categoriesSet.has('demo')) return 'demo';
  if (categoriesSet.has('canonical')) return 'canonical';
  if (categoriesSet.has('candidate')) return 'candidate';
  if (categoriesSet.has('limited')) return 'limited';
  return 'unknown';
}

function checkTemplatePolicy(htmlFilePath, sceneId, templateIndex) {
  const abs = path.resolve(htmlFilePath);
  const rel = normalizePathToSkillRoot(abs);
  const entry = templateIndex[rel];
  const issues = [];

  if (!entry) {
    return { policy: null, issues };
  }

  const categoriesSet = entry.categories || new Set();
  const scenesSet = entry.scenes || new Set();
  const categories = Array.from(categoriesSet);
  const scenes = Array.from(scenesSet);
  const grade = computeGradeFromCategories(categoriesSet);

  // 黑名单模板：一旦命中即 ERROR，禁止出现在审计通过路径
  if (categoriesSet.has('blacklist')) {
    issues.push({
      check: 'template_blacklisted',
      severity: 'ERROR',
      detail: [`模板 ${rel} 标记为 blacklist，禁止在任何审计通过路径中使用。`],
    });
  }

  // demo-only 模板：仅作为组件/样式展厅，禁止作为业务交付模板
  if (categoriesSet.has('demo') && !categoriesSet.has('canonical') && !categoriesSet.has('candidate')) {
    issues.push({
      check: 'template_demo_only',
      severity: 'ERROR',
      detail: [`模板 ${rel} 仅标记为 demo 示例，禁止作为业务交付模板使用。`],
    });
  }

  // limited 模板：只允许在登记的 scene 下使用
  if (categoriesSet.has('limited') && sceneId && sceneId !== 'auto' && scenes.length > 0 && !scenes.includes(sceneId)) {
    issues.push({
      check: 'template_scene_mismatch',
      severity: 'ERROR',
      detail: [`模板 ${rel} 标记为 limited，仅允许在场景 ${scenes.join(', ')} 使用；当前审计场景为 ${sceneId}。`],
    });
  }

  const policy = {
    path: rel,
    categories,
    scene: scenes.length === 1 ? scenes[0] : scenes,
    grade,
  };

  return { policy, issues };
}

// ── 自动判断场景 ──────────────────────────────────────────────────────────
function detectSceneFromDom(html) {
  // ai_assistant 建立在 b_system 骨架上，必须在 b_system 之前检测
  if (html.includes('message-bubble') || html.includes('tool-call-card') || html.includes('pj-b-ai-')) return 'ai_assistant';
  if (html.includes('b-layout-sidebar') || html.includes('b-sidebar')) return 'b_system';
  if (html.includes('ue5-overlay-root') || html.includes('topbar-hud')) return 'ue5_overlay';
  if (html.includes('website-nav') || html.includes('website-hero')) return 'website';
  if (html.includes('presentation-slide')) return 'presentation';
  return 'unknown';
}

const detectedScene = detectSceneFromDom(htmlContent);

if (scene === 'auto') {
  scene = detectedScene;
} else if (detectedScene !== 'unknown' && detectedScene !== scene) {
  // 用户显式传参与 DOM 特征不符，给出警告避免假阳性
  console.warn(`[WARN] --scene=${scene} 与 DOM 特征不符：检测到 "${detectedScene}" 场景的骨架类，但当前以 "${scene}" 规则审计。`);
  console.warn(`       若页面是 ${detectedScene} 场景，请改用: node scripts/skill-audit.js ${htmlPath} --scene ${detectedScene}`);
}

// ── 提取 HTML 中所有 class 值 ─────────────────────────────────────────────
function extractClasses(html) {
  const classes = new Set();
  const re = /class\s*=\s*["']([^"']+)["']/g;
  let m;
  while ((m = re.exec(html)) !== null) {
    m[1].trim().split(/\s+/).forEach(c => { if (c) classes.add(c); });
  }
  return [...classes];
}

// ── 提取 <link href> 和 <script src> 路径 ────────────────────────────────
function extractRefs(html) {
  const refs = [];
  const linkRe = /<link[^>]+href\s*=\s*["']([^"']+)["'][^>]*>/gi;
  const scriptRe = /<script[^>]+src\s*=\s*["']([^"']+)["'][^>]*>/gi;
  let m;
  while ((m = linkRe.exec(html)) !== null) refs.push({ type: 'link', path: m[1] });
  while ((m = scriptRe.exec(html)) !== null) refs.push({ type: 'script', path: m[1] });
  return refs;
}

// ── 常见错误类名 → 修复建议 ─────────────────────────────────────────────
// 当 unknown_classes 检查报错时，在控制台给出可操作的修复提示
const FIX_HINTS = {
  // b-stat-card 子类猜测错误
  'b-stat-body':    '💡 b-stat-body 不存在。b-stat-card 子类只有：b-stat-header > (b-stat-label + b-stat-icon) + b-stat-value + b-stat-change',
  'b-stat-trend':   '💡 b-stat-trend 不存在。请改用 b-stat-change（可加修饰符 --up / --down / --neutral）',
  'b-stat-sub':     '💡 b-stat-sub 不存在。额外说明文字请放在 b-stat-change 内或 <p> 标签中',
  // 全局筛选相关猜测错误
  'filter-group':   '💡 filter-group 不存在。页面全局筛选栏请使用 search-bar + filter-select 组合，参见 SKILL.md §1.3 b_system 深读入口',
  'filter-label':   '💡 filter-label 不存在。filter-select 的标签直接作为 <option> 的 placeholder，或使用 form-label',
  'filter-separator':'💡 filter-separator 不存在。search-bar 内无需分隔符，直接并排放 filter-select',
  'filter-actions': '💡 filter-actions 不存在。按钮直接放在 search-bar 内或使用 action-buttons',
  // 卡片嵌套猜测错误
  'card-body':           '💡 card-body 不存在。content-card 内直接放内容（search-bar / data-table-container 等），不需要 card-body',
  'content-card-header': '💡 content-card-header 不存在。content-card 内的标题行使用 card-header（含 card-title + 操作按钮），参见 §Recipe 5',
  'content-card-title':  '💡 content-card-title 不存在。卡片标题使用 card-title（放在 card-header 内的 h2/h3 上）',
  'content-card-body':   '💡 content-card-body 不存在。content-card 内容直接放在卡片内，gap 由 content-card 自身的 flex+gap 控制',
  // 顶栏猜测错误
  'b-header-title': '💡 b-header-title 不存在。顶栏标题使用 b-breadcrumb-current 或 b-breadcrumb-item',
  'user-avatar':    '💡 user-avatar 不存在。用户头像按钮使用 btn-icon + Lucide user 图标',
  // 表格分页猜测错误
  'table-pagination':'💡 table-pagination 不存在。分页放在 data-table-container 外，使用原生 HTML 或 pagination 类',
  'pagination-info':'💡 pagination-info 不存在。参考 b-system-composition-recipes.md 的分页实现',
  'pagination-controls':'💡 pagination-controls 不存在。参考 b-system-composition-recipes.md 的分页实现',
  // 进度条猜测
  'progress-bar':   '💡 progress-bar 不存在。请用 b-stat-change--neutral 文字表达进度，或自定义 CSS（须放在 :root 外层 <style> 标签中使用 CSS token）',
  'progress-bar-fill':'💡 progress-bar-fill 不存在。同上',
  'progress-text':  '💡 progress-text 不存在。同上',
  // 表格操作区
  'table-search':   '💡 table-search 不存在。表格上方搜索行使用 search-bar 放在 content-card 内',
  'table-actions':  '💡 table-actions 不存在。新建/导出等按钮使用 action-buttons 放在 content-card > card-header 内',
  // 侧边栏收起修饰符猜测错误
  'b-sidebar--collapsed': '💡 b-sidebar--collapsed 不存在。侧边栏收起请在 JS 中使用 sidebar.classList.add(\'collapsed\')，CSS 选择器为 .b-sidebar.collapsed',
  // 布局容器猜测错误
  'dashboard-container': '💡 dashboard-container 不存在。B端整体布局使用 b-layout-sidebar > b-sidebar + b-main',
  'metric-card':    '💡 metric-card 不存在。KPI指标卡请使用 b-stat-card，见 §Recipe 3',
  'global-filter-bar': '💡 global-filter-bar 不存在。全局筛选栏使用 search-bar + filter-select 组合',
};

// ── CHECK 1: 未知类名 / alias / demo_only / candidate / pj-* 项目前缀 ───────
function checkUnknownClasses(classes) {
  const unknown = [];
  const aliasUsed = [];
  const demoOnly = [];
  const candidateUsed = [];  // candidate 类：已验证业务价值，设计待完善 → WARN
  const projectScoped = [];  // pj-* 项目前缀类：SKILL.md §2.6 允许，级别 WARN

  for (const cls of classes) {
    const entry = registry[cls];
    if (!entry) {
      // Allow modifier suffixes for known bases (e.g. detail-panel--alarm)
      const base = cls.replace(/--[\w-]+$/, '');
      if (base !== cls && registry[base] && registry[base].type === 'canonical') continue;
      // Allow modifier suffixes for candidate bases
      if (base !== cls && registry[base] && registry[base].type === 'candidate') {
        candidateUsed.push(cls);
        continue;
      }
      // Allow pj-{scene}-* project-scoped classes (§2.6 convention → WARN, not ERROR)
      if (/^pj-[a-z]/.test(cls)) {
        projectScoped.push(cls);
        continue;
      }
      unknown.push(cls);
    } else if (entry.type === 'alias') {
      aliasUsed.push({ class: cls, canonical: entry.canonical });
    } else if (entry.type === 'demo_only') {
      demoOnly.push(cls);
    } else if (entry.type === 'candidate') {
      candidateUsed.push(cls);
    }
  }
  return { unknown, aliasUsed, demoOnly, candidateUsed, projectScoped };
}

// ── CHECK 2: <style> 标签污染 ─────────────────────────────────────────────
function checkStyleTagLeak(html) {
  const styleBlocks = [];
  const re = /<style[^>]*>([\s\S]*?)<\/style>/gi;
  let m;
  while ((m = re.exec(html)) !== null) {
    const content = m[1];
    // Allow only :root variable declarations
    const lines = content.split('\n');
    const nonRootLines = lines.filter(l => {
      const trimmed = l.trim();
      if (!trimmed || trimmed.startsWith('/*') || trimmed.startsWith('*') || trimmed.startsWith('//')) return false;
      if (trimmed.startsWith(':root') || trimmed.startsWith('--') || trimmed === '{' || trimmed === '}') return false;
      // Property lines inside :root are ok
      if (trimmed.match(/^--[\w-]+\s*:/)) return false;
      return trimmed.includes('{') || (trimmed.includes('.') && !trimmed.includes('--'));
    });
    if (nonRootLines.length > 0) {
      styleBlocks.push({ nonRootSelectors: nonRootLines.slice(0, 5) });
    }
  }
  return styleBlocks;
}

// ── CHECK 3: 内联 style 属性 ─────────────────────────────────────────────
// 豁免规则：world-marker 的 top/left/right/bottom/transform 定位属性是
// UE5 世界坐标标注的唯一实现方式，属于规范允许的内联定位，不计入违规。
const INLINE_STYLE_WHITELIST = [
  // world-marker 仅允许位置定位属性（UE5 世界坐标标注唯一实现方式）
  { classPattern: /\bworld-marker\b/, allowedProps: /^(top|left|right|bottom|transform)\s*:/i },
  // chart-placeholder 必须通过 style="height:Npx" 为 ECharts 指定容器高度（UE5 占位用）
  { classPattern: /\bchart-placeholder\b/, allowedProps: /^height\s*:/i },
  // B 端 ECharts 挂载目标：b-chart-body 内的普通 div，id 以 "chart" 开头，只允许 height
  // 规范：<div id="chartXxx" style="height:Npx"> 是唯一合法内联 height 使用场景
  { idPattern: /^chart/i, allowedProps: /^height\s*:/i },
];

function checkInlineStyles(html) {
  // Strip <script>…</script> and <style>…</style> blocks to avoid false positives
  // from HTML strings inside JS/CSS source code
  const stripped = html.replace(/<script[\s\S]*?<\/script>/gi, '')
                       .replace(/<style[\s\S]*?<\/style>/gi, '');
  const violations = [];
  const re = /<([a-zA-Z][^\s>]*)[^>]+\sstyle\s*=\s*["']([^"']+)["'][^>]*>/gi;
  let m;
  while ((m = re.exec(stripped)) !== null) {
    const fullTag = m[0];
    const styleVal = m[2];
    // Allow only CSS variable references (e.g. style="color: var(--primary)")
    // Disallow layout/position/sizing properties
    const badProps = styleVal.match(/(position|top|left|right|bottom|width|height|margin|padding|display|flex|grid|font-size|background|color)\s*:/gi);
    if (!badProps) continue;

    // Check whitelist: if this element matches a whitelist rule and all bad props are allowed
    const classMatch = fullTag.match(/\bclass\s*=\s*["']([^"']*)["']/);
    const elemClasses = classMatch ? classMatch[1] : '';
    const idMatch = fullTag.match(/\bid\s*=\s*["']([^"']*)["']/);
    const elemId = idMatch ? idMatch[1] : '';
    let whitelisted = false;
    for (const rule of INLINE_STYLE_WHITELIST) {
      const ruleMatches = rule.classPattern
        ? rule.classPattern.test(elemClasses)
        : (rule.idPattern ? rule.idPattern.test(elemId) : false);
      if (ruleMatches && badProps.every(p => rule.allowedProps.test(p))) {
        whitelisted = true;
        break;
      }
    }
    if (!whitelisted) {
      violations.push(fullTag.substring(0, 80) + '...');
    }
  }
  return violations;
}

// ── CHECK 4: Demo 修饰类泄漏 ─────────────────────────────────────────────
function checkDemoModifiers(classes) {
  return classes.filter(c => /-(demo|showcase)-/.test(c) || /--demo-[a-z]/.test(c));
}

// ── CHECK 5: 表格溢出保护 ─────────────────────────────────────────────────
function checkTableOverflow(html) {
  const issues = [];
  // Find all data-table usages
  const tableRe = /<table[^>]*class\s*=\s*["'][^"']*data-table[^"']*["'][^>]*>/gi;
  let m;
  while ((m = tableRe.exec(html)) !== null) {
    // Look backwards 500 chars for data-table-container
    const before = html.substring(Math.max(0, m.index - 500), m.index);
    if (!before.includes('data-table-container')) {
      issues.push('table.data-table found without data-table-container wrapper');
    }
  }
  return issues;
}

// ── CHECK 6: 框架层强一致性 ──────────────────────────────────────────────
function checkFrameShell(html, sceneId) {
  if (sceneId === 'b_system') {
    const required = ['b-layout-sidebar', 'b-sidebar', 'b-main', 'b-header'];
    const missing = required.filter(cls => !html.includes(cls));
    return { required: true, missing };
  }
  if (sceneId === 'ai_assistant') {
    const required = ['ai-workspace', 'assistant-sidebar', 'message-bubble'];
    const missing = required.filter(cls => !html.includes(cls));
    return { required: true, missing };
  }
  if (sceneId === 'ue5_overlay') {
    const required = ['ue5-overlay-root', 'ue5-overlay-viewport', 'ue5-overlay-safe-area'];
    const missing = required.filter(cls => !html.includes(cls));
    return { required: true, missing };
  }
  return { required: false };
}


// ── CHECK 6.b: list → advanced_list 升级 Guard（左侧筛选面板）──────────────
// Phase 1 约束：当页面属于 b_system 场景时，默认视为 list / dashboard 壳，
// 如检测到典型高级筛选面板结构（filter-panel / advanced-data-table-side 等），
// 视为违反 “普通列表误升为高级筛选列表” Guard，由审计直接给出 ERROR。
// （后续若引入正式的 b_system_advanced_list 模板，可在此处增加白名单。）
function checkBSystemListGuard(html, sceneId, taskId) {
  if (sceneId !== 'b_system') return [];
  // 当任务显式为 b_system_advanced_list 时，不在此处拦截，由高级列表 Guard 负责
  if (taskId === 'b_system_advanced_list') return [];
  const hasFilterPanel = html.includes('filter-panel');
  const hasAdvancedSide = html.includes('advanced-data-table-side') || html.includes('advanced-data-table');
  if (!hasFilterPanel && !hasAdvancedSide) return [];
  return [
    '检测到类似高级筛选面板结构（filter-panel / advanced-data-table-side / advanced-data-table 等）。Phase 1 中，除显式任务 id 为 b_system_advanced_list 外，默认禁止在 list 场景自动生成左侧筛选面板，请改用列表页 + 顶部 search-bar。'
  ];
}

// 新 Guard：高级筛选列表任务但缺少高级壳
function checkBSystemAdvancedListShell(html, sceneId, taskId) {
  if (sceneId !== 'b_system') return [];
  if (taskId !== 'b_system_advanced_list') return [];
  const hasAdvancedRootClass = /class\s*=\s*["'][^"']*advanced-data-table[^"']*["']/.test(html);
  const hasFilterPanelClass = /class\s*=\s*["'][^"']*filter-panel[^"']*["']/.test(html)
    || /class\s*=\s*["'][^"']*advanced-data-table-side[^"']*["']/.test(html);
  if (hasAdvancedRootClass && hasFilterPanelClass) return [];
  return [
    '任务 id = b_system_advanced_list，但页面中未检测到典型高级筛选列表壳（advanced-data-table + filter-panel / advanced-data-table-side）。请确认是否应降级为普通 list，或补齐左侧高级筛选面板结构。'
  ];
}

// 新 Guard：b_system_detail 误混入 Dashboard 壳
function checkBSystemDetailGuard(html, sceneId, taskId) {
  if (sceneId !== 'b_system') return [];
  if (taskId !== 'b_system_detail') return [];
  const hasStatsGrid = html.includes('stats-grid');
  const hasChartsGrid = html.includes('charts-grid');
  if (!hasStatsGrid && !hasChartsGrid) return [];
  return [
    '任务 id = b_system_detail，但页面中检测到 stats-grid / charts-grid 等仪表盘壳。详情页应以单实体信息为主，不应在顶部堆叠 Dashboard KPI 网格；建议拆分为 dashboard + detail 或调整任务类型。'
  ];
}

// ── CHECK 6.c: UE5 Mode 2 Guard（禁止 Dock / 双侧固定面板）───────────────
// 通过文件路径粗略推断 layout_mode：
//   · 包含 "ue5_overlay_quality_tracking" 视为 Mode 2
//   · 包含 "ue5_overlay_data_viz" 视为 Mode 1
//   · 包含 "ue5_overlay_dashboard"（且非 sidepanel_dock / digital_twin）视为 Mode 3
//   · 包含 "ue5_overlay_sidepanel_dock_layout" 视为 Mode 5
function detectUe5LayoutModeFromPath(htmlFilePath) {
  const rel = normalizePathToSkillRoot(htmlFilePath);
  if (/ue5_overlay_quality_tracking/.test(rel)) return 2;
  if (/ue5_overlay_data_viz/.test(rel)) return 1;
  if (/ue5_overlay_sidepanel_dock_layout/.test(rel)) return 5;
  if (/ue5_overlay_dashboard/.test(rel) && !/digital_twin_overlay_dashboard/.test(rel)) return 3;
  return null;
}

function checkUe5Mode2Guard(html, sceneId, htmlFilePath) {
  if (sceneId !== 'ue5_overlay') return [];
  const mode = detectUe5LayoutModeFromPath(htmlFilePath);
  if (mode !== 2) return [];
  const hasDockClass = /class\s*=\s*["'][^"']*ue5-overlay-bottom-dock[^"']*["']/.test(html)
    || /class\s*=\s*["'][^"']*ue5-overlay-dock[^"']*["']/.test(html);
  const hasDoublePinnedPanels = html.includes('pj-ue5-layout-left') && html.includes('pj-ue5-layout-right');
  const violations = [];
  if (hasDockClass) {
    violations.push('layout_mode = 2 的质量追踪页面中检测到 Dock 结构（ue5-overlay-bottom-dock / ue5-overlay-dock），Dock 属于 Mode 5 / 驾驶舱布局特征，违反 Mode 2 Guard：Mode 2 禁止引入 Dock。');
  }
  if (hasDoublePinnedPanels) {
    violations.push('layout_mode = 2 的页面中同时检测到 pj-ue5-layout-left 与 pj-ue5-layout-right 等双侧固定面板标记，这属于 Mode 5 布局特征，违反 Mode 2 Guard。');
  }
  return violations;
}

function checkUe5Mode3Guard(html, sceneId, htmlFilePath) {
  if (sceneId !== 'ue5_overlay') return [];
  const mode = detectUe5LayoutModeFromPath(htmlFilePath);
  if (mode !== 3) return [];
  const hasAlertCenter = /class\s*=\s*["'][^"']*alert-center[^"']*["']/.test(html);
  const hasDockClass = html.includes('ue5-overlay-bottom-dock') || html.includes('ue5-overlay-dock');
  const hasDoublePinnedPanels = html.includes('pj-ue5-layout-left') && html.includes('pj-ue5-layout-right');
  const violations = [];
  if (!hasAlertCenter) {
    violations.push('layout_mode = 3 的页面中未检测到告警中心壳（alert-center），Mode 3 必须具备完整告警中心；请考虑降级为 Mode 2（质量追踪）或补齐告警中心面板结构。');
  }
  if (hasDockClass || hasDoublePinnedPanels) {
    violations.push('layout_mode = 3 的页面中检测到 Dock 或双侧固定面板结构（ue5-overlay-bottom-dock / ue5-overlay-dock / pj-ue5-layout-left + pj-ue5-layout-right），这些属于 Mode 5 / 驾驶舱布局特征，违反 Mode 3 Guard：Mode 3 不应升级为完整驾驶舱。');
  }
  return violations;
}

// 新 Guard：UE5 Mode 1（单 HUD）与 minimal overlay 的边界
function checkUe5Mode1Guard(html, sceneId, htmlFilePath) {
  if (sceneId !== 'ue5_overlay') return [];
  const mode = detectUe5LayoutModeFromPath(htmlFilePath);
  if (mode !== 1) return [];
  const hasHud = /class\s*=\s*["'][^"']*topbar-hud[^"']*["']/.test(html);
  if (hasHud) return [];
  return [
    'layout_mode = 1（单 HUD）页面中未检测到 topbar-hud。若需求仅需极简 world-marker 标注、无需任何 HUD，请改用 minimal overlay（如 ue5_overlay_minimal_no_hud.html）；否则请补齐 HUD 或重新评估 Mode。'
  ];
}

// ── CHECK 7: 资源引用文件可达性 ──────────────────────────────────────────
// echarts.min.js v5.6.0 已随技能包一同分发（scripts/echarts.min.js，~1MB）
const KNOWN_USER_PROVIDED = [];

function checkResourceRefs(refs, htmlFilePath) {
  const htmlDir = path.dirname(path.resolve(htmlFilePath));
  const broken = [];
  const ok = [];
  for (const ref of refs) {
    const refPath = ref.path;
    // Skip CDN and data URIs
    if (refPath.startsWith('http') || refPath.startsWith('//') || refPath.startsWith('data:')) {
      ok.push({ ...ref, status: 'cdn_or_external' });
      continue;
    }
    // Skip known user-provided files (documented as intentionally absent from package)
    if (KNOWN_USER_PROVIDED.some(re => re.test(refPath))) {
      ok.push({ ...ref, status: 'user_provided' });
      continue;
    }
    const absPath = path.resolve(htmlDir, refPath);
    if (fs.existsSync(absPath)) {
      ok.push({ ...ref, status: 'ok' });
    } else {
      broken.push({ ...ref, resolvedPath: absPath });
    }
  }
  return { ok, broken };
}

// ── CHECK 8: 裸 echarts.init() 检查 ─────────────────────────────────────
// 文件中使用了 echarts.init() 但未使用 LingJingChart.init()，视为 ERROR。
// 根据 SKILL.md §0.0.2、§1.2 与 §1.3：必须经由 LingJingChart.init() 初始化图表。
function checkBareEchartsInit(html) {
  const violations = [];
  const hasEchartsInit = /\becharts\s*\.\s*init\s*\(/.test(html);
  const hasLingJingInit = /\bLingJingChart\s*\.\s*init\s*\(/.test(html);
  if (hasEchartsInit && !hasLingJingInit) {
    // Extract the offending lines for context
    const lines = html.split('\n');
    lines.forEach(function(line, i) {
      if (/\becharts\s*\.\s*init\s*\(/.test(line)) {
        violations.push('Line ' + (i + 1) + ': ' + line.trim().substring(0, 80));
      }
    });
  }
  return violations;
}

// ── 运行所有检查 ──────────────────────────────────────────────────────────
const classes = extractClasses(htmlContent);
const refs = extractRefs(htmlContent);

const c1 = checkUnknownClasses(classes);
const c2 = checkStyleTagLeak(htmlContent);
const c3 = checkInlineStyles(htmlContent);
const c4 = checkDemoModifiers(classes);
const c5 = checkTableOverflow(htmlContent);
const c6 = checkFrameShell(htmlContent, scene);
const c6b = checkBSystemListGuard(htmlContent, scene, taskId);
const c6c = checkUe5Mode2Guard(htmlContent, scene, htmlPath);
const c6d = checkBSystemAdvancedListShell(htmlContent, scene, taskId);
const c6e = checkUe5Mode3Guard(htmlContent, scene, htmlPath);
const c6f = checkBSystemDetailGuard(htmlContent, scene, taskId);
const c6g = checkUe5Mode1Guard(htmlContent, scene, htmlPath);
const c7 = checkResourceRefs(refs, htmlPath);
const c8 = checkBareEchartsInit(htmlContent);

let templatePolicyResult = { policy: null, issues: [] };
let templateIndex = null;
if (skillVersion && skillVersion.examples) {
  templateIndex = buildTemplateIndexFromSkillVersion(skillVersion);
  templatePolicyResult = checkTemplatePolicy(htmlPath, scene, templateIndex);
}

// ── 构建报告 ──────────────────────────────────────────────────────────────
const failItems = [];

if (c1.unknown.length > 0)
  failItems.push({ check: 'unknown_classes', severity: 'ERROR', count: c1.unknown.length, detail: c1.unknown });
if (c1.demoOnly.length > 0)
  failItems.push({ check: 'demo_only_classes', severity: 'ERROR', count: c1.demoOnly.length, detail: c1.demoOnly });
if (c1.aliasUsed.length > 0)
  failItems.push({ check: 'alias_classes_not_normalized', severity: 'WARN', count: c1.aliasUsed.length, detail: c1.aliasUsed });
if (c1.candidateUsed.length > 0)
  failItems.push({ check: 'candidate_classes', severity: 'WARN', count: c1.candidateUsed.length,
    detail: c1.candidateUsed.map(c => c + ' (candidate 候选组件，业务已验证；设计未完善，禁止跨项目直接复制；晋升条件见 §2.7)') });
if (c1.projectScoped.length > 0)
  failItems.push({ check: 'project_scoped_classes', severity: 'WARN', count: c1.projectScoped.length,
    detail: c1.projectScoped.map(c => c + ' (pj-* 项目前缀类，§2.6 允许；确认已使用 CSS token，无硬编码值)') });
if (c2.length > 0)
  failItems.push({ check: 'style_tag_leak', severity: 'ERROR', count: c2.length, detail: c2.map(b => b.nonRootSelectors) });
if (c3.length > 0)
  failItems.push({ check: 'inline_style_leak', severity: 'WARN', count: c3.length, detail: c3.slice(0, 3) });
if (c4.length > 0)
  failItems.push({ check: 'demo_modifier_leak', severity: 'ERROR', count: c4.length, detail: c4 });
if (c5.length > 0)
  failItems.push({ check: 'table_overflow_missing_container', severity: 'ERROR', count: c5.length, detail: c5 });
if (c6.required && c6.missing && c6.missing.length > 0)
  failItems.push({ check: 'frame_shell_missing', severity: 'ERROR', count: c6.missing.length, detail: c6.missing });
if (Array.isArray(c6b) && c6b.length > 0)
  failItems.push({ check: 'b_system_list_left_filter_panel_forbidden', severity: 'ERROR', count: c6b.length, detail: c6b });
if (Array.isArray(c6c) && c6c.length > 0)
  failItems.push({ check: 'ue5_mode2_dock_or_double_panel_forbidden', severity: 'ERROR', count: c6c.length, detail: c6c });
if (Array.isArray(c6d) && c6d.length > 0)
  failItems.push({ check: 'b_system_advanced_list_shell_missing', severity: 'ERROR', count: c6d.length, detail: c6d });
if (Array.isArray(c6e) && c6e.length > 0)
  failItems.push({ check: 'ue5_mode3_shell_invalid', severity: 'ERROR', count: c6e.length, detail: c6e });
if (Array.isArray(c6f) && c6f.length > 0)
  failItems.push({ check: 'b_system_detail_dashboard_shell_forbidden', severity: 'ERROR', count: c6f.length, detail: c6f });
if (Array.isArray(c6g) && c6g.length > 0)
  failItems.push({ check: 'ue5_mode1_hud_missing', severity: 'ERROR', count: c6g.length, detail: c6g });
if (c7.broken.length > 0)
  failItems.push({ check: 'broken_resource_refs', severity: 'ERROR', count: c7.broken.length, detail: c7.broken.map(r => r.path) });
if (c8.length > 0)
  failItems.push({ check: 'bare_echarts_init', severity: 'ERROR', count: c8.length, detail: c8 });

// 将模板分级策略检查结果纳入 failItems（如 blacklist / demo-only / limited 场景错用）
if (templatePolicyResult && Array.isArray(templatePolicyResult.issues) && templatePolicyResult.issues.length > 0) {
  templatePolicyResult.issues.forEach(issue => {
    const detail = issue.detail || [];
    const count = issue.count != null
      ? issue.count
      : (Array.isArray(detail) ? detail.length : 1);
    failItems.push({
      check: issue.check || 'template_policy_violation',
      severity: issue.severity || 'ERROR',
      count,
      detail,
    });
  });
}

const hasErrors = failItems.some(f => f.severity === 'ERROR');
const pass = !hasErrors;
const errorChecks = failItems.filter(f => f.severity === 'ERROR').map(f => f.check);
const warningChecks = failItems.filter(f => f.severity === 'WARN').map(f => f.check);
const errorCount = errorChecks.length;
const warnCount = warningChecks.length;
const exitCode = hasErrors ? 2 : (failItems.length > 0 ? 1 : 0);
const auditCommand = 'node scripts/skill-audit.js "' + htmlPath + '" --scene ' + scene + (taskId ? ' --task ' + taskId : '');

const report = {
  _meta: { auditor: 'skill-audit.js v1.1.0', skill_version: '3.0.0' },
  file: htmlPath,
  page_path: path.resolve(htmlPath),
  scene,
  audit_command: auditCommand,
  timestamp: new Date().toISOString(),
  pass,
  summary: {
    total_classes: classes.length,
    unknown_classes: c1.unknown.length,
    demo_only_classes: c1.demoOnly.length,
    alias_not_normalized: c1.aliasUsed.length,
    candidate_classes: c1.candidateUsed.length,
    project_scoped_classes: c1.projectScoped.length,
    style_tag_violations: c2.length,
    inline_style_violations: c3.length,
    demo_modifier_leaks: c4.length,
    table_overflow_issues: c5.length,
    frame_shell_missing: (c6.required && c6.missing) ? c6.missing.length : 'N/A',
    frame_shell_valid: c6.required ? c6.missing.length === 0 : 'N/A',
    style_integrity_valid: c2.length === 0 && c3.length === 0,
    broken_resource_refs: c7.broken.length,
    resource_closure_ok: c7.broken.length === 0,
    bare_echarts_init: c8.length,
    audit_exit_code: exitCode,
    blocking_error_checks: errorChecks,
    warning_checks: warningChecks,
    template_grade: templatePolicyResult && templatePolicyResult.policy ? templatePolicyResult.policy.grade : 'unknown',
    template_categories: templatePolicyResult && templatePolicyResult.policy ? templatePolicyResult.policy.categories : [],
    template_scene_from_registry: templatePolicyResult && templatePolicyResult.policy ? templatePolicyResult.policy.scene : null,
  },
  fail_items: failItems,
  delivery_gate: pass
    ? 'PASS — 可继续交付'
    : 'FAIL — 禁止声称已完成交付，必须修复 ERROR 项后重新运行审计',
};

// ── 写 JSON 报告 ──────────────────────────────────────────────────────────
const reportPath = path.join(path.dirname(path.resolve(htmlPath)), 'audit-report.json');
fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));

// ── 控制台输出 ────────────────────────────────────────────────────────────
const RED   = '\x1b[31m';
const GREEN = '\x1b[32m';
const YELLOW= '\x1b[33m';
const CYAN  = '\x1b[36m';
const BOLD  = '\x1b[1m';
const RESET = '\x1b[0m';

console.log('\n' + BOLD + '── skill-audit.js v1.1.0 ──' + RESET);
console.log(CYAN + 'File:  ' + RESET + htmlPath);
console.log(CYAN + 'Scene: ' + RESET + scene);
console.log(CYAN + 'Classes found: ' + RESET + classes.length);
console.log('');

if (failItems.length === 0) {
  console.log(GREEN + BOLD + '✓ PASS — 全部检查通过' + RESET);
} else {
  failItems.forEach(item => {
    const color = item.severity === 'ERROR' ? RED : YELLOW;
    console.log(color + BOLD + '[' + item.severity + '] ' + item.check + RESET + ' (' + item.count + ')');
    if (Array.isArray(item.detail)) {
      item.detail.slice(0, 5).forEach(d => {
        const line = typeof d === 'object' ? JSON.stringify(d) : String(d);
        console.log('  ' + line.substring(0, 100));
        if (item.check === 'unknown_classes' && FIX_HINTS[d]) {
          console.log('  ' + YELLOW + FIX_HINTS[d] + RESET);
        }
      });
      if (item.detail.length > 5) console.log('  ... (' + (item.detail.length - 5) + ' more)');
    }
  });
  console.log('');
  if (hasErrors) {
    console.log(RED + BOLD + '✗ FAIL — 存在 ERROR 项，禁止声称已完成规范交付' + RESET);
  } else {
    console.log(YELLOW + BOLD + '⚠ WARN — 无 ERROR，但有警告项需处理' + RESET);
  }
}

console.log('');
const summaryColor = exitCode === 2 ? RED : exitCode === 1 ? YELLOW : GREEN;
console.log(summaryColor + BOLD +
  'SUMMARY  ERROR: ' + errorCount +
  '  WARN: ' + warnCount +
  '  exit=' + exitCode +
  RESET);
console.log('Report: ' + reportPath);
console.log('resource_closure_ok: ' + (report.summary.resource_closure_ok ? GREEN + 'true' : RED + 'false') + RESET);
console.log('');

// 退出码：0 = 全部通过，1 = 仅 WARN（可接受），2 = 有 ERROR（阻断）
process.exit(exitCode);
