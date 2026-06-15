param(
    [string]$OutputPath = ''
)

$ErrorActionPreference = 'Stop'
$phaseRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$env:PYTHONPATH = $phaseRoot

$argsList = @('-m', 'app.core.state_snapshot')
if (-not [string]::IsNullOrWhiteSpace($OutputPath)) {
    $argsList += @('--output', $OutputPath)
}

& python @argsList
exit $LASTEXITCODE
