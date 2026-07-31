(function bootstrapOntoTwinBridge(global) {
  "use strict";

  const dataListeners = new Set();
  const actionListeners = new Set();
  const hostListeners = new Set();
  let currentPayload = null;
  let sequence = 0;
  let lastRegionSignature = "";
  let regionTimer = 0;

  function nativeHost() {
    return global.ue && (global.ue.ontotwinwebbridge || global.ue.ontotwinWebBridge || global.ue.ontotwinHud);
  }

  function post(type, payload, requestId) {
    const message = {
      type,
      request_id: requestId || `web-${Date.now()}-${++sequence}`,
      payload: payload || {}
    };
    const host = nativeHost();
    if (host && typeof host.onmessage === "function") host.onmessage(JSON.stringify(message));
    else if (host && typeof host.onMessage === "function") host.onMessage(JSON.stringify(message));
    return message.request_id;
  }

  function notify(payload, meta) {
    currentPayload = payload;
    dataListeners.forEach(listener => listener(payload, meta || {}));
  }

  function emitAction(action, payload) {
    const detail = { action, payload: payload || {}, page: document.body.dataset.page || "unknown", timestamp: new Date().toISOString() };
    actionListeners.forEach(listener => listener(detail));
    global.dispatchEvent(new CustomEvent("ontotwin:hud-action", { detail }));
    if (["select_instance", "clear_selection", "request_open_scope", "request_open_page"].includes(action)) {
      post(action, payload || {});
    }
    return detail;
  }

  function getInteractiveRegions() {
    return Array.from(document.querySelectorAll("[data-ontotwin-interactive],[data-ue-interactive]"))
      .filter(element => {
        const style = global.getComputedStyle(element);
        const rect = element.getBoundingClientRect();
        return style.visibility !== "hidden" && style.display !== "none" && rect.width > 0 && rect.height > 0;
      })
      .slice(0, 256)
      .map(element => {
        const rect = element.getBoundingClientRect();
        return {
          id: element.id || element.dataset.ontotwinInteractive || element.dataset.ueInteractive || element.getAttribute("aria-label") || "interactive",
          x: Math.max(0, Math.round(rect.x)), y: Math.max(0, Math.round(rect.y)),
          width: Math.round(rect.width), height: Math.round(rect.height)
        };
      });
  }

  function reportInteractiveRegions() {
    global.clearTimeout(regionTimer);
    regionTimer = global.setTimeout(() => {
      const regions = getInteractiveRegions();
      const signature = JSON.stringify(regions);
      if (signature !== lastRegionSignature) {
        lastRegionSignature = signature;
        post("interactive_regions", { regions });
      }
    }, 100);
  }

  global.OntoTwinBridge = Object.freeze({
    version: "1.0",
    post,
    receive(message) {
      hostListeners.forEach(listener => listener(message));
      global.dispatchEvent(new CustomEvent("ontotwin:host-message", { detail: message }));
    },
    subscribe(listener) {
      hostListeners.add(listener);
      return () => hostListeners.delete(listener);
    },
    reportInteractiveRegions
  });

  global.OntoTwinHUD = Object.freeze({
    version: "1.0",
    setData(payload, meta) { notify(payload, meta); },
    patchData(patch, meta) { notify(Object.assign({}, currentPayload || {}, patch || {}), Object.assign({ patch: true }, meta || {})); },
    getData() { return currentPayload; },
    subscribe(listener) { dataListeners.add(listener); return () => dataListeners.delete(listener); },
    onAction(listener) { actionListeners.add(listener); return () => actionListeners.delete(listener); },
    emitAction,
    getInteractiveRegions
  });

  function ready() {
    post("ready", { version: "1.0", capabilities: ["interactive_regions", "select_instance", "clear_selection", "request_open_scope", "request_open_page"] });
    reportInteractiveRegions();
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", ready, { once: true });
  else ready();
  global.addEventListener("resize", reportInteractiveRegions, { passive: true });
  global.addEventListener("scroll", reportInteractiveRegions, { passive: true, capture: true });
  new MutationObserver(reportInteractiveRegions).observe(document.documentElement, { childList: true, subtree: true, attributes: true });
})(window);
