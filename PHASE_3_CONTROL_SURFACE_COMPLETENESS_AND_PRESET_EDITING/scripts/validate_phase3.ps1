Set-StrictMode -Version 2.0
$ErrorActionPreference = "Stop"

$Phase3Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$AppRoot = Split-Path -Parent $Phase3Root
$Phase1Root = Join-Path $AppRoot "PHASE_1_EXPLORATION"
$Phase2Root = Join-Path $AppRoot "PHASE_2_APP_SKELETON_READONLY_DRYRUN"
$RawOut = Join-Path $Phase3Root "raw_outputs"
New-Item -ItemType Directory -Path $RawOut -Force | Out-Null

$Results = New-Object System.Collections.ArrayList

function Add-Check {
    param(
        [string]$Name,
        [bool]$Passed,
        [string]$Details = ""
    )
    [void]$script:Results.Add([pscustomobject]@{
        name = $Name
        passed = $Passed
        details = $Details
    })
}

function Read-JsonSafe {
    param([string]$Path)
    try {
        return Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json
    } catch {
        Add-Check -Name "json_parse:$([IO.Path]::GetFileName($Path))" -Passed $false -Details $_.Exception.Message
        return $null
    }
}

function Test-JsonFile {
    param([string]$Path)
    try {
        Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json | Out-Null
        Add-Check -Name "json_parse:$([IO.Path]::GetFileName($Path))" -Passed $true -Details $Path
    } catch {
        Add-Check -Name "json_parse:$([IO.Path]::GetFileName($Path))" -Passed $false -Details $_.Exception.Message
    }
}

$RequiredPaths = @(
    "phase3_report.md",
    "phase3_report.json",
    "phase3_validation.md",
    "raw_outputs",
    "logs",
    "screenshots",
    "tests",
    "scripts",
    "scripts\run_app.ps1",
    "scripts\validate_phase3.ps1",
    "scripts\collect_control_surface_snapshot.ps1",
    "scripts\export_control_surface_bundle.ps1",
    "docs\control_surface_design.md",
    "docs\coverage_rules.md",
    "docs\preset_editing_model.md",
    "docs\backup_restore_requirements.md",
    "docs\phase4_recommendation.md",
    "docs\unresolved_controls.md",
    "docs\known_risks.md",
    "app\__init__.py",
    "app\main.py",
    "app\core\app_paths.py",
    "app\core\control_surface.py",
    "app\core\command_runner.py",
    "app\core\state_snapshot.py",
    "app\adapters\phase1_data_adapter.py",
    "app\adapters\powercfg_adapter.py",
    "app\adapters\nvidia_smi_adapter.py",
    "app\adapters\msi_afterburner_adapter.py",
    "app\adapters\presentmon_adapter.py",
    "app\adapters\process_adapter.py",
    "app\adapters\librehardwaremonitor_adapter.py",
    "app\adapters\gigabyte_adapter.py",
    "app\ui\main_window.py",
    "app\ui\dashboard_tab.py",
    "app\ui\cpu_tab.py",
    "app\ui\gpu_tab.py",
    "app\ui\telemetry_tab.py",
    "app\ui\game_automation_tab.py",
    "app\ui\autotuning_tab.py",
    "app\ui\fan_experimental_tab.py",
    "app\ui\logs_tab.py",
    "app\ui\settings_safety_tab.py",
    "app\resources\app_styles.qss",
    "config\app_config.json",
    "config\tool_paths.json",
    "config\capability_cache.json",
    "config\control_surface_manifest.json",
    "config\ui_coverage_matrix.json",
    "config\action_catalog.json",
    "config\restore_requirement_catalog.json",
    "config\unsupported_or_blocked_controls.json",
    "presets\README.md",
    "presets\cpu_presets.json",
    "presets\gpu_profiles.json",
    "presets\game_rules.json",
    "presets\combined_presets.json",
    "presets\preset_schema.json",
    "presets\preset_validation_report.json",
    "restore\README.md",
    "restore\restore_strategy_preview.json",
    "restore\no_real_restore_manifest_yet.txt",
    "requirements.txt"
)

foreach ($Rel in $RequiredPaths) {
    $Path = Join-Path $Phase3Root $Rel
    Add-Check -Name "required_path:$Rel" -Passed (Test-Path -LiteralPath $Path) -Details $Path
}

$Phase1Required = @(
    "phase1_exploration_report.json",
    "discovered_paths.json",
    "discovered_capabilities.json",
    "risk_catalog.json",
    "app_probe\process_targets_seed.json",
    "raw_outputs\powercfg_detector_result.json"
)
foreach ($Rel in $Phase1Required) {
    $Path = Join-Path $Phase1Root $Rel
    Add-Check -Name "phase1_source:$Rel" -Passed (Test-Path -LiteralPath $Path) -Details $Path
    if (Test-Path -LiteralPath $Path) { Test-JsonFile -Path $Path }
}

$JsonFiles = @(Get-ChildItem -LiteralPath $Phase3Root -Recurse -File -Filter "*.json" -ErrorAction SilentlyContinue)
foreach ($File in $JsonFiles) {
    Test-JsonFile -Path $File.FullName
}

$Python = Get-Command python -ErrorAction SilentlyContinue
if ($Python) {
    $OldEap = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $Compile = & python -m compileall -q (Join-Path $Phase3Root "app") 2>&1
    $CompileExit = $LASTEXITCODE
    $ErrorActionPreference = $OldEap
    Add-Check -Name "python_compile_app" -Passed ($CompileExit -eq 0) -Details ($Compile -join "`n")

    $TestFile = Join-Path $Phase3Root "tests\phase3_static_import_check.py"
    if (Test-Path -LiteralPath $TestFile) {
        $env:PYTHONPATH = $Phase3Root
        $OldEap = $ErrorActionPreference
        $ErrorActionPreference = "Continue"
        $ImportOut = & python $TestFile 2>&1
        $ImportExit = $LASTEXITCODE
        $ErrorActionPreference = $OldEap
        Add-Check -Name "python_import_check" -Passed ($ImportExit -eq 0) -Details ($ImportOut -join "`n")
    }

    $Smoke = @'
import os
os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PySide6.QtWidgets import QApplication
from app.core.app_paths import AppPaths
from app.ui.main_window import MainWindow
app = QApplication([])
window = MainWindow(AppPaths.discover())
print(window.windowTitle())
print(window.centralWidget().count())
'@
    $env:PYTHONPATH = $Phase3Root
    $OldEap = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $SmokeOut = $Smoke | python - 2>&1
    $SmokeExit = $LASTEXITCODE
    $ErrorActionPreference = $OldEap
    Add-Check -Name "pyside6_offscreen_construct" -Passed ($SmokeExit -eq 0 -and (($SmokeOut -join "`n") -match "AERO X16 Control Center") -and (($SmokeOut -join "`n") -match "(?m)^9$")) -Details ($SmokeOut -join "`n")
}

$CodeFiles = @(Get-ChildItem -LiteralPath $Phase3Root -Recurse -File -ErrorAction SilentlyContinue | Where-Object {
    ($_.Extension -in @(".py", ".ps1")) -and $_.FullName -notmatch "\\scripts\\validate_phase3\.ps1$"
})
$HardBlockedPatterns = @(
    "Register-ScheduledTask",
    "New-ScheduledTask",
    "Start-Service",
    "Stop-Service",
    "Restart-Service",
    "Set-ItemProperty",
    "New-ItemProperty",
    "Remove-ItemProperty",
    "powercfg(\.exe)?\s+/(setacvalueindex|setdcvalueindex|setactive)",
    "nvidia-smi.*(\s-pl\s|--power-limit|-lgc|-lmc|--persistence-mode|\s-pm\s)",
    "ec\s*write",
    "fan\s*apply"
)
foreach ($Pattern in $HardBlockedPatterns) {
    $Hits = @()
    foreach ($File in $CodeFiles) {
        $Matches = Select-String -LiteralPath $File.FullName -Pattern $Pattern -AllMatches -ErrorAction SilentlyContinue
        foreach ($Match in @($Matches)) {
            $Line = $Match.Line
            if ($Line -notmatch "(?i)dry.?run|preview|template|blocked|validation|pattern|future|command|recommendation") {
                $Hits += "$($File.FullName):$($Match.LineNumber):$Line"
            }
        }
    }
    Add-Check -Name "static_no_disallowed_write:$Pattern" -Passed ($Hits.Count -eq 0) -Details ($Hits -join "`n")
}

$ShellTrueHits = @()
foreach ($File in $CodeFiles) {
    $Matches = Select-String -LiteralPath $File.FullName -Pattern "shell\s*=\s*True" -AllMatches -ErrorAction SilentlyContinue
    foreach ($Match in @($Matches)) {
        if ($Match.Line -notmatch "(?i)justified|comment|validation") {
            $ShellTrueHits += "$($File.FullName):$($Match.LineNumber):$($Match.Line)"
        }
    }
}
Add-Check -Name "static_no_unjustified_shell_true" -Passed ($ShellTrueHits.Count -eq 0) -Details ($ShellTrueHits -join "`n")

$ManifestPath = Join-Path $Phase3Root "config\control_surface_manifest.json"
$CoveragePath = Join-Path $Phase3Root "config\ui_coverage_matrix.json"
$UnsupportedPath = Join-Path $Phase3Root "config\unsupported_or_blocked_controls.json"
$RiskPath = Join-Path $Phase1Root "risk_catalog.json"
$CapsPath = Join-Path $Phase1Root "discovered_capabilities.json"
$PowerPath = Join-Path $Phase1Root "raw_outputs\powercfg_detector_result.json"

$Manifest = $null
$Unsupported = @()
if (Test-Path -LiteralPath $ManifestPath) { $Manifest = Read-JsonSafe -Path $ManifestPath }
if (Test-Path -LiteralPath $UnsupportedPath) {
    $UnsupportedJson = Read-JsonSafe -Path $UnsupportedPath
    if ($UnsupportedJson -and $UnsupportedJson.controls) { $Unsupported = @($UnsupportedJson.controls) }
}

if ($Manifest -and $Manifest.controls) {
    $Controls = @($Manifest.controls)
    $ControlIds = @($Controls | ForEach-Object { $_.control_id })
    Add-Check -Name "manifest_has_controls" -Passed ($Controls.Count -gt 0) -Details "count=$($Controls.Count)"
    Add-Check -Name "manifest_control_ids_unique" -Passed (($ControlIds | Select-Object -Unique).Count -eq $ControlIds.Count) -Details "unique=$(($ControlIds | Select-Object -Unique).Count); total=$($ControlIds.Count)"

    $RequiredControlIds = @(
        "cpu.power_plan.active_selection",
        "cpu.boost.mode",
        "cpu.boost.policy",
        "cpu.power.epp",
        "cpu.state.minimum",
        "cpu.state.maximum",
        "cpu.cooling.system_policy",
        "cpu.frequency.maximum",
        "cpu.parking.min_cores",
        "cpu.parking.max_cores",
        "cpu.idle.disable",
        "cpu.scheduling.heterogeneous_policy",
        "cpu.boost.performance_increase_threshold",
        "cpu.boost.performance_decrease_threshold",
        "gpu.msi.profile.slot1",
        "gpu.msi.profile.slot2",
        "gpu.msi.profile.slot3",
        "gpu.msi.profile.slot4",
        "gpu.msi.profile.slot5",
        "gpu.msi.backup.config_profiles",
        "gpu.msi.profile.slot_mapping",
        "gpu.msi.curve_editor.future",
        "gpu.profile.stock_safe_concept",
        "gpu.profile.efficient_undervolt_concept",
        "gpu.profile.balanced_concept",
        "gpu.profile.aggressive_concept",
        "gpu.profile.test_concept",
        "telemetry.nvidia.gpu_name",
        "telemetry.nvidia.driver_version",
        "telemetry.nvidia.gpu_utilization",
        "telemetry.nvidia.memory_utilization",
        "telemetry.nvidia.vram",
        "telemetry.nvidia.temperature",
        "telemetry.nvidia.power_draw",
        "telemetry.nvidia.power_limit_read",
        "telemetry.nvidia.graphics_clock",
        "telemetry.nvidia.memory_clock",
        "telemetry.nvidia.gpu_processes",
        "telemetry.nvidia.fallback_query",
        "telemetry.nvml.future_adapter",
        "presentmon.candidate.selection",
        "presentmon.syntax.verification",
        "presentmon.process_targeting",
        "presentmon.csv_output",
        "presentmon.timed_capture",
        "metrics.fps.average",
        "metrics.fps.one_percent_low",
        "metrics.frametime",
        "capture.session_folder",
        "lhm.dll.candidate",
        "lhm.sensor.cpu_temperature",
        "lhm.sensor.cpu_clock",
        "lhm.sensor.cpu_package_power",
        "lhm.sensor.fan_rpm",
        "lhm.sensor.voltage",
        "lhm.sensor.motherboard",
        "process.bf6",
        "process.steam",
        "process.ea_app",
        "process.epic_games",
        "process.sea_of_thieves",
        "process.minecraft",
        "process.msi_afterburner",
        "process.rtss",
        "process.presentmon",
        "process.hwinfo",
        "process.gigabyte_control_center",
        "process.nvidia_app",
        "process.false_positive_handling",
        "process.command_line_filtering",
        "automation.auto_apply.future",
        "automation.restore_on_exit.future",
        "network.ping_logger.future",
        "network.target_host.selection",
        "network.interval.setting",
        "network.session_logging",
        "network.ping_spike_detection",
        "fan.powercfg.cooling_policy",
        "fan.gigabyte.gcc_surfaces",
        "fan.gigabyte.powergear_service_status",
        "fan.official_api.status",
        "fan.command_line_control.status",
        "fan.config_file_control.status",
        "fan.ui_automation.status",
        "fan.ec_write.research_only",
        "fan.mode_display.future",
        "fan.apply_action.blocked",
        "restore.save_current_state",
        "restore.power_plan.clone_export",
        "restore.powercfg.previous_values",
        "restore.msi.config_backup",
        "restore.msi.config_restore",
        "restore.msi.known_safe_slot_future",
        "restore.app_preset_json",
        "restore.panic.future_command",
        "diagnostics.app_bundle",
        "startup.launch_app.future",
        "startup.scheduled_task.future",
        "startup.start_minimized.future",
        "startup.auto_detect_game.future",
        "startup.auto_apply_preset.future",
        "startup.automation.kill_switch"
    )
    foreach ($Id in $RequiredControlIds) {
        Add-Check -Name "required_control:$Id" -Passed ($ControlIds -contains $Id) -Details $Id
    }

    $MissingUi = @($Controls | Where-Object { -not $_.ui_tab -or -not $_.ui_section } | ForEach-Object { $_.control_id })
    Add-Check -Name "manifest_all_have_ui_assignment" -Passed ($MissingUi.Count -eq 0) -Details ($MissingUi -join ", ")

    $FutureWritesMissingBackup = @($Controls | Where-Object { $_.future_apply -and $_.future_apply.possible -eq $true -and $_.future_apply.enabled_now -ne $true -and (-not $_.future_apply.requires_backup -or -not $_.restore -or -not $_.restore.strategy) } | ForEach-Object { $_.control_id })
    Add-Check -Name "future_write_controls_have_backup_restore" -Passed ($FutureWritesMissingBackup.Count -eq 0) -Details ($FutureWritesMissingBackup -join ", ")

    $RiskWarningsMissing = @($Controls | Where-Object { $_.risk -and $_.risk.level -match "Medium|High|Dangerous" -and -not $_.risk.warning } | ForEach-Object { $_.control_id })
    Add-Check -Name "medium_high_dangerous_have_warning" -Passed ($RiskWarningsMissing.Count -eq 0) -Details ($RiskWarningsMissing -join ", ")

    $NonAppEditable = @($Controls | Where-Object { $_.desired_value_editing -and $_.desired_value_editing.editable_in_phase3 -eq $true -and $_.desired_value_editing.saved_to -notmatch "^(presets|config)/" } | ForEach-Object { $_.control_id })
    Add-Check -Name "editable_controls_save_only_app_json" -Passed ($NonAppEditable.Count -eq 0) -Details ($NonAppEditable -join ", ")

    if (Test-Path -LiteralPath $RiskPath) {
        $Risk = Read-JsonSafe -Path $RiskPath
        if ($Risk -and $Risk.items) {
            foreach ($Item in @($Risk.items)) {
                $Name = $Item.setting_control_name
                $Found = @($Controls | Where-Object { $_.source.phase1_risk_name -eq $Name -or $_.friendly_name -eq $Name }).Count -gt 0
                Add-Check -Name "risk_catalog_represented:$Name" -Passed $Found -Details $Name
            }
        }
    }

    if (Test-Path -LiteralPath $CapsPath) {
        $Caps = Read-JsonSafe -Path $CapsPath
        if ($Caps -and $Caps.capabilities) {
            foreach ($Cap in @($Caps.capabilities)) {
                $Name = $Cap.name
                $Found = (@($Controls | Where-Object { $_.source.capability_name -eq $Name }).Count -gt 0) -or (@($Unsupported | Where-Object { $_.source_capability_name -eq $Name }).Count -gt 0)
                Add-Check -Name "capability_represented:$Name" -Passed $Found -Details $Name
            }
        }
    }

    if (Test-Path -LiteralPath $PowerPath) {
        $Power = Read-JsonSafe -Path $PowerPath
        if ($Power -and $Power.processor_settings) {
            foreach ($Setting in @($Power.processor_settings)) {
                $Guid = $Setting.setting_guid
                $Alias = $Setting.alias
                $Found = @($Controls | Where-Object {
                    $ControlGuid = if ($_.PSObject.Properties.Name -contains "setting_guid") { $_.setting_guid } else { $null }
                    $ControlAlias = if ($_.PSObject.Properties.Name -contains "alias") { $_.alias } else { $null }
                    $ControlGuid -eq $Guid -or $ControlAlias -eq $Alias
                }).Count -gt 0
                Add-Check -Name "cpu_setting_represented:$Alias" -Passed $Found -Details $Guid
            }
        }
    }

    if (Test-Path -LiteralPath $CoveragePath) {
        $Coverage = Read-JsonSafe -Path $CoveragePath
        if ($Coverage -and $Coverage.coverage) {
            $CoverageIds = @($Coverage.coverage | ForEach-Object { $_.control_id })
            $MissingCoverage = @($ControlIds | Where-Object { $CoverageIds -notcontains $_ })
            Add-Check -Name "coverage_matrix_matches_manifest" -Passed ($MissingCoverage.Count -eq 0) -Details ($MissingCoverage -join ", ")
        }
    }
}

$Failed = @($Results | Where-Object { -not $_.passed })
$Summary = [pscustomobject]@{
    timestamp_local = (Get-Date).ToString("s")
    phase_root = $Phase3Root
    total_checks = $Results.Count
    failed_checks = $Failed.Count
    results = $Results
}
$JsonOut = Join-Path $RawOut "phase3_validation.json"
$Summary | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $JsonOut -Encoding UTF8

$MdOut = Join-Path $Phase3Root "phase3_validation.md"
$Lines = New-Object System.Collections.ArrayList
[void]$Lines.Add("# Phase 3 Validation")
[void]$Lines.Add("")
[void]$Lines.Add("- Timestamp: $($Summary.timestamp_local)")
[void]$Lines.Add("- Total checks: $($Summary.total_checks)")
[void]$Lines.Add("- Failed checks: $($Summary.failed_checks)")
[void]$Lines.Add("")
foreach ($Result in $Results) {
    $Mark = if ($Result.passed) { "PASS" } else { "FAIL" }
    [void]$Lines.Add("- $Mark - $($Result.name)")
    if (-not $Result.passed -and $Result.details) {
        [void]$Lines.Add("  - $($Result.details)")
    }
}
$Lines | Set-Content -LiteralPath $MdOut -Encoding UTF8

$Summary | ConvertTo-Json -Depth 10
if ($Failed.Count -gt 0) { exit 1 }
exit 0
