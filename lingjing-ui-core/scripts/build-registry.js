/**
 * build-registry.js
 * 从 dist CSS 文件提取类名并生成 data/class_registry.json
 * 运行：node scripts/build-registry.js（从 lingjing-ui-core 根目录执行）
 */

const fs = require('fs');
const path = require('path');

const BASE = path.resolve(__dirname, '..');
const distDir = path.join(BASE, 'components/dist');

// ── 1. 解析 aliases ──────────────────────────────────────────────────────
const matrixRaw = fs.readFileSync(path.join(BASE, 'scene_coverage_matrix.yml'), 'utf8');
const aliases = {};
// Handle both CRLF (Windows) and LF line endings
const normalizedMatrix = matrixRaw.replace(/\r\n/g, '\n');
const aliasStart = normalizedMatrix.indexOf('aliases:\n');
if (aliasStart >= 0) {
  const section = normalizedMatrix.substring(aliasStart + 8);
  section.split('\n').forEach(line => {
    const m = line.match(/^    ([\w-]+): ["']?([\w-]+)["']?/);
    if (m) aliases[m[1]] = m[2];
  });
}
console.log('Loaded aliases:', Object.keys(aliases).length, Object.entries(aliases).map(([k,v]) => k+'->'+v).join(', '));

// ── 2. 提取 dist CSS 中的所有类名（支持多行选择器）──────────────────────
const CSS_FILES = [
  { file: 'lingjing-core-b-system.css',      scene: 'b_system'    },
  { file: 'lingjing-core-ue5-overlay.css',   scene: 'ue5_overlay' },
  { file: 'lingjing-core-website.css',       scene: 'website'     },
  { file: 'lingjing-core-presentation.css',  scene: 'presentation'},
];

const classMap = {};
function extractFromSelector(selector, scene, file) {
  const classRe = /\.([a-zA-Z][a-zA-Z0-9_-]{2,})/g;
  let m;
  while ((m = classRe.exec(selector)) !== null) {
    const cls = m[1];
    if (!classMap[cls]) classMap[cls] = { scenes: [], files: [] };
    if (!classMap[cls].scenes.includes(scene)) classMap[cls].scenes.push(scene);
    if (!classMap[cls].files.includes(file)) classMap[cls].files.push(file);
  }
}

for (const { file, scene } of CSS_FILES) {
  const content = fs.readFileSync(path.join(distDir, file), 'utf8');
  // Remove comments before processing
  const noComments = content.replace(/\/\*[\s\S]*?\*\//g, '');
  // Split by { } to get selector blocks
  // Strategy: collect lines until we hit {, that's the selector
  const lines = noComments.split('\n');
  let pendingSelector = '';
  lines.forEach(line => {
    const trimmed = line.trim().replace(/\r$/, '');
    if (trimmed.startsWith('@') || trimmed.startsWith('//')) {
      pendingSelector = '';
      return;
    }
    if (trimmed.includes('{')) {
      // End of selector block
      const selectorPart = (pendingSelector + ' ' + trimmed.split('{')[0]).trim();
      extractFromSelector(selectorPart, scene, file);
      pendingSelector = '';
    } else if (trimmed.endsWith(',') || (trimmed.length > 0 && !trimmed.includes(':'))) {
      // Multi-line selector continuation (line ends with , or is a plain selector line)
      // But skip lines that look like CSS properties (have : but not pseudo-selectors)
      if (!trimmed.match(/^[\w-]+\s*:/)) {
        pendingSelector += ' ' + trimmed;
      }
    } else if (trimmed.includes('}')) {
      pendingSelector = '';
    }
  });
}
console.log('Total classes extracted from CSS:', Object.keys(classMap).length);

// ── 3. 分类规则 ──────────────────────────────────────────────────────────
const UTILITY_RE = [
  /^(flex|grid|block|inline|hidden|visible|relative|absolute|fixed|sticky|static)$/,
  /^(overflow|opacity|transition|duration|cursor|select|outline)(-|$)/,
  /^(justify|items|self|float|clear|whitespace|leading|tracking)(-|$)/,
  /^content-(center|around|between|end|start|evenly|stretch)$/,
  /^(font-bold|font-medium|font-normal|font-semibold)$/,
  /^(uppercase|lowercase|capitalize|underline|line-through|no-underline|normal-case)$/,
  /^(mix-blend|blur|drop-shadow|grayscale|sepia|saturate|contrast|brightness|hue-rotate|invert)(-|$)/,
  /^(sr-only|d-block|d-flex|d-grid|d-inline)(-\w+)?$/,
  /^text-(2xl|3xl|lg|base|sm|xs|xl|center|left|right|justify|uppercase|lowercase|capitalize|normal-case|placeholder|primary|secondary|indent|decoration|responsive|aero-blue|amber|blue|cyan|green|pulse-cyan|red|signal-green)(-\w+)?$/,
  /^bg-(base|card|glass|blue|cyan|green|amber|red|pulse|signal|error|warning|aero|transparent)(-\w+)?$/,
  /^border(-[0-9]+|-solid|-dashed|-dotted|-double|-none|-hidden|-primary|-aero|-blue|-pulse|-error|-signal|-warning|-transparent|-[btlr])?$/,
  /^shadow(-glow|-lg|-md|-sm|-none|-responsive)?$/,
  /^(glass-shadow|glass-opacity|glass-md|glass-sm|glass-lg|glass-xl|glass-border|glass-light|glass-strong|glass-medium|glass-colored|glass-frosted|glass-fixed|glass-sticky|glass-flowing|glass-interactive|glass-overlay)$/,
  /^rounded(-none|-sm|-md|-lg|-xl|-full|-responsive-\w+)?$/,
  /^(p|m|px|py|pt|pb|pl|pr|mx|my|mt|mb|ml|mr|gap)-(xs|sm|md|lg|xl|2xl|0|auto)$/,
  /^(p|m)-responsive-\w+$/,
  /^(w|h|min-w|min-h|max-w|max-h)-(auto|fit|full|screen|none|0|xs|sm|md|lg|xl|2xl|3xl|4xl|5xl|6xl|7xl)$/,
  /^(z|top|right|bottom|left)-(0|10|20|30|40|50|100|auto)$/,
  /^grid-(cols|rows|responsive)(-\w+)?$/,
  /^list-(none|disc|decimal|circle|square|inside|outside|upper|lower)(-\w+)?$/,
  /^position-(absolute|relative|fixed|static)$/,
  /^transition-(all|colors|fast|slow|normal|none|transform)$/,
  /^select-(all|none|text)$/,
  /^clear-(both|left|right|none)$/,
  /^(inline|inline-block|inline-flex|inline-grid)$/,
  /^(rounded|text|shadow|m|p)-responsive-\w+$/,
  /^(col|row)-\w+$/,
  /^animate-(breathe|fade-in|pulse|slide-up)$/,
  /^duration-\d+$/,
  /^(brightness|contrast|hue-rotate|saturate|sepia|opacity|grayscale)-\d+$/,
];

const DEMO_CLASSES = new Set([
  'world-marker--demo-a', 'world-marker--demo-b', 'world-marker--demo-d',
  'demo-info', 'demo-info-card',
]);

const DEPRECATED_MAP = {
  'nav-sidebar':                'b-sidebar / b-sidebar-nav',
  'nav-top':                    'b-header',
  'header-top':                 'b-header',
  'card-glass':                 'content-card',
  'card-solid':                 'content-card',
  'effect-glass':               'content-card',
  'card-glass-hud':             'detail-panel (ue5_overlay)',
  'advanced-table-layout':      'advanced-data-table',
  'advanced-table-layout-main': 'advanced-data-table',
  'advanced-table-layout-side': 'advanced-data-table',
  'activity-timeline':          'status-timeline',
  'activity-timeline-content':  'status-timeline-content',
  'activity-timeline-dot':      'status-timeline-dot',
  'activity-timeline-item':     'status-timeline-item',
  'activity-timeline-time':     'status-timeline-time',
  'activity-timeline-title':    'status-timeline-title',
};

function isUtility(cls) {
  for (const re of UTILITY_RE) {
    if (re.test(cls)) return true;
  }
  return false;
}

function classify(cls) {
  if (DEMO_CLASSES.has(cls))  return { type: 'demo_only' };
  if (cls in aliases)         return { type: 'alias', canonical: aliases[cls] };
  if (cls in DEPRECATED_MAP)  return { type: 'deprecated', use_instead: DEPRECATED_MAP[cls] };
  if (isUtility(cls))         return { type: 'utility' };
  return { type: 'canonical' };
}

// ── 4. 构建注册表 ────────────────────────────────────────────────────────
const registry = {};

for (const [cls, info] of Object.entries(classMap)) {
  const c = classify(cls);
  registry[cls] = { ...c, scenes: info.scenes, source: info.files[0] };
}

// 补充只在 matrix aliases 中存在、CSS 中无独立选择器的别名
for (const [aliasName, canonicalName] of Object.entries(aliases)) {
  if (!registry[aliasName]) {
    registry[aliasName] = {
      type: 'alias',
      canonical: canonicalName,
      scenes: [],
      source: 'scene_coverage_matrix.yml#canonical_class_contract.aliases',
      note: 'No standalone CSS selector; alias mapping only'
    };
  }
}

// ── 5. 统计 ──────────────────────────────────────────────────────────────
const stats = {};
for (const v of Object.values(registry)) {
  stats[v.type] = (stats[v.type] || 0) + 1;
}
console.log('Registry stats:', JSON.stringify(stats));
console.log('Total entries:', Object.keys(registry).length);

// ── 6. 输出 ──────────────────────────────────────────────────────────────
const output = {
  _meta: {
    version: '1.0.0',
    skill_version: '3.1.6',
    generated: new Date().toISOString().split('T')[0],
    source_of_truth: 'SKILL.md frontmatter metadata.version',
    type_legend: {
      canonical:  '正式可用类，可直接写入业务交付页面',
      alias:      '别名，落地前必须归一化为 .canonical 字段所指类名',
      deprecated: '已废弃类，应改用 use_instead 字段中的替代方案',
      demo_only:  '仅限 examples/demo/ 使用，业务交付页禁止出现',
      utility:    '通用CSS工具类，可直接使用，无组件级语义约束'
    },
    usage: 'AI生成HTML前(Pre-check)和生成后(Post-check)均需查此表。alias/deprecated/demo_only类必须处理替换。未收录类需走缺失组件处理流程(SKILL.md §0.0.2.a)。',
    rebuild_cmd: 'node scripts/build-registry.js  # 从 lingjing-ui-core 根目录执行'
  },
  stats,
  classes: registry
};

const OUTPUT = path.join(BASE, 'data/class_registry.json');
fs.writeFileSync(OUTPUT, JSON.stringify(output, null, 2));
const sizeKB = Math.round(fs.statSync(OUTPUT).size / 1024);
console.log('Written:', OUTPUT, '(' + sizeKB + ' KB)');

// ── 7. 验证关键类名 ──────────────────────────────────────────────────────
console.log('\n── Key class verification ──');
const verify = [
  'b-layout-sidebar', 'b-header', 'b-sidebar-nav-link',
  'status-timeline', 'activity-timeline',
  'world-marker--demo-a',
  'advanced-data-table', 'data-table-container', 'data-table',
  'website-nav', 'hero-section',
  'ue5-overlay-root', 'topbar-hud', 'detail-panel', 'world-marker',
  'content-card', 'chart-card', 'badge', 'status-dot',
  'table-toolbar', 'filter-bar', 'search-bar',
];
verify.forEach(c => {
  const r = registry[c];
  if (r) {
    const extra = r.canonical ? ' -> ' + r.canonical : (r.use_instead ? ' use: ' + r.use_instead : '');
    console.log('  ' + r.type.padEnd(12) + c + extra);
  } else {
    console.log('  MISSING      ' + c);
  }
});
