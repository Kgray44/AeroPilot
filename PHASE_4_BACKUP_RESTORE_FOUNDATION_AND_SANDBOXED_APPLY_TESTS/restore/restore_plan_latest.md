# Phase 4 Restore Plan

Restore scripts are preview-only in Phase 4.

## power_plan.active_export
- Source: C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_4_BACKUP_RESTORE_FOUNDATION_AND_SANDBOXED_APPLY_TESTS\backups\power_plans\active_power_plan_20260615-114052.pow
- Destination: Windows power plan store
- Preview command: powercfg [preview-only] /import <backup.pow>
- Restore proven: False

## msi_afterburner.files
- Source: C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_4_BACKUP_RESTORE_FOUNDATION_AND_SANDBOXED_APPLY_TESTS\backups\msi_afterburner\files
- Destination: C:\Program Files (x86)\MSI Afterburner
- Preview command: Copy backed-up MSI files to original paths
- Restore proven: False

## app_config.json_files
- Source: C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_4_BACKUP_RESTORE_FOUNDATION_AND_SANDBOXED_APPLY_TESTS\backups\app_config
- Destination: C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_4_BACKUP_RESTORE_FOUNDATION_AND_SANDBOXED_APPLY_TESTS
- Preview command: Copy app JSON backups into Phase 4 config/presets
- Restore proven: False
