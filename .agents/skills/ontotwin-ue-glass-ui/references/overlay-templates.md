# Overlay templates

## Composition model

Keep the six current template IDs visible to users. Implement them as recipes of shared components instead of six unrelated Widgets.

| Template ID | User label | Shared components |
| --- | --- | --- |
| `title_body` | 标题 + 正文 | GlassSurface, Title, Body |
| `title_subtitle_body` | 标题 + 小标题 + 正文 | GlassSurface, Title, Subtitle, Body |
| `title_metrics` | 标题 + 指标 | GlassSurface, Title, MetricRegion |
| `title_status_metrics` | 标题 + 状态 + 指标 | GlassSurface, Title, Status, MetricRegion |
| `title_video` | 标题 + 视频 | GlassSurface, Title, MediaWell, MediaControls |
| `title_video_body` | 标题 + 视频 + 正文 | GlassSurface, Title, MediaWell, Body, MediaControls |

Do not let template selection collapse into one universal layout with hidden empty rows. Each recipe defines its own density, order, spacing, and aspect.

## Common layer tree

```text
Overlay root
├─ Glass surface / scene sample
├─ Tint, rim, inner highlight and fine noise
├─ Status accent and model connector
├─ Sharp content
│  ├─ title / subtitle / body
│  ├─ status / value / gauge / chart
│  └─ video texture
└─ Real controls and hit targets
```

Glass and decoration layers are Self Hit Test Invisible. Only real controls accept pointer or keyboard input.

## Size families

Use logical pixels before DPI scaling.

| Family | Templates | Recommended width | Constraints |
| --- | --- | --- | --- |
| compact capsule | one-primary-metric forms | 320–440 | preserve pill silhouette; avoid paragraph text |
| information card | text and multi-value forms | 340–480 | body collapses when empty; cap height and lines |
| media card | video forms | 360 minimum, 480 recommended, up to 720 expanded | keep video 16:9; respect viewport safe area |

Constrain Screen panels to approximately 42% of viewport width and 70% of viewport height. For World Space, preserve hierarchy but simplify detail, body lines, axes, and controls.

## Text recipes

- Title: one or two lines, then ellipsis.
- Subtitle: one or two lines; remove row and spacing when empty.
- Body: bounded wrap in compact mode; controlled scroll only in an expanded Screen card.
- Empty required content uses configured empty text. Optional empty slots disappear with their spacing.

## Metric styles

The user keeps the same information template and selects one panel-level metric style inside it. Gauge or Trend requires an explicit `primary_metric_id`. The primary metric owns the visualization; up to three remaining metrics stay as compact Value summaries.

### Value

- Support one to four values.
- Use a large primary value for one metric.
- Use a deterministic 2×2 or primary-plus-secondary layout for multiple metrics.
- Keep formatted display text authoritative.

### Gauge

- Use one primary numeric metric.
- Select it explicitly from the current stable metric IDs.
- Render a restrained arc/ring, current value, unit, and range context.
- Derive geometry from raw numeric value and range, never from display text.
- Use status accent only on the active arc, icon, or key value.

### Trend

- Use one primary time series per panel in the first release.
- Select one primary scalar metric plus its real history binding; keep the remaining metrics as compact current values.
- Screen selected may show an area chart, current value, optional axes, and time range.
- World always uses only a simplified sparkline or falls back to Value.
- Empty history displays “暂无趋势数据”; never draw a fake series.
- Keep line and fill sharp above the glass layer.

## Video recipes

- Keep video pixels sharp in a separately clipped 16:9 MediaWell.
- Apply glass to the shell, title, and controls, not to the video texture.
- World always displays a poster/placeholder only and creates no player.
- Screen selected may resolve and play the URL using the existing media lifecycle.
- Expanding/collapsing changes layout without rebuilding the media session.
- For title_video_body, collapsed body is at most three lines. Expanded Screen keeps video above a body region capped at 160 logical px with internal scrolling. World uses at most two lines and no scroll.

## Smart Screen anchoring

1. Project the resolved model-top anchor into DPI-aware logical viewport coordinates.
2. Prefer a nearby quadrant with 16–32 logical px between anchor and card.
3. Draw a short, low-contrast connector and anchor point when separation is material.
4. Re-evaluate quadrant only after crossing a dead zone to prevent jitter.
5. Keep at least 24 logical px from safe-area edges.
6. If projection fails or the target is behind the camera, hide instead of pinning to an arbitrary edge.
7. If the target leaves the viewport or stays occluded, fade out after a short grace period.
8. Preserve selected-instance identity when a video card expands away from the anchor.

Selected and always remain mutually exclusive. An always panel remains the final World presentation when clicked and must not create a second Screen copy.
