param()

$ErrorActionPreference = 'Stop'
$phaseRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$env:PYTHONPATH = $phaseRoot

$check = & python -c "import importlib.util; raise SystemExit(0 if importlib.util.find_spec('PySide6') else 2)"
if ($LASTEXITCODE -ne 0) {
    Write-Host 'PySide6 is not installed in the active Python environment.'
    Write-Host 'The Phase 2 code and validation can still be reviewed statically.'
    Write-Host 'Install dependencies in a local virtual environment later with: pip install -r requirements.txt'
    exit 2
}

Write-Host 'Launching AERO X16 Control Center in READ-ONLY / DRY-RUN mode.'
& python -m app.main
