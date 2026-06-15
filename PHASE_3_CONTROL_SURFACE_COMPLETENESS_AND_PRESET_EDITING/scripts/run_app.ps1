Set-StrictMode -Version 2.0
$ErrorActionPreference = "Stop"

$Phase3Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$env:PYTHONPATH = $Phase3Root

Write-Host "Launching AERO X16 Control Center Phase 3 in READ-ONLY / DRY-RUN mode."
python -m app.main
