# Safety Model

Phase 2 safety mode is `READ-ONLY / DRY-RUN`.

## Allowed

- Read Phase 1 JSON and markdown artifacts.
- Run read-only commands such as `powercfg /query` and nvidia-smi query calls.
- Enumerate running processes.
- Show dry-run previews for future CPU and MSI profile actions.
- Write logs, snapshots, validation outputs, and reports inside the Phase 2 folder.

## Blocked

- Applying MSI Afterburner profiles.
- Editing MSI Afterburner configuration or profile files.
- Changing power plans or CPU settings.
- Changing NVIDIA clocks, power limits, persistence mode, or driver settings.
- Changing fan modes or embedded controller values.
- Starting or stopping services.
- Creating scheduled tasks or startup entries.
- Writing registry settings.

## Future Apply Gate

Future apply-capable functions must require:

- Explicit phase approval.
- Backup manifest.
- Restore method.
- Admin check when needed.
- Dry-run preview.
- User confirmation.
- Post-apply verification.

No high-risk action may be silently applied.
