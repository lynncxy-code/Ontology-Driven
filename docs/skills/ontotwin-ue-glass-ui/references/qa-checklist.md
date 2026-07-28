# QA checklist

## Contract and lifecycle

- [ ] All six template IDs render as distinct recipes.
- [ ] Template changes clear stale status, metric, body, poster, video, and control state.
- [ ] Selected and always never render two copies for one instance.
- [ ] Overlay disable/removal clears visuals and hit regions; compatible old labels recover as designed.
- [ ] Configuration revision changes rebuild composition; live values only update content.
- [ ] Missing theme, font, material, Postbuffer, or Blur support falls back to a readable surface.

## Content and status

- [ ] Test empty, one-line, multiline, maximum-length Chinese and English content.
- [ ] Optional empty rows collapse together with spacing.
- [ ] Test one to four metrics and explicit `emphasized` values.
- [ ] Missing `emphasized` renders ordinary Value; array order never changes emphasis.
- [ ] Gauge handles min=max, NaN, infinity, negative, and out-of-range values.
- [ ] Trend remains disabled and unsaved while no real history provider exists.
- [ ] When Trend is enabled later, test empty, one point, null gaps, duplicate/late points, offline history, expected interval, and 120-point cap.
- [ ] `status.level` covers all six levels with configured labels, approved tokens, and non-color cues.
- [ ] Metric `state` remains `ok/empty/offline` and is never mistaken for a semantic alert level.
- [ ] World video creates no MediaPlayer and resolves no playback URL.

## Visual and adaptive behavior

- [ ] Test white floors, dark machinery, direct lamps, high-frequency pipes, and mixed backgrounds.
- [ ] Normal text reaches 4.5:1; essential large text/graphics reach 3:1.
- [ ] Status accent does not flood the glass surface.
- [ ] Text, chart, icon, and video remain sharp and unrefracted.
- [ ] Motion stops after open, hover/focus, or one state pulse.
- [ ] ReduceMotion, ReduceTransparency, and HighContrast remain usable.
- [ ] World uses static deterministic highlights and never claims real scene blur/Fresnel behavior.

## Anchoring and DPI

- [ ] Test 720p, 1080p, 1440p/2K, 4K, 100/125/150/200% DPI, windowed, and fullscreen.
- [ ] Apply viewport scale exactly once; no fixed right-side offset or resolution drift.
- [ ] Test all safe-area edges and quadrant changes.
- [ ] Connector points to the correct model.
- [ ] Behind-camera, projection failure, offscreen, occluded, destroyed, or removed targets clean up predictably.
- [ ] Anchor smoothing avoids jitter without visible trailing.

## Input and media

- [ ] Near-view E and god-view pointer selection open the same instance.
- [ ] Decorative layers are `Self Hit Test Invisible`.
- [ ] Only real controls consume pointer/keyboard input.
- [ ] Media clicks do not clear scene selection.
- [ ] Play, pause, mute, expand, close, retry, and target switching follow the video PRD.
- [ ] Close, Esc, or target switch restores cursor, input mode, WASD, and camera controls.
- [ ] No invisible World hit box remains after removal.

## Rendering quality

- [ ] Force High, Balanced, and Performance in development.
- [ ] Verify High Screen uses one reserved Slate Postbuffer.
- [ ] Verify the material samples the same RT0–RT4 index the host reserves.
- [ ] Require explicit host reservation; downgrade when ownership or processor compatibility is ambiguous.
- [ ] Verify High failure downgrades once to Balanced, then Performance.
- [ ] Verify World never attempts real scene blur.
- [ ] Verify no panel owns a SceneCapture or private full-frame scene buffer.
- [ ] Verify Performance has no transparent-empty or checkerboard failure.
- [ ] Log requested/effective quality and fallback reason once.

## Performance and packaging

- [ ] Measure selected High at 1080p and 2K with `stat GPU` and `stat Slate`.
- [ ] Test 20, 50, and 100 always panels with distance/visibility limits.
- [ ] Confirm one shared selected Widget and one shared media session.
- [ ] Confirm World manual redraw updates live data without idle animation.
- [ ] Switch/close panels 100 times; check Widget, RenderTarget, callback, request, and MediaPlayer growth.
- [ ] Run for at least 30 minutes on target hardware and inspect memory stability.
- [ ] Test PIE, Standalone, packaged Development, and Shipping on real DX12 hardware.
- [ ] Verify all plugin fonts and `M_OT_GlassHigh_RT0...RT4` exist in final Cook/container.
- [ ] Check SDR/HDR, exposure, Bloom, TAA/TSR, and enabled upscalers.
- [ ] Record GPU, driver, CPU, resolution, quality tier, sample duration, median, and p95.

## Web editor

- [ ] Editor remains OntoTwin black/white/gray and does not imitate UE glass.
- [ ] High/Balanced/Performance shows persistent fallback help.
- [ ] Type default and instance override/restore are explicit.
- [ ] Metric emphasis and six-level status mapping persist and preview correctly.
- [ ] Metric style shows only applicable fields and submits no stale hidden values.
- [ ] Trend is disabled with explanation while no historical provider exists.
- [ ] Preview states final transparency/blur are verified in UE.
- [ ] Save remains explicit, reversible, and free of native `alert/confirm`.

