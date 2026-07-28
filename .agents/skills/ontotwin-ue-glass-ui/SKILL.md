---
name: ontotwin-ue-glass-ui
description: Design, review, implement, and validate visionOS-inspired liquid-glass information overlays for OntoTwin UE5.6 with UMG, Slate, WidgetComponent, and UI materials. Use for UE instance popups, status capsules, metric or trend cards, video overlays, Screen/World renderer choices, glass quality tiers, overlay anchoring and input, visual refactors, or packaged-build UI acceptance.
---

# OntoTwin UE Liquid Glass UI

Create a coherent OntoTwin information-overlay system that feels transparent and spatial while remaining readable, performant, and compatible with the existing I3D_Overlay contract.

## Required workflow

1. Determine the task phase: discussion/PRD, visual specification, implementation, or acceptance.
2. Inspect the current UE version, Widget space, overlay lifecycle, data contract, and input path before proposing changes.
3. Preserve the existing six user-facing templates. Compose them from shared glass, typography, status, metric, media, and control components.
4. Choose the Screen or World rendering path from the table below. Never promise real scene blur in World Space.
5. Keep glass decoration separate from sharp content. Place text, icons, charts, video, and controls above blur/refraction layers.
6. Keep business state and display formatting in the existing backend contract. Do not infer alarm thresholds or parse numbers from formatted strings in UE.
7. Validate DPI, background luminance, fallback quality, input restoration, performance, and packaged builds.

If the request is design-only, do not edit C++, WBP, materials, `.uasset` files, frontend code, routes, or storage. If implementation is requested, make the smallest change consistent with the approved PRD and verify the UE editor is closed before modifying generated or locked UE assets.

## Renderer selection

| Context | High | Balanced | Performance |
| --- | --- | --- | --- |
| selected / Screen Space | Shared Slate Postbuffer, blur processor, UI glass material | UBackgroundBlur plus tint/rim material | Static translucent or near-opaque surface |
| always / World Space | Enhanced pseudo-glass material; no scene sampling | Standard pseudo-glass | Static readable surface |

Treat High, Balanced, and Performance as requested quality. Allow runtime downgrade only: High → Balanced → Performance; Balanced → Performance; Performance stays fixed.

## Non-negotiable constraints

- Reserve at most one Slate Postbuffer for OntoTwin overlays and share it.
- Never create one SceneCapture or one full-screen buffer per panel.
- Never use Retainer Box as a source of the 3D scene behind a widget.
- Never refract or blur text, icons, charts, video pixels, or click targets.
- Set decorative glass, rim, noise, connector, and glow layers to `Self Hit Test Invisible`.
- Let only actual buttons and media controls intercept input.
- Keep `selected` and `always` mutually exclusive for one resolved instance.
- Keep one selected Screen widget and one shared media session at most.
- Do not introduce continuous liquid motion at idle. Use short event-driven motion.
- Do not copy Apple logos, proprietary assets, or unlicensed SF fonts. Describe the result as visionOS-inspired.
- Do not bring the UE glass visual language into the OntoTwin Web editor. For Web changes, also apply `ontotwin-ui`.

## Reference routing

- Read [visual-language.md](references/visual-language.md) for color, typography, glass layers, motion, and accessibility.
- Read [overlay-templates.md](references/overlay-templates.md) when designing any of the six templates, metric styles, sizing, or smart anchoring.
- Read [ue56-rendering-boundaries.md](references/ue56-rendering-boundaries.md) before choosing a blur, material, WidgetComponent, Retainer, or SceneCapture solution.
- Read [web-configuration.md](references/web-configuration.md) for the OntoTwin information-panel editor, inheritance, quality selection, and conditional metric fields.
- Read [data-contract.md](references/data-contract.md) before proposing gauge or trend rendering or changing runtime payloads.
- Read [qa-checklist.md](references/qa-checklist.md) for implementation review and acceptance.

## Output expectations

For a design or PRD task:

- State the Screen/World distinction and quality fallback.
- Map all affected user-facing templates to shared components.
- Separate current facts, approved decisions, proposed contract additions, and later enhancements.
- Include limitations, failure behavior, accessibility, performance budgets, and acceptance.

For an implementation task:

- Preserve the manager, selection, inheritance, revision, and media lifecycles unless the user explicitly changes them.
- Prefer a shared theme/profile and renderer separation over six duplicated Widgets.
- Make missing materials, fonts, or postbuffer support fall back to a readable panel rather than transparency or checkerboards.
- Validate in PIE for iteration, then Standalone and packaged Development/Shipping for acceptance.

For a review task:

- Reject per-panel SceneCapture, fake World Space “real blur,” unrestricted neon fills, continuous refraction, and hit-test decoration.
- Report whether the result maintains model association, text contrast, input behavior, and deterministic fallback.

