# Guarded CPU Apply Design

Phase 5 implements the plumbing for a future guarded CPU apply path, but the real active-plan apply path remains disabled.

Required gates:

- `active_power_plan_exported`
- `current_values_snapshot_exists`
- `restore_manifest_exists`
- `sandbox_powercfg_write_test_passed`
- `cpu_restore_available`
- `active_plan_write_enabled`
- `cpu_guarded_apply_enabled`

In Phase 5, `active_plan_write_enabled` and `cpu_guarded_apply_enabled` remain `false`. The active power plan export failed with error `0x522`, so there is not yet a proven active-plan restore file.

Future apply behavior should begin with one explicit low/medium-risk CPU setting only. It should capture before values, apply one setting, verify after values, and display immediate restore instructions. Broad multi-setting active-plan apply is intentionally not implemented here.

