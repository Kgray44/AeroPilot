# Phase 3 Control Surface Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a read-only/dry-run Phase 3 app copy where every discovered or planned AERO X16 control has a manifest entry, UI assignment, risk label, preset binding where appropriate, backup requirement, restore strategy, and validation coverage.

**Architecture:** Copy the Phase 2 PySide6 app into a new Phase 3 folder, then make the app manifest-driven. The manifest, coverage matrix, action catalog, restore catalog, and editable preset files are generated inside Phase 3 from Phase 1/2 source data and explicit Phase 3 required-control definitions.

**Tech Stack:** Python 3, PySide6, JSON preset/config files, PowerShell 5.1-compatible validation and read-only snapshot scripts.

---

### Task 1: Red Validation Guard

**Files:**
- Create: `scripts/validate_phase3.ps1`
- Create: `tests/phase3_static_import_check.py`

- [ ] **Step 1: Write validation before implementation**

Create a validator that checks required files, JSON parsing, Python compile/imports, PySide6 offscreen construction, static safety rules, and manifest coverage rules.

- [ ] **Step 2: Run validation and expect failure**

Run:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\scripts\validate_phase3.ps1"
```

Expected: failure because Phase 3 artifacts do not exist yet.

### Task 2: Copy Phase 2 App Forward

**Files:**
- Copy: `PHASE_2_APP_SKELETON_READONLY_DRYRUN\app\**`
- Copy: `PHASE_2_APP_SKELETON_READONLY_DRYRUN\requirements.txt`
- Copy: `PHASE_2_APP_SKELETON_READONLY_DRYRUN\app\resources\app_styles.qss`

- [ ] **Step 1: Copy only into Phase 3**

Use `Copy-Item` from Phase 2 into Phase 3. Do not write to Phase 1 or Phase 2.

- [ ] **Step 2: Remove copied cache files**

Delete copied `__pycache__` folders inside Phase 3 only.

### Task 3: Generate Manifest and Presets

**Files:**
- Create: `scripts/generate_phase3_artifacts.ps1`
- Create: `config/control_surface_manifest.json`
- Create: `config/ui_coverage_matrix.json`
- Create: `config/action_catalog.json`
- Create: `config/restore_requirement_catalog.json`
- Create: `config/unsupported_or_blocked_controls.json`
- Create: `presets/cpu_presets.json`
- Create: `presets/gpu_profiles.json`
- Create: `presets/game_rules.json`
- Create: `presets/combined_presets.json`
- Create: `presets/preset_schema.json`
- Create: `presets/preset_validation_report.json`

- [ ] **Step 1: Generate from Phase 1/2 source data**

Read Phase 1 risk items, processor settings, MSI data, NVIDIA telemetry data, PresentMon candidates, LibreHardwareMonitor data, Gigabyte data, process targets, and Phase 2 config/preset files.

- [ ] **Step 2: Include explicit required controls**

Add stable IDs for required CPU, GPU/MSI, NVIDIA telemetry, PresentMon/FPS, LibreHardwareMonitor, process automation, network/ping, fan/OEM, restore/backup, and startup/automation controls.

- [ ] **Step 3: Validate generated JSON**

Run `Get-ChildItem . -Recurse -Filter *.json | ConvertFrom-Json` and require zero parse failures.

### Task 4: Manifest-Driven UI

**Files:**
- Create: `app/core/control_surface.py`
- Modify: `app/core/app_paths.py`
- Modify: `app/ui/main_window.py`
- Modify: `app/ui/common.py`
- Modify: all tab modules under `app/ui`

- [ ] **Step 1: Add manifest loading helpers**

Expose manifest, coverage, actions, restore requirements, and editable presets through a small `ControlSurface` class.

- [ ] **Step 2: Add reusable table/filter/editor widgets**

Add helpers for manifest tables, search boxes, JSON-backed combo edits, and dry-run preview dialogs.

- [ ] **Step 3: Update each tab**

Dashboard summarizes manifest counts. CPU/GPU/Game/Telemetry/AutoTuning/Fan/Safety tabs show relevant manifest rows and app-side editors. Logs tab exposes Phase 3 logs and bundle export.

### Task 5: Docs, Reports, and Scripts

**Files:**
- Create: `phase3_report.md`
- Create: `phase3_report.json`
- Create: `phase3_validation.md`
- Create: `scripts/run_app.ps1`
- Create: `scripts/collect_control_surface_snapshot.ps1`
- Create: `scripts/export_control_surface_bundle.ps1`
- Create: `docs/control_surface_design.md`
- Create: `docs/coverage_rules.md`
- Create: `docs/preset_editing_model.md`
- Create: `docs/backup_restore_requirements.md`
- Create: `docs/phase4_recommendation.md`
- Create: `docs/unresolved_controls.md`
- Create: `docs/known_risks.md`
- Create: `restore/README.md`
- Create: `restore/restore_strategy_preview.json`
- Create: `restore/no_real_restore_manifest_yet.txt`

- [ ] **Step 1: Write docs from generated data**

Describe the manifest model, coverage rules, preset-only editing, backup/restore requirements, unresolved controls, and known risks.

- [ ] **Step 2: Write scripts**

Run script launches the Phase 3 app. Snapshot script writes read-only state inside Phase 3. Bundle export only zips files from the Phase 3 folder.

### Task 6: Verification

**Files:**
- Update: `phase3_validation.md`
- Update: `raw_outputs/phase3_validation.json`
- Update: `raw_outputs/control_surface_snapshot_latest.json`

- [ ] **Step 1: Run validator**

Run:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\scripts\validate_phase3.ps1"
```

Expected: all checks pass.

- [ ] **Step 2: Run offscreen app smoke**

Construct `MainWindow(AppPaths.discover())` with `QT_QPA_PLATFORM=offscreen`. Expected title is `AERO X16 Control Center` and tab count is 9.

- [ ] **Step 3: Run read-only snapshot**

Run:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\scripts\collect_control_surface_snapshot.ps1"
```

Expected: snapshot JSON appears under `raw_outputs` and contains `READ-ONLY / DRY-RUN`.

### Self-Review

- Spec coverage: manifest, presets, UI, safety, docs, reports, scripts, and validation are all represented by tasks.
- Placeholder scan: no task uses TBD or undefined future placeholders.
- Type consistency: manifest rows use `control_id`, `friendly_name`, `category`, `ui_tab`, `current_value`, `desired_value_editing`, `future_apply`, `restore`, `risk`, and `coverage` consistently.
