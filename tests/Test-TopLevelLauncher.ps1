Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$Root = Split-Path -Parent $PSScriptRoot
$Launcher = Join-Path $Root 'Start-AeroTune.ps1'

if (-not (Test-Path -LiteralPath $Launcher)) {
    throw "Missing top-level launcher: $Launcher"
}

$phaseCandidates = Get-ChildItem -LiteralPath $Root -Directory |
    Where-Object { $_.Name -match '^PHASE_(\d+)_' -and (Test-Path -LiteralPath (Join-Path $_.FullName 'scripts\run_app.ps1')) } |
    ForEach-Object {
        [pscustomobject]@{
            Number = [int]([regex]::Match($_.Name, '^PHASE_(\d+)_').Groups[1].Value)
            Name = $_.Name
            Runner = Join-Path $_.FullName 'scripts\run_app.ps1'
        }
    } |
    Sort-Object Number -Descending

if (-not $phaseCandidates) {
    throw 'No phase runner scripts were found for the launcher test.'
}

$expected = $phaseCandidates | Select-Object -First 1
$raw = & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $Launcher -DryRun -Json
if ($LASTEXITCODE -ne 0) {
    throw "Launcher dry-run failed with exit code $LASTEXITCODE"
}

$result = $raw | ConvertFrom-Json

if (-not $result.dry_run) {
    throw 'Expected launcher dry_run to be true.'
}

if ($result.selected_phase_name -ne $expected.Name) {
    throw "Expected phase '$($expected.Name)' but launcher selected '$($result.selected_phase_name)'."
}

if ($result.selected_runner -ne $expected.Runner) {
    throw "Expected runner '$($expected.Runner)' but launcher selected '$($result.selected_runner)'."
}

if ($result.command_preview -notmatch 'powershell\.exe') {
    throw 'Expected command_preview to contain powershell.exe.'
}

'top-level launcher contract ok'
