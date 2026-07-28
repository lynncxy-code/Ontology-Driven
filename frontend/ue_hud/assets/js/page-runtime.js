(function bootstrapOntoTwinPageRuntime(global) {
  "use strict";

  function query() {
    return Object.fromEntries(new URLSearchParams(global.location.search).entries());
  }

  function setText(id, value, fallback) {
    const element = document.getElementById(id);
    if (!element) return;
    const next = value === null || value === undefined || value === "" ? fallback : value;
    element.textContent = next === null || next === undefined ? "" : String(next);
  }

  function escapeHtml(value) {
    return String(value === null || value === undefined ? "" : value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function showState(kind, options) {
    const state = options || {};
    const host = document.getElementById("page-state");
    const content = document.getElementById("page-content");
    if (!host || !content) return;

    if (kind === "ready") {
      host.hidden = true;
      content.hidden = false;
      return;
    }

    content.hidden = true;
    host.hidden = false;
    host.dataset.state = kind;

    if (kind === "loading") {
      host.innerHTML = [
        '<div class="hud-page-state">',
        '<h2 class="hud-page-state__title">正在读取厂房数据</h2>',
        '<div class="hud-skeleton" aria-hidden="true">',
        '<span class="hud-skeleton__line"></span>',
        '<span class="hud-skeleton__line"></span>',
        '<span class="hud-skeleton__line"></span>',
        '</div>',
        '</div>'
      ].join("");
      return;
    }

    const title = kind === "empty" ? "暂无可展示数据" : "页面数据读取失败";
    const copy = state.message || (kind === "empty" ? "当前对象尚未发布厂房信息。" : "请检查数据源后重试。");
    host.innerHTML = [
      '<div class="hud-page-state">',
      '<h2 class="hud-page-state__title">', escapeHtml(title), '</h2>',
      '<p class="hud-page-state__copy">', escapeHtml(copy), '</p>',
      kind === "error" ? '<button class="hud-button" id="state-retry" type="button" data-ue-interactive="retry">重试</button>' : '',
      '</div>'
    ].join("");
  }

  function toast(message, type) {
    const host = document.getElementById("toast-region");
    if (!host || !message) return;
    const item = document.createElement("div");
    item.className = "hud-toast";
    item.dataset.type = type || "info";
    item.textContent = message;
    host.appendChild(item);
    global.setTimeout(() => item.remove(), 2400);
  }

  function create(options) {
    const config = options || {};
    const queryParams = query();
    let retryHandler = null;

    async function loadMock() {
      if (!config.mockUrl) throw new Error("未配置预览数据");
      const response = await global.fetch(config.mockUrl, { cache: "no-store" });
      if (!response.ok) throw new Error(`无法读取预览数据 (${response.status})`);
      return response.json();
    }

    async function load() {
      showState("loading");

      if (queryParams.preview_state === "loading") return;
      if (queryParams.preview_state === "empty") {
        showState("empty");
        return;
      }
      if (queryParams.preview_state === "error") {
        showState("error", { message: "预览：数据源暂不可用。" });
        return;
      }

      try {
        const initial = global.__ONTOTWIN_INITIAL_DATA__ || await loadMock();
        global.OntoTwinHUD.setData(initial, { source: global.__ONTOTWIN_INITIAL_DATA__ ? "host" : "mock" });
      } catch (error) {
        showState("error", { message: error && error.message });
      }
    }

    retryHandler = load;
    document.addEventListener("click", (event) => {
      if (event.target && event.target.id === "state-retry" && retryHandler) retryHandler();
    });

    global.OntoTwinHUD.subscribe((payload, meta) => {
      if (!payload || (typeof config.isEmpty === "function" && config.isEmpty(payload))) {
        showState("empty");
        return;
      }
      config.render(payload, { meta: meta || {}, query: queryParams });
      showState("ready");
    });

    global.addEventListener("resize", () => {
      global.dispatchEvent(new CustomEvent("ontotwin:hud-regions-changed", {
        detail: global.OntoTwinHUD.getInteractiveRegions()
      }));
    });

    return {
      load,
      query: queryParams,
      toast,
      setText,
      escapeHtml
    };
  }

  global.OntoTwinPageRuntime = Object.freeze({ create, escapeHtml, setText });
})(window);
