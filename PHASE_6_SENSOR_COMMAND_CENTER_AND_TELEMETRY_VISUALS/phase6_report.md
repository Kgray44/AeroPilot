# Phase 6 Report

## Summary

Phase 6 copied the completed Phase 5 app into `PHASE_6_SENSOR_COMMAND_CENTER_AND_TELEMETRY_VISUALS` and redesigned the Sensors tab into a read-only telemetry command center.

## What Changed From Phase 5

- Added `app/core/sensor_normalizer.py`.
- Added `app/core/sensor_history.py`.
- Added reusable telemetry widgets in `app/ui/telemetry_widgets.py`.
- Rebuilt `app/ui/telemetry_tab.py` with overview cards, history charts, grouped panels, raw explorer, favorites, and CPU diagnostics.
- Updated the bottom status bar to use normalized telemetry.
- Added sensor readiness to Dashboard.
- Added sensor configuration visibility to Settings / Safety.
- Added `config/sensor_favorites.json`.
- Added Phase 6 screenshot capture targets and validation scripts.

## Sensor Tab Redesign

The Sensors tab now opens with modern metric cards for CPU, GPU, VRAM, RAM, fan, FPS, frame time, and sensor status. Below that are mini history charts, grouped hardware panels, an All Sensors explorer, and a CPU temperature diagnostics view.

## CPU Temperature Detection Improvements

The normalizer now ranks CPU temperature candidates, rejects impossible values, and records accepted/rejected candidates. Mocked validation passes for `CPU Package`, `Package`, `Core Max`, `P-Core Max`, and `Tctl/Tdie`.

Live read-only probe result:

- LHM sensor count: 139
- Normalized raw sensor count: 149
- CPU temperature selected: no
- Reason: the only CPU-like live temperature candidate, `Core (Tctl/Tdie)`, reported `0 C`, which is invalid and rejected.
- GPU telemetry: available through nvidia-smi.
- CPU load: available through LHM.

## Status Bar Telemetry

The bottom status bar now reads from the normalized model. It cannot construct `CPU CPU temp n/a` because it uses the model's `status_display` directly.

## PresentMon

PresentMon remains manually started only. The Sensors tab displays capture state and latest CSV-derived readings when present.

## Safety Boundary

No MSI, NVIDIA write, fan, EC, service, startup, scheduled-task, registry, game automation apply, or automatic tuning apply paths were enabled in Phase 6.

## Validation

Validation passed with 145 checks and 0 failures. Results are written to `phase6_validation.md` and `raw_outputs/phase6_validation.json`.

## Known Issues

- Live LHM currently exposes CPU load but not a valid CPU temperature. The app now explains this instead of silently failing.
- Fan RPM is unavailable, which is common on laptops that hide fan sensors from LHM.

## Recommended Phase 7

Stabilize live telemetry over longer sessions and add optional app-side telemetry logging/export while keeping tuning writes gated.
