(function bootstrapOntoTwinBusinessPage(global) {
  "use strict";

  const body = document.body;
  const root = document.getElementById("root");
  const query = Object.fromEntries(new URLSearchParams(global.location.search).entries());
  const actions = new Map();
  let actionSequence = 0;

  function escapeHtml(value) {
    return String(value === null || value === undefined ? "" : value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function shell() {
    root.innerHTML = [
      '<main id="app" class="hud-layout" aria-label="OntoTwin 透明业务页面">',
      '<header class="hud-topbar hud-surface hud-surface--strong" data-ontotwin-interactive="context-bar">',
      '<div class="hud-topbar__context"><div class="hud-brand-mark" aria-hidden="true">OT</div>',
      '<div class="hud-topbar__title"><strong id="context-title">正在读取页面</strong><span id="context-path">OntoTwin Nexus</span></div></div>',
      '<div class="hud-topbar__meta"><span class="hud-context-code" id="context-code">—</span>',
      '<div class="hud-live-strip"><span class="hud-dot" id="status-dot" data-level="unknown" aria-hidden="true"></span><span class="hud-live-strip__label" id="status-label">未知</span></div></div>',
      '</header>',
      '<aside class="hud-panel hud-panel--left hud-surface hud-surface--strong" data-ontotwin-interactive="primary-panel" aria-label="主要业务信息">',
      '<div id="page-state" aria-live="polite"></div>',
      '<div id="page-content" class="hud-panel__scroll" hidden></div>',
      '</aside>',
      '<section class="hud-scene-clear-zone" aria-label="透明三维模型观察区域" data-ue-decoration></section>',
      '<aside class="hud-panel hud-panel--right hud-surface" data-ontotwin-interactive="secondary-panel" aria-label="补充业务信息">',
      '<div id="secondary-content" class="hud-panel__scroll" hidden></div>',
      '</aside>',
      '<nav class="hud-actionbar hud-surface hud-surface--strong" id="page-actions" data-ontotwin-interactive="action-bar" aria-label="页面操作"></nav>',
      '<div class="hud-toast-region" id="toast-region" aria-live="polite" aria-atomic="true"></div>',
      '</main>'
    ].join("");
  }

  function showState(kind, message) {
    const state = document.getElementById("page-state");
    const content = document.getElementById("page-content");
    const secondary = document.getElementById("secondary-content");
    if (kind === "ready") {
      state.hidden = true;
      content.hidden = false;
      secondary.hidden = false;
      return;
    }
    state.hidden = false;
    content.hidden = true;
    secondary.hidden = true;
    const title = kind === "loading" ? "正在读取页面数据" : kind === "empty" ? "暂无可展示数据" : "页面数据读取失败";
    const copy = message || (kind === "empty" ? "当前范围尚未发布业务内容。" : "请检查页面数据源后重试。");
    state.innerHTML = [
      '<div class="hud-page-state">',
      '<h2 class="hud-page-state__title">', escapeHtml(title), '</h2>',
      kind === "loading" ? '<div class="hud-skeleton" aria-hidden="true"><span class="hud-skeleton__line"></span><span class="hud-skeleton__line"></span><span class="hud-skeleton__line"></span></div>' : '<p class="hud-page-state__copy">' + escapeHtml(copy) + '</p>',
      kind === "error" ? '<button class="hud-button" id="state-retry" type="button" data-ontotwin-interactive="retry">重试</button>' : '',
      '</div>'
    ].join("");
  }

  function metricMarkup(metric) {
    return [
      '<article class="hud-metric">',
      '<span class="hud-metric__label">', escapeHtml(metric.label), '</span>',
      '<strong class="hud-metric__value">', escapeHtml(metric.display_value || "—"), '</strong>',
      '<span class="hud-metric__note">', escapeHtml(metric.note || ""), '</span>',
      '</article>'
    ].join("");
  }

  function resolvePayload(payload, contextValue) {
    const next = {};
    Object.entries(payload || {}).forEach(([key, value]) => {
      next[key] = value === "$context" ? contextValue : value;
    });
    return next;
  }

  function itemMarkup(item, contextValue) {
    const isAction = item.action && item.action.type;
    const tag = isAction ? "button" : "article";
    const className = isAction ? "hud-record-button" : "hud-record";
    let actionAttribute = "";
    if (isAction) {
      const key = `action-${++actionSequence}`;
      actions.set(key, { type: item.action.type, payload: resolvePayload(item.action.payload, contextValue) });
      actionAttribute = ` type="button" data-action-key="${key}" data-ontotwin-interactive="${key}"`;
    }
    return [
      '<li><', tag, ' class="', className, '" data-level="', escapeHtml(item.level || "unknown"), '"', actionAttribute, '>',
      '<span><span class="hud-record__title">', escapeHtml(item.title || "未命名"), '</span><span class="hud-record__meta">', escapeHtml(item.meta || ""), '</span></span>',
      '<span class="hud-record__value">', escapeHtml(item.value || (isAction ? "查看" : "—")), '</span>',
      '</', tag, '></li>'
    ].join("");
  }

  function groupMarkup(group, contextValue) {
    const items = Array.isArray(group.items) ? group.items : [];
    return [
      '<section class="hud-section">',
      '<div class="hud-section__head"><h2 class="hud-section__title">', escapeHtml(group.title || "信息"), '</h2><span class="hud-muted">', escapeHtml(group.hint || ""), '</span></div>',
      items.length ? '<ul class="hud-records">' + items.map(item => itemMarkup(item, contextValue)).join("") + '</ul>' : '<div class="hud-page-state"><p class="hud-page-state__copy">暂无数据。</p></div>',
      '</section>'
    ].join("");
  }

  function actionMarkup(action, contextValue, index) {
    const key = `footer-${index}-${++actionSequence}`;
    actions.set(key, { type: action.type, payload: resolvePayload(action.payload, contextValue) });
    const primary = action.primary ? " hud-button--primary" : "";
    return '<button class="hud-button' + primary + '" type="button" data-action-key="' + key + '" data-ontotwin-interactive="' + key + '">' + escapeHtml(action.label || "操作") + '</button>';
  }

  function setText(id, value, fallback) {
    const element = document.getElementById(id);
    if (element) element.textContent = value || fallback || "";
  }

  function render(payload) {
    actions.clear();
    const page = payload.page || {};
    const contextKey = page.context_query || "space_id";
    const contextValue = query[contextKey] || page.context_id || "";
    setText("context-title", page.title, "业务页面");
    setText("context-path", page.path_label, "OntoTwin Nexus");
    setText("context-code", contextValue, page.context_label || "—");
    setText("status-label", page.status_label, "未知");
    const dot = document.getElementById("status-dot");
    if (dot) dot.dataset.level = page.status_level || "unknown";

    const metrics = Array.isArray(payload.metrics) ? payload.metrics.slice(0, 4) : [];
    const primaryGroups = Array.isArray(payload.primary_groups) ? payload.primary_groups : [];
    const secondaryGroups = Array.isArray(payload.secondary_groups) ? payload.secondary_groups : [];
    const primary = document.getElementById("page-content");
    primary.innerHTML = [
      '<section class="hud-section"><p class="hud-eyebrow">', escapeHtml(page.level || "业务视图"), '</p><h1 class="hud-heading">', escapeHtml(page.heading || page.title || "业务页面"), '</h1><p class="hud-copy">', escapeHtml(page.description || ""), '</p></section>',
      metrics.length ? '<div class="hud-divider"></div><section class="hud-section"><div class="hud-section__head"><h2 class="hud-section__title">核心指标</h2><span class="hud-muted">' + escapeHtml(page.revision || "实时") + '</span></div><div class="hud-metric-grid">' + metrics.map(metricMarkup).join("") + '</div></section>' : '',
      primaryGroups.map(group => groupMarkup(group, contextValue)).join("")
    ].join("");

    document.getElementById("secondary-content").innerHTML = secondaryGroups.map(group => groupMarkup(group, contextValue)).join("");
    const footerActions = Array.isArray(payload.actions) ? payload.actions : [];
    document.getElementById("page-actions").innerHTML = footerActions.map((action, index) => actionMarkup(action, contextValue, index)).join("");
    showState("ready");
    global.OntoTwinBridge.reportInteractiveRegions();
  }

  function toast(message) {
    const host = document.getElementById("toast-region");
    const item = document.createElement("div");
    item.className = "hud-toast";
    item.textContent = message;
    host.appendChild(item);
    global.setTimeout(() => item.remove(), 2200);
  }

  async function load() {
    showState("loading");
    if (query.preview_state === "loading") return;
    if (query.preview_state === "empty") { showState("empty"); return; }
    if (query.preview_state === "error") { showState("error", "预览：数据源暂不可用。"); return; }
    try {
      const response = await global.fetch(body.dataset.mockUrl, { cache: "no-store" });
      if (!response.ok) throw new Error(`无法读取页面数据 (${response.status})`);
      const payload = global.__ONTOTWIN_INITIAL_DATA__ || await response.json();
      global.OntoTwinHUD.setData(payload, { source: global.__ONTOTWIN_INITIAL_DATA__ ? "host" : "mock" });
    } catch (error) {
      showState("error", error && error.message);
    }
  }

  document.addEventListener("click", event => {
    if (event.target && event.target.id === "state-retry") { load(); return; }
    const control = event.target.closest("[data-action-key]");
    if (!control) return;
    const action = actions.get(control.dataset.actionKey);
    if (!action) return;
    global.OntoTwinHUD.emitAction(action.type, action.payload);
    toast(`已发送：${control.textContent.trim()}`);
  });

  shell();
  global.OntoTwinHUD.subscribe(payload => {
    if (!payload || !payload.page) { showState("empty"); return; }
    render(payload);
  });
  load();
})(window);
