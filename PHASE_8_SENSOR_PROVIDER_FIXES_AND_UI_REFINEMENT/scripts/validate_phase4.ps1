Set-StrictMode -Version 2.0
$ErrorActionPreference = "Stop"

$Phase4Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$AppRoot = Split-Path -Parent $Phase4Root
$Phase3Root = Join-Path $AppRoot "PHASE_3_CONTROL_SURFACE_COMPLETENESS_AND_PRESET_EDITING"
$RawOut = Join-Path $Phase4Root "raw_outputs"
New-Item -ItemType Directory -Path $RawOut -Force | Out-Null

$Results = New-Object System.Collections.ArrayList

function Add-Check {
    param([string]$Name, [bool]$Passed, [string]$Details = "")
    [void]$script:Results.Add([pscustomobject]@{
        name = $Name
        passed = $Passed
        details = $Details
    })
}

function Load-Json {
    param([string]$Path)
    try {
        return Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json
    } catch {
        Add-Check "json_parse:$([IO.Path]::GetFileName($Path))" $false $_.Exception.Message
        return $null
    }
}

function Test-JsonFile {
    param([string]$Path)
    try {
        Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json | Out-Null
        Add-Check "json_parse:$([IO.Path]::GetFileName($Path))" $true $Path
    } catch {
        Add-Check "json_parse:$([IO.Path]::GetFileName($Path))" $false $_.Exception.Message
    }
}

$RequiredPaths = @(
    "phase4_report.md",
    "phase4_report.json",
    "phase4_validation.md",
    "raw_outputs",
    "logs",
    "screenshots",
    "tests",
    "scripts\run_app.ps1",
    "scripts\validate_phase4.ps1",
    "scripts\collect_phase4_snapshot.ps1",
    "scripts\capture_page_photos.py",
    "scripts\create_backup_manifest.ps1",
    "scripts\export_active_power_plan.ps1",
    "scripts\backup_msi_afterburner_configs.ps1",
    "scripts\sandbox_powercfg_apply_test.ps1",
    "scripts\cleanup_sandbox_power_plan.ps1",
    "scripts\generate_restore_scripts.ps1",
    "scripts\read_librehardwaremonitor_sensors.ps1",
    "page_photos",
    "page_photos\README.md",
    "docs\phase4_safety_boundary.md",
    "docs\backup_manifest_design.md",
    "docs\restore_manifest_design.md",
    "docs\sandbox_apply_test_design.md",
    "docs\msi_backup_restore_notes.md",
    "docs\power_plan_backup_restore_notes.md",
    "docs\phase5_recommendation.md",
    "docs\blocked_actions.md",
    "app\__init__.py",
    "app\main.py",
    "app\core\app_paths.py",
    "app\core\control_surface.py",
    "app\core\state_snapshot.py",
    "config\app_config.json",
    "config\tool_paths.json",
    "config\capability_cache.json",
    "config\control_surface_manifest.json",
    "config\action_catalog.json",
    "config\restore_requirement_catalog.json",
    "config\apply_gate_config.json",
    "config\backup_policy.json",
    "config\sandbox_test_policy.json",
    "presets\cpu_presets.json",
    "presets\gpu_profiles.json",
    "presets\game_rules.json",
    "presets\combined_presets.json",
    "presets\preset_schema.json",
    "presets\preset_validation_report.json",
    "backups\README.md",
    "backups\backup_manifest_latest.json",
    "restore\README.md",
    "restore\restore_manifest_latest.json",
    "restore\restore_plan_latest.md",
    "restore\generated_scripts\restore_power_plan_preview.ps1",
    "restore\generated_scripts\restore_msi_afterburner_files_preview.ps1",
    "restore\generated_scripts\restore_app_config_preview.ps1",
    "sandbox\README.md",
    "sandbox\sandbox_powercfg_test_result.json",
    "sandbox\sandbox_powercfg_test_log.md",
    "requirements.txt"
)

foreach ($Rel in $RequiredPaths) {
    $Path = Join-Path $Phase4Root $Rel
    Add-Check "required_path:$Rel" (Test-Path -LiteralPath $Path) $Path
}

foreach ($Rel in @(
    "config\control_surface_manifest.json",
    "config\action_catalog.json",
    "config\restore_requirement_catalog.json",
    "phase3_report.json"
)) {
    $Path = Join-Path $Phase3Root $Rel
    Add-Check "phase3_source:$Rel" (Test-Path -LiteralPath $Path) $Path
    if (Test-Path -LiteralPath $Path) { Test-JsonFile $Path }
}

foreach ($File in @(Get-ChildItem -LiteralPath $Phase4Root -Recurse -File -Filter "*.json" -ErrorAction SilentlyContinue)) {
    Test-JsonFile $File.FullName
}

$Python = Get-Command python -ErrorAction SilentlyContinue
if ($Python) {
    $Old = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $Compile = & python -m compileall -q (Join-Path $Phase4Root "app") 2>&1
    $CompileExit = $LASTEXITCODE
    $ErrorActionPreference = $Old
    Add-Check "python_compile_app" ($CompileExit -eq 0) ($Compile -join "`n")

    $ImportTest = Join-Path $Phase4Root "tests\phase4_static_import_check.py"
    if (Test-Path -LiteralPath $ImportTest) {
        $env:PYTHONPATH = $Phase4Root
        $Old = $ErrorActionPreference
        $ErrorActionPreference = "Continue"
        $ImportOut = & python $ImportTest 2>&1
        $ImportExit = $LASTEXITCODE
        $ErrorActionPreference = $Old
        Add-Check "python_import_check" ($ImportExit -eq 0) ($ImportOut -join "`n")
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
    $env:PYTHONPATH = $Phase4Root
    $Old = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $SmokeOut = $Smoke | python - 2>&1
    $SmokeExit = $LASTEXITCODE
    $ErrorActionPreference = $Old
    Add-Check "pyside6_offscreen_construct" ($SmokeExit -eq 0 -and (($SmokeOut -join "`n") -match "AeroTune") -and (($SmokeOut -join "`n") -match "(?m)^9$")) ($SmokeOut -join "`n")

    $UiContract = Join-Path $Phase4Root "tests\aerotune_ui_contract_check.py"
    if (Test-Path -LiteralPath $UiContract) {
        $env:PYTHONPATH = $Phase4Root
        $Old = $ErrorActionPreference
        $ErrorActionPreference = "Continue"
        $UiOut = & python $UiContract 2>&1
        $UiExit = $LASTEXITCODE
        $ErrorActionPreference = $Old
        Add-Check "aerotune_ui_contract" ($UiExit -eq 0) ($UiOut -join "`n")
    }
}

$BackupManifestPath = Join-Path $Phase4Root "backups\backup_manifest_latest.json"
$RestoreManifestPath = Join-Path $Phase4Root "restore\restore_manifest_latest.json"
$SandboxPath = Join-Path $Phase4Root "sandbox\sandbox_powercfg_test_result.json"
$GatePath = Join-Path $Phase4Root "config\apply_gate_config.json"

$Backup = if (Test-Path -LiteralPath $BackupManifestPath) { Load-Json $BackupManifestPath } else { $null }
$Restore = if (Test-Path -LiteralPath $RestoreManifestPath) { Load-Json $RestoreManifestPath } else { $null }
$Sandbox = if (Test-Path -LiteralPath $SandboxPath) { Load-Json $SandboxPath } else { $null }
$Gates = if (Test-Path -LiteralPath $GatePath) { Load-Json $GatePath } else { $null }

if ($Backup) {
    Add-Check "backup_manifest_exists" $true $BackupManifestPath
    $PowerExportPath = [string]$Backup.active_power_plan_export_path
    $PowerExportFileExists = ($PowerExportPath -and (Test-Path -LiteralPath $PowerExportPath))
    $PowerExportFileLength = 0
    if ($PowerExportFileExists) { $PowerExportFileLength = (Get-Item -LiteralPath $PowerExportPath).Length }
    $PowerExportUsable = ($Backup.active_power_plan_export_succeeded -eq $true -and $PowerExportFileLength -gt 0)
    $PowerExportBlocked = (-not $PowerExportUsable -and [string]$Backup.active_power_plan_export_failure_reason)
    Add-Check "active_power_plan_export_usable_or_explicitly_blocked" ($PowerExportUsable -or $PowerExportBlocked) "usable=$PowerExportUsable length=$PowerExportFileLength reason=$($Backup.active_power_plan_export_failure_reason)"
    Add-Check "cpu_settings_snapshot_exists" (Test-Path -LiteralPath $Backup.cpu_readable_values_snapshot_path) $Backup.cpu_readable_values_snapshot_path
    Add-Check "msi_backup_manifest_exists" (Test-Path -LiteralPath (Join-Path $Phase4Root "backups\msi_afterburner\msi_backup_manifest.json")) ""
    Add-Check "app_config_backup_exists" (Test-Path -LiteralPath (Join-Path $Phase4Root "backups\app_config")) ""
    $MissingCopies = @()
    foreach ($File in @($Backup.msi_files_copied)) {
        if ($File.destination_path -and -not (Test-Path -LiteralPath $File.destination_path)) { $MissingCopies += $File.destination_path }
    }
    Add-Check "msi_copied_files_exist" ($MissingCopies.Count -eq 0) ($MissingCopies -join "`n")
}

if ($Restore) {
    Add-Check "restore_manifest_exists" $true $RestoreManifestPath
    Add-Check "restore_manifest_preview_only" ([bool]$Restore.preview_only) "preview_only=$($Restore.preview_only)"
}

if ($Sandbox) {
    Add-Check "sandbox_result_exists" $true $SandboxPath
    $Ran = [bool]$Sandbox.ran
    Add-Check "sandbox_passed_or_skipped_with_reason" (($Sandbox.passed -eq $true) -or ($Ran -eq $false -and $Sandbox.skip_reason)) "ran=$Ran passed=$($Sandbox.passed) skip=$($Sandbox.skip_reason)"
    if ($Ran) {
        Add-Check "sandbox_active_guid_unchanged" ($Sandbox.active_scheme_before.guid -eq $Sandbox.active_scheme_after.guid) "$($Sandbox.active_scheme_before.guid) -> $($Sandbox.active_scheme_after.guid)"
        Add-Check "sandbox_not_set_active" (-not [bool]$Sandbox.sandbox_was_active) "sandbox_was_active=$($Sandbox.sandbox_was_active)"
        Add-Check "sandbox_deleted_or_warning" (($Sandbox.cleanup.deleted -eq $true) -or [bool]$Sandbox.cleanup.warning) "deleted=$($Sandbox.cleanup.deleted) warning=$($Sandbox.cleanup.warning)"
        Add-Check "no_write_command_targeted_active_scheme" (-not [bool]$Sandbox.safety.write_targeted_active_scheme) ""
        Add-Check "no_write_command_used_scheme_current" (-not [bool]$Sandbox.safety.write_used_scheme_current) ""
        Add-Check "no_setactive_executed" (-not [bool]$Sandbox.safety.setactive_executed) ""
    }
}

if ($Gates) {
    foreach ($GateName in @("active_plan_write_enabled","msi_profile_apply_enabled","fan_write_enabled","ec_write_enabled","automation_apply_enabled")) {
        Add-Check "gate_false:$GateName" ($Gates.$GateName -eq $false) "$GateName=$($Gates.$GateName)"
    }
    if ($Backup) {
        Add-Check "gate_backups_exist_reflects_files" ($Gates.backups_exist -eq (Test-Path -LiteralPath $BackupManifestPath)) "gate=$($Gates.backups_exist)"
        $PowerExportPath = [string]$Backup.active_power_plan_export_path
        $PowerExportFileExists = ($PowerExportPath -and (Test-Path -LiteralPath $PowerExportPath))
        $PowerExportFileLength = 0
        if ($PowerExportFileExists) { $PowerExportFileLength = (Get-Item -LiteralPath $PowerExportPath).Length }
        $PowerExportUsable = ($Backup.active_power_plan_export_succeeded -eq $true -and $PowerExportFileLength -gt 0)
        Add-Check "gate_power_export_reflects_usable_export" ($Gates.active_power_plan_exported -eq $PowerExportUsable) "gate=$($Gates.active_power_plan_exported) usable=$PowerExportUsable length=$PowerExportFileLength"
    }
    if ($Sandbox) {
        Add-Check "gate_sandbox_reflects_result" ($Gates.sandbox_powercfg_write_test_passed -eq [bool]$Sandbox.passed) "gate=$($Gates.sandbox_powercfg_write_test_passed) result=$($Sandbox.passed)"
    }
}

$CodeFiles = @(Get-ChildItem -LiteralPath $Phase4Root -Recurse -File -ErrorAction SilentlyContinue | Where-Object {
    ($_.Extension -in @(".ps1", ".py")) -and $_.FullName -notmatch "\\scripts\\validate_phase4\.ps1$"
})
$BlockedPatterns = @(
    "MSIAfterburner\.exe.*-Profile[1-5]",
    "nvidia-smi.*(\s-pl\s|--power-limit|-lgc|-lmc|--persistence-mode|\s-pm\s)",
    "Set-ItemProperty",
    "New-ItemProperty",
    "Remove-ItemProperty",
    "Register-ScheduledTask",
    "New-ScheduledTask",
    "Start-Service",
    "Stop-Service",
    "Restart-Service",
    "fan\s*apply",
    "ec\s*write",
    "shell\s*=\s*True"
)
foreach ($Pattern in $BlockedPatterns) {
    $Hits = @()
    foreach ($File in $CodeFiles) {
        $Matches = Select-String -LiteralPath $File.FullName -Pattern $Pattern -AllMatches -ErrorAction SilentlyContinue
        foreach ($Match in @($Matches)) {
            if ($Match.Line -notmatch "(?i)preview|template|blocked|validation|pattern|future|recommendation|dry.?run|not executed") {
                $Hits += "$($File.FullName):$($Match.LineNumber):$($Match.Line)"
            }
        }
    }
    Add-Check "static_no_blocked_pattern:$Pattern" ($Hits.Count -eq 0) ($Hits -join "`n")
}

$BadPowerWrites = @()
foreach ($File in $CodeFiles) {
    foreach ($Match in @(Select-String -LiteralPath $File.FullName -Pattern "powercfg(\.exe)?\s+/(setacvalueindex|setdcvalueindex|setactive)" -AllMatches -ErrorAction SilentlyContinue)) {
        $Line = $Match.Line
        if ($Line -match "/setactive") {
            $BadPowerWrites += "$($File.FullName):$($Match.LineNumber):$Line"
        } elseif ($Line -match "SCHEME_CURRENT") {
            $BadPowerWrites += "$($File.FullName):$($Match.LineNumber):$Line"
        } elseif ($Line -notmatch "(?i)sandbox|template|preview|dry.?run|validation|future|not executed") {
            $BadPowerWrites += "$($File.FullName):$($Match.LineNumber):$Line"
        }
    }
}
Add-Check "static_powercfg_writes_sandbox_only" ($BadPowerWrites.Count -eq 0) ($BadPowerWrites -join "`n")

$Failed = @($Results | Where-Object { -not $_.passed })
$Summary = [pscustomobject]@{
    timestamp_local = (Get-Date).ToString("s")
    phase_root = $Phase4Root
    total_checks = $Results.Count
    failed_checks = $Failed.Count
    results = $Results
}
$JsonOut = Join-Path $RawOut "phase4_validation.json"
$Summary | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $JsonOut -Encoding UTF8

$Md = New-Object System.Collections.ArrayList
[void]$Md.Add("# Phase 4 Validation")
[void]$Md.Add("")
[void]$Md.Add("- Timestamp: $($Summary.timestamp_local)")
[void]$Md.Add("- Total checks: $($Summary.total_checks)")
[void]$Md.Add("- Failed checks: $($Summary.failed_checks)")
[void]$Md.Add("")
foreach ($Result in $Results) {
    $Mark = if ($Result.passed) { "PASS" } else { "FAIL" }
    [void]$Md.Add("- $Mark - $($Result.name)")
    if (-not $Result.passed -and $Result.details) { [void]$Md.Add("  - $($Result.details)") }
}
$Md | Set-Content -LiteralPath (Join-Path $Phase4Root "phase4_validation.md") -Encoding UTF8

$Summary | ConvertTo-Json -Depth 12
if ($Failed.Count -gt 0) { exit 1 }
exit 0
