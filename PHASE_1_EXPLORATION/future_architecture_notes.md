# Future Architecture Notes

## Preferred Stack

- Python
- PySide6 GUI
- JSON preset files
- PowerShell helper scripts for Windows-specific discovery and guarded writes
- Subprocess calls for powercfg, 
vidia-smi, MSI Afterburner, and PresentMon
- Optional LibreHardwareMonitor integration later
- Optional NVML integration later

## Proposed App Layout

- pp/: PySide6 application package
- pp/core/: preset schema, risk labels, logging, state snapshots
- pp/adapters/: powercfg, nvidia-smi, MSI Afterburner, PresentMon, LibreHardwareMonitor/NVML adapters
- pp/ui/: dashboard widgets and tabs
- presets/: JSON CPU/GPU/game presets
- logs/: timestamped app logs and benchmark session folders
- estore/: generated restore manifests and panic restore scripts
- scripts/: PowerShell helpers kept dry-run by default

## Suggested Tabs

- Dashboard
- CPU Presets
- GPU Profiles
- Sensors / Telemetry
- Game Automation
- Auto Tuning
- Fan Control / Experimental
- Logs
- Settings / Safety

## Critical Future Features

- Save current state
- Apply preset
- Restore previous state
- Panic restore
- Export report
- Run benchmark/tuning session
- Compare preset results
- Auto-apply on game launch
- Auto-restore on game exit
- Danger labels and tooltips
- Require confirmation for dangerous actions
- Require admin mode for advanced writes
- Never silently apply high-risk changes

## Safety Model

The backend should own truth. The GUI should display capabilities, risk labels, and current state returned by adapters, not invent state locally. Any apply-capable adapter should support --dry-run by default and require an explicit --apply or equivalent confirmation path.

High-risk writes should be gated by:

- Current state snapshot
- Backup manifest
- Restore plan
- User confirmation
- Admin check when required
- Post-apply verification
