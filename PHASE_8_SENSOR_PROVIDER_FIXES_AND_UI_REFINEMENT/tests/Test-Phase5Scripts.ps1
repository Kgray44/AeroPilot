Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$Root = Split-Path -Parent $PSScriptRoot

$requiredScripts = @(
    'scripts\export_active_power_plan_phase5.ps1',
    'scripts\create_phase5_backup_manifest.ps1',
    'scripts\generate_phase5_restore_scripts.ps1',
    'scripts\validate_phase5.ps1'
)

foreach ($relative in $requiredScripts) {
    $path = Join-Path $Root $relative
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Missing required Phase 5 script: $relative"
    }
    $errors = $null
    [System.Management.Automation.PSParser]::Tokenize((Get-Content -LiteralPath $path -Raw), [ref]$errors) | Out-Null
    if ($errors -and $errors.Count) {
        throw "PowerShell parse errors in ${relative}: $($errors[0].Message)"
    }
}

$gatePath = Join-Path $Root 'config\apply_gate_config.json'
if (-not (Test-Path -LiteralPath $gatePath)) {
    throw 'Missing config\apply_gate_config.json'
}

$gate = Get-Content -LiteralPath $gatePath -Raw | ConvertFrom-Json
foreach ($field in @('cpu_guarded_apply_enabled', 'cpu_apply_requires_confirmation', 'cpu_apply_low_medium_risk_only', 'cpu_restore_available', 'active_plan_write_enabled')) {
    if (-not ($gate.PSObject.Properties.Name -contains $field)) {
        throw "Missing Phase 5 apply gate field: $field"
    }
}

if ($gate.cpu_guarded_apply_enabled -ne $false) {
    throw 'cpu_guarded_apply_enabled must default false in Phase 5.'
}

if ($gate.active_plan_write_enabled -ne $false) {
    throw 'active_plan_write_enabled must remain false in Phase 5 unless gates are proven.'
}

'phase5 script contract ok'
