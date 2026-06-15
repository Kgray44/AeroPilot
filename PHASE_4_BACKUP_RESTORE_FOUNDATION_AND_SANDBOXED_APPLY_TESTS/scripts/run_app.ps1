Set-StrictMode -Version 2.0
$ErrorActionPreference = "Stop"

$Phase4Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$env:PYTHONPATH = $Phase4Root
Write-Host "Launching AeroTune Phase 4 in guarded backup/restore mode."
python -m app.main
