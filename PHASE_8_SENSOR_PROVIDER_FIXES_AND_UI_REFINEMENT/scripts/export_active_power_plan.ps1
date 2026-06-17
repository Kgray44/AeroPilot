Set-StrictMode -Version 2.0
$ErrorActionPreference = "Stop"
. "$PSScriptRoot\Phase4Common.ps1"

$Phase4Root = Get-Phase4Root
$Raw = Join-Path $Phase4Root "raw_outputs\power_plan_backup"
$BackupDir = Join-Path $Phase4Root "backups\power_plans"
$SnapshotDir = Join-Path $Phase4Root "backups\snapshots"
$Phase3Root = Join-Path (Split-Path -Parent $Phase4Root) "PHASE_3_CONTROL_SURFACE_COMPLETENESS_AND_PRESET_EDITING"
Ensure-Directory $Raw
Ensure-Directory $BackupDir
Ensure-Directory $SnapshotDir

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$active = Get-ActivePowerSchemeCaptured -RawOutputDir $Raw
if (-not $active.guid) {
    throw "Unable to parse active power scheme. Refusing to continue."
}

$exportPath = Join-Path $BackupDir "active_power_plan_$timestamp.pow"
$export = Invoke-CapturedCommand -Name "powercfg_export_active_plan" -Command @("powercfg.exe", "/export", $exportPath, $active.guid) -RawOutputDir $Raw
$exportFileLength = 0
if (Test-Path -LiteralPath $exportPath) {
    $exportFileLength = (Get-Item -LiteralPath $exportPath).Length
}
$exportSucceeded = ($export.exit_code -eq 0 -and $exportFileLength -gt 0)

$fullQuery = Invoke-CapturedCommand -Name "powercfg_query_scheme_current_full" -Command @("powercfg.exe", "/query", "SCHEME_CURRENT") -RawOutputDir $Raw
$processorQuery = Invoke-CapturedCommand -Name "powercfg_query_scheme_current_processor" -Command @("powercfg.exe", "/query", "SCHEME_CURRENT", "SUB_PROCESSOR") -RawOutputDir $Raw

$manifest = Get-Content -LiteralPath (Join-Path $Phase3Root "config\control_surface_manifest.json") -Raw | ConvertFrom-Json
$cpuRows = @($manifest.controls | Where-Object {
    ($_.PSObject.Properties.Name -contains "setting_guid") -and $_.setting_guid -and $_.category -match "^CPU|Fan control"
})
$settings = New-Object System.Collections.ArrayList
foreach ($row in $cpuRows) {
    $guid = [string]$row.setting_guid
    $alias = if ($row.PSObject.Properties.Name -contains "alias") { [string]$row.alias } else { $null }
    $name = [string]$row.friendly_name
    $safeName = (($alias, $row.control_id, "setting") | Where-Object { $_ } | Select-Object -First 1) -replace "[^A-Za-z0-9_.-]", "_"
    $cmd = Invoke-CapturedCommand -Name "powercfg_query_active_$safeName" -Command @("powercfg.exe", "/query", "SCHEME_CURRENT", "SUB_PROCESSOR", $guid) -RawOutputDir $Raw
    $values = Parse-PowerCfgSettingValues -Text $cmd.stdout
    [void]$settings.Add([pscustomobject]@{
        control_id = $row.control_id
        friendly_name = $name
        alias = $alias
        setting_guid = $guid
        readable = ($cmd.exit_code -eq 0 -and ($values.ac_value -ne $null -or $values.dc_value -ne $null))
        ac_value = $values.ac_value
        dc_value = $values.dc_value
        ac_hex = $values.ac_hex
        dc_hex = $values.dc_hex
        command = $cmd
    })
}

$cpuSnapshotPath = Join-Path $SnapshotDir "cpu_readable_values_$timestamp.json"
$powerSnapshotPath = Join-Path $SnapshotDir "active_power_plan_snapshot_$timestamp.json"

$snapshot = [pscustomobject]@{
    generated_local = (Get-Date).ToString("s")
    active_power_plan = [pscustomobject]@{ guid = $active.guid; name = $active.name; raw = $active.raw }
    active_power_plan_export_path = $exportPath
    full_query_stdout_path = $fullQuery.stdout_path
    processor_query_stdout_path = $processorQuery.stdout_path
    cpu_settings = $settings
    commands = @($active.command, $export, $fullQuery, $processorQuery)
}

Write-JsonFile -Path $cpuSnapshotPath -Data ([pscustomobject]@{
    generated_local = (Get-Date).ToString("s")
    active_power_plan_guid = $active.guid
    active_power_plan_name = $active.name
    cpu_settings = $settings
}) | Out-Null
Write-JsonFile -Path $powerSnapshotPath -Data $snapshot | Out-Null

$result = [pscustomobject]@{
    generated_local = (Get-Date).ToString("s")
    active_power_plan_guid = $active.guid
    active_power_plan_name = $active.name
    active_power_plan_export_path = $exportPath
    active_power_plan_export_file_length = $exportFileLength
    active_power_plan_query_snapshot_path = $powerSnapshotPath
    cpu_readable_values_snapshot_path = $cpuSnapshotPath
    export_succeeded = $exportSucceeded
    export_failure_reason = if ($exportSucceeded) { $null } else { ($export.error, $export.stderr, "Export command failed or produced an empty .pow file.") -ne $null | Select-Object -First 1 }
    commands = @($active.command, $export, $fullQuery, $processorQuery)
}

Write-JsonFile -Path (Join-Path $Raw "export_active_power_plan_result.json") -Data $result | Out-Null
$result | ConvertTo-Json -Depth 12
