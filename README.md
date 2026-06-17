# AeroTune

AeroTune is the current name of the AERO X16 / RTX 5070 laptop optimization control app subproject.

The latest usable app lives in:

`PHASE_8_SENSOR_PROVIDER_FIXES_AND_UI_REFINEMENT`

Phase 8 remains telemetry/UI-only. It fixes sensor-provider interpretation, adds explicit validity states, treats CPU temperature 0 C as invalid, treats CPU power 0 W and CPU clock 0 MHz as stale-zero/unavailable when CPU load is nonzero, improves GpuNvidia/GpuAmd classification, and refines the Sensors page. It does not apply MSI Afterburner profiles, change NVIDIA driver settings, change fan modes, access embedded-controller write paths, create scheduled tasks, write registry settings, automate game-triggered apply, or change the active power plan.

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

The current Phase 8 runner is also available directly:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\PHASE_8_SENSOR_PROVIDER_FIXES_AND_UI_REFINEMENT\scripts\run_app.ps1
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

Basic GPU, VRAM, CPU/LHM, fan availability, and FPS status is always visible in the app status bar. Phase 8 also shows every normalized raw sensor in the Sensors tab with validity, validity reason, provider, and subcategory columns.

## Page Photos

Screenshots for quick inspection are mirrored at the repository root in:

`page_photos`

The Phase 8 source copy is also in:

`PHASE_8_SENSOR_PROVIDER_FIXES_AND_UI_REFINEMENT\page_photos`

Regenerate them with:

```powershell
python .\PHASE_8_SENSOR_PROVIDER_FIXES_AND_UI_REFINEMENT\scripts\capture_page_photos.py
```

## Validation

The Phase 8 validator checks required files, JSON parsing, Python compilation/imports, PySide6 construction, sensor validity behavior, AeroTune UI contracts, LHM headline parsing, screenshots, apply gates, and blocked write patterns:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\PHASE_8_SENSOR_PROVIDER_FIXES_AND_UI_REFINEMENT\scripts\validate_phase8.ps1
```

Latest known result: `160` checks, `0` failures.

## Phase History

- `PHASE_1_EXPLORATION`: read-only discovery foundation.
- `PHASE_2_APP_SKELETON_READONLY_DRYRUN`: first PySide6 read-only app skeleton.
- `PHASE_3_CONTROL_SURFACE_COMPLETENESS_AND_PRESET_EDITING`: complete control surface and app-side preset editing.
- `PHASE_4_BACKUP_RESTORE_FOUNDATION_AND_SANDBOXED_APPLY_TESTS`: backup/restore foundation, sandboxed inactive power-plan write test, modern AeroTune UI, screenshots, and sensor integration.
- `PHASE_5_GUARDED_CPU_APPLY_FOUNDATION_AND_UI_REFINEMENT`: guarded CPU apply foundation, AC/DC CPU editor, power plan visibility, process command-line matching, PresentMon cleanup, LHM headline fix, and validation.
- `PHASE_6_SENSOR_COMMAND_CENTER_AND_TELEMETRY_VISUALS`: telemetry command center, sensor normalization, CPU temp diagnostics, raw sensor explorer, favorites, screenshots, and validation.
- `PHASE_7_SENSOR_UI_POLISH_AND_PRO_TUNING_LAYOUT`: professional Sensors page polish with hero metric cards, status pills, hardware panels, and cleaner diagnostics.
- `PHASE_8_SENSOR_PROVIDER_FIXES_AND_UI_REFINEMENT`: sensor validity model, CPU partial-provider handling, LHM multi-sample probe, GPU classification fixes, refined Sensors UI, screenshots, and validation.
