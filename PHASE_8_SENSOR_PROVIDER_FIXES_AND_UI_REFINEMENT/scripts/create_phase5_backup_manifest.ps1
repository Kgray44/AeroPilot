[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'Phase5Common.ps1')

function Set-GateField {
    param(
        [Parameter(Mandatory = $true)]$Object,
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)]$Value
    )
    if ($Object.PSObject.Properties.Name -contains $Name) {
        $Object.$Name = $Value
    } else {
        $Object | Add-Member -NotePropertyName $Name -NotePropertyValue $Value
    }
}

$root = Get-Phase5Root
$appRoot = Split-Path -Parent $root
$phase4Root = Join-Path $appRoot 'PHASE_4_BACKUP_RESTORE_FOUNDATION_AND_SANDBOXED_APPLY_TESTS'
$timestamp = Get-Phase5Timestamp
$backupRoot = Join-Path $root 'backups'
$snapshotDir = Join-Path $backupRoot 'snapshots'
$appConfigBackup = Join-Path $backupRoot 'app_config'
New-Phase5Directory -Path $backupRoot
New-Phase5Directory -Path $snapshotDir
New-Phase5Directory -Path $appConfigBackup

& (Join-Path $PSScriptRoot 'export_active_power_plan_phase5.ps1') | Out-Null
$exportJson = Join-Path $root 'raw_outputs\export_active_power_plan_phase5_result.json'
if (Test-Path -LiteralPath $exportJson) {
    $exportResult = Get-Content -LiteralPath $exportJson -Raw | ConvertFrom-Json
} else {
    $exportResult = [pscustomobject]@{
        active_power_plan_guid = $null
        active_power_plan_name = $null
        export_succeeded = $false
        failure_reason = 'Power plan export result JSON was not produced.'
    }
}

$activeQuery = Invoke-Phase5Command -Name 'phase5_powercfg_query_scheme_current_full' -Command @('powercfg.exe', '/query', 'SCHEME_CURRENT') -OutputDirectory (Join-Path $root 'raw_outputs\power_plan_backup_phase5')
$processorQuery = Invoke-Phase5Command -Name 'phase5_powercfg_query_scheme_current_processor' -Command @('powercfg.exe', '/query', 'SCHEME_CURRENT', 'SUB_PROCESSOR') -OutputDirectory (Join-Path $root 'raw_outputs\power_plan_backup_phase5')

$activeSnapshotPath = Join-Path $snapshotDir "active_power_plan_snapshot_phase5_$timestamp.json"
Write-Phase5Json -Path $activeSnapshotPath -Data ([pscustomobject]@{
    generated_local = Get-Date -Format 's'
    active_power_plan_guid = Get-Phase5Property -Object $exportResult -Name 'active_power_plan_guid' -Default $null
    active_power_plan_name = Get-Phase5Property -Object $exportResult -Name 'active_power_plan_name' -Default $null
    full_query = ConvertTo-Phase5CommandSummary -Result $activeQuery
    processor_query = ConvertTo-Phase5CommandSummary -Result $processorQuery
})

$latestCpuSnapshot = $null
$cpuSnapshotCopiedPath = $null
$existingCpu = Get-ChildItem -LiteralPath $snapshotDir -Filter 'cpu_readable_values_*.json' -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $existingCpu) {
    $existingCpu = Get-ChildItem -LiteralPath (Join-Path $phase4Root 'backups\snapshots') -Filter 'cpu_readable_values_*.json' -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
}
if ($existingCpu) {
    $cpuSnapshotCopiedPath = Join-Path $snapshotDir "cpu_readable_values_phase5_$timestamp.json"
    Copy-Item -LiteralPath $existingCpu.FullName -Destination $cpuSnapshotCopiedPath -Force
    $latestCpuSnapshot = $cpuSnapshotCopiedPath
}

foreach ($relative in @('config', 'presets', 'restore')) {
    $source = Join-Path $root $relative
    if (Test-Path -LiteralPath $source) {
        $dest = Join-Path $appConfigBackup $relative
        New-Phase5Directory -Path $dest
        Get-ChildItem -LiteralPath $source -Filter '*.json' -File -ErrorAction SilentlyContinue | ForEach-Object {
            Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $dest $_.Name) -Force
        }
    }
}

$phase4Backup = Join-Path $phase4Root 'backups\backup_manifest_latest.json'
$phase4Restore = Join-Path $phase4Root 'restore\restore_manifest_latest.json'
$phase4Sandbox = Join-Path $phase4Root 'sandbox\sandbox_powercfg_test_result.json'
$phase4MsiBackup = Join-Path $phase4Root 'backups\msi_afterburner\msi_backup_manifest.json'
$phase5MsiBackup = Join-Path $root 'backups\msi_afterburner\msi_backup_manifest.json'
$phase4BackupData = $null
$phase4RestoreData = $null
$sandboxData = $null
if (Test-Path -LiteralPath $phase4Backup) { $phase4BackupData = Get-Content -LiteralPath $phase4Backup -Raw | ConvertFrom-Json }
if (Test-Path -LiteralPath $phase4Restore) { $phase4RestoreData = Get-Content -LiteralPath $phase4Restore -Raw | ConvertFrom-Json }
if (Test-Path -LiteralPath $phase4Sandbox) { $sandboxData = Get-Content -LiteralPath $phase4Sandbox -Raw | ConvertFrom-Json }

$phase4MsiCopied = @()
if ($phase4BackupData) {
    $phase4MsiCopied = @(Get-Phase5Property -Object $phase4BackupData -Name 'msi_files_copied' -Default @())
}
$msiBackupContinued = [bool](
    (Test-Path -LiteralPath $phase5MsiBackup) -or
    (Test-Path -LiteralPath $phase4MsiBackup) -or
    ($phase4MsiCopied.Count -gt 0)
)

$currentValuesSnapshotExists = [bool]$latestCpuSnapshot
$restoreManifestExists = Test-Path -LiteralPath (Join-Path $root 'restore\restore_manifest_latest.json')
$sandboxPassed = [bool]($sandboxData -and (Get-Phase5Property -Object $sandboxData -Name 'passed' -Default $false))
$exported = [bool](Get-Phase5Property -Object $exportResult -Name 'export_succeeded' -Default $false)
$cpuRestoreAvailable = [bool]($currentValuesSnapshotExists -and $restoreManifestExists -and $exported)
$phase5Ready = [bool]($currentValuesSnapshotExists -and $restoreManifestExists -and $sandboxPassed -and $exported)

$gatePath = Join-Path $root 'config\apply_gate_config.json'
$gates = Get-Content -LiteralPath $gatePath -Raw | ConvertFrom-Json
Set-GateField -Object $gates -Name 'active_power_plan_exported' -Value $exported
Set-GateField -Object $gates -Name 'current_values_snapshot_exists' -Value $currentValuesSnapshotExists
Set-GateField -Object $gates -Name 'restore_manifest_exists' -Value $restoreManifestExists
Set-GateField -Object $gates -Name 'sandbox_powercfg_write_test_passed' -Value $sandboxPassed
Set-GateField -Object $gates -Name 'cpu_restore_available' -Value $cpuRestoreAvailable
Set-GateField -Object $gates -Name 'cpu_guarded_apply_enabled' -Value $false
Set-GateField -Object $gates -Name 'cpu_apply_requires_confirmation' -Value $true
Set-GateField -Object $gates -Name 'cpu_apply_low_medium_risk_only' -Value $true
Set-GateField -Object $gates -Name 'active_plan_write_enabled' -Value $false
Set-GateField -Object $gates -Name 'msi_profile_apply_enabled' -Value $false
Set-GateField -Object $gates -Name 'fan_write_enabled' -Value $false
Set-GateField -Object $gates -Name 'ec_write_enabled' -Value $false
Set-GateField -Object $gates -Name 'automation_apply_enabled' -Value $false
Write-Phase5Json -Path $gatePath -Data $gates

$manifest = [pscustomobject]@{
    generated_local = Get-Date -Format 's'
    phase = 'PHASE_5_GUARDED_CPU_APPLY_FOUNDATION_AND_UI_REFINEMENT'
    source_phase = 'PHASE_4_BACKUP_RESTORE_FOUNDATION_AND_SANDBOXED_APPLY_TESTS'
    active_power_plan_guid = Get-Phase5Property -Object $exportResult -Name 'active_power_plan_guid' -Default $null
    active_power_plan_name = Get-Phase5Property -Object $exportResult -Name 'active_power_plan_name' -Default $null
    active_power_plan_export = [pscustomobject]@{
        elevated = Get-Phase5Property -Object $exportResult -Name 'elevated' -Default $false
        export_path = Get-Phase5Property -Object $exportResult -Name 'export_path' -Default $null
        export_succeeded = $exported
        export_file_length = Get-Phase5Property -Object $exportResult -Name 'export_file_length' -Default 0
        failure_reason = Get-Phase5Property -Object $exportResult -Name 'failure_reason' -Default $null
        active_command = Get-Phase5Property -Object $exportResult -Name 'active_command' -Default $null
        export_command = Get-Phase5Property -Object $exportResult -Name 'export_command' -Default $null
        active_plan_modified = Get-Phase5Property -Object $exportResult -Name 'active_plan_modified' -Default $false
    }
    active_power_plan_query_snapshot_path = $activeSnapshotPath
    cpu_readable_values_snapshot_path = $latestCpuSnapshot
    app_config_backup_path = $appConfigBackup
    phase4_backup_manifest_present = [bool]$phase4BackupData
    phase4_restore_manifest_present = [bool]$phase4RestoreData
    phase4_sandbox_passed = $sandboxPassed
    msi_backup_continued_from_phase4 = $msiBackupContinued
    gates = $gates
    phase5_cpu_apply_gates_satisfied = $phase5Ready
    failures_or_blockers = @()
}

if (-not $exported) { $manifest.failures_or_blockers += "Active power plan export is not valid: $(Get-Phase5Property -Object $exportResult -Name 'failure_reason' -Default 'unknown failure')" }
if (-not $restoreManifestExists) { $manifest.failures_or_blockers += 'Phase 5 restore manifest does not exist yet.' }
if (-not $currentValuesSnapshotExists) { $manifest.failures_or_blockers += 'CPU readable values snapshot is missing.' }
if (-not $sandboxPassed) { $manifest.failures_or_blockers += 'Sandbox powercfg write test is not proven passed.' }

$manifestPath = Join-Path $backupRoot 'backup_manifest_latest.json'
Write-Phase5Json -Path $manifestPath -Data $manifest
$manifest
