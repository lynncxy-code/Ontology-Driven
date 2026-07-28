# OntoTwin UE Screen Space Web HUD

This directory contains transparent, standalone Web pages intended for an Unreal Engine 5.6 Screen Space WebBrowser host.

## First implemented page

- `pages/s3-building.html?space_id=SF.SB.M01`

The Flask app serves `frontend/` at the site root, so the page is available at:

```text
http://localhost:5000/ue_hud/pages/s3-building.html?space_id=SF.SB.M01
```

## Rendering boundary

- `html`, `body`, `#root`, `#app`, and the central scene observation area are transparent.
- Only elements with `.hud-surface` paint a local translucent surface.
- CSS `backdrop-filter` is intentionally not used. Unreal Engine owns any real scene blur.
- The page does not render close, refresh, back, or security controls. The OntoTwin host owns them.

## Input boundary

- The page root is `pointer-events: none`.
- Real controls and panel surfaces use `data-ue-interactive` and accept input.
- `window.OntoTwinHUD.getInteractiveRegions()` returns the current interactive rectangles for future UE host hit-test routing.
- `window.OntoTwinHUD.emitAction(action, payload)` emits `ontotwin:hud-action` and calls a bound `window.ue.ontotwinHud.onAction(...)` object when available.

Visual alpha does not by itself make a full-screen WebBrowser pass pointer input through to the 3D scene. The UE host still needs to route input according to these interactive regions.

## Data lifecycle

- Browser preview loads `mock/building.json`.
- `preview_state=loading`, `preview_state=empty`, and `preview_state=error` expose the local state variants without painting a full-screen mask.
- A UE host may define `window.__ONTOTWIN_INITIAL_DATA__` before page startup.
- Live data may be pushed with `window.OntoTwinHUD.setData(payload, meta)`.
- Lightweight top-level updates may use `window.OntoTwinHUD.patchData(patch, meta)`.

No backend route, storage structure, or existing `I3D_Overlay` template is changed by this page package.
