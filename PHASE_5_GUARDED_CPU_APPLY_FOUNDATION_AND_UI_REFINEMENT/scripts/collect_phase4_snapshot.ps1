Set-StrictMode -Version 2.0
$ErrorActionPreference = "Stop"

$Phase4Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$env:PYTHONPATH = $Phase4Root
python -m app.core.state_snapshot --output (Join-Path $Phase4Root "raw_outputs\phase4_snapshot_latest.json")
if ($LASTEXITCODE -ne 0) {
    throw "Phase 4 snapshot failed with exit code $LASTEXITCODE"
}
