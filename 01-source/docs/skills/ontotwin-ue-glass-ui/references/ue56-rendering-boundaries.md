# UE 5.6 rendering boundaries

## Decision matrix

| Technique | Real scene blur | Screen | World | Use |
| --- | --- | --- | --- | --- |
| Slate Postbuffer + UI material | yes | yes | no | High selected panel |
| `UBackgroundBlur` | yes in main Slate composition | yes | not behind a World `UWidgetComponent` | Balanced selected panel |
| translucent UI/material layers | no | yes | yes | pseudo-glass and fallback |
| Retainer Box | no scene capture | yes | yes | cache/effect child UI only |
| SceneCapture2D | technically yes | possible | possible | not permitted for normal/batched overlays |

## High Screen

Use one shared Slate Postbuffer:

1. Enable `Slate.CopyBackbufferToSlatePostRenderTargets=1` before Slate renderer initialization.
2. Require the host to reserve one `SlatePostRT_N`, N=0–4.
3. Apply one compatible shared Blur Processor.
4. Sample the matching `GetSlatePostN` in a User Interface material. Use an index-specific precompiled material variant. Never reserve RT1–RT4 while sampling `GetSlatePost0`.
5. Apply rounded mask, neutral tint, mild desaturation, edge-only refraction, inner highlight, and fine noise in the glass surface.
6. Draw all content in later Slate layers.

UE5.6 treats Slate Postbuffers as Experimental. Test DX12 Standalone and packaged Development/Shipping. Each enabled Postbuffer requires a full-frame copy in this version; do not import newer half-resolution guidance.

Slate Postbuffers are host-global and UE5.6 has no complete consumer-ownership registry. The plugin may verify that the chosen RT is enabled and its processor is compatible, but cannot discover every other material sampling the same RT. If reservation is ambiguous, initialization is late, the processor conflicts, or the material is missing, downgrade to Balanced. Never overwrite host use silently.

The verified default path is RT0. Treat RT1–RT4 as requiring explicit cold-start and packaged validation before promising support in a new host.

## Balanced Screen

Use `UBackgroundBlur` with a rounded fallback surface, then separate tint, rim, highlight, noise, and status layers. Configure a low-quality fallback brush but do not treat it as general capability detection. If Blur or required assets are unavailable, use Performance rather than rendering an empty transparent panel.

## Performance

Use a static translucent-to-near-opaque neutral surface, one rim, and sharp content. Disable scene sampling, refraction, chromatic split, animated noise, and Bloom dependency. Keep this final fallback fully usable.

## World Space

A World `UWidgetComponent` renders UI into its own RenderTarget before placing it in the 3D scene. A normal Background Blur inside that widget cannot see the factory scene behind it.

Use deterministic pseudo-glass:

- translucent neutral surface;
- top/inner static highlight;
- subtle shared static grain;
- restrained status lamp/accent;
- depth test, distance culling, and model anchoring.

The current World panel billboards toward the camera, so a true view-angle Fresnel would not produce meaningful variation. Do not fake it. High World may increase RenderTarget density and surface detail but must not claim real background blur.

Never create one SceneCapture or scene buffer per always panel. A future exceptional hero panel requires a separate GPU-budget decision outside this standard system.

## Retainer and composition

Retainer Box captures child UI, not the 3D scene. Use it only for demonstrated child caching/effects. Watch premultiplied alpha, gamma, text softness, invalidation, and cadence. Never put sharp content inside a refractive Retainer effect.

## Input and hit testing

- Mark glass, blur, rim, noise, glow, chart fill, anchor, and connector `Self Hit Test Invisible`.
- Keep ordinary text panels non-focusable.
- Let only media buttons and explicit controls intercept input.
- Preserve near-view E selection and god-view pointer selection.
- Restore input mode, cursor state, and roaming controls on close, Esc, or target switch.
- Prevent media-control clicks from propagating into scene-clear selection.

## Implementation boundary

Keep the scene manager and resolved-data lifecycle. Separate:

- normalized Overlay ViewModel;
- Screen and World renderer profiles;
- shared Glass Theme/Profile;
- reusable Title, Body, Status, Metric, Chart, Media, and Control components;
- six composition recipes.

Do not create six copied widget trees. Do not replace the current dynamic C++ Widget with a designer WBP before exposing a stable data/update interface.

## Cook and build

- Keep plugin fonts, materials, textures, and theme assets reachable from the Cook reference graph.
- In UE5.6 hosts whose PrimaryAssetLabel scan only covers `/Game`, a plugin Label alone may not collect `/OntoTwinSync/UI`.
- The verified fallback is a plugin-class hard reference to `M_OT_GlassHigh_RT0...RT4`; do not require every host to add `DirectoriesToAlwaysCook` for OntoTwin.
- Validate plugin fonts and all five High materials in the final Cooked Asset Registry/container.
- Check SDR/HDR, exposure, Bloom, TAA/TSR, enabled upscalers, window resize, rounded-edge leaks, World blend/depth, and manual redraw.
- Log requested/effective quality and fallback reason once, not every frame.

Official references:

- https://dev.epicgames.com/documentation/unreal-engine/using-slate-postbuffers-in-unreal-engine?application_version=5.6
- https://dev.epicgames.com/documentation/unreal-engine/using-the-background-blur-widget-in-unreal-engine
- https://dev.epicgames.com/documentation/en-us/unreal-engine/widget-components-in-unreal-engine?application_version=5.6
- https://dev.epicgames.com/documentation/unreal-engine/API/Runtime/UMG/URetainerBox?application_version=5.6

