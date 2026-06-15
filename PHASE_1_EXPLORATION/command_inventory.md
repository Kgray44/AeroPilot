# Command Inventory

Commands are grouped by safety status. Phase 1 only ran read-only discovery commands and detector scripts.

## Read-only Commands Run In Phase 1

- `C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\scripts\detect_msi_afterburner.ps1 -PhaseRoot C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION`
- `C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\scripts\detect_powercfg_settings.ps1 -PhaseRoot C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION`
- `C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\scripts\detect_nvidia_telemetry.ps1 -PhaseRoot C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION`
- `C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\scripts\detect_presentmon.ps1 -PhaseRoot C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION`
- `C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\scripts\detect_librehardwaremonitor.ps1 -PhaseRoot C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION`
- `C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\scripts\detect_gigabyte_controls.ps1 -PhaseRoot C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION`
- `C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\scripts\detect_process_targets.ps1 -PhaseRoot C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION`
- `powercfg.exe /getactivescheme`
- `powercfg.exe /list`
- `powercfg.exe /query SCHEME_CURRENT`
- `powercfg.exe /query SCHEME_CURRENT SUB_PROCESSOR`
- `powercfg.exe /qh SCHEME_CURRENT SUB_PROCESSOR`
- `powercfg.exe /aliases`
- `powercfg.exe /query SCHEME_CURRENT 54533251-82be-4824-96c1-47b60b740d00 be337238-0d82-4146-a960-4f3749d470c7`
- `powercfg.exe /query SCHEME_CURRENT 54533251-82be-4824-96c1-47b60b740d00 45bcc044-d885-43e2-8605-ee0ec6e96b59`
- `powercfg.exe /query SCHEME_CURRENT 54533251-82be-4824-96c1-47b60b740d00 36687f9e-e3a5-4dbf-b1dc-15eb381c6863`
- `powercfg.exe /query SCHEME_CURRENT 54533251-82be-4824-96c1-47b60b740d00 893dee8e-2bef-41e0-89c6-b55d0929964c`
- `powercfg.exe /query SCHEME_CURRENT 54533251-82be-4824-96c1-47b60b740d00 bc5038f7-23e0-4960-96da-33abaf5935ec`
- `powercfg.exe /query SCHEME_CURRENT 54533251-82be-4824-96c1-47b60b740d00 94d3a615-a899-4ac5-ae2b-e4d8f634367f`
- `powercfg.exe /query SCHEME_CURRENT 54533251-82be-4824-96c1-47b60b740d00 75b0ae3f-bce0-45a7-8c89-c9611c25e100`
- `powercfg.exe /query SCHEME_CURRENT 54533251-82be-4824-96c1-47b60b740d00 0cc5b647-c1df-4637-891a-dec35c318583`
- `powercfg.exe /query SCHEME_CURRENT 54533251-82be-4824-96c1-47b60b740d00 ea062031-0e34-4ff1-9b6d-eb1059334028`
- `powercfg.exe /query SCHEME_CURRENT 54533251-82be-4824-96c1-47b60b740d00 5d76a2ca-e8c0-402f-a133-2158492d58ad`
- `powercfg.exe /query SCHEME_CURRENT 54533251-82be-4824-96c1-47b60b740d00 7f2f5cfa-f10c-4823-b5e1-e93ae85f46b5`
- `powercfg.exe /query SCHEME_CURRENT 54533251-82be-4824-96c1-47b60b740d00 06cadf0e-64ed-448a-8927-ce7bf90eb35d`
- `powercfg.exe /query SCHEME_CURRENT 54533251-82be-4824-96c1-47b60b740d00 12a0ab44-fe28-4fa9-b3bd-4b64f44960a6`
- `C:\WINDOWS\system32\nvidia-smi.exe`
- `C:\WINDOWS\system32\nvidia-smi.exe --help-query-gpu`
- `C:\WINDOWS\system32\nvidia-smi.exe --query-gpu=name,driver_version,cuda_version,utilization.gpu,utilization.memory,memory.total,memory.used,memory.free,temperature.gpu,power.draw,power.limit,clocks.current.graphics,clocks.current.memory --format=csv,noheader,nounits`
- `C:\WINDOWS\system32\nvidia-smi.exe --query-gpu=name,driver_version,utilization.gpu,utilization.memory,memory.total,memory.used,memory.free,temperature.gpu,power.draw,power.limit,clocks.current.graphics,clocks.current.memory --format=csv,noheader,nounits`
- `C:\WINDOWS\system32\nvidia-smi.exe --query-compute-apps=pid,process_name,used_memory --format=csv`
- `C:\WINDOWS\system32\nvidia-smi.exe pmon -c 1`
- `C:\Program Files\AMD\CNext\CNext\PresentMon-x64.exe --help`
- `C:\Program Files\AMD\CNext\CNext\PresentMon-x64.exe -h`
- `C:\Program Files\AMD\CNext\CNext\PresentMon-x64.exe --version`

## Dry-run Templates

- `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\run_phase1_exploration.ps1`
- Future apply helpers should default to `--dry-run` or no-op preview mode.
- Read-only capability check: `"C:\Program Files\AMD\CNext\CNext\PresentMon-x64.exe" --help` - Help command attempted with timeout.
- Future CSV capture by process: `"C:\Program Files\AMD\CNext\CNext\PresentMon-x64.exe" --process_name <game.exe> --output_file "<session.csv>"` - Template only. Not executed in Phase 1.
- Future timed capture: `"C:\Program Files\AMD\CNext\CNext\PresentMon-x64.exe" --process_name <game.exe> --timed 60 --output_file "<session.csv>"` - Template only. Syntax must be verified against installed PresentMon version.

## Future Apply Commands, Not Run In Phase 1

- MSI profile slot 1: `"C:\Program Files (x86)\MSI Afterburner\MSIAfterburner.exe" -Profile1` - not run in Phase 1.
- MSI profile slot 2: `"C:\Program Files (x86)\MSI Afterburner\MSIAfterburner.exe" -Profile2` - not run in Phase 1.
- MSI profile slot 3: `"C:\Program Files (x86)\MSI Afterburner\MSIAfterburner.exe" -Profile3` - not run in Phase 1.
- MSI profile slot 4: `"C:\Program Files (x86)\MSI Afterburner\MSIAfterburner.exe" -Profile4` - not run in Phase 1.
- MSI profile slot 5: `"C:\Program Files (x86)\MSI Afterburner\MSIAfterburner.exe" -Profile5` - not run in Phase 1.
- CPU AC write template: `powercfg /setacvalueindex <scheme_guid> SUB_PROCESSOR <setting_guid> <value>` - not run in Phase 1.
- CPU DC write template: `powercfg /setdcvalueindex <scheme_guid> SUB_PROCESSOR <setting_guid> <value>` - not run in Phase 1.
- Activate plan template: `powercfg /setactive <scheme_guid>` - not run in Phase 1.
- Scheduled task/startup automation templates are intentionally not created in Phase 1.
- Fan/EC write commands are intentionally absent. Treat as dangerous research only.
