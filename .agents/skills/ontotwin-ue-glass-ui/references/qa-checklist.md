# QA checklist

## Contract and lifecycle

- [ ] All six template IDs render as distinct recipes.
- [ ] Template changes clear old status, metric, body, poster, video, and control state.
- [ ] Selected and always never render two copies for one resolved instance.
- [ ] Overlay disable/removal clears visual and hit regions; compatible old labels recover as designed.
- [ ] Configuration revision changes rebuild composition; live values only update content.
- [ ] Missing theme, font, material, or blur support falls back to a readable surface.

## Template content

- [ ] Test empty, one-line, multiline, maximum-length Chinese and English content.
- [ ] Optional empty rows collapse with spacing.
- [ ] Test one to four values, explicit primary-metric selection, one Gauge, and one Trend.
- [ ] Gauge handles min=max, NaN, infinity, negative, and out-of-range values.
- [ ] Trend handles empty, one point, explicit null gaps, duplicate/late points, offline history, expected sample interval, and 120-point cap.
- [ ] `status.level` covers normal, info, warning, critical, offline, and unknown with non-color cues.
- [ ] Metric `state` remains ok/empty/offline and is never mistaken for a semantic alert level.
- [ ] Video covers poster, loading, play, pause, mute, expand, close, resolve failure, retry, and switch.
- [ ] World video creates no MediaPlayer and resolves no playback URL.

## Visual and adaptive behavior

- [ ] Test white floor, dark machinery, direct lamps, high-frequency pipes, and mixed backgrounds.
- [ ] Normal text reaches 4.5:1; essential large text/graphics reach 3:1.
- [ ] Status accent does not flood the glass surface.
- [ ] Text, chart, icon, and video remain sharp and unrefracted.
- [ ] Motion stops after open, hover, or one state pulse.
- [ ] Reduced-motion and high-contrast/reduced-transparency fallback remain usable.

## Anchoring and DPI

- [ ] Test 720p, 1080p, 1440p/2K, 4K, 100/125/150/200% DPI, windowed, and fullscreen.
- [ ] Apply viewport scale exactly once; no fixed right-side offset or resolution drift.
- [ ] Test all safe-area edges and quadrant changes.
- [ ] Connector points to the correct model.
- [ ] Behind-camera, projection failure, offscreen, occluded, destroyed, or removed targets clean up predictably.
- [ ] Anchor smoothing avoids jitter without visible trailing.

## Input

- [ ] Near-view E and god-view pointer selection still open the same instance.
- [ ] Decorative layers are Self Hit Test Invisible.
- [ ] Only real controls consume pointer/keyboard input.
- [ ] Media clicks do not clear scene selection.
- [ ] Close, Esc, or target switch restores cursor and prior input mode.
- [ ] WASD and camera controls resume; no invisible World hit box remains.
- [ ] Focus, hover, pressed, disabled, and keyboard focus states are visible.

## Rendering quality

- [ ] Force High, Balanced, and Performance in development.
- [ ] Verify High Screen uses one reserved Slate postbuffer.
- [ ] Require an explicit host RT0–RT4 reservation; verify enabled/processor compatibility and downgrade when ownership is ambiguous.
- [ ] For RT1–RT4, verify enablement occurs before Slate renderer initialization in UE 5.6.
- [ ] Verify High failure downgrades to Balanced then Performance only once.
- [ ] Verify World never attempts real scene blur.
- [ ] Verify no panel owns a SceneCapture or private full-frame scene buffer.
- [ ] Verify Performance has no transparent-empty/checkerboard failure.
- [ ] Log requested/effective quality and fallback reason once.

## Performance and packaging

- [ ] Measure High selected at 1080p and 2K with `stat GPU` and `stat Slate`.
- [ ] Test 20, 50, and 100 always panels with distance/visibility limits.
- [ ] Confirm one shared selected widget and one shared media session.
- [ ] Confirm World manual-redraw updates live data without idle animation.
- [ ] Test PIE, Standalone, packaged Development, and Shipping on target DX12 hardware.
- [ ] Verify plugin fonts/materials/textures/theme assets are cooked.
- [ ] Check SDR/HDR, automatic exposure, Bloom, TAA/TSR, and enabled upscalers.
- [ ] Force ReduceMotion, ReduceTransparency, and HighContrast acceptance settings.
- [ ] Switch instances 100 times and change/close levels; verify no Widget, RenderTarget, callback, or MediaPlayer leak.

## Web editor

- [ ] Editor remains OntoTwin black/white/gray and does not mimic UE glass.
- [ ] High/Balanced/Performance has persistent fallback help.
- [ ] Type default and instance override/restore are explicit.
- [ ] Metric style shows only applicable fields and submits no stale hidden values.
- [ ] Trend is disabled with explanation when no historical source exists.
- [ ] Structural preview states final transparency/blur are verified in UE.
- [ ] Save remains explicit, reversible, and free of native alert/confirm.
