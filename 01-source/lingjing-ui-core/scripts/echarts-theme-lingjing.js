/**
 * echarts-theme-lingjing.js — 灵境 ECharts 场景主题包 v1.0.0
 *
 * 将灵境设计系统的 CSS Token 映射为 ECharts 主题对象，保证图表与页面视觉和谐一致。
 * 覆盖 4 个场景：
 *   lingjing-ue5          UE5 Web Overlay（深色 HUD / 霓虹发光）
 *   lingjing-b-system     B 端管理系统（专业浅色）
 *   lingjing-b-dark       B 端深色模式
 *   lingjing-website      营销门户（简洁明快）
 *   lingjing-presentation 专业演示（高对比度，适合投影）
 *
 * 依赖：echarts.min.js（需在本脚本之前加载）
 *
 * 用法：
 *   // 1. 引入（顺序必须正确）
 *   <script src="scripts/echarts.min.js"></script>
 *   <script src="scripts/echarts-theme-lingjing.js"></script>
 *
 *   // 2. 初始化图表（自动绑定场景主题）
 *   const chart = LingJingChart.init(el, 'ue5_overlay');
 *   chart.setOption({ ... });
 *
 *   // 3. 响应窗口大小变化
 *   window.addEventListener('resize', () => LingJingChart.resizeAll());
 *
 * 规范约束：
 *   - 禁止直接使用裸 echarts.init()，必须经由 LingJingChart.init() 以确保主题绑定
 *   - 图表容器必须放在 .charts-grid 或 .chart-card-body / .detail-panel__body 内
 *   - 颜色禁止硬编码，必须从本文件提供的 LINGJING_TOKENS 中取值
 *   - skill-audit.js 会检查 runtime_chart_ready 字段，空容器不得声称图表已就绪
 */

(function (global) {
  'use strict';

  // ── 设计 Token（与 CSS :root / [data-theme="dark"] 完全对应） ──────────────

  var TOKENS = {
    /** UE5 Overlay 深色（data-theme="dark"，HUD 霓虹风格） */
    ue5: {
      bg:           'transparent',
      bgPanel:      'rgba(3, 7, 18, 0.60)',
      bgGrid:       'rgba(203, 213, 225, 0.06)',
      axisLine:     'rgba(203, 213, 225, 0.20)',
      splitLine:    'rgba(203, 213, 225, 0.08)',
      textPrimary:  '#F8FAFC',
      textSecond:   '#94A3B8',
      series: ['#00E5FF', '#00FFC8', '#FFB020', '#FF4D4F', '#818CF8', '#0084FF'],
      //          cyan      green      amber      red        indigo     blue
      tooltipBg:    'rgba(3, 7, 18, 0.90)',
      tooltipBorder:'rgba(0, 229, 255, 0.30)'
    },
    /** B 端浅色（data-theme="light"，专业清晰） */
    bLight: {
      bg:           'transparent',
      bgPanel:      'rgba(255, 255, 255, 0.90)',
      bgGrid:       'rgba(241, 245, 249, 0.80)',
      axisLine:     'rgba(203, 213, 225, 0.80)',
      splitLine:    'rgba(203, 213, 225, 0.50)',
      textPrimary:  '#0F172A',
      textSecond:   '#475569',
      series: ['#0066CC', '#0099AA', '#00A383', '#D97706', '#DC2626', '#4338CA'],
      tooltipBg:    'rgba(255, 255, 255, 0.97)',
      tooltipBorder:'rgba(28, 102, 196, 0.25)'
    },
    /** B 端深色（data-theme="dark"） */
    bDark: {
      bg:           'transparent',
      bgPanel:      'rgba(15, 30, 60, 0.80)',
      bgGrid:       'rgba(31, 41, 55, 0.60)',
      axisLine:     'rgba(55, 65, 81, 0.80)',
      splitLine:    'rgba(31, 41, 55, 0.80)',
      textPrimary:  '#F8FAFC',
      textSecond:   '#94A3B8',
      series: ['#0084FF', '#00E5FF', '#00FFC8', '#FFB020', '#FF4D4F', '#818CF8'],
      tooltipBg:    'rgba(15, 30, 60, 0.95)',
      tooltipBorder:'rgba(0, 132, 255, 0.30)'
    },
    /** 营销门户 / 企业官网（浅色，简洁明快） */
    website: {
      bg:           'transparent',
      bgPanel:      'rgba(255, 255, 255, 0.95)',
      bgGrid:       '#F8FAFC',
      axisLine:     '#E2E8F0',
      splitLine:    '#F1F5F9',
      textPrimary:  '#0F172A',
      textSecond:   '#64748B',
      series: ['#0066CC', '#0099AA', '#00A383', '#D97706', '#DC2626', '#7C3AED'],
      tooltipBg:    '#FFFFFF',
      tooltipBorder:'rgba(0, 102, 204, 0.20)'
    },
    /** 专业演示 / 汇报（高对比度，适合投影） */
    presentation: {
      bg:           'transparent',
      bgPanel:      'rgba(15, 23, 42, 0.90)',
      bgGrid:       'rgba(30, 41, 59, 0.50)',
      axisLine:     'rgba(148, 163, 184, 0.60)',
      splitLine:    'rgba(51, 65, 85, 0.60)',
      textPrimary:  '#F8FAFC',
      textSecond:   '#CBD5E1',
      series: ['#38BDF8', '#34D399', '#FCD34D', '#F87171', '#A78BFA', '#60A5FA'],
      tooltipBg:    'rgba(15, 23, 42, 0.95)',
      tooltipBorder:'rgba(56, 189, 248, 0.40)'
    }
  };

  // ── 公共 option 构建器 ────────────────────────────────────────────────────

  function buildTheme(t) {
    return {
      color: t.series,
      backgroundColor: t.bg,

      textStyle: { color: t.textSecond, fontFamily: "'Source Han Mono CN Regular', 'Noto Sans SC', sans-serif" },

      title: {
        textStyle: { color: t.textPrimary, fontSize: 13, fontWeight: 600 },
        subtextStyle: { color: t.textSecond, fontSize: 11 }
      },

      legend: {
        textStyle: { color: t.textSecond, fontSize: 12 },
        pageTextStyle: { color: t.textSecond },
        icon: 'circle',
        itemWidth: 8,
        itemHeight: 8
      },

      tooltip: {
        backgroundColor: t.tooltipBg,
        borderColor: t.tooltipBorder,
        borderWidth: 1,
        textStyle: { color: t.textPrimary, fontSize: 12 },
        extraCssText: 'backdrop-filter: blur(8px); border-radius: 6px;'
      },

      grid: {
        left: '3%', right: '4%', top: '12%', bottom: '8%',
        containLabel: true
      },

      categoryAxis: {
        axisLine:  { lineStyle: { color: t.axisLine } },
        axisTick:  { lineStyle: { color: t.axisLine }, length: 3 },
        axisLabel: { color: t.textSecond, fontSize: 11 },
        splitLine: { lineStyle: { color: t.splitLine, type: 'dashed' } }
      },

      valueAxis: {
        axisLine:  { show: false },
        axisTick:  { show: false },
        axisLabel: { color: t.textSecond, fontSize: 11 },
        splitLine: { lineStyle: { color: t.splitLine, type: 'dashed' } },
        nameTextStyle: { color: t.textSecond, fontSize: 10 }
      },

      line: {
        symbol: 'circle',
        symbolSize: 5,
        lineStyle: { width: 2 },
        smooth: true,
        emphasis: { focus: 'series' }
      },

      bar: {
        itemStyle: { borderRadius: [2, 2, 0, 0] },
        barMaxWidth: 40,
        emphasis: { focus: 'series' }
      },

      pie: {
        radius: ['40%', '70%'],
        label: { color: t.textSecond, fontSize: 11 },
        labelLine: { lineStyle: { color: t.axisLine } },
        emphasis: { scale: true, scaleSize: 6 }
      },

      scatter: {
        symbol: 'circle',
        symbolSize: 8,
        emphasis: { focus: 'series' }
      }
    };
  }

  // ── UE5 专用补丁（霓虹发光 + 零背景） ────────────────────────────────────
  // 在 buildTheme 基础上叠加 UE5 HUD 特有的视觉增强

  function buildUe5Theme() {
    var base = buildTheme(TOKENS.ue5);
    var seriesColors = TOKENS.ue5.series;

    // 折线图：增加发光阴影
    base.line.lineStyle = { width: 2, shadowBlur: 8, shadowColor: seriesColors[0], shadowOffsetY: 0 };
    base.line.areaStyle = { opacity: 0.12 };
    base.line.symbol = 'none';          // HUD 折线去掉端点更干净

    // 柱状图：细条 + 渐变
    base.bar.itemStyle = {
      borderRadius: [2, 2, 0, 0],
      // 渐变需在 setOption 中用 echarts.graphic.LinearGradient 定义
    };
    base.bar.barMaxWidth = 28;

    // 饼图：仅显示外环
    base.pie.radius = ['55%', '78%'];
    base.pie.label = { show: false };   // HUD 内环形图默认不显示标签

    return base;
  }

  // ── 注册主题 ──────────────────────────────────────────────────────────────

  var THEME_MAP = {
    'lingjing-ue5':          buildUe5Theme(),
    'lingjing-b-system':     buildTheme(TOKENS.bLight),
    'lingjing-b-dark':       buildTheme(TOKENS.bDark),
    'lingjing-website':      buildTheme(TOKENS.website),
    'lingjing-presentation': buildTheme(TOKENS.presentation)
  };

  // 场景 ID → 主题名映射
  var SCENE_THEME = {
    'ue5_overlay':   'lingjing-ue5',
    'b_system':      'lingjing-b-system',
    'b_system_dark': 'lingjing-b-dark',
    'website':       'lingjing-website',
    'presentation':  'lingjing-presentation'
  };

  if (typeof echarts !== 'undefined') {
    Object.keys(THEME_MAP).forEach(function (name) {
      echarts.registerTheme(name, THEME_MAP[name]);
    });
  } else {
    console.warn('[LingJingChart] echarts 未加载，主题注册跳过。请先引入 echarts.min.js。');
  }

  // ── LingJingChart 公共 API ────────────────────────────────────────────────

  var _instances = [];  // 跟踪所有实例，支持 resizeAll

  /**
   * 检测当前页面场景，返回主题名
   * @param {string} [hint]  显式指定场景 ID（ue5_overlay / b_system / website / presentation）
   * @returns {string} ECharts 主题名
   */
  function detectTheme(hint) {
    if (hint && SCENE_THEME[hint]) return SCENE_THEME[hint];

    // 自动检测：优先看 <html data-scene>，其次看 body class，最后看 DOM 特征
    var htmlEl = document.documentElement;
    var scene = htmlEl.getAttribute('data-scene');
    if (scene && SCENE_THEME[scene]) return SCENE_THEME[scene];

    if (document.querySelector('.ue5-overlay-root'))  return 'lingjing-ue5';
    if (document.querySelector('.b-layout-sidebar'))   return 'lingjing-b-system';
    if (document.querySelector('.website-nav'))        return 'lingjing-website';
    if (document.querySelector('.presentation-slide')) return 'lingjing-presentation';

    // 深色 / 浅色 fallback
    var theme = htmlEl.getAttribute('data-theme');
    return (theme === 'dark') ? 'lingjing-ue5' : 'lingjing-b-system';
  }

  /**
   * 初始化图表实例（替代裸 echarts.init）
   * @param {HTMLElement|string} el      容器元素或选择器
   * @param {string}             [scene] 场景 ID（可选，自动检测）
   * @param {object}             [opts]  echarts.init 的 opts 参数
   * @returns {echarts.ECharts}
   */
  function init(el, scene, opts) {
    if (typeof el === 'string') el = document.querySelector(el);
    if (!el) { console.error('[LingJingChart] 容器元素不存在'); return null; }

    var themeName = detectTheme(scene);
    var chart = echarts.init(el, themeName, Object.assign({ renderer: 'canvas' }, opts || {}));
    _instances.push(chart);
    return chart;
  }

  /**
   * 批量响应 resize（在 window.resize 时调用）
   */
  function resizeAll() {
    _instances.forEach(function (c) {
      if (c && !c.isDisposed()) c.resize();
    });
  }

  /**
   * 获取当前场景的颜色 Token（用于在 setOption 中手动构造 LinearGradient 等）
   * @param {string} [scene]
   * @returns {object} token 对象
   */
  function getTokens(scene) {
    var theme = detectTheme(scene);
    var map = {
      'lingjing-ue5':          TOKENS.ue5,
      'lingjing-b-system':     TOKENS.bLight,
      'lingjing-b-dark':       TOKENS.bDark,
      'lingjing-website':      TOKENS.website,
      'lingjing-presentation': TOKENS.presentation
    };
    return map[theme] || TOKENS.bLight;
  }

  // ── 导出 ──────────────────────────────────────────────────────────────────

  global.LingJingChart = {
    init:       init,
    resizeAll:  resizeAll,
    getTokens:  getTokens,
    detectTheme: detectTheme,
    TOKENS:     TOKENS,
    /** ECharts 主题名常量，供直接传给 echarts.init 使用 */
    THEMES: {
      UE5:          'lingjing-ue5',
      B_SYSTEM:     'lingjing-b-system',
      B_DARK:       'lingjing-b-dark',
      WEBSITE:      'lingjing-website',
      PRESENTATION: 'lingjing-presentation'
    }
  };

}(typeof window !== 'undefined' ? window : this));
