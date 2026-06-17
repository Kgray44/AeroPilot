Set-StrictMode -Version 2.0
$ErrorActionPreference = "Stop"
. "$PSScriptRoot\Phase4Common.ps1"

$Phase4Root = Get-Phase4Root
$RestoreDir = Join-Path $Phase4Root "restore"
$Generated = Join-Path $RestoreDir "generated_scripts"
$BackupManifestPath = Join-Path $Phase4Root "backups\backup_manifest_latest.json"
Ensure-Directory $Generated

$backup = if (Test-Path -LiteralPath $BackupManifestPath) { Get-Content -LiteralPath $BackupManifestPath -Raw | ConvertFrom-Json } else { $null }

$powerScript = @'
Set-StrictMode -Version 2.0
$ErrorActionPreference = "Stop"
Write-Host "PREVIEW ONLY: This script would import/reactivate a backed-up power plan in a future approved phase."
Write-Host "No command is executed in Phase 4."
Write-Host "Future command template:"
Write-Host "powercfg [preview-only] /import <backup.pow>"
Write-Host "powercfg [preview-only] /setactive <imported_scheme_guid>"
'@
$msiScript = @'
Set-StrictMode -Version 2.0
$ErrorActionPreference = "Stop"
Write-Host "PREVIEW ONLY: This script would restore MSI Afterburner backup files in a future approved phase."
Write-Host "No files are copied back in Phase 4."
Write-Host "Future operation template: Copy-Item -LiteralPath <backup_file> -Destination <original_file> -Force"
'@
$appScript = @'
Set-StrictMode -Version 2.0
$ErrorActionPreference = "Stop"
Write-Host "PREVIEW ONLY: This script would restore app config/preset JSON from Phase 4 backup."
Write-Host "No files are copied back in Phase 4."
Write-Host "Future operation template: Copy-Item -LiteralPath <backup_json> -Destination <phase4_json> -Force"
'@

$powerPath = Join-Path $Generated "restore_power_plan_preview.ps1"
$msiPath = Join-Path $Generated "restore_msi_afterburner_files_preview.ps1"
$appPath = Join-Path $Generated "restore_app_config_preview.ps1"
$powerScript | Set-Content -LiteralPath $powerPath -Encoding UTF8
$msiScript | Set-Content -LiteralPath $msiPath -Encoding UTF8
$appScript | Set-Content -LiteralPath $appPath -Encoding UTF8

$entries = New-Object System.Collections.ArrayList
if ($backup) {
    $powerExportPath = [string]$backup.active_power_plan_export_path
    $powerExportUsable = ($backup.active_power_plan_export_succeeded -eq $true -and $powerExportPath -and (Test-Path -LiteralPath $powerExportPath) -and ((Get-Item -LiteralPath $powerExportPath).Length -gt 0))
    [void]$entries.Add([pscustomobject]@{
        restore_id = "power_plan.active_export"
        can_restore = $powerExportUsable
        source_backup_path = $backup.active_power_plan_export_path
        destination_path = "Windows power plan store"
        restore_proven = $false
        preview_only = $true
        needs_admin = "maybe"
        preview_command = "powercfg [preview-only] /import <backup.pow>"
        blocked_reason = if ($powerExportUsable) { $null } else { "No usable .pow export is available. The non-admin export attempt was blocked or produced an empty file." }
        risk_level = "Medium"
        required_user_confirmation = "Explicit future apply-phase confirmation"
        verification_steps = @("Import plan", "confirm GUID", "compare settings", "only then set active if explicitly approved")
    })
    [void]$entries.Add([pscustomobject]@{
        restore_id = "msi_afterburner.files"
        can_restore = ($backup.msi_files_copied.Count -gt 0)
        source_backup_path = Join-Path $Phase4Root "backups\msi_afterburner\files"
        destination_path = $backup.msi_afterburner_install_folder
        restore_proven = $false
        preview_only = $true
        needs_admin = "yes_for_program_files"
        preview_command = "Copy backed-up MSI files to original paths"
        risk_level = "High"
        required_user_confirmation = "Explicit future restore confirmation"
        verification_steps = @("Close MSI Afterburner", "copy files", "verify hashes", "restart MSI manually")
    })
    [void]$entries.Add([pscustomobject]@{
        restore_id = "app_config.json_files"
        can_restore = $true
        source_backup_path = Join-Path $Phase4Root "backups\app_config"
        destination_path = $Phase4Root
        restore_proven = $false
        preview_only = $true
        needs_admin = "no"
        preview_command = "Copy app JSON backups into Phase 4 config/presets"
        risk_level = "Safe"
        required_user_confirmation = "Explicit future app-config restore confirmation"
        verification_steps = @("Parse JSON", "restart app", "verify expected preset state")
    })
}

$manifest = [pscustomobject]@{
    generated_local = (Get-Date).ToString("s")
    preview_only = $true
    restore_entries = $entries
    generated_scripts = @($powerPath, $msiPath, $appPath)
}
Write-JsonFile -Path (Join-Path $RestoreDir "restore_manifest_latest.json") -Data $manifest | Out-Null

$lines = New-Object System.Collections.ArrayList
[void]$lines.Add("# Phase 4 Restore Plan")
[void]$lines.Add("")
[void]$lines.Add("Restore scripts are preview-only in Phase 4.")
foreach ($entry in $entries) {
    [void]$lines.Add("")
    [void]$lines.Add("## $($entry.restore_id)")
    [void]$lines.Add("- Source: $($entry.source_backup_path)")
    [void]$lines.Add("- Destination: $($entry.destination_path)")
    [void]$lines.Add("- Preview command: $($entry.preview_command)")
    [void]$lines.Add("- Restore proven: $($entry.restore_proven)")
}
$lines | Set-Content -LiteralPath (Join-Path $RestoreDir "restore_plan_latest.md") -Encoding UTF8
$manifest | ConvertTo-Json -Depth 10
