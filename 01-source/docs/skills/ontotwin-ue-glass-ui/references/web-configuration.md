# Web configuration

Keep the OntoTwin Web editor black, white, and gray. It configures UE behavior; it does not imitate liquid glass.

## Placement

Use the existing `/interaction` information-panel editor. Add no route. Place a normal white “展示效果” section near Display Rules and reuse existing segmented controls, inheritance indicators, explicit save, dirty/loading state, Toast, and modal patterns from `ontotwin-ui`.

Do not add blur, translucent browser chrome, colored glow, Apple-like toolbars, emoji, native `alert/confirm`, or native title tooltips.

## Quality selection

| Stored value | Web label | Persistent help |
| --- | --- | --- |
| `high` | 高质量 | 请求完整模糊与细节；不支持时向下回退 |
| `balanced` | 均衡（推荐） | 保留主要玻璃层次并控制成本；不支持时转性能优先 |
| `performance` | 性能优先 | 使用静态或近静态可读表面，不自动升档 |

Treat these as requested quality. Never promise requested equals effective.

ObjectType stores the default. An Instance may enable one grouped “覆盖展示效果” override. Restoring inheritance deletes the instance override instead of copying the type value. Batch override shows affected count and uses an OntoTwin modal.

## Metric style

Only metric templates show one panel-level selector:

- 大数字 (`value`)
- 仪表 (`gauge`)
- 趋势图 (`trend`)

Progressively disclose:

| Style | Extra fields |
| --- | --- |
| value | none beyond current binding/format |
| gauge | primary metric, minimum, maximum, clamp-display toggle |
| trend | primary metric, real history binding, time window, sampling/aggregation, optional axes |

Require `max > min`. Keep Trend disabled with persistent explanation while no real history provider exists. Do not turn scalar `raw_state` into fake history. Remove hidden conditional fields from submitted drafts.

Each metric exposes an independent “强调” checkbox. Missing or unchecked means ordinary white Value style. Checked values may use the larger weight and resolved status accent. Do not infer emphasis from metric order.

## Status mapping

For status templates, show all six standard levels in a compact mapping table. Each row edits the display label and selects one approved token: `green | cyan | amber | red | gray`.

Defaults:

| Level | Label | Token |
| --- | --- | --- |
| normal | 在线 | green |
| info | 信息 | cyan |
| warning | 注意 | amber |
| critical | 告警 | red |
| offline | 离线 | gray |
| unknown | 未知 | gray |

Keep any bound supplementary status description separate. Do not expose arbitrary HEX. Do not offer a persistent full-height status color edge.

## Preview

Keep the right rail structural:

- show composition, density, empty/offline state, status mapping, explicit metric emphasis, metric style, and approximate size;
- use Web black/white/gray styling;
- display “透明、模糊、曝光和遮挡效果以 UE 运行端为准”;
- never claim CSS blur previews UE exposure, occlusion, DPI, or Postbuffer behavior.

## Save behavior

- Keep editing after a successful save.
- Show requested quality, inheritance source, and validation near the field.
- Increment the existing Overlay configuration revision for quality, emphasis, status appearance, or metric-style changes.
- Restore inheritance by removing the instance difference.
- Keep save explicit and reversible.

