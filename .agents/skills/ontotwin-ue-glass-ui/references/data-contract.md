# Data contract

These are backward-compatible design additions for future implementation. Do not apply them to storage or APIs during a design-only task.

## Persisted request configuration

Keep requested visual choices inside the existing I3D_Overlay configuration:

```json
{
  "presentation": {
    "quality_tier": "balanced",
    "metrics": {
      "style": "gauge",
      "primary_metric_id": "utilization",
      "gauge": {
        "min": 0.0,
        "max": 100.0,
        "clamp_visual": true
      }
    }
  }
}
```

- Quality values are `high`, `balanced`, and `performance`; missing resolves to `balanced`.
- Metric style is panel-level: `value`, `gauge`, or `trend`.
- Gauge/Trend requires a `primary_metric_id` that references one stable ID in `slots.metrics`.
- The primary metric owns the visual; up to three remaining metrics render as compact Value.
- ObjectType provides the default; an instance may sparsely override the presentation group.

This object is configuration only. Never persist an effective renderer or degradation reason.

Trend persistence uses a real history binding and panel-level options:

```json
{
  "presentation": {
    "quality_tier": "balanced",
    "metrics": {
      "style": "trend",
      "primary_metric_id": "temperature",
      "trend": {
        "series_binding": {"source": "telemetry_history", "path": "temperature"},
        "window_seconds": 600,
        "sample_interval_seconds": 5,
        "aggregation": "avg",
        "show_axis": true,
        "y_min": null,
        "y_max": null
      }
    }
  }
}
```

`telemetry_history` is a future registered time-series source placeholder, not a currently supported Binding Source. Do not save Trend configuration until such a provider exists.

## UE-local diagnostics

UE may log or expose local diagnostics:

```json
{
  "requested_quality": "high",
  "effective_quality": "balanced",
  "renderer": "screen_background_blur",
  "degrade_reason": "slate_postbuffer_unavailable"
}
```

Do not write these fields back to ProjectStore or require them in the backend snapshot.

## Resolved runtime payload

Keep current metric fields, especially `id`, `label`, `display_value`, and `state`. Add optional drawing data only after backend support exists:

```json
{
  "status": {
    "display_value": "注意",
    "detail_value": "温度接近上限",
    "level": "warning",
    "accent_token": "amber",
    "state": "ok"
  },
  "metrics": [
    {
      "id": "utilization",
      "label": "负载率",
      "display_value": "68%",
      "emphasized": false,
      "state": "ok",
      "numeric_value": 68.0
    }
  ],
  "metrics_visual": {
    "style": "gauge",
    "primary_metric_id": "utilization",
    "range": {"min": 0.0, "max": 100.0, "clamp_visual": true}
  }
}
```

The two state concepts are different:

- Metric `state` is data availability: `ok | empty | offline`.
- Panel `status.level` is business semantics: `normal | info | warning | critical | offline | unknown`.

Persisted metric items may include `emphasized: true|false`; missing means `false`. Persisted status slots may include an `appearance` map keyed by the six standard levels, with `{label, color}` values. `color` is one of `green | cyan | amber | red | gray`; UE receives the resolved `accent_token` and never accepts project HEX colors.

Use `status.level` for the semantic rim and Gauge/Trend accent. When the template has no status slot, use a neutral accent. Never treat metric `state` as warning/critical.

Trend attaches real history to the primary resolved metric and includes panel-level visual resolution:

```json
{
  "metrics": [
    {
      "id": "temperature",
      "label": "温度",
      "display_value": "36.5 °C",
      "state": "ok",
      "numeric_value": 36.5,
      "series": {
        "unit": "°C",
        "sample_interval_seconds": 5,
        "points": [
          {"timestamp": "2026-07-23T10:00:00Z", "value": 35.8},
          {"timestamp": "2026-07-23T10:00:05Z", "value": null},
          {"timestamp": "2026-07-23T10:00:10Z", "value": 36.5}
        ]
      }
    }
  ],
  "metrics_visual": {
    "style": "trend",
    "primary_metric_id": "temperature",
    "window_seconds": 600,
    "sample_interval_seconds": 5,
    "show_axis": true,
    "y_min": null,
    "y_max": null
  }
}
```

## Rules

- UE displays `display_value` and never parses it back into a number.
- Gauge requires finite `numeric_value` and a finite non-zero range.
- Trend points contain a finite numeric value or an explicit null gap and are sorted oldest-to-newest.
- Use ISO 8601 UTC timestamps on the wire.
- Resolve duplicate timestamps in the backend.
- Encode a known gap as `value: null`; include the expected sample interval and preserve null segments during downsampling. Do not draw a continuous lie across an outage.
- Cap a resolved series at 120 points and downsample before the snapshot reaches UE.
- Allow one primary Trend series per panel initially.
- Use backend-provided `status.level`; UE does not derive alert thresholds.
- Invalid drawing data falls back to Value with explicit no-data/offline treatment.
- Real-time values/points update content without changing configuration revision or rebuilding the template.
- Quality, template, primary metric, metric style, range, series binding, window, sampling/aggregation, and axis changes do change configuration revision.

Avoid a new top-level ProjectStore structure. Keep additions within existing I3D_Overlay configuration and runtime payload, subject to implementation approval.

Trend configuration must use a future registered numeric time-series binding. Until the backend has a history provider and resolver, keep Trend disabled rather than persisting raw history in ProjectStore.
