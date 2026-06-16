Set-StrictMode -Version 2.0
$ErrorActionPreference = "Stop"

$Phase6Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$env:PYTHONPATH = $Phase6Root
Write-Host "Launching AeroTune Phase 6 sensor command center."
python -m app.main
