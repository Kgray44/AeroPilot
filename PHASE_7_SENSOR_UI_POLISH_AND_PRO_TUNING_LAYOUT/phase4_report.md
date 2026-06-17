# Phase 4 Report

## Summary

Phase 4 built the backup, restore, and guarded apply-test foundation for the AERO X16 Control Center.

The app and scripts now create backup and restore manifests, copy MSI Afterburner configuration/profile files into the Phase 4 backup area, snapshot readable CPU/powercfg values, back up app-side JSON, and prove clone-only CPU write plumbing against a temporary inactive power scheme.

The app has also been renamed to `AeroTune`. The Phase 4 UI was revised into a cleaner card/form layout with top navigation, editable app-side preset controls, dropdowns for fixed-option settings, an always-visible telemetry status bar, and a dedicated Sensors tab for NVIDIA, PresentMon, and LibreHardwareMonitor readings.

No active laptop tuning behavior was intentionally changed. MSI profiles were not launched. NVIDIA, fan, EC, service, startup, scheduled-task, and registry writes remained blocked.

One important blocker remains: `powercfg /export` for the active plan failed from this non-admin session with Windows privilege error `0x522`. The manifest records the failure, the `.pow` export gate remains false, and Phase 5 readiness is false until that export is completed from an elevated session or another approved backup path is proven.

## What Changed From Phase 3

- Copied the Phase 3 app surface into the Phase 4 folder.
- Added Phase 4 backup/restore/apply-gate scripts.
- Added backup, restore, sandbox, and safety docs.
- Added manifest-driven backup and restore status to the app dashboard and safety views.
- Added sandbox apply-test status to Dashboard, CPU Presets, and Settings / Safety.
- Kept real active-plan writes, MSI profile launches, fan writes, EC writes, automation apply, and NVIDIA writes disabled.

## Safety Boundary

- Active power plan before sandbox: `692ee1d0-ffc2-4c47-91b3-2a4814f3964e` (`AERO24_MODERATE_AGGRESSIVE_GAMING`).
- Active power plan after sandbox: `692ee1d0-ffc2-4c47-91b3-2a4814f3964e` (`AERO24_MODERATE_AGGRESSIVE_GAMING`).
- Temporary sandbox plan: `ef24eec5-0039-4bfc-bc34-dd232ec94767`.
- Sandbox cleanup: deleted successfully.
- Leftover sandbox plan check: no `AERO_X16_CC_SANDBOX_DO_NOT_USE` plan remains.

## Files Created

Primary artifacts:

- `phase4_report.md`
- `phase4_report.json`
- `phase4_validation.md`
- `raw_outputs/phase4_validation.json`
- `raw_outputs/phase4_snapshot_latest.json`
- `backups/backup_manifest_latest.json`
- `restore/restore_manifest_latest.json`
- `restore/restore_plan_latest.md`
- `sandbox/sandbox_powercfg_test_result.json`
- `sandbox/sandbox_powercfg_test_log.md`

Scripts:

- `scripts/create_backup_manifest.ps1`
- `scripts/export_active_power_plan.ps1`
- `scripts/backup_msi_afterburner_configs.ps1`
- `scripts/generate_restore_scripts.ps1`
- `scripts/sandbox_powercfg_apply_test.ps1`
- `scripts/cleanup_sandbox_power_plan.ps1`
- `scripts/collect_phase4_snapshot.ps1`
- `scripts/validate_phase4.ps1`
- `scripts/run_app.ps1`
- `scripts/capture_page_photos.py`
- `scripts/read_librehardwaremonitor_sensors.ps1`

Page photos:

- `page_photos/01_dashboard.png`
- `page_photos/02_cpu_presets.png`
- `page_photos/03_gpu_profiles.png`
- `page_photos/04_sensors.png`
- `page_photos/05_game_automation.png`
- `page_photos/06_auto_tuning.png`
- `page_photos/07_fan_experimental.png`
- `page_photos/08_logs.png`
- `page_photos/09_settings.png`

Restore preview scripts:

- `restore/generated_scripts/restore_power_plan_preview.ps1`
- `restore/generated_scripts/restore_msi_afterburner_files_preview.ps1`
- `restore/generated_scripts/restore_app_config_preview.ps1`

Docs:

- `docs/phase4_safety_boundary.md`
- `docs/backup_manifest_design.md`
- `docs/restore_manifest_design.md`
- `docs/sandbox_apply_test_design.md`
- `docs/msi_backup_restore_notes.md`
- `docs/power_plan_backup_restore_notes.md`
- `docs/blocked_actions.md`
- `docs/phase5_recommendation.md`

## Backup Manifest Summary

- Manifest path: `backups/backup_manifest_latest.json`
- Generated: `2026-06-15T11:40:55`
- Source phase: `PHASE_3_CONTROL_SURFACE_COMPLETENESS_AND_PRESET_EDITING`
- MSI files copied: `14`
- App config/preset/restore JSON files copied: `18`
- CPU readable values snapshot: present
- Active power plan query snapshot: present
- NVIDIA telemetry snapshot from Phase 1: present
- Process snapshot from Phase 1: present
- Phase 5 backup sufficient: `false`

## Power Plan Backup Summary

- Active plan name: `AERO24_MODERATE_AGGRESSIVE_GAMING`
- Active plan GUID: `692ee1d0-ffc2-4c47-91b3-2a4814f3964e`
- Full `powercfg /query SCHEME_CURRENT` snapshot: captured.
- `powercfg /query SCHEME_CURRENT SUB_PROCESSOR` snapshot: captured.
- Structured CPU values snapshot: captured.
- `.pow` export: blocked.
- Export failure: `Unable to perform operation. An unexpected error (0x522) has occurred: A required privilege is not held by the client.`

The `.pow` export file path is recorded, but the file is zero bytes and is not treated as a valid backup.

## MSI Backup Summary

- MSI Afterburner executable: `C:\Program Files (x86)\MSI Afterburner\MSIAfterburner.exe`
- MSI install folder: `C:\Program Files (x86)\MSI Afterburner`
- Backup manifest: `backups/msi_afterburner/msi_backup_manifest.json`
- Copied files: `14`
- Original MSI files modified: `false`
- Hashes recorded for source and destination files.

Backed up file groups include main config files, OEM files, profile-slot files, and device-specific profile files discovered in the MSI Afterburner profiles folder.

## App Config Backup Summary

Phase 4 backed up JSON config, preset, and restore files into `backups/app_config/`.

This includes copied Phase 3/Phase 4 control-surface config files, preset files, apply-gate config, backup policy, sandbox policy, and restore manifest JSON where present.

## Restore Manifest Summary

- Restore manifest: `restore/restore_manifest_latest.json`
- Restore mode: preview-only.
- MSI file restore: available as future preview, not executed.
- App config restore: available as future preview, not executed.
- Power plan restore: blocked until a valid `.pow` export exists.

Generated restore scripts are preview-only and do not copy files back, import a plan, set a plan active, or run automatically.

## Sandbox Apply Test Summary

The only write test performed in Phase 4 was against a temporary inactive cloned power scheme.

- Sandbox test ran: `true`
- Sandbox test passed: `true`
- Sandbox scheme was active: `false`
- EPP AC test write on clone: verified
- System cooling policy AC test write on clone: verified
- Sandbox values restored inside clone before deletion: yes
- Sandbox plan deleted: `true`
- Active plan GUID unchanged: `true`

No write command targeted `SCHEME_CURRENT`, and no write command targeted the active plan GUID.

## Apply Gate Status

- `backups_exist`: `true`
- `active_power_plan_exported`: `false`
- `current_values_snapshot_exists`: `true`
- `restore_manifest_exists`: `true`
- `sandbox_powercfg_write_test_passed`: `true`
- `msi_configs_backed_up`: `true`
- `msi_slot_mapping_verified`: `false`
- `active_plan_write_enabled`: `false`
- `msi_profile_apply_enabled`: `false`
- `fan_write_enabled`: `false`
- `ec_write_enabled`: `false`
- `automation_apply_enabled`: `false`

Phase 5 must not enable active-plan writes until the missing active power plan export gate is resolved.

## App UI Updates

The Phase 4 app is now branded `AeroTune` and keeps nine tabs:

- Dashboard
- CPU Presets
- GPU Profiles
- Sensors
- Game Automation
- Auto Tuning
- Fan / Experimental
- Logs
- Settings

Phase 4 additions show backup status, restore-manifest status, sandbox result, active-plan before/after status, MSI backup status, and apply-gate status.

The previous table-heavy editing surfaces were replaced with app-side form editors:

- CPU presets use dropdowns for boost mode and system cooling policy, with numeric/text editors for other values.
- GPU profile slots use editable cards for labels, intent, risk, notes, and verification state.
- Game automation rules use form cards for process names, command-line filters, future preset mapping, and disabled automation state.
- Auto Tuning uses editable experiment-plan cards while keeping all run controls locked for later phases.

Read-only tables remain where they fit: manifests, logs, sensor lists, read-only command output, and process matches.

The Sensors tab now reads:

- NVIDIA telemetry through `nvidia-smi`.
- PresentMon candidates with opt-in capture controls. Capture is not started automatically.
- LibreHardwareMonitor sensors through a read-only PowerShell probe. The latest successful probe used `C:\Program Files (x86)\RivaTuner Statistics Server\Plugins\Client\LHMDataProvider\LibreHardwareMonitorLib.dll` and returned `139` sensor readings.

The app status bar keeps basic GPU, VRAM, CPU/LHM, and FPS status visible across all tabs.

## Validation Result

- Validation timestamp: `2026-06-15T12:16:02`
- Total checks: `168`
- Failed checks: `0`
- PySide6 offscreen construction: passed
- App tab count: `9`
- AeroTune UI contract: passed
- Static safety scans: passed

The validation treats the failed `.pow` export as an explicit blocker, not a successful backup.

## Known Issues

- Active power plan `.pow` export requires a privilege not available in this non-admin session.
- Phase 5 readiness is intentionally false until the active power plan export is completed or replaced by an approved equivalent.
- MSI profile slot mapping remains unverified.
- MSI profile apply remains blocked.
- Fan and EC control remain research-only and blocked.
- NVIDIA write paths remain blocked.

## Phase 5 Recommendation

Manual MSI profile slot verification and first real guarded active CPU preset apply/restore test. Require successful Phase 4 backup/restore gates first. Verify MSI slot mapping manually with telemetry before allowing app-launched MSI profiles. For CPU, allow one explicitly selected low/medium-risk setting apply to the active plan with immediate verification and one-click restore. No fan control or EC writes yet.
