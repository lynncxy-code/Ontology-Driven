# Visual language

## Purpose

Translate the spatial, adaptive, layered qualities of visionOS glass into an OntoTwin industrial overlay. Do not reproduce Apple components pixel-for-pixel. Preserve OntoTwin industrial status semantics.

## Principles

1. Keep the glass base neutral. Apply semantic color only to a status lamp, icon, Gauge/Trend body, explicit key value, or restrained local glow.
2. Keep the environment recognizable through Screen glass while drawing content sharply above the optical layer.
3. Use depth on the surface and controls, not on body text.
4. Prefer continuous rounded silhouettes, generous internal space, and few separators.
5. Stop optical movement after an event finishes.
6. Preserve meaning without color through labels, icons, and shape.
7. Treat World Space as deterministic pseudo-glass, never as sampled scene blur.

## Baseline tokens

Treat these values as tuning ranges owned by quality profiles, not user-editable project fields.

| Role | Baseline |
| --- | --- |
| High Screen tint | neutral blue-black, 28–44% apparent opacity after blur |
| Balanced Screen tint | neutral blue-black, 44–58% |
| Performance surface | neutral blue-black, 72–88% |
| Primary text | near white, 92–100% |
| Secondary text | white, 66–76% |
| Disabled/offline text | white, 42–55% |
| Outer rim | 1 logical px, 18–34% white |
| Inner highlight | 1 logical px, 10–24% white; strongest at top/upper-left |
| Capsule radius | half-height or 28–36 logical px |
| Card radius | 20–24 logical px |
| Refraction displacement | edge-only, visually at most 1–2 logical px |
| Chromatic split | edge-only and below 0.5 logical px at 1080p |
| Noise | fine, low contrast, below 3% opacity |

Do not expose blur radius, refraction, tint alpha, noise, chromatic split, or font as first-release project fields.

## Status semantics

| State | Default token | Non-color cue |
| --- | --- | --- |
| normal | green | steady/check marker and “在线” |
| info | cyan | information marker and “信息” |
| warning | amber | warning marker and “注意” |
| critical | red | critical marker and “告警” |
| offline | gray | broken-connection marker and “离线” |
| unknown | gray | question marker and “未知” |

Allow Web to edit the display label and select only `green | cyan | amber | red | gray`. Never accept arbitrary project HEX colors. Do not fill the entire glass surface with a status color. Pulse the status lamp once on transition, then settle.

Each metric owns an explicit `emphasized` boolean. Missing means `false`. Do not infer emphasis from array order. Only emphasized metrics may use the larger weight and resolved status accent.

## Typography and icons

- Package explicit font assets; do not depend on editor-only CoreStyle fonts.
- Use an explicitly cooked Composite Font: Inter for Latin/tabular numbers and Noto Sans CJK SC for Chinese fallback.
- Preserve both font licenses with plugin resources.
- Use tabular numerals for live metrics.
- Reserve medium/semibold for titles, explicit primary values, and buttons.
- Maintain at least 4.5:1 contrast for normal text and 3:1 for large text and essential graphics.
- Do not add glow or extrusion to paragraph text.
- Use OntoTwin-owned monochrome icons. Do not use Apple SF Symbols.

## Adaptive luminance

High Screen may use a stateless local-luminance curve from the Slate Postbuffer to adjust surface tint, rim, and text scrim. A normal UI Material has no previous-frame state. Do not add a history render target or GPU-to-CPU readback merely to smooth glass.

`UBackgroundBlur` does not expose a supported local-luminance result. Use a conservative, tested scrim for Balanced unless a Renderer Spike proves a stable global-exposure parameter. Only that optional global parameter may use roughly 150–300 ms smoothing and a dead zone.

Use a fixed, conservative dark neutral surface for Performance and World. Prefer readability whenever capability or luminance confidence is low.

## Motion

| Event | Motion |
| --- | --- |
| Open | 180–240 ms opacity plus 0.97→1.0 scale and short highlight travel |
| Close | 120–180 ms opacity/scale |
| Hover/focus | 120–160 ms rim and local highlight shift |
| State change | one soft pulse under 900 ms |
| Anchor follow | damped smoothing without visible lag |
| Idle | no continuous refraction, breathing, or traveling shine |

Honor reduced-motion mode by replacing scale and highlight travel with a short fade.

Expose acceptance settings through plugin Project Settings or development CVars, not per-panel fields:

- ReduceMotion: remove scale, highlight travel, and status pulse; Performance implies this behavior.
- ReduceTransparency: force the Performance surface without changing the saved request.
- HighContrast: strengthen scrim/rim contrast without changing business status semantics.

## Prohibited results

- Full-panel green, orange, or red neon fills.
- Strong blur over text, charts, controls, or video.
- Continuous liquid wobble, rainbow edge separation, or idle refraction.
- Unreadable transparent surfaces over white floors, lamps, or high-frequency backgrounds.
- Decorative hit regions that consume E, mouse, keyboard focus, or scene-selection input.
- Apple logos, screenshots, copied Figma assets, or claims that the UI is an Apple component.

