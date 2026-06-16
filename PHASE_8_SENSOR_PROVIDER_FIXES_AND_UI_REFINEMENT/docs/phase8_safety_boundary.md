# Phase 8 Safety Boundary

Phase 8 is telemetry, diagnostics, and UI refinement only.

Allowed:
- Read sensor data from existing read-only providers.
- Run read-only nvidia-smi telemetry queries.
- Run LibreHardwareMonitor read-only probes.
- Read PresentMon state and optional user-started capture output.
- Write app-side JSON, reports, screenshots, and diagnostics inside the Phase 8 folder.

Still blocked:
- MSI Afterburner profile launches.
- NVIDIA write commands.
- Fan writes or embedded-controller access.
- Service start, stop, or restart commands.
- Startup entries and scheduled tasks.
- Registry writes.
- Automatic game-triggered apply.
- Automatic CPU or GPU tuning apply.

Phase 8 does not expand any apply gate. Provider diagnostics explain missing or stale telemetry without changing laptop tuning behavior.
