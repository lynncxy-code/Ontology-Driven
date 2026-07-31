(function bootstrapS3BuildingPage(global) {
  "use strict";

  const runtime = global.OntoTwinPageRuntime.create({
    mockUrl: "../mock/building.json",
    isEmpty(payload) {
      return !payload || !payload.space;
    },
    render(payload, context) {
      renderBuilding(payload, context);
    }
  });

  function metricMarkup(metric) {
    const escape = global.OntoTwinPageRuntime.escapeHtml;
    return [
      '<article class="hud-metric">',
      '<span class="hud-metric__label">', escape(metric.label), '</span>',
      '<strong class="hud-metric__value">', escape(metric.display_value || metric.empty_text || "—"), '</strong>',
      '<span class="hud-metric__note">', escape(metric.note || metric.state || ""), '</span>',
      '</article>'
    ].join("");
  }

  function zoneMarkup(zone) {
    const escape = global.OntoTwinPageRuntime.escapeHtml;
    return [
      '<li>',
      '<button class="hud-list-button" type="button" data-ontotwin-interactive="zone-', escape(zone.id), '" data-action="open-zone" data-id="', escape(zone.id), '">',
      '<span><span class="hud-list-button__title">', escape(zone.name), '</span>',
      '<span class="hud-list-button__meta">', escape(zone.summary || "暂无摘要"), '</span></span>',
      '<span class="hud-count">', escape(zone.event_count === undefined ? "—" : zone.event_count), '</span>',
      '</button>',
      '</li>'
    ].join("");
  }

  function eventMarkup(event) {
    const escape = global.OntoTwinPageRuntime.escapeHtml;
    return [
      '<li class="hud-event" data-level="', escape(event.level || "unknown"), '">',
      '<div class="hud-event__head"><span class="hud-event__title">', escape(event.name), '</span>',
      '<button class="hud-button" type="button" data-ontotwin-interactive="event-', escape(event.id), '" data-action="open-event" data-id="', escape(event.id), '">查看</button></div>',
      '<div class="hud-event__meta">', escape(event.location || "未定位"), ' · ', escape(event.display_time || "时间未知"), '</div>',
      '</li>'
    ].join("");
  }

  function renderBuilding(payload, context) {
    const space = payload.space || {};
    const status = payload.status || {};
    const asset = payload.asset || {};
    const metrics = Array.isArray(payload.metrics) ? payload.metrics.slice(0, 4) : [];
    const zones = Array.isArray(payload.zones) ? payload.zones : [];
    const events = Array.isArray(payload.events) ? payload.events.slice(0, 3) : [];
    const floors = Array.isArray(payload.floors) ? payload.floors : [];
    const requestedId = context.query.space_id;

    runtime.setText("context-title", space.name, "未命名厂房");
    runtime.setText("context-path", space.path_label, "园区 / 厂房");
    runtime.setText("space-level", space.level, "S3");
    runtime.setText("space-id", requestedId || space.id, "—");
    runtime.setText("status-label", status.display_value, "未知");
    runtime.setText("status-detail", status.detail_value, "暂无状态说明");
    runtime.setText("config-revision", payload.config_revision, "未发布");

    const dot = document.getElementById("status-dot");
    if (dot) dot.dataset.level = status.level || "unknown";

    const metricHost = document.getElementById("metric-grid");
    if (metricHost) metricHost.innerHTML = metrics.length
      ? metrics.map(metricMarkup).join("")
      : '<div class="hud-page-state"><p class="hud-page-state__copy">暂无指标数据。</p></div>';

    const floorHost = document.getElementById("floor-segment");
    if (floorHost) floorHost.innerHTML = floors.length
      ? floors.map((floor, index) => [
        '<button class="hud-segment__button" type="button" data-ontotwin-interactive="floor-', runtime.escapeHtml(floor.id), '" data-action="select-floor" data-id="',
        runtime.escapeHtml(floor.id), '" aria-pressed="', index === 0 ? "true" : "false", '">',
        runtime.escapeHtml(floor.name), '</button>'
      ].join("")).join("")
      : '<span class="hud-muted">暂无楼层</span>';

    const zoneHost = document.getElementById("zone-list");
    if (zoneHost) zoneHost.innerHTML = zones.length
      ? zones.map(zoneMarkup).join("")
      : '<li class="hud-page-state"><p class="hud-page-state__copy">该厂房暂无分区。</p></li>';

    const eventHost = document.getElementById("event-list");
    if (eventHost) eventHost.innerHTML = events.length
      ? events.map(eventMarkup).join("")
      : '<li class="hud-page-state"><p class="hud-page-state__copy">当前没有待处置事件。</p></li>';

    runtime.setText("asset-code", asset.code, "—");
    runtime.setText("asset-category", asset.category, "—");
    runtime.setText("asset-area", asset.area_display, "—");
    runtime.setText("asset-capability", asset.capability, "—");
    runtime.setText("action-context", space.name, "当前厂房");
  }

  document.addEventListener("click", (event) => {
    const control = event.target.closest("[data-action]");
    if (!control) return;

    const action = control.dataset.action;
    const id = control.dataset.id || "";

    if (action === "select-floor") {
      document.querySelectorAll('[data-action="select-floor"]').forEach((button) => {
        button.setAttribute("aria-pressed", button === control ? "true" : "false");
      });
      runtime.toast(`已切换至 ${control.textContent.trim()}`, "ok");
    }

    global.OntoTwinHUD.emitAction(action, { id });
    if ((action === "select-floor" || action === "open-zone") && id) {
      global.OntoTwinBridge.post("request_open_scope", { scope_type: "zone", zone_id: id });
    }
  });

  runtime.load();
})(window);
