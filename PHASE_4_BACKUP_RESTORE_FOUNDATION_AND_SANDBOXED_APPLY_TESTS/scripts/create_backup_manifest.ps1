Set-StrictMode -Version 2.0
$ErrorActionPreference = "Stop"
. "$PSScriptRoot\Phase4Common.ps1"

$Phase4Root = Get-Phase4Root
$AppRoot = Split-Path -Parent $Phase4Root
$Phase1Root = Join-Path $AppRoot "PHASE_1_EXPLORATION"
$Phase3Root = Join-Path $AppRoot "PHASE_3_CONTROL_SURFACE_COMPLETENESS_AND_PRESET_EDITING"
$Raw = Join-Path $Phase4Root "raw_outputs\backup_manifest"
$Backups = Join-Path $Phase4Root "backups"
$AppBackup = Join-Path $Backups "app_config"
$Snapshots = Join-Path $Backups "snapshots"
Ensure-Directory $Raw
Ensure-Directory $AppBackup
Ensure-Directory $Snapshots

$powerJson = powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "export_active_power_plan.ps1")
if ($LASTEXITCODE -ne 0) { throw "export_active_power_plan.ps1 failed with exit code $LASTEXITCODE" }
$powerResult = $powerJson | ConvertFrom-Json

$msiJson = powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "backup_msi_afterburner_configs.ps1")
if ($LASTEXITCODE -ne 0) { throw "backup_msi_afterburner_configs.ps1 failed with exit code $LASTEXITCODE" }
$msiResult = $msiJson | ConvertFrom-Json

$appCopied = New-Object System.Collections.ArrayList
foreach ($RelRoot in @("config", "presets", "restore")) {
    $sourceRoot = Join-Path $Phase4Root $RelRoot
    if (-not (Test-Path -LiteralPath $sourceRoot)) { continue }
    foreach ($file in Get-ChildItem -LiteralPath $sourceRoot -File -Filter "*.json" -ErrorAction SilentlyContinue) {
        $destDir = Join-Path $AppBackup $RelRoot
        Ensure-Directory $destDir
        $dest = Join-Path $destDir $file.Name
        Copy-Item -LiteralPath $file.FullName -Destination $dest -Force
        [void]$appCopied.Add([pscustomobject]@{
            source_path = $file.FullName
            destination_path = $dest
            source_hash = Get-FileHashRecord -Path $file.FullName
            destination_hash = Get-FileHashRecord -Path $dest
        })
    }
}

$nvidia = $null
$phase1Nvidia = Join-Path $Phase1Root "raw_outputs\nvidia_telemetry_detector_result.json"
if (Test-Path -LiteralPath $phase1Nvidia) {
    $nvidia = Get-Content -LiteralPath $phase1Nvidia -Raw | ConvertFrom-Json
}
$nvidiaSnapshotPath = Join-Path $Snapshots "nvidia_smi_telemetry_phase1_snapshot.json"
Write-JsonFile -Path $nvidiaSnapshotPath -Data $nvidia | Out-Null

$processSnapshotPath = Join-Path $Snapshots "process_snapshot_phase1.json"
$phase1Process = Join-Path $Phase1Root "raw_outputs\process_targets_detector_result.json"
if (Test-Path -LiteralPath $phase1Process) {
    Copy-Item -LiteralPath $phase1Process -Destination $processSnapshotPath -Force
} else {
    Write-JsonFile -Path $processSnapshotPath -Data ([pscustomobject]@{ missing = $true; source = $phase1Process }) | Out-Null
}

$toolPaths = Get-Content -LiteralPath (Join-Path $Phase4Root "config\tool_paths.json") -Raw | ConvertFrom-Json
$failures = New-Object System.Collections.ArrayList
if (-not $powerResult.export_succeeded) { [void]$failures.Add("Active power plan export did not succeed.") }
if (-not (Test-Path -LiteralPath $powerResult.cpu_readable_values_snapshot_path)) { [void]$failures.Add("CPU readable values snapshot missing.") }

$activeExportBackedUp = ($powerResult.export_succeeded -eq $true -and (Test-Path -LiteralPath $powerResult.active_power_plan_export_path) -and ((Get-Item -LiteralPath $powerResult.active_power_plan_export_path).Length -gt 0))
$backupSufficient = ($failures.Count -eq 0 -and $activeExportBackedUp -and ($msiResult.copied_files.Count -gt 0) -and ($appCopied.Count -gt 0))

$manifest = [pscustomobject]@{
    generated_local = (Get-Date).ToString("s")
    machine_name = $env:COMPUTERNAME
    user_name = $env:USERNAME
    phase_root = $Phase4Root
    source_phase = "PHASE_3_CONTROL_SURFACE_COMPLETENESS_AND_PRESET_EDITING"
    active_power_plan_guid_before_backup = $powerResult.active_power_plan_guid
    active_power_plan_name_before_backup = $powerResult.active_power_plan_name
    active_power_plan_export_path = $powerResult.active_power_plan_export_path
    active_power_plan_export_succeeded = [bool]$powerResult.export_succeeded
    active_power_plan_export_file_length = $powerResult.active_power_plan_export_file_length
    active_power_plan_export_failure_reason = $powerResult.export_failure_reason
    active_power_plan_query_snapshot_path = $powerResult.active_power_plan_query_snapshot_path
    cpu_readable_values_snapshot_path = $powerResult.cpu_readable_values_snapshot_path
    msi_afterburner_executable_path = $msiResult.msi_afterburner_executable_path
    msi_afterburner_install_folder = $msiResult.install_folder
    msi_files_copied = $msiResult.copied_files
    msi_skipped_items = $msiResult.skipped_items
    app_config_files_copied = $appCopied
    tool_paths = $toolPaths
    nvidia_smi_telemetry_snapshot_path = $nvidiaSnapshotPath
    process_snapshot_path = $processSnapshotPath
    failures_or_skipped_items = $failures
    backup_sufficient_for_phase5_apply_tests = $backupSufficient
}
Write-JsonFile -Path (Join-Path $Backups "backup_manifest_latest.json") -Data $manifest | Out-Null

powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "generate_restore_scripts.ps1") | Out-Null

$restoreManifestExists = Test-Path -LiteralPath (Join-Path $Phase4Root "restore\restore_manifest_latest.json")
$sandboxResultPath = Join-Path $Phase4Root "sandbox\sandbox_powercfg_test_result.json"
$sandboxPassed = $false
if (Test-Path -LiteralPath $sandboxResultPath) {
    $sandboxPassed = [bool]((Get-Content -LiteralPath $sandboxResultPath -Raw | ConvertFrom-Json).passed)
}
$gates = [pscustomobject]@{
    generated_local = (Get-Date).ToString("s")
    backups_exist = (Test-Path -LiteralPath (Join-Path $Backups "backup_manifest_latest.json"))
    active_power_plan_exported = $activeExportBackedUp
    current_values_snapshot_exists = (Test-Path -LiteralPath $powerResult.cpu_readable_values_snapshot_path)
    restore_manifest_exists = $restoreManifestExists
    sandbox_powercfg_write_test_passed = $sandboxPassed
    msi_configs_backed_up = ($msiResult.copied_files.Count -gt 0)
    msi_slot_mapping_verified = $false
    nvidia_write_blocked = $true
    fan_write_blocked = $true
    ec_write_blocked = $true
    active_plan_write_enabled = $false
    msi_profile_apply_enabled = $false
    fan_write_enabled = $false
    ec_write_enabled = $false
    automation_apply_enabled = $false
}
Write-JsonFile -Path (Join-Path $Phase4Root "config\apply_gate_config.json") -Data $gates | Out-Null

$backupPolicy = [pscustomobject]@{
    phase = "PHASE_4_BACKUP_RESTORE_FOUNDATION_AND_SANDBOXED_APPLY_TESTS"
    required_before_phase5 = @("active power plan export", "CPU values snapshot", "MSI config/profile copy", "app JSON backup", "restore manifest")
    original_msi_files_must_not_be_modified = $true
}
Write-JsonFile -Path (Join-Path $Phase4Root "config\backup_policy.json") -Data $backupPolicy | Out-Null

$sandboxPolicy = [pscustomobject]@{
    phase = "PHASE_4_BACKUP_RESTORE_FOUNDATION_AND_SANDBOXED_APPLY_TESTS"
    only_allowed_write_target = "temporary inactive cloned power scheme"
    setactive_allowed = $false
    write_scheme_current_allowed = $false
    cleanup_required = $true
}
Write-JsonFile -Path (Join-Path $Phase4Root "config\sandbox_test_policy.json") -Data $sandboxPolicy | Out-Null

$manifest | ConvertTo-Json -Depth 12
