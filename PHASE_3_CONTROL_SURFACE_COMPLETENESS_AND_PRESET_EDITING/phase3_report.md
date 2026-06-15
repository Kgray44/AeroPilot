# Phase 3 Report

## Summary

Phase 3 builds the manifest-driven control surface for the AERO X16 Control Center. It remains `READ-ONLY / DRY-RUN` and only edits app-side JSON preset/config files.

## What Changed From Phase 2

- Added `control_surface_manifest.json` as the app control source of truth.
- Added coverage, action, restore, unsupported/blocked, and editable preset catalogs.
- Promoted CPU, GPU, telemetry, game automation, auto tuning, fan/OEM, restore, and startup controls into structured rows.
- Kept all apply paths disabled or dry-run only.

## Control Surface Manifest Summary

- Controls represented: 102
- Editable in Phase 3: 31
- Read-only rows: 31
- Dry-run preview rows: 13
- Blocked/future rows: 53

## Number By Category

- CPU boost behavior: 4
- CPU frequency limits: 3
- CPU power behavior: 9
- CPU scheduling/core parking: 4
- FPS/frame capture: 9
- Fan control: 11
- GPU power/clock telemetry: 13
- GPU profile loading: 11
- GPU voltage/frequency curve profile: 2
- Game detection: 16
- Ping/network logging: 5
- Restore/backup: 9
- Startup automation: 6

## Number By Risk Level

- Dangerous / Experimental: 2
- High: 15
- Low: 28
- Medium: 22
- Read-only: 20
- Safe: 14
- Unknown: 1

## Preset Editing Status

CPU presets, GPU profile mappings, game rules, combined presets, polling settings, PresentMon preference, network preferences, and automation kill-switches are stored as app-side JSON only.

## Tab Improvements

- CPU Presets: full manifest-backed CPU table, active plan status, preset editor, dry-run command preview.
- GPU Profiles: MSI paths/files, slot mapping editor, unverified slot warnings, dry-run command previews.
- Sensors / Telemetry: NVIDIA field catalog, polling config editor, PresentMon candidates, LibreHardwareMonitor future sensors.
- Game Automation: editable process rules, live matching preview, false-positive warnings.
- Auto Tuning: experiment plan definitions and future scoring model.
- Fan Control / Experimental: OEM/GCC surfaces and blocked action rows.
- Settings / Safety: risk catalog and coverage audit tables.

## Known Issues

No real restore manifest exists yet. PresentMon syntax remains unverified. MSI slot mapping remains unverified. Fan controls remain blocked.

## Validation Result

- Validation script: `scripts/validate_phase3.ps1`
- Total checks: 265
- Failed checks: 0
- PySide6 offscreen launch: passed with window title `AERO X16 Control Center` and 9 tabs
- Latest snapshot: `raw_outputs/control_surface_snapshot_latest.json`
- System changes applied: false

## Recommended Phase 4

Backup/restore foundation and first explicitly-approved apply tests. Build restore manifests, export/clone active power plan, back up MSI Afterburner configs/profiles, manually verify MSI profile slot mapping, and add one or two guarded CPU setting apply tests with immediate restore. No fan control or EC writes yet.
