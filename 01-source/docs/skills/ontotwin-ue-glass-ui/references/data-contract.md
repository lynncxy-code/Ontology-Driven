# Data contract

## Capability status

Keep current and reserved fields separate:

- Current: requested quality, Value/Gauge, explicit metric emphasis, six-level status labels/tokens, numeric Gauge payload.
- Reserved: Trend configuration and runtime series. Do not enable or persist Trend until a registered real history provider and resolver exist.

Keep all additions inside the existing `I3D_Overlay` values and runtime payload. Do not add a ProjectStore top-level structure, schema version, PostgreSQL column, or separate migration for presentation settings.

## Persisted request configuration

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

- Quality values: `high | balanced | performance`; missing resolves to `balanced`.
- Current metric styles: `value | gauge`.
- Gauge requires a `primary_metric_id` referencing one stable `slots.metrics` ID.
- ObjectType provides the default; Instance stores a sparse presentation override.
- Never persist the effective renderer or degradation reason.

Persist metric emphasis and status appearance inside existing slots:

```json
{
  "slots": {
    "status": {
      "appearance": {
        "normal": {"label": "在线", "color": "green"},
        "info": {"label": "信息", "color": "cyan"},
        "warning": {"label": "注意", "color": "amber"},
        "critical": {"label": "告警", "color": "red"},
        "offline": {"label": "离线", "color": "gray"},
        "unknown": {"label": "未知", "color": "gray"}
      }
    },
    "metrics": [
      {"id": "utilization", "label": "负载率", "emphasized": true}
    ]
  }
}
```

- Missing `emphasized` means `false`.
- Status color accepts only `green | cyan | amber | red | gray`.
- Do not accept project HEX colors.

## Reserved Trend configuration

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

Treat `telemetry_history` as a future registered source placeholder, not a currently valid Binding Source. Do not persist this object while the provider is absent.

## UE-local diagnostics

UE may log or expose:

```json
{
  "requested_quality": "high",
  "effective_quality": "balanced",
  "renderer": "screen_background_blur",
  "degrade_reason": "slate_postbuffer_unavailable"
}
```

Do not write these fields to ProjectStore or require the backend snapshot to echo them.

## Resolved Value/Gauge payload

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
      "emphasized": true,
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

Keep the two state concepts separate:

- Metric `state`: data availability, `ok | empty | offline`.
- Panel `status.level`: business semantics, `normal | info | warning | critical | offline | unknown`.

Use `status.level`/`accent_token` for semantic emphasis. Never treat metric `state` as warning/critical. When no status slot exists, use a neutral accent.

## Reserved Trend payload

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

- Display `display_value`; never parse it back into a number in UE.
- Require finite `numeric_value` and finite non-zero range for Gauge.
- Fall back to Value when Gauge drawing data is invalid.
- Use ISO 8601 UTC timestamps for Trend and sort oldest-to-newest.
- Resolve duplicates/late points and downsample in the backend.
- Encode a known gap as `value: null`; preserve null segments while downsampling.
- Cap resolved Trend series at 120 points.
- Never synthesize history by repeating a scalar value.
- Let live values/points update content without changing configuration revision or rebuilding the template.
- Increment configuration revision for quality, template, emphasis, status appearance, primary metric, metric style, range, series binding, window, sampling/aggregation, or axis changes.

