# Visual language

## Purpose

Translate the spatial, adaptive, layered qualities of visionOS glass into an OntoTwin industrial overlay. Do not reproduce Apple components pixel-for-pixel. The result must remain an OntoTwin system with industrial status semantics.

## Design principles

1. Keep the glass base neutral. Apply semantic color only to the rim, icon, gauge, key value, or a restrained local glow.
2. Let the environment remain recognizable through the surface while keeping content sharp.
3. Use depth at the panel surface and controls, not on body text.
4. Prefer rounded continuous silhouettes, generous internal space, and few separators.
5. Stop optical movement after an event completes.
6. Preserve meaning without color through labels, icons, and shape.

## Baseline tokens

These are tuning ranges, not user-editable fields.

| Role | Baseline |
| --- | --- |
| Screen glass tint | neutral blue-black, 28–44% apparent opacity after blur |
| Balanced glass tint | neutral blue-black, 44–58% |
| Performance surface | neutral blue-black, 72–88% |
| Primary text | near white, 92–100% |
| Secondary text | white, 66–76% |
| Disabled/offline text | white, 42–55% |
| Outer rim | 1 logical px, 18–34% white |
| Inner highlight | 1 logical px, 10–24% white; strongest at top/upper-left |
| Capsule radius | half-height or 28–36 logical px |
| Card radius | 20–24 logical px |
| Refraction displacement | edge-only, visually no more than about 1–2 logical px |
| Chromatic split | edge-only and below 0.5 logical px at 1080p |
| Noise | fine, low contrast, below 3% opacity |

Do not expose blur radius, refraction, tint alpha, noise, or chromatic split as project fields in the first release. Quality profiles own those values.

## Status semantics

| State | Accent role | Non-color cue |
| --- | --- | --- |
| normal | restrained green | check/steady marker and “正常” |
| info | cool cyan-blue | information marker and label |
| warning | amber-orange | warning marker and label |
| critical | warm red | critical marker and label |
| offline | desaturated gray | broken connection marker and “离线” |
| unknown | neutral gray | question marker and “未知” |

Do not fill the entire glass surface with the status color. OntoTwin may remap each standard state to one of the approved semantic color tokens (`green`, `cyan`, `amber`, `red`, or `gray`) and configure its display label in Web; arbitrary HEX values are not allowed. A transition pulses the status lamp once, then settles.

## Typography

- Package explicit font assets; do not depend on editor-only CoreStyle fonts.
- Use an explicitly cooked Composite Font: Inter for Latin/tabular numbers and Noto Sans SC for Chinese fallback. Preserve their license files with the plugin assets.
- Use tabular numerals for live metrics.
- Reserve medium/semibold for titles, primary values, and buttons.
- Maintain at least 4.5:1 contrast for normal text and 3:1 for large text and essential graphics.
- Do not add glow or extrusion to paragraphs.
- Use OntoTwin-owned monochrome SDF/SVG status icons. Do not use Apple SF Symbols.

## Adaptive luminance

High Screen may use a stateless local-luminance curve from the Slate Postbuffer to adjust surface tint, rim, and text scrim. A normal UI Material has no previous-frame state. Do not add a history render target or GPU→CPU readback merely to smooth glass.

`UBackgroundBlur` does not expose a supported local-luminance result, so Balanced uses a conservative tested scrim unless a Renderer Spike proves a stable global-exposure parameter. Only that optional global parameter may use roughly 150–300 ms smoothing and a dead zone. In all paths, increase scrim on bright/high-frequency backgrounds and prefer readability when confidence is low.

Performance and World Space use a fixed, conservative dark neutral surface.

## Motion

| Event | Motion |
| --- | --- |
| Open | 180–240 ms opacity plus 0.97→1.0 scale and short highlight travel |
| Close | 120–180 ms opacity/scale |
| Hover/focus | 120–160 ms rim and local luminance shift |
| State change | one soft pulse, total under 900 ms |
| Anchor follow | critically damped smoothing; avoid visible lag |
| Idle | no continuous refraction, breathing, or traveling shine |

Honor reduced-motion mode by replacing scale and highlight travel with a short fade.

Provide plugin Project Settings or development CVars for acceptance rather than per-panel fields:

- ReduceMotion: remove scale, highlight travel, and status pulse; Performance implies this behavior.
- ReduceTransparency: force the Performance surface.
- HighContrast: strengthen scrim/rim contrast without changing business-state semantics.

## Prohibited results

- Full-panel green, orange, or red neon fills.
- Strong blur over text or video.
- Continuous liquid wobble or rainbow edge separation.
- Transparent surfaces with unreadable text over white factory floors or lamps.
- Decorative hit regions that consume E, mouse, or scene-selection input.
- Apple logos, screenshots, copied Figma assets, or claims that the UI is an Apple component.
