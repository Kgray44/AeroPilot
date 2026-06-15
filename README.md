# AeroTune

AeroTune is the current name of the AERO X16 / RTX 5070 laptop optimization control app subproject.

The latest usable app lives in:

`PHASE_6_SENSOR_COMMAND_CENTER_AND_TELEMETRY_VISUALS`

Phase 6 remains telemetry/UI-only. It upgrades the Sensors tab into a sensor command center with overview metric cards, grouped panels, an all-sensors raw explorer, CPU temperature diagnostics, sensor favorites, and normalized bottom-bar telemetry. It does not apply MSI Afterburner profiles, change NVIDIA driver settings, change fan modes, access embedded-controller write paths, create scheduled tasks, write registry settings, automate game-triggered apply, or change the active power plan.

## Launch

From the repository/app root:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\Start-AeroTune.ps1
```

The top-level launcher automatically selects the newest `PHASE_*` folder that contains `scripts\run_app.ps1`, so future phases can become the default without changing the launch command.

Useful checks:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\Start-AeroTune.ps1 -DryRun
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\Start-AeroTune.ps1 -ListPhases
```

The current Phase 6 runner is still available directly:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\PHASE_6_SENSOR_COMMAND_CENTER_AND_TELEMETRY_VISUALS\scripts\run_app.ps1
```

## Current UI

AeroTune now has nine tabs:

- Dashboard
- CPU Presets
- GPU Profiles
- Sensors
- Game Automation
- Auto Tuning
- Fan / Experimental
- Logs
- Settings

The app uses form-based editors for app-side CPU presets, GPU profile labels, game rules, and auto-tuning plans. Tables are kept for read-only data, logs, manifests, and complete sensor listings.

## Sensor Support

Read-only sensor surfaces currently include:

- NVIDIA telemetry through `nvidia-smi`
- PresentMon candidate discovery plus opt-in capture controls
- LibreHardwareMonitor sensor reads through a discovered DLL and a read-only PowerShell probe

Basic GPU, VRAM, CPU/LHM, fan availability, and FPS status is always visible in the app status bar. Phase 6 also shows every normalized raw sensor in the Sensors tab.

## Page Photos

Screenshots for quick inspection are mirrored at the repository root in:

`page_photos`

The Phase 6 source copy is also in:

`PHASE_6_SENSOR_COMMAND_CENTER_AND_TELEMETRY_VISUALS\page_photos`

Regenerate them with:

```powershell
python .\PHASE_6_SENSOR_COMMAND_CENTER_AND_TELEMETRY_VISUALS\scripts\capture_page_photos.py
```

## Validation

The Phase 6 validator checks required files, JSON parsing, Python compilation/imports, PySide6 construction, sensor normalizer behavior, AeroTune UI contracts, LHM headline parsing, screenshots, apply gates, and blocked write patterns:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\PHASE_6_SENSOR_COMMAND_CENTER_AND_TELEMETRY_VISUALS\scripts\validate_phase6.ps1
```

Latest known result: `145` checks, `0` failures.

## Phase History

- `PHASE_1_EXPLORATION`: read-only discovery foundation.
- `PHASE_2_APP_SKELETON_READONLY_DRYRUN`: first PySide6 read-only app skeleton.
- `PHASE_3_CONTROL_SURFACE_COMPLETENESS_AND_PRESET_EDITING`: complete control surface and app-side preset editing.
- `PHASE_4_BACKUP_RESTORE_FOUNDATION_AND_SANDBOXED_APPLY_TESTS`: backup/restore foundation, sandboxed inactive power-plan write test, modern AeroTune UI, screenshots, and sensor integration.
- `PHASE_5_GUARDED_CPU_APPLY_FOUNDATION_AND_UI_REFINEMENT`: guarded CPU apply foundation, AC/DC CPU editor, power plan visibility, process command-line matching, PresentMon cleanup, LHM headline fix, and validation.
- `PHASE_6_SENSOR_COMMAND_CENTER_AND_TELEMETRY_VISUALS`: telemetry command center, sensor normalization, CPU temp diagnostics, raw sensor explorer, favorites, screenshots, and validation.
