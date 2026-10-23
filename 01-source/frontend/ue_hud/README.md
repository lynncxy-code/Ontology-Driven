# OntoTwin UE Screen Space Web HUD

This directory contains transparent, standalone Web pages intended for an Unreal Engine 5.6 Screen Space WebBrowser host.

## Independent pages

| Page | Purpose | Example URL |
| --- | --- | --- |
| `s3-building.html` | S3 building overview | `/ue_hud/pages/s3-building.html?space_id=SF.SB.M01` |
| `s4-zone.html` | S4 zone overview | `/ue_hud/pages/s4-zone.html?zone_id=SF.SB.M01.ZA` |
| `s5-workstation.html` | S5 workstation detail | `/ue_hud/pages/s5-workstation.html?instance_id=WS-M01-A01` |
| `event-workbench.html` | park-wide event workbench | `/ue_hud/pages/event-workbench.html?project_id=ueproj_test0316` |
| `event-detail.html` | single event detail | `/ue_hud/pages/event-detail.html?event_id=EVT-M01-012` |
| `energy-overview.html` | E1/E2 energy overview | `/ue_hud/pages/energy-overview.html?zone_id=SF.SB.M01` |
| `energy-device.html` | E3 energy device detail | `/ue_hud/pages/energy-device.html?instance_id=AHU-M01-02` |

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
- Real controls and panel surfaces use `data-ontotwin-interactive` and accept input; the bridge still reads legacy `data-ue-interactive` markers.
- `window.OntoTwinHUD.getInteractiveRegions()` returns the current interactive rectangles for future UE host hit-test routing.
- `window.OntoTwinBridge.post(type, payload)` implements Web Bridge 1.0 through `window.ue.ontotwinwebbridge.onmessage(...)`.

Visual alpha does not by itself make a full-screen WebBrowser pass pointer input through to the 3D scene. The UE host still needs to route input according to these interactive regions.

## Data lifecycle

- Browser preview loads `mock/building.json`.
- `preview_state=loading`, `preview_state=empty`, and `preview_state=error` expose the local state variants without painting a full-screen mask.
- A UE host may define `window.__ONTOTWIN_INITIAL_DATA__` before page startup.
- Live data may be pushed with `window.OntoTwinHUD.setData(payload, meta)`.
- Lightweight top-level updates may use `window.OntoTwinHUD.patchData(patch, meta)`.

No backend route, storage structure, or existing `I3D_Overlay` template is changed by this page package.
