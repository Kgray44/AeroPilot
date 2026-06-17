Set-StrictMode -Version 2.0
$ErrorActionPreference = "Stop"

$Phase8Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$env:PYTHONPATH = $Phase8Root
Write-Host "Launching AeroTune Phase 8 sensor provider fixes and UI refinement."
python -m app.main
