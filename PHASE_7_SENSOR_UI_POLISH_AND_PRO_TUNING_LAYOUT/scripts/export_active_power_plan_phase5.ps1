[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'Phase5Common.ps1')

$root = Get-Phase5Root
$timestamp = Get-Phase5Timestamp
$rawDir = Join-Path $root 'raw_outputs\power_plan_backup_phase5'
$backupDir = Join-Path $root 'backups\power_plans'
New-Phase5Directory -Path $rawDir
New-Phase5Directory -Path $backupDir

$activeResult = Invoke-Phase5Command -Name 'phase5_powercfg_get_active_scheme' -Command @('powercfg.exe', '/getactivescheme') -OutputDirectory $rawDir
$active = Get-Phase5ActiveScheme -RawText $activeResult.stdout
$exportPath = Join-Path $backupDir "active_power_plan_phase5_$timestamp.pow"
$exportResult = $null
$usable = $false
$failureReason = $null

if ($active.guid) {
    $exportResult = Invoke-Phase5Command -Name 'phase5_powercfg_export_active_plan' -Command @('powercfg.exe', '/export', $exportPath, $active.guid) -OutputDirectory $rawDir
    if ((Test-Path -LiteralPath $exportPath) -and ((Get-Item -LiteralPath $exportPath).Length -gt 0) -and $exportResult.exit_code -eq 0) {
        $usable = $true
    } else {
        $combined = (($exportResult.stdout + "`n" + $exportResult.stderr).Trim())
        if ($combined) {
            $failureReason = $combined
        } else {
            $failureReason = 'Export failed or produced a zero-byte file.'
        }
    }
} else {
    $failureReason = 'Could not read active power scheme GUID.'
}

$fileLength = 0
if (Test-Path -LiteralPath $exportPath) {
    $fileLength = (Get-Item -LiteralPath $exportPath).Length
}

$result = [pscustomobject]@{
    generated_local = Get-Date -Format 's'
    phase = 'PHASE_5_GUARDED_CPU_APPLY_FOUNDATION_AND_UI_REFINEMENT'
    elevated = Test-Phase5Elevated
    active_power_plan_guid = $active.guid
    active_power_plan_name = $active.name
    export_path = $exportPath
    export_succeeded = $usable
    export_file_length = $fileLength
    failure_reason = $failureReason
    active_command = [pscustomobject]@{
        command = $activeResult.command
        exit_code = $activeResult.exit_code
        stdout_path = $activeResult.stdout_path
        stderr_path = $activeResult.stderr_path
    }
    export_command = if ($exportResult) {
        [pscustomobject]@{
            command = $exportResult.command
            exit_code = $exportResult.exit_code
            stdout_path = $exportResult.stdout_path
            stderr_path = $exportResult.stderr_path
        }
    } else {
        $null
    }
    active_plan_modified = $false
}

$resultPath = Join-Path $rawDir 'export_active_power_plan_phase5_result.json'
Write-Phase5Json -Path $resultPath -Data $result
$latestPath = Join-Path $root 'raw_outputs\export_active_power_plan_phase5_result.json'
Write-Phase5Json -Path $latestPath -Data $result
$result
