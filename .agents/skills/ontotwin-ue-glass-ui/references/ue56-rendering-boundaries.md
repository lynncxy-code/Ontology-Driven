# UE 5.6 rendering boundaries

## Decision matrix

| Technique | Real scene blur | Screen | World | Use |
| --- | --- | --- | --- | --- |
| Slate Postbuffer + UI material | yes | yes | no | High selected panel |
| UBackgroundBlur | yes in main Slate composition | yes | not behind a World WidgetComponent | Balanced selected panel |
| translucent UI/material layers | no | yes | yes | pseudo-glass and fallback |
| Retainer Box | no scene capture | yes | yes | cache/effect child UI only |
| SceneCapture2D | technically yes | possible | possible | exceptional single hero panel only |

## High Screen path

Use one shared Slate postbuffer:

1. Enable `Slate.CopyBackbufferToSlatePostRenderTargets=1` early enough for the target build.
2. Use one host-reserved `SlatePostRT_N`; the current host may reserve N=0, while other hosts choose N=0–4 explicitly.
3. Apply one shared blur processor such as `USlatePostBufferBlur`.
4. Sample the matching `GetSlatePostN` in a User Interface material. Use an index-specific precompiled material variant, or a compile-time static branch only after the Renderer Spike proves it reliable. Never reserve RT1–RT4 while still sampling `GetSlatePost0`; one runtime profile still enables, copies, and samples only one postbuffer.
5. Apply rounded mask, neutral tint, mild desaturation, edge-only refraction, inner highlight, and fine noise in the glass surface.
6. Draw all content in later Slate layers.

UE 5.6 treats this path as Experimental. Test DX12 Standalone and packaged Development/Shipping. Each enabled postbuffer requires a full-frame copy in this version; do not copy newer UE guidance about half-resolution postbuffers into a 5.6 implementation.

Slate Postbuffers are host-global resources, and UE 5.6 has no complete consumer-ownership registry. Require the host to declare a reserved RT0–RT4 index in plugin Project Settings. The plugin may verify that the chosen RT is enabled and that the configured processor is compatible, but it cannot discover every other UI Material sampling that texture. RT1–RT4 must be enabled in project/renderer configuration before Slate renderer initialization; confirm the exact UE 5.6 setting during the Renderer Spike. If reservation is ambiguous, initialization is late, or the processor is incompatible, downgrade to Balanced. Never silently overwrite host usage.

## Balanced Screen path

Use `UBackgroundBlur` with a rounded mask/fallback surface, then add separate tint, rim, highlight, and status layers. Configure a low-quality fallback brush, but do not mistake that brush for general capability detection. An explicit quality resolver checks renderer/backend support and required assets; if blur or material is missing, fall through to Performance rather than rendering an empty transparent panel.

## Performance path

Use a static translucent-to-near-opaque neutral gradient, one rim, and sharp content. Disable background sampling, refraction, chromatic split, animated noise, and Bloom dependency. This is the final safety net and must remain fully usable.

## World Space path

A World `UWidgetComponent` renders UI into a separate render target before placing it in the 3D scene. A normal Background Blur inside that widget cannot see the factory scene behind it.

Use pseudo-glass:

- translucent neutral surface;
- controlled Fresnel/view-angle highlight;
- subtle static grain;
- restrained semantic rim;
- depth test, distance culling, and model anchoring.

High World may add better highlights and higher render-target density, but must not claim real background blur. Balanced World is the normal default. Performance World is almost opaque and static.

Never create a SceneCapture or unique scene render target for every always panel. A future exceptional hero panel requires a separate GPU-budget decision.

## Retainer and composition

Retainer Box captures child UI, not the 3D scene. Use it only for demonstrated child caching/effects. Watch premultiplied alpha, gamma, text softness, invalidation, and cadence. Never place sharp text inside a refractive Retainer effect.

## Input and hit testing

- Make glass, blur, rim, noise, glow, chart-fill decoration, anchor, and connector Self Hit Test Invisible.
- Keep ordinary text panels non-focusable.
- Let only media buttons and explicit controls intercept input.
- Preserve near-view E selection and god-view pointer selection.
- Restore the prior input mode, cursor state, and roaming controls on close, Esc, or target switch.
- Prevent media-control clicks from propagating into scene-clear selection.

## Recommended implementation boundary

Keep the scene manager and resolved-data lifecycle. Separate:

- a normalized overlay view model;
- Screen and World renderer profiles;
- a shared glass theme/profile;
- reusable title, body, status, metric, chart, media, and control components;
- six composition recipes.

Do not make six copied widget trees. Do not expect a designer WBP to replace the current dynamic C++ widget without first exposing a stable data/update interface.

## Build risks

- Explicitly cook plugin fonts, materials, textures, and theme assets.
- Validate SDR/HDR, automatic exposure, Bloom, TSR/TAA, enabled upscalers, and window resize.
- Check rounded blur edges for rectangular leaks/black fringes.
- Check UWidgetComponent blend, depth, two-sided behavior, and manual redraw.
- Continuous World animation may not update under manual redraw; this design avoids idle animation.
- Log requested/effective quality and fallback reason once, not every frame.

Official references:

- https://dev.epicgames.com/documentation/unreal-engine/using-slate-postbuffers-in-unreal-engine?application_version=5.6
- https://dev.epicgames.com/documentation/unreal-engine/using-the-background-blur-widget-in-unreal-engine?application_version=5.6
- https://dev.epicgames.com/documentation/en-us/unreal-engine/widget-components-in-unreal-engine?application_version=5.6
- https://dev.epicgames.com/documentation/unreal-engine/API/Runtime/UMG/URetainerBox?application_version=5.6
