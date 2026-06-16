[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'Phase5Common.ps1')

$root = Get-Phase5Root
$restoreRoot = Join-Path $root 'restore'
$scriptRoot = Join-Path $restoreRoot 'generated_scripts'
New-Phase5Directory -Path $restoreRoot
New-Phase5Directory -Path $scriptRoot

$backupManifestPath = Join-Path $root 'backups\backup_manifest_latest.json'
$backup = $null
if (Test-Path -LiteralPath $backupManifestPath) {
    $backup = Get-Content -LiteralPath $backupManifestPath -Raw | ConvertFrom-Json
}

$powerPreview = Join-Path $scriptRoot 'restore_power_plan_preview.ps1'
@"
# Preview only. Do not run as a restore operation in Phase 5.
Write-Host 'PREVIEW ONLY: This would import a saved .pow file and optionally reactivate the prior active plan after explicit approval.'
# powercfg /import "<export_path_from_restore_manifest>"
# powercfg /setactive "<restored_or_previous_scheme_guid>"
"@ | Set-Content -LiteralPath $powerPreview -Encoding UTF8

$msiPreview = Join-Path $scriptRoot 'restore_msi_afterburner_files_preview.ps1'
@"
# Preview only. Do not run as a restore operation in Phase 5.
Write-Host 'PREVIEW ONLY: This would copy backed-up MSI Afterburner files back to their original paths after explicit approval.'
# Copy-Item -LiteralPath "<backup_file>" -Destination "<original_msi_path>" -Force
"@ | Set-Content -LiteralPath $msiPreview -Encoding UTF8

$appPreview = Join-Path $scriptRoot 'restore_app_config_preview.ps1'
@"
# Preview only. Do not run as a restore operation in Phase 5.
Write-Host 'PREVIEW ONLY: This would copy backed-up AeroTune config and preset JSON back into the app folder.'
# Copy-Item -LiteralPath "<backup_json>" -Destination "<phase5_config_or_preset_path>" -Force
"@ | Set-Content -LiteralPath $appPreview -Encoding UTF8

$cpuPreview = Join-Path $scriptRoot 'restore_cpu_settings_from_snapshot_preview.ps1'
$cpuLines = @(
    '# Preview only. Do not run as a restore operation in Phase 5.',
    "Write-Host 'PREVIEW ONLY: This would restore captured CPU setting values with powercfg after explicit approval.'"
)
$cpuSnapshotPath = Get-Phase5Property -Object $backup -Name 'cpu_readable_values_snapshot_path' -Default $null
if ($cpuSnapshotPath -and (Test-Path -LiteralPath $cpuSnapshotPath)) {
    $cpu = Get-Content -LiteralPath $cpuSnapshotPath -Raw | ConvertFrom-Json
    foreach ($setting in (Get-Phase5Property -Object $cpu -Name 'cpu_settings' -Default @())) {
        $settingGuid = Get-Phase5Property -Object $setting -Name 'setting_guid' -Default $null
        $readable = Get-Phase5Property -Object $setting -Name 'readable' -Default $false
        if ($readable -and $settingGuid) {
            $acValue = Get-Phase5Property -Object $setting -Name 'ac_value' -Default $null
            $dcValue = Get-Phase5Property -Object $setting -Name 'dc_value' -Default $null
            $activePlanGuid = Get-Phase5Property -Object $cpu -Name 'active_power_plan_guid' -Default '<active_plan_guid_from_snapshot>'
            if ($acValue -ne $null) {
                $cpuLines += "# powercfg /setacvalueindex $activePlanGuid SUB_PROCESSOR $settingGuid $acValue"
            }
            if ($dcValue -ne $null) {
                $cpuLines += "# powercfg /setdcvalueindex $activePlanGuid SUB_PROCESSOR $settingGuid $dcValue"
            }
        }
    }
}
$cpuLines | Set-Content -LiteralPath $cpuPreview -Encoding UTF8

$activeExport = Get-Phase5Property -Object $backup -Name 'active_power_plan_export' -Default $null
$activeExportSucceeded = [bool](Get-Phase5Property -Object $activeExport -Name 'export_succeeded' -Default $false)
$msiBackupAvailable = [bool](Get-Phase5Property -Object $backup -Name 'msi_backup_continued_from_phase4' -Default $false)
$appConfigBackupPath = Get-Phase5Property -Object $backup -Name 'app_config_backup_path' -Default $null

$restoreItems = @(
    [pscustomobject]@{
        name = 'Power plan export/import'
        available = $activeExportSucceeded
        preview_only = $true
        needs_admin = $true
        script = $powerPreview
        risk = 'Medium'
    },
    [pscustomobject]@{
        name = 'MSI Afterburner backed-up files'
        available = $msiBackupAvailable
        preview_only = $true
        needs_admin = 'maybe'
        script = $msiPreview
        risk = 'Medium'
    },
    [pscustomobject]@{
        name = 'AeroTune app config/presets'
        available = [bool]$appConfigBackupPath
        preview_only = $true
        needs_admin = $false
        script = $appPreview
        risk = 'Low'
    },
    [pscustomobject]@{
        name = 'CPU settings from captured current values'
        available = [bool]$cpuSnapshotPath
        preview_only = $true
        needs_admin = 'maybe'
        script = $cpuPreview
        risk = 'Medium'
    }
)

$manifest = [pscustomobject]@{
    generated_local = Get-Date -Format 's'
    phase = 'PHASE_5_GUARDED_CPU_APPLY_FOUNDATION_AND_UI_REFINEMENT'
    preview_only = $true
    restore_proven = $false
    items = $restoreItems
    required_confirmation = 'Explicit future-phase user approval required before any restore script executes.'
}
$manifestPath = Join-Path $restoreRoot 'restore_manifest_latest.json'
Write-Phase5Json -Path $manifestPath -Data $manifest

$planPath = Join-Path $restoreRoot 'restore_plan_latest.md'
@(
    '# Phase 5 Restore Plan',
    '',
    'All generated scripts are preview-only in Phase 5.',
    '',
    '- Power plan restore requires a valid `.pow` export and explicit future approval.',
    '- CPU setting restore commands are generated as comments from captured current values.',
    '- MSI Afterburner restore remains preview-only and does not run automatically.',
    '- App config restore remains preview-only.'
) | Set-Content -LiteralPath $planPath -Encoding UTF8

$manifest
