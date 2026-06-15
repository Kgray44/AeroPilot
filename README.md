# AeroTune

AeroTune is the current name of the AERO X16 / RTX 5070 laptop optimization control app subproject.

The latest usable app lives in:

`PHASE_5_GUARDED_CPU_APPLY_FOUNDATION_AND_UI_REFINEMENT`

Phase 5 remains safety-gated. It adds guarded CPU apply foundation plumbing, a cleaner AC/DC CPU preset editor, read-only power plan management visibility, command-line game process matching, PresentMon lifecycle cleanup, and improved LibreHardwareMonitor headline parsing. It does not apply MSI Afterburner profiles, change NVIDIA driver settings, change fan modes, access embedded-controller write paths, create scheduled tasks, write registry settings, or change the active power plan.

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

The current Phase 5 runner is still available directly:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\PHASE_5_GUARDED_CPU_APPLY_FOUNDATION_AND_UI_REFINEMENT\scripts\run_app.ps1
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

The app uses form-based editors for app-side CPU presets, GPU profile labels, game rules, and auto-tuning plans. Tables are kept for read-only data, logs, manifests, and sensor listings.

## Sensor Support

Read-only sensor surfaces currently include:

- NVIDIA telemetry through `nvidia-smi`
- PresentMon candidate discovery plus opt-in capture controls
- LibreHardwareMonitor sensor reads through a discovered DLL and a read-only PowerShell probe

Basic GPU, VRAM, CPU/LHM, load, fan availability, and FPS status is always visible in the app status bar.

## Page Photos

Screenshots for quick inspection are mirrored at the repository root in:

`page_photos`

The Phase 5 source copy is also in:

`PHASE_5_GUARDED_CPU_APPLY_FOUNDATION_AND_UI_REFINEMENT\page_photos`

Regenerate them with:

```powershell
python .\scripts\capture_page_photos.py
```

## Validation

The Phase 5 validator checks required files, JSON parsing, Python compilation/imports, PySide6 construction, AeroTune UI contracts, LHM headline parsing, backup/restore artifacts, apply gates, screenshots, and blocked write patterns:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\PHASE_5_GUARDED_CPU_APPLY_FOUNDATION_AND_UI_REFINEMENT\scripts\validate_phase5.ps1
```

Latest known result: `122` checks, `0` failures.

## Phase History

- `PHASE_1_EXPLORATION`: read-only discovery foundation.
- `PHASE_2_APP_SKELETON_READONLY_DRYRUN`: first PySide6 read-only app skeleton.
- `PHASE_3_CONTROL_SURFACE_COMPLETENESS_AND_PRESET_EDITING`: complete control surface and app-side preset editing.
- `PHASE_4_BACKUP_RESTORE_FOUNDATION_AND_SANDBOXED_APPLY_TESTS`: backup/restore foundation, sandboxed inactive power-plan write test, modern AeroTune UI, screenshots, and sensor integration.
- `PHASE_5_GUARDED_CPU_APPLY_FOUNDATION_AND_UI_REFINEMENT`: guarded CPU apply foundation, AC/DC CPU editor, power plan visibility, process command-line matching, PresentMon cleanup, LHM headline fix, and validation.
