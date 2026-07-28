# Web configuration

Keep the OntoTwin Web editor black, white, and gray. It configures the UE effect; it does not imitate liquid glass.

## Placement

Add a normal white “UE 展示效果” section near Display Rules in the information-panel editor. Use existing fields, segmented controls, inheritance indicators, explicit save, dirty/loading state, Toast, and modal patterns from `ontotwin-ui`.

Do not add blur, translucent chrome, colored glows, Apple-like toolbars, emoji, native alert/confirm, or native title tooltips to the Web page.

## Quality selection

| Stored value | Web label | Help |
| --- | --- | --- |
| `high` | 高质量 | 优先完整模糊、边缘高光和轻微折射；不支持时向下回退 |
| `balanced` | 均衡（推荐） | 保留主要玻璃层次并控制成本；不支持时转性能优先 |
| `performance` | 性能优先 | 使用静态或近静态可读表面，不自动升档 |

Show fallback order as persistent inline help. Do not promise requested quality equals runtime quality.

ObjectType stores the default. An instance may enable one grouped “覆盖 UE 展示效果” override. Restoring inheritance deletes the instance override instead of copying the type value. Effective configuration identifies `source: type|instance`. Batch override shows affected count and uses an OntoTwin modal.

## Metric style

Only metric templates show one panel-level style selector:

- 大数字 (`value`)
- 仪表 (`gauge`)
- 趋势图 (`trend`)

Progressively disclose:

| Style | Extra fields |
| --- | --- |
| value | none beyond current binding, precision, unit, and empty text |
| gauge | primary metric, minimum, maximum, and clamp-display toggle |
| trend | primary metric, numeric-series binding, time window, sampling/aggregation, optional axes |

Require maximum greater than minimum. Disable Trend with a persistent explanation when the source has no real history. A series binding may only reference a registered numeric time-series provider; current scalar `raw_state` cannot be treated as history. Do not synthesize history from a scalar value.

In the first release, the chosen primary metric owns the one Gauge or Trend; up to three remaining metrics render as compact Value. Allow four metrics total. Remove hidden conditional fields from submitted drafts. Keep status colors standardized; disallow arbitrary HEX input.

Each metric also exposes an independent “强调” checkbox. Missing or unchecked values render with the ordinary white Value style. Checked values may use the larger weight and the resolved status accent. Do not infer emphasis from array order.

For status templates, show all six standard levels in a compact mapping table. Each row edits the status display label and selects one approved lamp token from green, cyan, amber, red, or gray. Defaults are 在线/green, 信息/cyan, 注意/amber, 告警/red, 离线/gray, and 未知/gray. Keep the optional binding as a separate supplementary status description. Do not expose arbitrary HEX input.

## Preview

The right rail is a structural preview:

- show composition, density, empty/offline states, metric style, and approximate size;
- use the Web black/white/gray system;
- show “透明与模糊效果以 UE 运行端为准”;
- never claim browser CSS blur accurately previews UE exposure, occlusion, or DPI.

## Save behavior

- Keep editing after successful save.
- Show requested quality, inheritance source, and validation near the field.
- Quality or metric-style changes increment existing overlay configuration revision when implemented.
- Do not add a route.
- Do not change storage/API during a design-only task.
