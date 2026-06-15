# Phase 5 Guarded CPU Apply UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build Phase 5 from Phase 4 with a safer CPU preset editor, power plan management visibility, guarded apply gates, improved process matching, PresentMon cleanup, reports, validation, and screenshots.

**Architecture:** Copy Phase 4 forward and keep all edits in Phase 5. Add contract tests first, then implement focused adapters/scripts/UI changes. Real system writes remain disabled unless documented backup gates prove they are safe; Phase 5 creates preview/foundation paths only.

**Tech Stack:** Python, PySide6, PowerShell 5.1-compatible scripts, JSON manifests, `powercfg`, `nvidia-smi`, PresentMon, LibreHardwareMonitor read-only probe.

---

### Task 1: Phase 5 Folder And Contract Tests

**Files:**
- Create: `tests/phase5_contract_check.py`
- Create: `tests/Test-Phase5Scripts.ps1`

- [x] Copy Phase 4 to `PHASE_5_GUARDED_CPU_APPLY_FOUNDATION_AND_UI_REFINEMENT`.
- [ ] Add a PySide6 contract test for the AC/DC CPU selector, power-plan management surface, process command-line columns, PresentMon cleanup hook, and 9-tab shell.
- [ ] Add a PowerShell contract test for Phase 5 scripts and JSON output paths.
- [ ] Run both tests and confirm they fail before implementation.

### Task 2: Phase 5 Backup/Restore And Gate Scripts

**Files:**
- Create: `scripts/Phase5Common.ps1`
- Create: `scripts/export_active_power_plan_phase5.ps1`
- Create: `scripts/create_phase5_backup_manifest.ps1`
- Create: `scripts/generate_phase5_restore_scripts.ps1`
- Create/modify: `config/apply_gate_config.json`

- [ ] Implement elevation detection and read-only active plan export attempt.
- [ ] Build a Phase 5 backup manifest from Phase 4 status plus current query snapshots.
- [ ] Generate preview-only restore scripts.
- [ ] Keep `cpu_guarded_apply_enabled` and `active_plan_write_enabled` false unless backup/restore gates are proven.

### Task 3: CPU Presets AC/DC Redesign

**Files:**
- Modify: `app/ui/cpu_tab.py`
- Modify: `app/adapters/powercfg_adapter.py`
- Modify: `app/core/control_surface.py`

- [ ] Add a top-level AC/DC selector.
- [ ] Save visible edits before switching views.
- [ ] Show only one desired value editor per setting card.
- [ ] Add current-vs-desired status and visible summary counts.
- [ ] Add safe buttons: refresh current values, save JSON, refresh preview, check gates, preview guarded apply, restore preview.

### Task 4: Power Plan Management Surface

**Files:**
- Create: `app/adapters/power_plan_adapter.py`
- Modify: `app/ui/settings_safety_tab.py`
- Modify: `app/ui/dashboard_tab.py`

- [ ] List all power plans read-only.
- [ ] Add preview-only controls to create/clone and set existing plans.
- [ ] Keep actual active plan switching blocked by gates.
- [ ] Surface active plan export and Phase 5 readiness.

### Task 5: Process Matching And PresentMon Lifecycle

**Files:**
- Modify: `app/adapters/process_adapter.py`
- Modify: `app/ui/game_automation_tab.py`
- Modify: `app/adapters/presentmon_adapter.py`
- Modify: `app/ui/main_window.py`
- Modify: `app/ui/telemetry_tab.py`

- [ ] Read process command lines through CIM/WMI.
- [ ] Match configured command-line filters with clear unavailable/false-positive flags.
- [ ] Prevent multiple PresentMon captures.
- [ ] Stop active PresentMon capture on app close.
- [ ] Log capture lifecycle metadata.

### Task 6: Docs, Reports, Screenshots, Validation

**Files:**
- Create: `phase5_report.md`
- Create: `phase5_report.json`
- Create: `phase5_validation.md`
- Create: `docs/*.md`
- Modify: `scripts/capture_page_photos.py`
- Create: `scripts/validate_phase5.ps1`

- [ ] Generate Phase 5 docs and reports.
- [ ] Capture 10 screenshots, including CPU AC and CPU DC views.
- [ ] Validate JSON, PowerShell parsing, Python compilation, PySide6 construction, contracts, safety scans, and screenshots.
