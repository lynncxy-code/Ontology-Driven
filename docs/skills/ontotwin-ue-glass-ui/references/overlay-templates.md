# Overlay templates

## Composition model

Keep all six template IDs visible to users. Build each one as a recipe of shared components, not as an unrelated copied Widget.

| Template ID | User label | Shared components |
| --- | --- | --- |
| `title_body` | 标题 + 正文 | GlassSurface, Title, Body |
| `title_subtitle_body` | 标题 + 小标题 + 正文 | GlassSurface, Title, Subtitle, Body |
| `title_metrics` | 标题 + 指标 | GlassSurface, Title, MetricRegion |
| `title_status_metrics` | 标题 + 状态 + 指标 | GlassSurface, Title, Status, MetricRegion |
| `title_video` | 标题 + 视频 | GlassSurface, Title, MediaWell, MediaControls |
| `title_video_body` | 标题 + 视频 + 正文 | GlassSurface, Title, MediaWell, Body, MediaControls |

Do not reduce template selection to one universal layout with hidden rows. Each recipe owns its density, order, spacing, and aspect.

## Shared layer tree

```text
Overlay root
├─ Screen scene sample or World pseudo-glass surface
├─ Tint, rim, inner highlight, and fine noise
├─ Status lamp and model connector
├─ Sharp content
│  ├─ title / subtitle / body
│  ├─ status / value / gauge / chart
│  └─ video texture
└─ Real controls and hit targets
```

Set glass and decoration layers to `Self Hit Test Invisible`. Let only real controls accept input.

## Size families

Use logical pixels before DPI scaling.

| Family | Templates | Recommended width | Constraints |
| --- | --- | --- | --- |
| compact capsule | one-primary-metric forms | 320–440 | preserve a capsule silhouette; avoid paragraph text |
| information card | text and multi-value forms | 340–480 | collapse an empty body; bound lines and height |
| media card | video forms | 360 minimum, 480 recommended, up to 720 expanded | keep video 16:9 and respect safe areas |

Keep Screen panels within about 42% of viewport width and 70% of viewport height. Simplify World detail, body lines, axes, and controls.

## Text rules

- Title: one or two lines, then ellipsis.
- Subtitle: one or two lines; remove the row and spacing when empty.
- Body: bounded wrap when compact; controlled internal scrolling only in expanded Screen cards.
- Required empty content: display configured empty text.
- Optional empty content: remove the row and its spacing.
- Template changes: clear stale body, status, metric, poster, media, and control state.

## Metric styles

Choose one panel-level style. Gauge or Trend requires an explicit `primary_metric_id`. The primary metric owns the visualization; up to three remaining metrics stay as compact Value summaries.

Each metric also owns `emphasized: true|false`. Default to `false`. Do not use array order to choose emphasis.

### Value

- Support one to four values.
- Use a large primary style only for an explicitly emphasized metric.
- Use deterministic 2×2 or primary-plus-secondary layouts.
- Keep backend-formatted `display_value` authoritative.

### Gauge

- Use at most one primary numeric metric per panel.
- Select the primary metric from stable current metric IDs.
- Derive arc/ring geometry from raw numeric value and range, never display text.
- Clamp geometry only when configured; keep the displayed value truthful.
- Use status accent only on the active arc, icon, or explicit key value.
- Fall back to Value with an explicit no-data/offline treatment when drawing data is invalid.

### Trend

- Keep Trend visible but disabled until a registered real history provider exists.
- After enablement, use at most one primary time series per panel initially.
- Keep remaining metrics as compact current values.
- Let selected Screen show an area chart, current value, optional axes, and time range.
- Let always World show only a simplified sparkline or fall back to Value.
- Show “暂无趋势数据” for empty history; never synthesize a series from a scalar.
- Keep line and fill sharp above the glass layer.

## Video recipes

- Keep video pixels sharp in a separately clipped 16:9 MediaWell.
- Apply glass to the shell, title, and controls, not the video texture.
- Let World show a poster/placeholder only and create no player.
- Reuse the existing media resolve, retry, sharing, and release lifecycle from the video PRD.
- Expanding/collapsing changes layout without rebuilding the media session.
- For `title_video_body`, cap collapsed body at three lines. In expanded Screen, keep video above a body region capped at 160 logical px with internal scrolling. In World, use at most two lines and no scroll.

## Smart Screen anchoring

1. Project the resolved model-top anchor into DPI-aware logical viewport coordinates.
2. Prefer a nearby quadrant with 16–32 logical px between anchor and card.
3. Draw a short, low-contrast connector and anchor point when separation is material.
4. Re-evaluate the quadrant only after crossing a dead zone.
5. Keep at least 24 logical px from safe-area edges.
6. Hide if projection fails or the target is behind the camera; do not pin to an arbitrary edge.
7. Fade after a short grace period when the target leaves the viewport or remains occluded.
8. Preserve selected-instance identity when a media card expands away from the anchor.

Apply viewport/DPI scale exactly once. Keep `selected` and `always` mutually exclusive. Clicking an always World panel must not create a second Screen copy.

