# AeroTune

AeroTune is the current name of the AERO X16 / RTX 5070 laptop optimization control app subproject.

The latest usable app lives in:

`PHASE_4_BACKUP_RESTORE_FOUNDATION_AND_SANDBOXED_APPLY_TESTS`

Phase 4 remains safety-gated. It builds the backup/restore foundation, keeps active laptop tuning protected, and adds a cleaner PySide6 UI with editable app-side presets, read-only telemetry, and dry-run apply previews. It does not apply MSI Afterburner profiles, change NVIDIA driver settings, change fan modes, write EC registers, create scheduled tasks, write registry settings, or change the active power plan.

## Launch

From the Phase 4 folder:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\run_app.ps1
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

Basic GPU, VRAM, CPU/LHM, and FPS status is always visible in the app status bar.

## Page Photos

Screenshots for quick inspection are mirrored at the repository root in:

`page_photos`

The Phase 4 source copy is also in:

`PHASE_4_BACKUP_RESTORE_FOUNDATION_AND_SANDBOXED_APPLY_TESTS\page_photos`

Regenerate them with:

```powershell
python .\scripts\capture_page_photos.py
```

## Validation

The Phase 4 validator checks required files, JSON parsing, Python compilation/imports, PySide6 construction, AeroTune UI contracts, backup/restore artifacts, sandbox power plan safety, apply gates, and blocked write patterns:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\validate_phase4.ps1
```

Latest known result: `168` checks, `0` failures.

## Phase History

- `PHASE_1_EXPLORATION`: read-only discovery foundation.
- `PHASE_2_APP_SKELETON_READONLY_DRYRUN`: first PySide6 read-only app skeleton.
- `PHASE_3_CONTROL_SURFACE_COMPLETENESS_AND_PRESET_EDITING`: complete control surface and app-side preset editing.
- `PHASE_4_BACKUP_RESTORE_FOUNDATION_AND_SANDBOXED_APPLY_TESTS`: backup/restore foundation, sandboxed inactive power-plan write test, modern AeroTune UI, screenshots, and sensor integration.
