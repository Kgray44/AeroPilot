param(
    [switch]$SkipDetectors
)

$ErrorActionPreference = 'Stop'

$PhaseRoot = $PSScriptRoot
$AppRoot = Split-Path -Parent $PhaseRoot
$ScriptsRoot = Join-Path $PhaseRoot 'scripts'
$RawOutputDir = Join-Path $PhaseRoot 'raw_outputs'
$AppProbeDir = Join-Path $PhaseRoot 'app_probe'

. (Join-Path $ScriptsRoot 'common_phase1.ps1')

New-Phase1Directory -Path $RawOutputDir
New-Phase1Directory -Path $AppProbeDir

$context = Initialize-DetectorContext -PhaseRoot $PhaseRoot -DetectorName 'phase1_orchestrator'

function Invoke-Phase1Detector {
    param(
        [string]$Name,
        [string]$ScriptName
    )

    $scriptPath = Join-Path $ScriptsRoot $ScriptName
    $powershellPath = Join-Path $PSHOME 'powershell.exe'
    $cmd = Invoke-Phase1ReadOnlyCommand -Context $context -Name ("detector_$Name") -FilePath $powershellPath -Arguments @('-NoProfile','-ExecutionPolicy','Bypass','-File',$scriptPath,'-PhaseRoot',$PhaseRoot) -TimeoutSeconds 120

    $parsed = $null
    $parseError = $null
    try {
        if (-not [string]::IsNullOrWhiteSpace($cmd.stdout)) {
            $parsed = $cmd.stdout | ConvertFrom-Json -ErrorAction Stop
        }
    } catch {
        $parseError = $_.Exception.Message
    }

    return [pscustomobject]@{
        name        = $Name
        script_path = $scriptPath
        command     = [pscustomobject]@{
            command_line = $cmd.command_line
            exit_code    = $cmd.exit_code
            timed_out    = $cmd.timed_out
            succeeded    = $cmd.succeeded
            stdout_path  = $cmd.stdout_path
            stderr_path  = $cmd.stderr_path
            error        = $cmd.error
        }
        parsed      = $parsed
        parse_error = $parseError
        succeeded   = ($cmd.succeeded -and $null -ne $parsed -and $null -eq $parseError)
    }
}

function Get-Result {
    param(
        [hashtable]$Map,
        [string]$Name
    )
    if ($Map.ContainsKey($Name)) { return $Map[$Name] }
    return $null
}

function New-Capability {
    param(
        [string]$Name,
        [string]$Category,
        [string]$Reachability,
        [string]$PhaseStatus,
        [string]$Risk,
        [string]$ControlOwner,
        [string]$Notes
    )

    return [pscustomobject]@{
        name           = $Name
        category       = $Category
        reachability   = $Reachability
        phase1_status  = $PhaseStatus
        risk_level     = $Risk
        control_owner  = $ControlOwner
        notes          = $Notes
    }
}

function New-RiskItem {
    param(
        [string]$Name,
        [string]$Category,
        [string]$Reachability,
        [string]$PhaseStatus,
        [string]$Risk,
        [string]$WhatCanGoWrong,
        [string]$Backup,
        [string]$Restore,
        [bool]$ShowInGui,
        [string]$Warning,
        [string]$DefaultState
    )

    return [pscustomobject]@{
        setting_control_name = $Name
        category             = $Category
        reachability_status  = $Reachability
        current_phase_status = $PhaseStatus
        risk_level           = $Risk
        what_can_go_wrong    = $WhatCanGoWrong
        how_to_back_it_up    = $Backup
        how_to_restore_it    = $Restore
        should_appear_in_future_gui = $ShowInGui
        suggested_warning_label = $Warning
        suggested_default_enabled_state = $DefaultState
    }
}

function Format-ValuePair {
    param($Ac, $Dc)

    $acText = if ($null -ne $Ac) { [string]$Ac } else { 'unknown' }
    $dcText = if ($null -ne $Dc) { [string]$Dc } else { 'unknown' }
    return "AC=$acText; DC=$dcText"
}

function Build-DiscoveredPaths {
    param([hashtable]$Results)

    $msi = Get-Result -Map $Results -Name 'msi_afterburner'
    $nvidia = Get-Result -Map $Results -Name 'nvidia_telemetry'
    $presentmon = Get-Result -Map $Results -Name 'presentmon'
    $lhm = Get-Result -Map $Results -Name 'librehardwaremonitor'
    $gigabyte = Get-Result -Map $Results -Name 'gigabyte_controls'
    $processTargets = Get-Result -Map $Results -Name 'process_targets'

    return [pscustomobject]@{
        generated_local = (Get-Date).ToString('s')
        app_root        = $AppRoot
        phase_root      = $PhaseRoot
        raw_outputs     = $RawOutputDir
        msi_afterburner = [pscustomobject]@{
            installed        = if ($msi) { $msi.installed } else { $false }
            executable_paths = if ($msi) { $msi.executable_paths } else { @() }
            rtss_paths       = if ($msi) { $msi.rtss_executable_paths } else { @() }
            install_folder   = if ($msi) { $msi.install_folder } else { $null }
            config_files     = if ($msi) { $msi.config_files } else { @() }
            profile_files    = if ($msi) { $msi.profile_files } else { @() }
            profiles_folder  = if ($msi) { $msi.profiles_folder } else { $null }
        }
        powercfg        = [pscustomobject]@{
            executable_path     = (Get-Command 'powercfg.exe' -ErrorAction SilentlyContinue).Source
            active_scheme_guid  = (Get-Result -Map $Results -Name 'powercfg').active_scheme_guid
            active_scheme_name  = (Get-Result -Map $Results -Name 'powercfg').active_scheme_name
            sub_processor_guid  = (Get-Result -Map $Results -Name 'powercfg').sub_processor_guid
        }
        nvidia          = [pscustomobject]@{
            nvidia_smi_available = if ($nvidia) { $nvidia.nvidia_smi_available } else { $false }
            nvidia_smi_path      = if ($nvidia) { $nvidia.nvidia_smi_path } else { $null }
            candidate_paths      = if ($nvidia) { $nvidia.candidate_paths } else { @() }
        }
        presentmon      = [pscustomobject]@{
            found                 = if ($presentmon) { $presentmon.presentmon_found } else { $false }
            primary_executable    = if ($presentmon) { $presentmon.primary_executable_path } else { $null }
            executable_paths      = if ($presentmon) { $presentmon.executable_paths } else { @() }
        }
        librehardwaremonitor = [pscustomobject]@{
            found              = if ($lhm) { $lhm.found } else { $false }
            primary_executable = if ($lhm) { $lhm.primary_executable_path } else { $null }
            primary_library    = if ($lhm) { $lhm.primary_library_path } else { $null }
            executable_paths   = if ($lhm) { $lhm.executable_paths } else { @() }
            library_paths      = if ($lhm) { $lhm.library_paths } else { @() }
        }
        gigabyte_gcc    = [pscustomobject]@{
            installed_entries = if ($gigabyte) { $gigabyte.installed_entries } else { @() }
            running_processes = if ($gigabyte) { $gigabyte.running_processes } else { @() }
            services          = if ($gigabyte) { $gigabyte.services } else { @() }
            folders           = if ($gigabyte) { $gigabyte.folders } else { @() }
        }
        process_targets = [pscustomobject]@{
            seed_list_path    = if ($processTargets) { $processTargets.seed_list_path } else { $null }
            all_processes_csv = if ($processTargets) { $processTargets.all_processes_csv } else { $null }
        }
    }
}

function Build-Capabilities {
    param([hashtable]$Results)

    $items = New-Object System.Collections.ArrayList
    $msi = Get-Result -Map $Results -Name 'msi_afterburner'
    $power = Get-Result -Map $Results -Name 'powercfg'
    $nvidia = Get-Result -Map $Results -Name 'nvidia_telemetry'
    $presentmon = Get-Result -Map $Results -Name 'presentmon'
    $lhm = Get-Result -Map $Results -Name 'librehardwaremonitor'
    $gigabyte = Get-Result -Map $Results -Name 'gigabyte_controls'
    $processTargets = Get-Result -Map $Results -Name 'process_targets'

    [void]$items.Add((New-Capability -Name 'MSI Afterburner profile launch templates' -Category 'GPU profile loading' -Reachability $(if ($msi -and $msi.installed) { 'Likely reachable by launching MSI Afterburner with profile arguments' } else { 'Not reachable: executable not found' }) -PhaseStatus 'Dry-run templates only. Not executed.' -Risk 'Medium' -ControlOwner 'MSI Afterburner' -Notes 'Future app can map friendly preset names to MSI profile slots after manual verification.'))
    [void]$items.Add((New-Capability -Name 'MSI Afterburner profile/config backup' -Category 'GPU voltage/frequency curve profile' -Reachability $(if ($msi -and ($msi.msi_afterburner_cfg -or $msi.profiles_folder_exists)) { 'Discoverable' } else { 'Not found or incomplete' }) -PhaseStatus 'File metadata read only.' -Risk 'Low' -ControlOwner 'App can back up files later' -Notes 'Future writes require backup and restore manifest first.'))
    [void]$items.Add((New-Capability -Name 'Windows CPU power setting viewer' -Category 'CPU power behavior' -Reachability $(if ($power -and $power.active_scheme_guid) { 'Reachable through powercfg' } else { 'powercfg query incomplete' }) -PhaseStatus 'Read-only query complete where supported.' -Risk 'Read-only' -ControlOwner 'In-house via powercfg reads' -Notes 'Values are captured for active scheme only in Phase 1.'))
    [void]$items.Add((New-Capability -Name 'Windows CPU power setting writes later' -Category 'CPU power behavior' -Reachability $(if ($power) { 'Likely possible for readable settings, not tested' } else { 'Unknown' }) -PhaseStatus 'Not executed.' -Risk 'Medium' -ControlOwner 'In-house via powercfg with admin/confirmation' -Notes 'Future app should export or clone plans before writes.'))
    [void]$items.Add((New-Capability -Name 'NVIDIA telemetry through nvidia-smi' -Category 'GPU power/clock telemetry' -Reachability $(if ($nvidia -and $nvidia.nvidia_smi_available) { 'Reachable' } else { 'Not reachable: nvidia-smi missing' }) -PhaseStatus 'Read-only telemetry queries only.' -Risk 'Read-only' -ControlOwner 'In-house subprocess polling' -Notes 'Good candidate for MVP telemetry if available.'))
    [void]$items.Add((New-Capability -Name 'NVML Python telemetry later' -Category 'GPU power/clock telemetry' -Reachability 'Planned optional integration' -PhaseStatus 'Not tested in Phase 1.' -Risk 'Read-only' -ControlOwner 'Optional Python library' -Notes 'Use later if nvidia-smi polling is too slow or awkward.'))
    [void]$items.Add((New-Capability -Name 'PresentMon frame-time capture' -Category 'FPS/frame capture' -Reachability $(if ($presentmon -and $presentmon.presentmon_found) { 'Executable found' } else { 'Missing optional tool' }) -PhaseStatus 'Help/version attempted only if found.' -Risk 'Low' -ControlOwner 'Optional subprocess tool' -Notes 'Strongly recommended for benchmark sessions.'))
    [void]$items.Add((New-Capability -Name 'LibreHardwareMonitor sensors' -Category 'CPU power behavior' -Reachability $(if ($lhm -and $lhm.found) { 'Files found' } else { 'Missing optional tool' }) -PhaseStatus 'File/library discovery only. Not launched.' -Risk 'Read-only' -ControlOwner 'Optional library/tool' -Notes 'Useful for temperatures, fans, voltages, and motherboard sensors if supported.'))
    [void]$items.Add((New-Capability -Name 'Gigabyte/GCC discovery' -Category 'Fan control' -Reachability $(if ($gigabyte -and (@($gigabyte.installed_entries).Count -gt 0 -or @($gigabyte.services).Count -gt 0 -or @($gigabyte.running_processes).Count -gt 0)) { 'Some OEM surfaces discovered' } else { 'No clear OEM control surface found' }) -PhaseStatus 'Read-only process/service/file metadata.' -Risk 'Unknown' -ControlOwner 'Unknown/OEM' -Notes 'Fan control remains unproven and should stay experimental.'))
    [void]$items.Add((New-Capability -Name 'Game and tool process detection' -Category 'Game detection' -Reachability $(if ($processTargets) { 'Reachable through Get-Process' } else { 'Unknown' }) -PhaseStatus 'Read-only enumeration only.' -Risk 'Safe' -ControlOwner 'In-house' -Notes 'Future app can use editable seed list and per-game overrides.'))
    [void]$items.Add((New-Capability -Name 'Restore and panic restore framework' -Category 'Restore/backup' -Reachability 'Planned; file backups and power plan exports are feasible later' -PhaseStatus 'Architecture only. No restore point or backup created outside app folder.' -Risk 'Safe' -ControlOwner 'In-house' -Notes 'Must precede any apply phase.'))

    return @($items)
}

function Build-RiskCatalog {
    param([hashtable]$Results)

    $items = New-Object System.Collections.ArrayList
    $power = Get-Result -Map $Results -Name 'powercfg'

    if ($power) {
        foreach ($setting in @($power.processor_settings)) {
            $values = Format-ValuePair -Ac $setting.current_ac_value -Dc $setting.current_dc_value
            [void]$items.Add((New-RiskItem -Name $setting.friendly_name -Category $setting.category -Reachability $(if ($setting.powercfg_can_read) { "Readable via powercfg. Current $values" } else { 'Not currently readable by direct powercfg query' }) -PhaseStatus 'Read-only in Phase 1' -Risk $setting.risk_level -WhatCanGoWrong 'Can change heat, battery life, fan behavior, stability, latency, or benchmark results depending on the setting.' -Backup 'Export or clone the active power scheme before writing.' -Restore 'Re-import or reactivate the backed-up power scheme, or set the previous AC/DC values.' -ShowInGui $true -Warning $setting.suggested_future_tooltip_warning -DefaultState 'Disabled for writes; visible as read-only until Phase 2+ confirmation.'))
        }
    }

    [void]$items.Add((New-RiskItem -Name 'MSI profile slot launch' -Category 'GPU profile loading' -Reachability 'Likely reachable if MSIAfterburner.exe is present' -PhaseStatus 'Dry-run command templates only' -Risk 'Medium' -WhatCanGoWrong 'Wrong slot may apply an unintended GPU voltage/frequency curve or power behavior.' -Backup 'Back up MSIAfterburner.cfg and Profiles folder before launch testing.' -Restore 'Launch known stock/safe MSI profile or restore backed-up MSI files.' -ShowInGui $true -Warning 'Applies an external MSI Afterburner profile slot. Verify slot mapping first.' -DefaultState 'Disabled until manually verified.'))
    [void]$items.Add((New-RiskItem -Name 'GPU voltage/frequency curve profile editing' -Category 'GPU voltage/frequency curve profile' -Reachability 'Requires MSI Afterburner or future manual profile-file research' -PhaseStatus 'Not edited in Phase 1' -Risk 'High' -WhatCanGoWrong 'Unstable clocks, driver resets, crashes, poor performance, or excessive heat if misconfigured.' -Backup 'Back up MSI profile files and record current NVIDIA telemetry before changes.' -Restore 'Apply stock MSI profile and restore backed-up profile files.' -ShowInGui $true -Warning 'Advanced GPU curve control. Changes can crash games or reset the driver.' -DefaultState 'Disabled; require explicit confirmation.'))
    [void]$items.Add((New-RiskItem -Name 'NVIDIA telemetry polling' -Category 'GPU power/clock telemetry' -Reachability 'Reachable when nvidia-smi works' -PhaseStatus 'Read-only queries only' -Risk 'Read-only' -WhatCanGoWrong 'Overly aggressive polling can add overhead or noisy logs.' -Backup 'No system backup needed; preserve log configuration.' -Restore 'Stop polling and delete generated logs if desired.' -ShowInGui $true -Warning 'Read-only GPU telemetry. Use sane polling intervals.' -DefaultState 'Enabled for read-only dashboard if available.'))
    [void]$items.Add((New-RiskItem -Name 'PresentMon capture' -Category 'FPS/frame capture' -Reachability 'Optional tool; discovered or missing per report' -PhaseStatus 'Not used for capture in Phase 1' -Risk 'Low' -WhatCanGoWrong 'Wrong process targeting can capture no data or the wrong app; high-frequency logs can grow large.' -Backup 'Keep capture outputs in timestamped session folders.' -Restore 'Stop capture process and archive/delete session logs.' -ShowInGui $true -Warning 'Captures frame-time logs for the selected process.' -DefaultState 'Disabled until user starts a benchmark session.'))
    [void]$items.Add((New-RiskItem -Name 'Ping/network logging' -Category 'Ping/network logging' -Reachability 'Known feasible from previous project helpers; not expanded in this app Phase 1' -PhaseStatus 'Planned' -Risk 'Safe' -WhatCanGoWrong 'Large logs or misleading results if endpoint choice is poor.' -Backup 'No system backup required; keep log files with session metadata.' -Restore 'Stop logger and archive/delete logs.' -ShowInGui $true -Warning 'Read-only network logging. Does not change adapter settings.' -DefaultState 'Optional per session.'))
    [void]$items.Add((New-RiskItem -Name 'Fan mode/control through GCC or OEM paths' -Category 'Fan control' -Reachability 'Unknown; direct control not proven' -PhaseStatus 'Discovery only' -Risk 'High' -WhatCanGoWrong 'Unexpected fan behavior, high temperatures, OEM service conflicts, or persistent config changes.' -Backup 'Export app/OEM config if proven safe; record current mode manually first.' -Restore 'Use OEM app to return to default/auto fan mode; reboot if needed.' -ShowInGui $true -Warning 'Fan control is experimental until an official reversible path is proven.' -DefaultState 'Read-only/disabled.'))
    [void]$items.Add((New-RiskItem -Name 'Embedded controller writes' -Category 'Experimental low-level hardware access' -Reachability 'Not attempted; research only' -PhaseStatus 'Blocked from Phase 1 writes' -Risk 'Dangerous / Experimental' -WhatCanGoWrong 'Can destabilize hardware control, break fan behavior, or require reboot/recovery.' -Backup 'No reliable generic backup; requires dedicated research and OEM documentation.' -Restore 'Reboot, OEM defaults, or vendor service recovery may be required.' -ShowInGui $true -Warning 'Dangerous low-level hardware access. Research only.' -DefaultState 'Hidden from apply path but visible in Experimental read-only notes.'))
    [void]$items.Add((New-RiskItem -Name 'Startup automation' -Category 'Startup automation' -Reachability 'Feasible later through scheduled tasks or startup entries' -PhaseStatus 'Not created in Phase 1' -Risk 'Medium' -WhatCanGoWrong 'Bad automation can apply presets at the wrong time or make login noisy.' -Backup 'Export scheduled task/startup entry definitions before modification.' -Restore 'Disable/remove created task or startup entry.' -ShowInGui $true -Warning 'Automation can change system behavior on login or game launch.' -DefaultState 'Disabled until explicitly configured.'))
    [void]$items.Add((New-RiskItem -Name 'Game detection and auto preset switching' -Category 'Game detection' -Reachability 'Readable through process enumeration; automation planned' -PhaseStatus 'Read-only detection seed created' -Risk 'Low' -WhatCanGoWrong 'False positives can apply the wrong preset if future writes are enabled.' -Backup 'Save automation rules as JSON before edits.' -Restore 'Disable the game rule or restore previous JSON rules.' -ShowInGui $true -Warning 'Auto switching should require clear game/process matches.' -DefaultState 'Detection enabled; auto-apply disabled.'))
    [void]$items.Add((New-RiskItem -Name 'Save current state / restore previous state' -Category 'Restore/backup' -Reachability 'Planned; feasible for files and powercfg exports' -PhaseStatus 'Architecture only' -Risk 'Safe' -WhatCanGoWrong 'Incomplete backups can create false confidence.' -Backup 'Save power plan export, MSI files, preset JSON, app settings, and command logs.' -Restore 'Run restore workflow and verify telemetry/settings after restore.' -ShowInGui $true -Warning 'Always save state before applying tuning.' -DefaultState 'Enabled by default before any apply action.'))

    return @($items)
}

function Write-AppReadme {
    param([object]$Report)

    $path = Join-Path $AppRoot 'README.md'
    $content = @"
# AERO X16 Control Center App

This is a new, isolated subproject for a future AERO X16 / RTX 5070 optimization control app.

Phase 1 is exploration only. It creates read-only detection helpers, raw command captures, machine-readable JSON, and a human-readable report. It does not change CPU boost, EPP, power plans, NVIDIA settings, MSI Afterburner profiles, fan modes, registry settings, startup entries, scheduled tasks, or system services.

Primary Phase 1 entrypoint:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$PhaseRoot\run_phase1_exploration.ps1"
```

Important outputs:

- `PHASE_1_EXPLORATION\phase1_exploration_report.md`
- `PHASE_1_EXPLORATION\phase1_exploration_report.json`
- `PHASE_1_EXPLORATION\discovered_paths.json`
- `PHASE_1_EXPLORATION\discovered_capabilities.json`
- `PHASE_1_EXPLORATION\risk_catalog.json`
- `PHASE_1_EXPLORATION\command_inventory.md`
- `PHASE_1_EXPLORATION\raw_outputs\`

Recommended Phase 2:

Build the first PySide6 app skeleton with a dashboard, read-only telemetry, MSI profile dry-run buttons, CPU setting viewer, risk labels, and JSON preset schema. No destructive writes yet except optional explicitly-confirmed test commands.
"@
    Set-Content -LiteralPath $path -Value $content -Encoding UTF8
}

function Write-AppProbeReadme {
    $path = Join-Path $AppProbeDir 'README.md'
    $content = @"
# App Probe

This folder contains seed files and notes for future app runtime probes.

Phase 1 contents are read-only discovery outputs. `process_targets_seed.json` is an editable starting point for future game/tool detection rules. It was generated from a fixed seed list plus a read-only process enumeration; no process was modified.
"@
    Set-Content -LiteralPath $path -Value $content -Encoding UTF8
}

function Write-FutureArchitectureNotes {
    $path = Join-Path $PhaseRoot 'future_architecture_notes.md'
    $content = @"
# Future Architecture Notes

## Preferred Stack

- Python
- PySide6 GUI
- JSON preset files
- PowerShell helper scripts for Windows-specific discovery and guarded writes
- Subprocess calls for `powercfg`, `nvidia-smi`, MSI Afterburner, and PresentMon
- Optional LibreHardwareMonitor integration later
- Optional NVML integration later

## Proposed App Layout

- `app/`: PySide6 application package
- `app/core/`: preset schema, risk labels, logging, state snapshots
- `app/adapters/`: powercfg, nvidia-smi, MSI Afterburner, PresentMon, LibreHardwareMonitor/NVML adapters
- `app/ui/`: dashboard widgets and tabs
- `presets/`: JSON CPU/GPU/game presets
- `logs/`: timestamped app logs and benchmark session folders
- `restore/`: generated restore manifests and panic restore scripts
- `scripts/`: PowerShell helpers kept dry-run by default

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

The backend should own truth. The GUI should display capabilities, risk labels, and current state returned by adapters, not invent state locally. Any apply-capable adapter should support `--dry-run` by default and require an explicit `--apply` or equivalent confirmation path.

High-risk writes should be gated by:

- Current state snapshot
- Backup manifest
- Restore plan
- User confirmation
- Admin check when required
- Post-apply verification
"@
    Set-Content -LiteralPath $path -Value $content -Encoding UTF8
}

function Write-CommandInventory {
    param(
        [hashtable]$Results,
        [object[]]$DetectorRuns
    )

    $path = Join-Path $PhaseRoot 'command_inventory.md'
    $lines = New-Object System.Collections.ArrayList
    [void]$lines.Add('# Command Inventory')
    [void]$lines.Add('')
    [void]$lines.Add('Commands are grouped by safety status. Phase 1 only ran read-only discovery commands and detector scripts.')
    [void]$lines.Add('')
    [void]$lines.Add('## Read-only Commands Run In Phase 1')
    [void]$lines.Add('')

    foreach ($run in @($DetectorRuns)) {
        [void]$lines.Add('- `' + $run.command.command_line + '`')
    }

    foreach ($name in @('powercfg','nvidia_telemetry','presentmon')) {
        $result = Get-Result -Map $Results -Name $name
        if ($result -and $result.read_only_commands) {
            foreach ($cmd in @($result.read_only_commands)) {
                [void]$lines.Add('- `' + $cmd.command_line + '`')
            }
        }
    }

    [void]$lines.Add('')
    [void]$lines.Add('## Dry-run Templates')
    [void]$lines.Add('')
    [void]$lines.Add('- `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\run_phase1_exploration.ps1`')
    [void]$lines.Add('- Future apply helpers should default to `--dry-run` or no-op preview mode.')

    $presentmon = Get-Result -Map $Results -Name 'presentmon'
    if ($presentmon -and $presentmon.command_templates) {
        foreach ($template in @($presentmon.command_templates)) {
            [void]$lines.Add('- ' + $template.label + ': `' + ([string]$template.command) + '` - ' + $template.phase1_state)
        }
    }

    [void]$lines.Add('')
    [void]$lines.Add('## Future Apply Commands, Not Run In Phase 1')
    [void]$lines.Add('')
    $msi = Get-Result -Map $Results -Name 'msi_afterburner'
    if ($msi -and $msi.future_profile_commands) {
        foreach ($cmd in @($msi.future_profile_commands)) {
            [void]$lines.Add('- MSI profile slot ' + $cmd.profile_slot + ': `' + ([string]$cmd.command) + '` - not run in Phase 1.')
        }
    } else {
        foreach ($slot in 1..5) {
            [void]$lines.Add('- MSI profile slot ' + $slot + ': `MSIAfterburner.exe -Profile' + $slot + '` - not run in Phase 1.')
        }
    }

    [void]$lines.Add('- CPU AC write template: `powercfg /setacvalueindex <scheme_guid> SUB_PROCESSOR <setting_guid> <value>` - not run in Phase 1.')
    [void]$lines.Add('- CPU DC write template: `powercfg /setdcvalueindex <scheme_guid> SUB_PROCESSOR <setting_guid> <value>` - not run in Phase 1.')
    [void]$lines.Add('- Activate plan template: `powercfg /setactive <scheme_guid>` - not run in Phase 1.')
    [void]$lines.Add('- Scheduled task/startup automation templates are intentionally not created in Phase 1.')
    [void]$lines.Add('- Fan/EC write commands are intentionally absent. Treat as dangerous research only.')

    Set-Content -LiteralPath $path -Value @($lines) -Encoding UTF8
}

function Write-HumanReport {
    param(
        [hashtable]$Results,
        [object]$Paths,
        [object[]]$Capabilities,
        [object[]]$RiskCatalog,
        [object[]]$DetectorRuns
    )

    $path = Join-Path $PhaseRoot 'phase1_exploration_report.md'
    $msi = Get-Result -Map $Results -Name 'msi_afterburner'
    $power = Get-Result -Map $Results -Name 'powercfg'
    $nvidia = Get-Result -Map $Results -Name 'nvidia_telemetry'
    $presentmon = Get-Result -Map $Results -Name 'presentmon'
    $lhm = Get-Result -Map $Results -Name 'librehardwaremonitor'
    $gigabyte = Get-Result -Map $Results -Name 'gigabyte_controls'
    $processTargets = Get-Result -Map $Results -Name 'process_targets'

    $filesCreated = Get-ChildItem -LiteralPath $AppRoot -Recurse -File -ErrorAction SilentlyContinue | Sort-Object FullName | ForEach-Object { $_.FullName }

    $lines = New-Object System.Collections.ArrayList
    [void]$lines.Add('# AERO X16 Control Center App - Phase 1 Exploration Report')
    [void]$lines.Add('')
    [void]$lines.Add('- Generated local: ' + (Get-Date).ToString('s'))
    [void]$lines.Add('- App root: `' + $AppRoot + '`')
    [void]$lines.Add('- Phase root: `' + $PhaseRoot + '`')
    [void]$lines.Add("- Safety boundary: exploration only; no tuning changes applied.")
    [void]$lines.Add('')
    [void]$lines.Add('## Summary')
    [void]$lines.Add('')
    [void]$lines.Add('Phase 1 created an isolated app subproject and read-only discovery foundation for a future AERO X16 optimization control app. The run queried installed tools, powercfg settings, NVIDIA telemetry, optional telemetry tools, Gigabyte/GCC surfaces, and current process targets. It wrote raw outputs and structured JSON for Phase 2 app skeleton work.')
    [void]$lines.Add('')
    [void]$lines.Add('No CPU boost, EPP, min/max processor state, active power plan, NVIDIA setting, MSI profile, MSI config file, fan mode, service, scheduled task, startup entry, registry setting, or EC register was changed.')
    [void]$lines.Add('')
    [void]$lines.Add('## What Was Discovered')
    [void]$lines.Add('')
    $msiInstalled = if ($msi) { $msi.installed } else { $false }
    $msiPath = if ($msi -and @($msi.executable_paths).Count -gt 0) { @($msi.executable_paths)[0].path } else { 'not found' }
    $rtssCount = if ($msi) { @($msi.rtss_executable_paths).Count } else { 0 }
    $msiProfileCount = if ($msi) { @($msi.profile_files).Count } else { 0 }
    $activePlanText = if ($power) { "$($power.active_scheme_name) / $($power.active_scheme_guid)" } else { 'unknown' }
    $processorSettingCount = if ($power) { @($power.processor_settings).Count } else { 0 }
    $nvidiaAvailable = if ($nvidia) { $nvidia.nvidia_smi_available } else { $false }
    $presentmonFound = if ($presentmon) { $presentmon.presentmon_found } else { $false }
    $lhmFound = if ($lhm) { $lhm.found } else { $false }
    $gigabyteInstalledCount = if ($gigabyte) { @($gigabyte.installed_entries).Count } else { 0 }
    $gigabyteServiceCount = if ($gigabyte) { @($gigabyte.services).Count } else { 0 }
    $seedListPath = if ($processTargets) { $processTargets.seed_list_path } else { 'not created' }

    [void]$lines.Add("- MSI Afterburner installed: $msiInstalled")
    [void]$lines.Add('- MSI Afterburner path: `' + $msiPath + '`')
    [void]$lines.Add("- RTSS paths found: $rtssCount")
    [void]$lines.Add("- MSI profile files found: $msiProfileCount")
    [void]$lines.Add('- Active power plan: `' + $activePlanText + '`')
    [void]$lines.Add("- Processor settings cataloged: $processorSettingCount")
    [void]$lines.Add("- nvidia-smi available: $nvidiaAvailable")
    [void]$lines.Add("- PresentMon found: $presentmonFound")
    [void]$lines.Add("- LibreHardwareMonitor found: $lhmFound")
    [void]$lines.Add("- Gigabyte/GCC installed entries: $gigabyteInstalledCount")
    [void]$lines.Add("- Gigabyte/GCC services discovered: $gigabyteServiceCount")
    [void]$lines.Add('- Process targets seed list: `' + $seedListPath + '`')
    [void]$lines.Add('')
    [void]$lines.Add('## Reachability Matrix')
    [void]$lines.Add('')
    [void]$lines.Add('| Capability | Reachability | Phase 1 Status | Risk | Owner |')
    [void]$lines.Add('|---|---|---|---|---|')
    foreach ($cap in @($Capabilities)) {
        [void]$lines.Add("| $($cap.name) | $($cap.reachability) | $($cap.phase1_status) | $($cap.risk_level) | $($cap.control_owner) |")
    }
    [void]$lines.Add('')
    [void]$lines.Add('## What Is Reachable')
    [void]$lines.Add('')
    [void]$lines.Add('- CPU power setting reads are reachable through `powercfg` for supported settings.')
    [void]$lines.Add('- NVIDIA telemetry is reachable through `nvidia-smi` if marked available above.')
    [void]$lines.Add('- Game/tool process detection is reachable through read-only process enumeration.')
    [void]$lines.Add('- MSI profile launch templates are available if MSI Afterburner was found, but they were not executed.')
    [void]$lines.Add('')
    [void]$lines.Add('## What Is Not Reachable Or Missing')
    [void]$lines.Add('')
    [void]$lines.Add('- PresentMon is optional; if not found, install planning is deferred to a later user-approved phase.')
    [void]$lines.Add('- LibreHardwareMonitor is optional; if not found, integration is planned but not installed.')
    [void]$lines.Add('- Direct Gigabyte/GCC fan control is not proven safe or reachable by an official API in Phase 1.')
    [void]$lines.Add('- NVML Python integration was not tested; it remains a future optional adapter.')
    [void]$lines.Add('')
    [void]$lines.Add('## What Can Be Controlled In-house Later')
    [void]$lines.Add('')
    [void]$lines.Add('- CPU preset viewing and eventually guarded powercfg writes.')
    [void]$lines.Add('- JSON preset schema, risk labels, state snapshots, logs, and restore manifests.')
    [void]$lines.Add('- NVIDIA read-only telemetry polling through `nvidia-smi`, and possibly NVML later.')
    [void]$lines.Add('- Game/process detection and automation rules, with auto-apply disabled by default.')
    [void]$lines.Add('')
    [void]$lines.Add('## What Requires MSI Afterburner')
    [void]$lines.Add('')
    [void]$lines.Add('- GPU voltage/frequency curve profiles should remain owned by MSI Afterburner for now.')
    [void]$lines.Add('- The future app can map friendly GPU preset names to MSI profile slots after manual slot verification.')
    [void]$lines.Add('- Future apply phases must back up MSI config/profile files before launching any profile command.')
    [void]$lines.Add('')
    [void]$lines.Add('## What May Require Optional Tools')
    [void]$lines.Add('')
    [void]$lines.Add('- PresentMon for FPS/frame-time capture.')
    [void]$lines.Add('- LibreHardwareMonitor for broader CPU/motherboard/fan/voltage sensors.')
    [void]$lines.Add('- NVML Python bindings for cleaner GPU telemetry beyond subprocess polling.')
    [void]$lines.Add('')
    [void]$lines.Add('## Dangerous But Possible')
    [void]$lines.Add('')
    [void]$lines.Add('- CPU boost, frequency caps, EPP, and core parking writes through powercfg may be possible later, but need backups and explicit confirmation.')
    [void]$lines.Add('- GPU curve/profile application through MSI Afterburner can be powerful but risky if slot mapping is wrong.')
    [void]$lines.Add('- Fan control through OEM files, services, UI automation, or EC writes is high risk or dangerous until proven reversible.')
    [void]$lines.Add('- Startup automation and automatic preset switching should be visible in the GUI but disabled by default.')
    [void]$lines.Add('')
    [void]$lines.Add('## Risk Catalog Summary')
    [void]$lines.Add('')
    [void]$lines.Add('| Item | Category | Reachability | Risk | Default |')
    [void]$lines.Add('|---|---|---|---|---|')
    foreach ($item in @($RiskCatalog)) {
        [void]$lines.Add("| $($item.setting_control_name) | $($item.category) | $($item.reachability_status) | $($item.risk_level) | $($item.suggested_default_enabled_state) |")
    }
    [void]$lines.Add('')
    [void]$lines.Add('## Recommended Phase 2')
    [void]$lines.Add('')
    [void]$lines.Add('Build the first PySide6 app skeleton with a dashboard, read-only telemetry, MSI profile dry-run buttons, CPU setting viewer, risk labels, and JSON preset schema. No destructive writes yet except optional explicitly-confirmed test commands.')
    [void]$lines.Add('')
    [void]$lines.Add('## Raw Outputs')
    [void]$lines.Add('')
    [void]$lines.Add('Raw command stdout/stderr, detector logs, detector JSON, and process CSV files are stored under `' + $RawOutputDir + '`.')
    [void]$lines.Add('')
    [void]$lines.Add('## Detector Run Status')
    [void]$lines.Add('')
    [void]$lines.Add('| Detector | Succeeded | Exit Code | Timed Out | Parse Error |')
    [void]$lines.Add('|---|---:|---:|---:|---|')
    foreach ($run in @($DetectorRuns)) {
        [void]$lines.Add("| $($run.name) | $($run.succeeded) | $($run.command.exit_code) | $($run.command.timed_out) | $($run.parse_error) |")
    }
    [void]$lines.Add('')
    [void]$lines.Add('## Exact Files Created')
    [void]$lines.Add('')
    foreach ($file in @($filesCreated)) {
        [void]$lines.Add('- `' + $file + '`')
    }

    Set-Content -LiteralPath $path -Value @($lines) -Encoding UTF8
}

$detectorSpecs = @(
    [pscustomobject]@{ name='msi_afterburner'; script='detect_msi_afterburner.ps1' },
    [pscustomobject]@{ name='powercfg'; script='detect_powercfg_settings.ps1' },
    [pscustomobject]@{ name='nvidia_telemetry'; script='detect_nvidia_telemetry.ps1' },
    [pscustomobject]@{ name='presentmon'; script='detect_presentmon.ps1' },
    [pscustomobject]@{ name='librehardwaremonitor'; script='detect_librehardwaremonitor.ps1' },
    [pscustomobject]@{ name='gigabyte_controls'; script='detect_gigabyte_controls.ps1' },
    [pscustomobject]@{ name='process_targets'; script='detect_process_targets.ps1' }
)

$detectorRuns = New-Object System.Collections.ArrayList
$resultMap = @{}

if (-not $SkipDetectors) {
    foreach ($spec in $detectorSpecs) {
        Write-Phase1Log -Context $context -Message "Running detector $($spec.name)"
        $run = Invoke-Phase1Detector -Name $spec.name -ScriptName $spec.script
        [void]$detectorRuns.Add($run)
        if ($run.parsed) {
            $resultMap[$spec.name] = $run.parsed
        }
    }
} else {
    Write-Phase1Log -Context $context -Level 'WARN' -Message 'SkipDetectors was requested. Loading detector JSON from raw_outputs where possible.'
    foreach ($spec in $detectorSpecs) {
        $jsonPath = Join-Path $RawOutputDir ("{0}_detector_result.json" -f $spec.name)
        if (Test-Path -LiteralPath $jsonPath) {
            $parsed = Get-Content -LiteralPath $jsonPath -Raw | ConvertFrom-Json
            $resultMap[$spec.name] = $parsed
            [void]$detectorRuns.Add([pscustomobject]@{ name=$spec.name; script_path=(Join-Path $ScriptsRoot $spec.script); command=[pscustomobject]@{ command_line='loaded from existing JSON'; exit_code=0; timed_out=$false; succeeded=$true; stdout_path=$jsonPath; stderr_path=$null; error=$null }; parsed=$parsed; parse_error=$null; succeeded=$true })
        }
    }
}

$paths = Build-DiscoveredPaths -Results $resultMap
$capabilities = Build-Capabilities -Results $resultMap
$riskCatalog = Build-RiskCatalog -Results $resultMap

Write-Phase1JsonFile -Path (Join-Path $PhaseRoot 'discovered_paths.json') -InputObject $paths -Depth 16
Write-Phase1JsonFile -Path (Join-Path $PhaseRoot 'discovered_capabilities.json') -InputObject ([pscustomobject]@{
    generated_local = (Get-Date).ToString('s')
    capabilities    = $capabilities
}) -Depth 14
Write-Phase1JsonFile -Path (Join-Path $PhaseRoot 'risk_catalog.json') -InputObject ([pscustomobject]@{
    generated_local = (Get-Date).ToString('s')
    risk_labels     = @('Safe','Low','Medium','High','Dangerous / Experimental','Read-only','Unknown')
    items           = $riskCatalog
}) -Depth 14

Write-AppReadme -Report $null
Write-AppProbeReadme
Write-FutureArchitectureNotes
Write-CommandInventory -Results $resultMap -DetectorRuns @($detectorRuns)
Write-HumanReport -Results $resultMap -Paths $paths -Capabilities $capabilities -RiskCatalog $riskCatalog -DetectorRuns @($detectorRuns)

$machineReport = [pscustomobject]@{
    generated_local       = (Get-Date).ToString('s')
    phase                 = 'Phase 1 Exploration'
    safety_boundary       = 'Read-only discovery. No tuning changes applied.'
    app_root              = $AppRoot
    phase_root            = $PhaseRoot
    detector_runs         = @($detectorRuns | ForEach-Object {
        [pscustomobject]@{
            name        = $_.name
            succeeded   = $_.succeeded
            command     = $_.command
            parse_error = $_.parse_error
        }
    })
    discovered_paths_file = Join-Path $PhaseRoot 'discovered_paths.json'
    discovered_capabilities_file = Join-Path $PhaseRoot 'discovered_capabilities.json'
    risk_catalog_file     = Join-Path $PhaseRoot 'risk_catalog.json'
    raw_outputs_dir       = $RawOutputDir
    results               = $resultMap
    recommended_phase2    = 'Build the first PySide6 app skeleton with a dashboard, read-only telemetry, MSI profile dry-run buttons, CPU setting viewer, risk labels, and JSON preset schema. No destructive writes yet except optional explicitly-confirmed test commands.'
}
Write-Phase1JsonFile -Path (Join-Path $PhaseRoot 'phase1_exploration_report.json') -InputObject $machineReport -Depth 18

Write-Phase1Log -Context $context -Message 'Finished Phase 1 orchestrator'

$summary = [pscustomobject]@{
    generated_local = (Get-Date).ToString('s')
    phase_root      = $PhaseRoot
    detector_count  = @($detectorRuns).Count
    failed_detectors = @($detectorRuns | Where-Object { -not $_.succeeded } | Select-Object -ExpandProperty name)
    report_md       = Join-Path $PhaseRoot 'phase1_exploration_report.md'
    report_json     = Join-Path $PhaseRoot 'phase1_exploration_report.json'
}

$summary | ConvertTo-Json -Depth 6
