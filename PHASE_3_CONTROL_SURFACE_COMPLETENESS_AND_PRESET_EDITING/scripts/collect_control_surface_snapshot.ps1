Set-StrictMode -Version 2.0
$ErrorActionPreference = "Stop"

$Phase3Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$env:PYTHONPATH = $Phase3Root

python -m app.core.state_snapshot
if ($LASTEXITCODE -ne 0) {
    throw "Read-only control-surface snapshot failed with exit code $LASTEXITCODE"
}
