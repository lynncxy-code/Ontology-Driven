(function bootstrapOntoTwinHudBridge(global) {
  "use strict";

  const listeners = new Set();
  const actionListeners = new Set();
  let currentPayload = null;

  function notify(payload, meta) {
    currentPayload = payload;
    listeners.forEach((listener) => listener(payload, meta || {}));
  }

  function emitAction(action, payload) {
    const detail = {
      action,
      payload: payload || {},
      page: document.body.dataset.page || "unknown",
      timestamp: new Date().toISOString()
    };

    actionListeners.forEach((listener) => listener(detail));
    global.dispatchEvent(new CustomEvent("ontotwin:hud-action", { detail }));

    const host = global.ue && global.ue.ontotwinHud;
    if (host && typeof host.onAction === "function") {
      host.onAction(JSON.stringify(detail));
    }

    return detail;
  }

  function getInteractiveRegions() {
    return Array.from(document.querySelectorAll("[data-ue-interactive]"))
      .filter((element) => {
        const style = global.getComputedStyle(element);
        const rect = element.getBoundingClientRect();
        return style.visibility !== "hidden" && style.display !== "none" && rect.width > 0 && rect.height > 0;
      })
      .map((element) => {
        const rect = element.getBoundingClientRect();
        return {
          id: element.id || element.dataset.ueInteractive || element.getAttribute("aria-label") || "interactive",
          x: Math.round(rect.x),
          y: Math.round(rect.y),
          width: Math.round(rect.width),
          height: Math.round(rect.height)
        };
      });
  }

  global.OntoTwinHUD = Object.freeze({
    version: "0.1.0",
    setData(payload, meta) {
      notify(payload, meta);
    },
    patchData(patch, meta) {
      const next = Object.assign({}, currentPayload || {}, patch || {});
      notify(next, Object.assign({ patch: true }, meta || {}));
    },
    getData() {
      return currentPayload;
    },
    subscribe(listener) {
      listeners.add(listener);
      return function unsubscribe() {
        listeners.delete(listener);
      };
    },
    onAction(listener) {
      actionListeners.add(listener);
      return function unsubscribeAction() {
        actionListeners.delete(listener);
      };
    },
    emitAction,
    getInteractiveRegions
  });
})(window);
