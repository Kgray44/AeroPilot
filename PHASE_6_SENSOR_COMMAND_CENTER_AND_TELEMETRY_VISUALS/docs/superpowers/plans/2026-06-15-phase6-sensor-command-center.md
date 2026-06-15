# Phase 6 Sensor Command Center Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the AeroTune Phase 6 Sensors tab as a modern telemetry command center with robust sensor normalization and CPU temperature diagnostics.

**Architecture:** Copy Phase 5 forward unchanged, then add a focused `sensor_normalizer.py` core model that all sensor UI/status surfaces consume. Keep writes blocked; this phase only reads telemetry, saves app-side favorites JSON, and generates reports/screenshots.

**Tech Stack:** Python 3, PySide6, PowerShell read-only probes, JSON configs, no new external plotting dependency.

---

### Task 1: Phase Folder And Contracts

**Files:**
- Create: `PHASE_6_SENSOR_COMMAND_CENTER_AND_TELEMETRY_VISUALS/tests/phase6_sensor_normalizer_check.py`
- Create: `PHASE_6_SENSOR_COMMAND_CENTER_AND_TELEMETRY_VISUALS/tests/phase6_ui_contract_check.py`
- Create: `PHASE_6_SENSOR_COMMAND_CENTER_AND_TELEMETRY_VISUALS/scripts/validate_phase6.ps1`

- [ ] Write mocked tests for CPU Package, Package, Core Max, P-Core Max, Tctl/Tdie, fallback, and no-valid-temp diagnostics.
- [ ] Run the test and verify it fails because `app.core.sensor_normalizer` does not exist.
- [ ] Add UI contract checks for overview cards, raw explorer, diagnostics view, and no automatic PresentMon start.

### Task 2: Sensor Normalization Core

**Files:**
- Create: `app/core/sensor_normalizer.py`
- Create: `app/core/sensor_history.py`
- Create/update: `config/sensor_favorites.json`

- [ ] Implement `SensorNormalizer.normalize(lhm_snapshot, nvidia_snapshot, presentmon_snapshot, favorites)` returning headline, cards, groups, raw_sensors, and diagnostics.
- [ ] Preserve every raw sensor in `raw_sensors`.
- [ ] Implement CPU temperature ranking and rejection reasons.
- [ ] Add history buffer for core metrics with max 120 samples.
- [ ] Add JSON-only favorite matching and saving.

### Task 3: Sensors UI Command Center

**Files:**
- Create: `app/ui/telemetry_widgets.py`
- Replace: `app/ui/telemetry_tab.py`
- Update: `app/resources/app_styles.qss`

- [ ] Build `MetricCard`, `SensorBarCard`, and `MiniHistoryChart`.
- [ ] Add overview cards for CPU, GPU, VRAM, FPS, RAM, fan, and sensor status.
- [ ] Add grouped CPU/GPU/memory/fans/storage/network/other/PresentMon panels.
- [ ] Add All Sensors explorer with search and filters.
- [ ] Add CPU diagnostics panel listing accepted/rejected candidates.
- [ ] Add favorite sensor cards and JSON save action.
- [ ] Keep refresh non-blocking enough for the UI by using a background worker and last-known-good data.

### Task 4: Shared Status And Existing Tabs

**Files:**
- Update: `app/ui/main_window.py`
- Update: `app/ui/dashboard_tab.py`
- Update: `app/ui/settings_safety_tab.py`

- [ ] Make the bottom status bar read from the normalized model.
- [ ] Add dashboard telemetry readiness fields.
- [ ] Add settings fields for polling, favorites config, and normalizer status.
- [ ] Keep apply gates unchanged and blocked.

### Task 5: Docs, Screenshots, Validation, Publish

**Files:**
- Create: `phase6_report.md`, `phase6_report.json`, `phase6_validation.md`
- Create: `docs/phase6_safety_boundary.md`, `docs/sensor_command_center_design.md`, `docs/sensor_normalization_model.md`, `docs/cpu_temperature_detection_debugging.md`, `docs/sensor_cards_and_visuals.md`, `docs/presentmon_sensor_integration.md`, `docs/phase7_recommendation.md`
- Update: `scripts/capture_page_photos.py`
- Update root: `README.md`, `page_photos/`

- [ ] Generate 12 screenshots.
- [ ] Run `scripts/validate_phase6.ps1` and get 0 failures.
- [ ] Verify root `Start-AeroTune.ps1 -DryRun -Json` selects Phase 6.
- [ ] Commit and push to `Kgray44/AeroPilot`.

