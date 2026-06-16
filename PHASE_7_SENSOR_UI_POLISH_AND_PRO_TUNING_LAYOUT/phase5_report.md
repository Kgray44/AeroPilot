# Phase 5 Report

## Summary

Phase 5 created the AeroTune guarded CPU apply foundation and UI refinement layer from the completed Phase 4 app. The app remains safe by default: real active power plan writes are blocked, MSI profile launching is blocked, and high-risk hardware write paths remain unavailable.

## What Changed From Phase 4

- Copied the Phase 4 app into `PHASE_5_GUARDED_CPU_APPLY_FOUNDATION_AND_UI_REFINEMENT`.
- Added Phase 5 backup/export scripts, restore preview generation, and validation.
- Redesigned the CPU Presets page with a global AC/DC selector.
- Added current-vs-desired CPU setting status and selected-side dry-run previews.
- Added read-only power plan listing plus preview-only create/set controls.
- Hardened process detection with command-line matching through CIM/WMI.
- Improved PresentMon lifecycle cleanup and running-state reporting.
- Fixed LibreHardwareMonitor headline parsing so the bottom bar uses a selected CPU temperature sensor and cannot show `CPU CPU temp n/a`.

## Safety Boundary

Phase 5 does not enable real active CPU apply. The app may read state and show dry-run previews. The following remain blocked: MSI profile launches, NVIDIA writes, fan/EC writes, service control, startup changes, scheduled tasks, registry writes, and automatic game-triggered apply.

## Backup And Export Status

- Backup manifest: `backups/backup_manifest_latest.json`
- Restore manifest: `restore/restore_manifest_latest.json`
- CPU values snapshot: present.
- Phase 4 sandbox write test: passed and carried forward.
- MSI backup: continued from Phase 4.
- Active power plan export: failed with Windows error `0x522` because the current session was not elevated.

The `.pow` export file is zero bytes and is not treated as a valid restore path.

## CPU AC/DC Selector UI

The CPU page now shows a top-level `Power source view` selector. AC view shows only AC desired values. DC view shows only DC desired values. Switching preserves edits in memory and refreshes the selected-side dry-run preview.

Each card shows risk, enabled state, current value, desired value, difference status, restore status, and apply-blocked status.

## Guarded CPU Apply State

Guarded CPU apply is foundation-only. These gates are intentionally false:

- `cpu_guarded_apply_enabled`
- `active_plan_write_enabled`

The active power plan export blocker keeps real active-plan writes unavailable.

## Telemetry And Sensor Updates

LibreHardwareMonitor headline selection now prefers CPU hardware temperature sensors, ranks package/core/max style names, falls back to highest valid CPU temperature, and reports load/fan data when available. Missing fan RPM is shown as `Fan unavailable`, not as a failure.

PresentMon capture remains user-started only and is cleaned up when AeroTune closes.

## Game Detection Updates

Game Automation now reads process command lines where available, applies command-line filters, warns on broad targets, and keeps automation apply disabled.

## Known Issues

- Active power plan export requires elevation or another approved restore path before real CPU apply can be enabled.
- MSI slot mapping remains unverified and app-launched profile commands remain blocked.
- Fan/EC control remains research-only.

## Validation Result

`scripts/validate_phase5.ps1` passed on 2026-06-15T18:09:17 with 122 checks and 0 failures.

## Phase 6 Recommendation

Manual MSI profile slot verification and first real guarded active CPU preset apply/restore test. Require successful backup/restore gates first. Verify MSI slot mapping manually with telemetry before allowing app-launched MSI profiles. For CPU, allow one explicitly selected low/medium-risk setting apply to the active plan with immediate verification and one-click restore. No fan control or EC writes yet.
