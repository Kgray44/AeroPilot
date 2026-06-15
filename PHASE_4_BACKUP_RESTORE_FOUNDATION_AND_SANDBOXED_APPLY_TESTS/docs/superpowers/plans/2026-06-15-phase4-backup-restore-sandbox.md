# Phase 4 Backup Restore Sandbox Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build Phase 4 backup/restore foundations and prove guarded write/verify/cleanup logic only against a temporary inactive cloned power plan.

**Architecture:** Copy the Phase 3 app forward, then add Phase 4 backup manifests, restore manifests, apply gates, and PowerShell scripts. The only system write test is `powercfg /duplicatescheme` plus `powercfg /setacvalueindex` on the temporary clone and `powercfg /delete` for cleanup.

**Tech Stack:** Python 3, PySide6, JSON manifests, Windows PowerShell 5.1-compatible scripts, `powercfg`, file-copy backups.

---

### Task 1: Create Phase 4 Guard Rails

**Files:**
- Create: `scripts/validate_phase4.ps1`
- Create: `tests/phase4_static_import_check.py`

- [ ] Write validation first and run it red.
- [ ] Validation checks required artifacts, JSON parsing, Python compile/imports, PySide6 offscreen construction, backup files, sandbox safety, blocked actions, and apply gates.

### Task 2: Copy Phase 3 Forward

**Files:**
- Copy: `PHASE_3_CONTROL_SURFACE_COMPLETENESS_AND_PRESET_EDITING/app/**`
- Copy: `PHASE_3_CONTROL_SURFACE_COMPLETENESS_AND_PRESET_EDITING/config/*.json`
- Copy: `PHASE_3_CONTROL_SURFACE_COMPLETENESS_AND_PRESET_EDITING/presets/*.json`
- Copy: `PHASE_3_CONTROL_SURFACE_COMPLETENESS_AND_PRESET_EDITING/requirements.txt`

- [ ] Copy only into Phase 4.
- [ ] Remove copied `__pycache__`.
- [ ] Update path metadata to use `phase4_root`.

### Task 3: Build Backup And Restore Scripts

**Files:**
- Create: `scripts/export_active_power_plan.ps1`
- Create: `scripts/backup_msi_afterburner_configs.ps1`
- Create: `scripts/create_backup_manifest.ps1`
- Create: `scripts/generate_restore_scripts.ps1`

- [ ] Export the active plan and query CPU values without changing the active plan.
- [ ] Copy MSI files into `backups/msi_afterburner`.
- [ ] Copy app config/presets into `backups/app_config`.
- [ ] Generate restore manifests and preview-only restore scripts.

### Task 4: Build Sandbox Apply Test

**Files:**
- Create: `scripts/sandbox_powercfg_apply_test.ps1`
- Create: `scripts/cleanup_sandbox_power_plan.ps1`

- [ ] Duplicate the active scheme into a clearly named inactive sandbox clone.
- [ ] Verify the clone is not active.
- [ ] Write only EPP/cooling values to the clone GUID.
- [ ] Verify the clone changed.
- [ ] Delete the clone.
- [ ] Verify the active GUID is unchanged and the clone is gone.

### Task 5: Update Phase 4 App UI

**Files:**
- Modify: `app/core/app_paths.py`
- Modify: `app/core/control_surface.py`
- Modify: dashboard, CPU, GPU, logs, and safety tabs.

- [ ] Add backup status, restore status, sandbox result, and apply gate summaries.
- [ ] Keep all real apply buttons blocked or dry-run-only.

### Task 6: Reports And Final Verification

**Files:**
- Create: `phase4_report.md`
- Create: `phase4_report.json`
- Create: `phase4_validation.md`
- Create: `docs/*.md`

- [ ] Run backup manifest generation.
- [ ] Run sandbox apply test or record a clear skip/failure.
- [ ] Run Phase 4 validation.
- [ ] Update reports with actual validation evidence.
