# Phase 2 Report

## Summary

Phase 2 built the first working PySide6 skeleton for the AERO X16 Control Center under `PHASE_2_APP_SKELETON_READONLY_DRYRUN`.

The app is intentionally limited to `READ-ONLY / DRY-RUN` behavior. It loads Phase 1 discovery data, displays CPU/GPU/tool/process/risk state, refreshes read-only NVIDIA and powercfg data, and previews future CPU/MSI commands without executing them.

No CPU, GPU, fan, startup, scheduled task, registry, NVIDIA, MSI profile, service, or power-plan change was applied.

## Files Created

Key Phase 2 outputs:

- `phase2_report.md`
- `phase2_report.json`
- `phase2_validation.md`
- `requirements.txt`
- `scripts/run_app.ps1`
- `scripts/validate_phase2.ps1`
- `scripts/collect_readonly_snapshot.ps1`
- `docs/app_architecture_cleaned.md`
- `docs/safety_model.md`
- `docs/phase3_recommendation.md`
- `docs/presentmon_candidate_notes.md`
- `docs/msi_profile_slot_mapping_notes.md`
- `raw_outputs/readonly_snapshot_latest.json`
- `raw_outputs/phase2_validation.json`
- `config/app_config.json`
- `config/tool_paths.json`
- `config/capability_cache.json`
- `presets/preset_schema.example.json`
- `presets/cpu_presets.example.json`
- `presets/gpu_profiles.example.json`
- `presets/game_rules.example.json`
- `restore/README.md`
- `restore/no_restore_manifests_yet.txt`
- Python app package under `app/`

## App Launch Status

PySide6 is installed in the active Python environment. The app can be launched with:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\run_app.ps1
```

An offscreen PySide6 smoke test successfully constructed the `AERO X16 Control Center` main window with 9 tabs.

## PySide6 Availability

PySide6 availability: installed and importable.

`requirements.txt` includes `PySide6` for future environment setup.

## Phase 1 Data Loaded

The app loads these Phase 1 sources:

- `phase1_exploration_report.json`
- `discovered_paths.json`
- `discovered_capabilities.json`
- `risk_catalog.json`
- `command_inventory.md`
- `future_architecture_notes.md`
- `app_probe/process_targets_seed.json`

Current loaded highlights:

- Active power plan from Phase 1: `AERO24_MODERATE_AGGRESSIVE_GAMING`
- MSI Afterburner: detected
- RTSS: detected
- nvidia-smi: detected
- PresentMon candidate: detected
- LibreHardwareMonitor DLL: detected
- Gigabyte/GCC relevant service: detected

## Tabs Built

- Dashboard
- CPU Presets
- GPU Profiles
- Sensors / Telemetry
- Game Automation
- Auto Tuning
- Fan Control / Experimental
- Logs
- Settings / Safety

## Telemetry Works

Read-only NVIDIA telemetry works through `nvidia-smi`. The latest snapshot reported:

- GPU: `NVIDIA GeForce RTX 5070 Laptop GPU`
- Telemetry source: live `nvidia-smi`
- Snapshot file: `raw_outputs/readonly_snapshot_latest.json`

The telemetry tab supports manual refresh and conservative 2-second polling.

## Dry-run Only

Dry-run previews exist for:

- MSI Afterburner profile slots 1 through 5
- Future CPU powercfg setting writes
- Placeholder CPU presets
- Game automation rule previews

These previews clearly state that Phase 2 does not execute the command.

## Locked / Disabled

The following remain locked or disabled:

- MSI profile apply
- CPU setting apply
- active power plan changes
- PresentMon capture sessions
- auto tuning runs
- auto-apply on game launch
- fan control
- service control
- scheduled task creation
- startup entry creation
- registry writes
- NVIDIA write commands

## PresentMon Candidate Findings

Phase 1 found `C:\Program Files\AMD\CNext\CNext\PresentMon-x64.exe`, but help/version probes did not confirm usable syntax. Phase 2 lists and ranks candidates but does not capture frames.

Phase 3 should verify a specific PresentMon executable and command syntax before benchmark workflows depend on it.

## MSI Profile Slot Mapping Status

MSI Afterburner is detected at `C:\Program Files (x86)\MSI Afterburner\MSIAfterburner.exe`.

Slots 1 through 5 are all labeled unverified. Phase 2 does not assume any slot is stock or safe. Phase 3 must manually verify mapping and back up MSI configs/profiles before any profile launch test.

## Known Issues

- PresentMon syntax is not confirmed.
- LibreHardwareMonitor is represented as a discovered DLL, not loaded as a sensor library.
- The GUI is a skeleton; visual polish and deeper workflows are intentionally deferred.
- No screenshots were generated in Phase 2.

## Validation

Validation passed:

- Total checks: 103
- Failed checks: 0
- Python compile: pass
- Python import check: pass
- PySide6 availability: pass
- JSON parse checks: pass
- Static safety checks: pass

## Phase 3 Recommendation

Backup/restore foundation and first explicitly-approved apply tests. Build restore manifests, export/clone active power plan, back up MSI Afterburner configs/profiles, verify MSI profile slot mapping manually, and add one or two guarded CPU setting apply tests with immediate restore. No fan control or EC writes yet.
