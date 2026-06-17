# AeroTune UI Modernization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rename the app to AeroTune, replace cramped table-based setting editors with modern form/card editors, capture each tab into `page_photos`, and publish the app to `Kgray44/AeroPilot`.

**Architecture:** Keep Phase 4 safety gates intact and edit only app-side JSON/preset files. Add reusable PySide6 UI helpers for pages, cards, summary metrics, and value editors; use tables only for read-only data such as telemetry, logs, file lists, and validation matrices.

**Tech Stack:** Python, PySide6, PowerShell validation scripts, Git/GitHub CLI.

---

### Task 1: UI Contract Tests

**Files:**
- Create: `tests/aerotune_ui_contract_check.py`

- [ ] Write a PySide6 offscreen test that asserts the app title is `AeroTune`.
- [ ] Assert the CPU, GPU, Game Automation, and Auto Tuning pages expose form editors with stable object names.
- [ ] Assert CPU option-style controls have dropdown widgets for boost mode and cooling policy.
- [ ] Assert `scripts/capture_page_photos.py` exists for tab screenshots.
- [ ] Run the test and confirm it fails before production edits.

### Task 2: Shared Modern UI Helpers

**Files:**
- Modify: `app/ui/common.py`
- Modify: `app/resources/app_styles.qss`

- [ ] Add scroll-page, card, metric, section-title, status-row, and value-editor helpers.
- [ ] Add compact form controls for booleans, small enumerations, numeric values, text values, and nullable values.
- [ ] Style the app with a lighter page background, clean cards, larger spacing, modern tabs, and readable buttons.

### Task 3: AeroTune Branding

**Files:**
- Modify: `app/__init__.py`
- Modify: `app/ui/main_window.py`
- Modify: `app/ui/dashboard_tab.py`
- Modify: `scripts/run_app.ps1`

- [ ] Change `APP_NAME` and the window title to `AeroTune`.
- [ ] Replace visible `AERO X16 Control Center` headers with `AeroTune`.
- [ ] Keep phase and safety copy visible.

### Task 4: Form-Based Editors

**Files:**
- Modify: `app/ui/cpu_tab.py`
- Modify: `app/ui/gpu_tab.py`
- Modify: `app/ui/game_automation_tab.py`
- Modify: `app/ui/autotuning_tab.py`

- [ ] Replace editable tables with scrollable cards/forms.
- [ ] Use dropdowns for CPU boost mode, cooling policy, GPU slot number, restore behavior, and preset candidates.
- [ ] Use checkboxes for enabled/restore booleans.
- [ ] Use spin boxes for numeric CPU values and duration.
- [ ] Save changes only to Phase 4 app JSON/preset files.
- [ ] Leave dry-run previews and real apply gates locked.

### Task 5: Screenshots

**Files:**
- Create: `scripts/capture_page_photos.py`
- Create folder: `page_photos/`

- [ ] Launch the app offscreen at a stable size.
- [ ] Capture one PNG per tab into `page_photos`.
- [ ] Ensure screenshot filenames are readable and deterministic.

### Task 6: Validation and Publish

**Files:**
- Modify as needed: `phase4_report.md`, `phase4_report.json`, `README.md`

- [ ] Run `tests/aerotune_ui_contract_check.py`.
- [ ] Run `scripts/validate_phase4.ps1`.
- [ ] Run screenshot capture.
- [ ] Check active power plan and sandbox cleanup state.
- [ ] Clone or initialize `Kgray44/AeroPilot`, stage only intended files, commit, push, and open/publish using GitHub CLI.
