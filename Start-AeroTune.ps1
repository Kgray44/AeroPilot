[CmdletBinding()]
param(
    [int]$Phase,
    [switch]$DryRun,
    [switch]$Json,
    [switch]$ListPhases
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Convert-ToLauncherJson {
    param([Parameter(Mandatory = $true)]$Value)
    $Value | ConvertTo-Json -Depth 6
}

function Get-AeroTunePhaseRunners {
    param([Parameter(Mandatory = $true)][string]$Root)

    Get-ChildItem -LiteralPath $Root -Directory |
        Where-Object { $_.Name -match '^PHASE_(\d+)_' } |
        ForEach-Object {
            $match = [regex]::Match($_.Name, '^PHASE_(\d+)_')
            $runner = Join-Path $_.FullName 'scripts\run_app.ps1'
            [pscustomobject]@{
                phase_number = [int]$match.Groups[1].Value
                phase_name = $_.Name
                phase_root = $_.FullName
                runner = $runner
                runner_exists = Test-Path -LiteralPath $runner -PathType Leaf
            }
        } |
        Sort-Object phase_number -Descending
}

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$phaseRunners = @(Get-AeroTunePhaseRunners -Root $Root)
$runnablePhases = @($phaseRunners | Where-Object { $_.runner_exists })

if ($ListPhases) {
    if ($Json) {
        Convert-ToLauncherJson ([pscustomobject]@{
            app_name = 'AeroTune'
            root = $Root
            phases = $phaseRunners
        })
    } else {
        Write-Host 'AeroTune phase runners:'
        foreach ($item in $phaseRunners) {
            $status = if ($item.runner_exists) { 'runnable' } else { 'missing scripts\run_app.ps1' }
            Write-Host ("  Phase {0}: {1} [{2}]" -f $item.phase_number, $item.phase_name, $status)
        }
    }
    exit 0
}

if (-not $runnablePhases) {
    $message = "No runnable AeroTune phase was found under $Root. Expected PHASE_* folders with scripts\run_app.ps1."
    if ($Json) {
        Convert-ToLauncherJson ([pscustomobject]@{
            app_name = 'AeroTune'
            root = $Root
            ok = $false
            error = $message
        })
    } else {
        Write-Error $message
    }
    exit 1
}

if ($PSBoundParameters.ContainsKey('Phase')) {
    $selected = $runnablePhases | Where-Object { $_.phase_number -eq $Phase } | Select-Object -First 1
    if (-not $selected) {
        $available = ($runnablePhases | ForEach-Object { $_.phase_number }) -join ', '
        $message = "Requested Phase $Phase does not have a runnable scripts\run_app.ps1. Available runnable phases: $available"
        if ($Json) {
            Convert-ToLauncherJson ([pscustomobject]@{
                app_name = 'AeroTune'
                root = $Root
                ok = $false
                requested_phase = $Phase
                available_runnable_phases = @($runnablePhases | Select-Object -ExpandProperty phase_number)
                error = $message
            })
        } else {
            Write-Error $message
        }
        exit 1
    }
} else {
    $selected = $runnablePhases | Select-Object -First 1
}

$commandPreview = 'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "{0}"' -f $selected.runner
$result = [pscustomobject]@{
    app_name = 'AeroTune'
    root = $Root
    ok = $true
    dry_run = [bool]$DryRun
    selected_phase_number = $selected.phase_number
    selected_phase_name = $selected.phase_name
    selected_phase_root = $selected.phase_root
    selected_runner = $selected.runner
    command_preview = $commandPreview
}

if ($DryRun) {
    if ($Json) {
        Convert-ToLauncherJson $result
    } else {
        Write-Host 'AeroTune launcher dry-run:'
        Write-Host ("  Selected phase: {0} ({1})" -f $selected.phase_number, $selected.phase_name)
        Write-Host ("  Runner: {0}" -f $selected.runner)
        Write-Host ("  Command: {0}" -f $commandPreview)
    }
    exit 0
}

if ($Json) {
    Convert-ToLauncherJson $result
}

Write-Host ("Launching AeroTune from Phase {0}: {1}" -f $selected.phase_number, $selected.phase_name)
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $selected.runner
exit $LASTEXITCODE
