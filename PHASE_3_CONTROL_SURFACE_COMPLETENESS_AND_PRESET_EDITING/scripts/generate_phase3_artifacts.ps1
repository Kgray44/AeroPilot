Set-StrictMode -Version 2.0
$ErrorActionPreference = "Stop"

$Phase3Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Generator = Join-Path $Phase3Root "scripts\generate_phase3_artifacts.py"

if (-not (Test-Path -LiteralPath $Generator)) {
    throw "Missing generator: $Generator"
}

$env:PYTHONPATH = $Phase3Root
python $Generator
if ($LASTEXITCODE -ne 0) {
    throw "Phase 3 artifact generation failed with exit code $LASTEXITCODE"
}
