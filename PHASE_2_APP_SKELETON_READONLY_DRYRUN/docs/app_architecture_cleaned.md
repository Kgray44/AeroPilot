# App Architecture Cleaned

## Goal

Build a Python and PySide6 desktop app that displays AERO X16 tuning state from trusted adapters. Phase 2 is read-only and dry-run only.

## Clean Project Layout

- `app/core`: paths, configuration, risk model, command runner, dry-run previews, state snapshots, logging, and preset validation.
- `app/adapters`: Phase 1 data, powercfg reads, nvidia-smi reads, MSI Afterburner dry-run previews, PresentMon candidate discovery, process detection, LibreHardwareMonitor metadata, and Gigabyte/GCC metadata.
- `app/ui`: tab widgets and the main window.
- `config`: app settings and detected tool path cache.
- `presets`: preview-only JSON preset examples.
- `logs`: app logs and command runner JSONL.
- `raw_outputs`: read-only snapshot exports and validation JSON.
- `restore`: future restore manifests. Empty in Phase 2 by design.

## Adapter Rule

Adapters return structured state. The GUI displays that state. The GUI does not invent backend truth and does not apply hidden state changes.

## Phase 2 Tabs

- Dashboard
- CPU Presets
- GPU Profiles
- Sensors / Telemetry
- Game Automation
- Auto Tuning
- Fan Control / Experimental
- Logs
- Settings / Safety

## Phase 3 Expansion Points

- Backup and restore manifest service
- Power plan export/clone service
- MSI profile backup service
- Manual MSI slot verification workflow
- One or two explicitly approved CPU setting apply tests with immediate restore
