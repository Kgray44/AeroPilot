# Sensor Cards and Visuals

Phase 6 adds reusable PySide6 telemetry widgets:

- `MetricCard`: title, large value, unit, status text, tone, and optional progress bar.
- `SensorBarCard`: metric-card variant for progress-driven readings.
- `MiniHistoryChart`: lightweight custom-painted rolling chart with no plotting dependency.

Tones are `normal`, `safe`, `warn`, `danger`, and `unavailable`. Styling lives in `app/resources/app_styles.qss` so threshold decisions stay in the normalizer/UI model instead of being duplicated throughout the interface.
