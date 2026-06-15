# AERO X16 Control Center App - Phase 1 Exploration Report

- Generated local: 2026-06-14T21:10:07
- App root: `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP`
- Phase root: `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION`
- Safety boundary: exploration only; no tuning changes applied.

## Summary

Phase 1 created an isolated app subproject and read-only discovery foundation for a future AERO X16 optimization control app. The run queried installed tools, powercfg settings, NVIDIA telemetry, optional telemetry tools, Gigabyte/GCC surfaces, and current process targets. It wrote raw outputs and structured JSON for Phase 2 app skeleton work.

No CPU boost, EPP, min/max processor state, active power plan, NVIDIA setting, MSI profile, MSI config file, fan mode, service, scheduled task, startup entry, registry setting, or EC register was changed.

## What Was Discovered

- MSI Afterburner installed: True
- MSI Afterburner path: `C:\Program Files (x86)\MSI Afterburner\MSIAfterburner.exe`
- RTSS paths found: 1
- MSI profile files found: 8
- Active power plan: `AERO24_MODERATE_AGGRESSIVE_GAMING / 692ee1d0-ffc2-4c47-91b3-2a4814f3964e`
- Processor settings cataloged: 13
- nvidia-smi available: True
- PresentMon found: True
- LibreHardwareMonitor found: True
- Gigabyte/GCC installed entries: 1
- Gigabyte/GCC services discovered: 1
- Process targets seed list: `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\app_probe\process_targets_seed.json`

## Reachability Matrix

| Capability | Reachability | Phase 1 Status | Risk | Owner |
|---|---|---|---|---|
| MSI Afterburner profile launch templates | Likely reachable by launching MSI Afterburner with profile arguments | Dry-run templates only. Not executed. | Medium | MSI Afterburner |
| MSI Afterburner profile/config backup | Discoverable | File metadata read only. | Low | App can back up files later |
| Windows CPU power setting viewer | Reachable through powercfg | Read-only query complete where supported. | Read-only | In-house via powercfg reads |
| Windows CPU power setting writes later | Likely possible for readable settings, not tested | Not executed. | Medium | In-house via powercfg with admin/confirmation |
| NVIDIA telemetry through nvidia-smi | Reachable | Read-only telemetry queries only. | Read-only | In-house subprocess polling |
| NVML Python telemetry later | Planned optional integration | Not tested in Phase 1. | Read-only | Optional Python library |
| PresentMon frame-time capture | Executable found | Help/version attempted only if found. | Low | Optional subprocess tool |
| LibreHardwareMonitor sensors | Files found | File/library discovery only. Not launched. | Read-only | Optional library/tool |
| Gigabyte/GCC discovery | Some OEM surfaces discovered | Read-only process/service/file metadata. | Unknown | Unknown/OEM |
| Game and tool process detection | Reachable through Get-Process | Read-only enumeration only. | Safe | In-house |
| Restore and panic restore framework | Planned; file backups and power plan exports are feasible later | Architecture only. No restore point or backup created outside app folder. | Safe | In-house |

## What Is Reachable

- CPU power setting reads are reachable through `powercfg` for supported settings.
- NVIDIA telemetry is reachable through `nvidia-smi` if marked available above.
- Game/tool process detection is reachable through read-only process enumeration.
- MSI profile launch templates are available if MSI Afterburner was found, but they were not executed.

## What Is Not Reachable Or Missing

- PresentMon is optional; if not found, install planning is deferred to a later user-approved phase.
- LibreHardwareMonitor is optional; if not found, integration is planned but not installed.
- Direct Gigabyte/GCC fan control is not proven safe or reachable by an official API in Phase 1.
- NVML Python integration was not tested; it remains a future optional adapter.

## What Can Be Controlled In-house Later

- CPU preset viewing and eventually guarded powercfg writes.
- JSON preset schema, risk labels, state snapshots, logs, and restore manifests.
- NVIDIA read-only telemetry polling through `nvidia-smi`, and possibly NVML later.
- Game/process detection and automation rules, with auto-apply disabled by default.

## What Requires MSI Afterburner

- GPU voltage/frequency curve profiles should remain owned by MSI Afterburner for now.
- The future app can map friendly GPU preset names to MSI profile slots after manual slot verification.
- Future apply phases must back up MSI config/profile files before launching any profile command.

## What May Require Optional Tools

- PresentMon for FPS/frame-time capture.
- LibreHardwareMonitor for broader CPU/motherboard/fan/voltage sensors.
- NVML Python bindings for cleaner GPU telemetry beyond subprocess polling.

## Dangerous But Possible

- CPU boost, frequency caps, EPP, and core parking writes through powercfg may be possible later, but need backups and explicit confirmation.
- GPU curve/profile application through MSI Afterburner can be powerful but risky if slot mapping is wrong.
- Fan control through OEM files, services, UI automation, or EC writes is high risk or dangerous until proven reversible.
- Startup automation and automatic preset switching should be visible in the GUI but disabled by default.

## Risk Catalog Summary

| Item | Category | Reachability | Risk | Default |
|---|---|---|---|---|
| Processor performance boost mode | CPU boost behavior | Readable via powercfg. Current AC=0; DC=2 | Medium | Disabled for writes; visible as read-only until Phase 2+ confirmation. |
| Processor performance boost policy | CPU boost behavior | Not currently readable by direct powercfg query | Medium | Disabled for writes; visible as read-only until Phase 2+ confirmation. |
| Processor energy performance preference / EPP | CPU power behavior | Readable via powercfg. Current AC=55; DC=0 | Low | Disabled for writes; visible as read-only until Phase 2+ confirmation. |
| Minimum processor state | CPU frequency limits | Readable via powercfg. Current AC=5; DC=100 | Medium | Disabled for writes; visible as read-only until Phase 2+ confirmation. |
| Maximum processor state | CPU frequency limits | Readable via powercfg. Current AC=99; DC=100 | Medium | Disabled for writes; visible as read-only until Phase 2+ confirmation. |
| System cooling policy | Fan control | Readable via powercfg. Current AC=1; DC=1 | Low | Disabled for writes; visible as read-only until Phase 2+ confirmation. |
| Maximum processor frequency | CPU frequency limits | Readable via powercfg. Current AC=3250; DC=0 | High | Disabled for writes; visible as read-only until Phase 2+ confirmation. |
| Processor performance core parking min cores | CPU scheduling/core parking | Not currently readable by direct powercfg query | High | Disabled for writes; visible as read-only until Phase 2+ confirmation. |
| Processor performance core parking max cores | CPU scheduling/core parking | Not currently readable by direct powercfg query | High | Disabled for writes; visible as read-only until Phase 2+ confirmation. |
| Processor idle disable | CPU scheduling/core parking | Not currently readable by direct powercfg query | Dangerous / Experimental | Disabled for writes; visible as read-only until Phase 2+ confirmation. |
| Heterogeneous policy in effect | CPU scheduling/core parking | Not currently readable by direct powercfg query | Unknown | Disabled for writes; visible as read-only until Phase 2+ confirmation. |
| Processor performance increase threshold | CPU boost behavior | Not currently readable by direct powercfg query | High | Disabled for writes; visible as read-only until Phase 2+ confirmation. |
| Processor performance decrease threshold | CPU boost behavior | Not currently readable by direct powercfg query | High | Disabled for writes; visible as read-only until Phase 2+ confirmation. |
| MSI profile slot launch | GPU profile loading | Likely reachable if MSIAfterburner.exe is present | Medium | Disabled until manually verified. |
| GPU voltage/frequency curve profile editing | GPU voltage/frequency curve profile | Requires MSI Afterburner or future manual profile-file research | High | Disabled; require explicit confirmation. |
| NVIDIA telemetry polling | GPU power/clock telemetry | Reachable when nvidia-smi works | Read-only | Enabled for read-only dashboard if available. |
| PresentMon capture | FPS/frame capture | Optional tool; discovered or missing per report | Low | Disabled until user starts a benchmark session. |
| Ping/network logging | Ping/network logging | Known feasible from previous project helpers; not expanded in this app Phase 1 | Safe | Optional per session. |
| Fan mode/control through GCC or OEM paths | Fan control | Unknown; direct control not proven | High | Read-only/disabled. |
| Embedded controller writes | Experimental low-level hardware access | Not attempted; research only | Dangerous / Experimental | Hidden from apply path but visible in Experimental read-only notes. |
| Startup automation | Startup automation | Feasible later through scheduled tasks or startup entries | Medium | Disabled until explicitly configured. |
| Game detection and auto preset switching | Game detection | Readable through process enumeration; automation planned | Low | Detection enabled; auto-apply disabled. |
| Save current state / restore previous state | Restore/backup | Planned; feasible for files and powercfg exports | Safe | Enabled by default before any apply action. |

## Recommended Phase 2

Build the first PySide6 app skeleton with a dashboard, read-only telemetry, MSI profile dry-run buttons, CPU setting viewer, risk labels, and JSON preset schema. No destructive writes yet except optional explicitly-confirmed test commands.

## Raw Outputs

Raw command stdout/stderr, detector logs, detector JSON, and process CSV files are stored under `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs`.

## Detector Run Status

| Detector | Succeeded | Exit Code | Timed Out | Parse Error |
|---|---:|---:|---:|---|
| msi_afterburner | True | 0 | False |  |
| powercfg | True | 0 | False |  |
| nvidia_telemetry | True | 0 | False |  |
| presentmon | True | 0 | False |  |
| librehardwaremonitor | True | 0 | False |  |
| gigabyte_controls | True | 0 | False |  |
| process_targets | True | 0 | False |  |

## Exact Files Created

- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\app_probe\process_targets_seed.json`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\app_probe\README.md`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\command_inventory.md`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\discovered_capabilities.json`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\discovered_paths.json`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\future_architecture_notes.md`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\phase1_exploration_report.json`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\phase1_exploration_report.md`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\gigabyte_controls_detector_result.json`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\gigabyte_controls_log.txt`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\librehardwaremonitor_detector_result.json`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\librehardwaremonitor_log.txt`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\msi_afterburner_detector_result.json`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\msi_afterburner_log.txt`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\nvidia_telemetry_detector_result.json`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\nvidia_telemetry_log.txt`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\nvidia_telemetry_nvidia_smi_help_query_gpu_stderr.txt`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\nvidia_telemetry_nvidia_smi_help_query_gpu_stdout.txt`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\nvidia_telemetry_nvidia_smi_plain_stderr.txt`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\nvidia_telemetry_nvidia_smi_plain_stdout.txt`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\nvidia_telemetry_nvidia_smi_pmon_once_stderr.txt`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\nvidia_telemetry_nvidia_smi_pmon_once_stdout.txt`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\nvidia_telemetry_nvidia_smi_query_compute_apps_stderr.txt`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\nvidia_telemetry_nvidia_smi_query_compute_apps_stdout.txt`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\nvidia_telemetry_nvidia_smi_query_gpu_fallback_stderr.txt`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\nvidia_telemetry_nvidia_smi_query_gpu_fallback_stdout.txt`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\nvidia_telemetry_nvidia_smi_query_gpu_full_stderr.txt`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\nvidia_telemetry_nvidia_smi_query_gpu_full_stdout.txt`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\phase1_orchestrator_detector_gigabyte_controls_stderr.txt`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\phase1_orchestrator_detector_gigabyte_controls_stdout.txt`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\phase1_orchestrator_detector_librehardwaremonitor_stderr.txt`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\phase1_orchestrator_detector_librehardwaremonitor_stdout.txt`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\phase1_orchestrator_detector_msi_afterburner_stderr.txt`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\phase1_orchestrator_detector_msi_afterburner_stdout.txt`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\phase1_orchestrator_detector_nvidia_telemetry_stderr.txt`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\phase1_orchestrator_detector_nvidia_telemetry_stdout.txt`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\phase1_orchestrator_detector_powercfg_stderr.txt`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\phase1_orchestrator_detector_powercfg_stdout.txt`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\phase1_orchestrator_detector_presentmon_stderr.txt`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\phase1_orchestrator_detector_presentmon_stdout.txt`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\phase1_orchestrator_detector_process_targets_stderr.txt`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\phase1_orchestrator_detector_process_targets_stdout.txt`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\phase1_orchestrator_log.txt`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\powercfg_detector_result.json`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\powercfg_log.txt`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\powercfg_powercfg_aliases_stderr.txt`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\powercfg_powercfg_aliases_stdout.txt`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\powercfg_powercfg_get_active_scheme_stderr.txt`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\powercfg_powercfg_get_active_scheme_stdout.txt`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\powercfg_powercfg_list_schemes_stderr.txt`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\powercfg_powercfg_list_schemes_stdout.txt`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\powercfg_powercfg_query_current_full_stderr.txt`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\powercfg_powercfg_query_current_full_stdout.txt`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\powercfg_powercfg_query_current_processor_stderr.txt`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\powercfg_powercfg_query_current_processor_stdout.txt`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\powercfg_powercfg_query_hidden_current_processor_stderr.txt`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\powercfg_powercfg_query_hidden_current_processor_stdout.txt`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\powercfg_setting_cpmaxcores_stderr.txt`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\powercfg_setting_cpmaxcores_stdout.txt`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\powercfg_setting_cpmincores_stderr.txt`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\powercfg_setting_cpmincores_stdout.txt`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\powercfg_setting_heteropolicy_stderr.txt`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\powercfg_setting_heteropolicy_stdout.txt`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\powercfg_setting_idledisable_stderr.txt`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\powercfg_setting_idledisable_stdout.txt`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\powercfg_setting_perfboostmode_stderr.txt`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\powercfg_setting_perfboostmode_stdout.txt`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\powercfg_setting_perfboostpol_stderr.txt`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\powercfg_setting_perfboostpol_stdout.txt`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\powercfg_setting_perfdecthreshold_stderr.txt`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\powercfg_setting_perfdecthreshold_stdout.txt`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\powercfg_setting_perfepp_stderr.txt`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\powercfg_setting_perfepp_stdout.txt`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\powercfg_setting_perfincthreshold_stderr.txt`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\powercfg_setting_perfincthreshold_stdout.txt`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\powercfg_setting_procfreqmax_stderr.txt`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\powercfg_setting_procfreqmax_stdout.txt`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\powercfg_setting_procthrottlemax_stderr.txt`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\powercfg_setting_procthrottlemax_stdout.txt`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\powercfg_setting_procthrottlemin_stderr.txt`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\powercfg_setting_procthrottlemin_stdout.txt`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\powercfg_setting_syscoolpol_stderr.txt`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\powercfg_setting_syscoolpol_stdout.txt`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\presentmon_detector_result.json`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\presentmon_log.txt`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\presentmon_presentmon_help_long_stderr.txt`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\presentmon_presentmon_help_long_stdout.txt`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\presentmon_presentmon_help_short_stderr.txt`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\presentmon_presentmon_help_short_stdout.txt`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\presentmon_presentmon_version_stderr.txt`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\presentmon_presentmon_version_stdout.txt`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\process_targets_all_running_processes.csv`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\process_targets_detector_result.json`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\raw_outputs\process_targets_log.txt`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\risk_catalog.json`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\run_phase1_exploration.ps1`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\scripts\common_phase1.ps1`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\scripts\detect_gigabyte_controls.ps1`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\scripts\detect_librehardwaremonitor.ps1`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\scripts\detect_msi_afterburner.ps1`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\scripts\detect_nvidia_telemetry.ps1`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\scripts\detect_powercfg_settings.ps1`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\scripts\detect_presentmon.ps1`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\scripts\detect_process_targets.ps1`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\PHASE_1_EXPLORATION\tests\Invoke-Phase1Validation.ps1`
- `C:\Users\kkids\Documents\Codex_Computer_Optimizing\AERO_X16_CONTROL_CENTER_APP\README.md`
