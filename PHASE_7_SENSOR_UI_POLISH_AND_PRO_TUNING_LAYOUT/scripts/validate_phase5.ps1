[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'Phase5Common.ps1')

$root = Get-Phase5Root
$results = New-Object System.Collections.Generic.List[object]

function Add-Check {
    param([string]$Name, [bool]$Passed, [string]$Details = '')
    $script:results.Add([pscustomobject]@{ name = $Name; passed = $Passed; details = $Details }) | Out-Null
}

foreach ($relative in @(
    'phase5_report.md',
    'phase5_report.json',
    'phase5_validation.md',
    'scripts\export_active_power_plan_phase5.ps1',
    'scripts\create_phase5_backup_manifest.ps1',
    'scripts\generate_phase5_restore_scripts.ps1',
    'scripts\validate_phase5.ps1',
    'tests\phase5_contract_check.py',
    'tests\Test-Phase5Scripts.ps1',
    'config\apply_gate_config.json',
    'backups\backup_manifest_latest.json',
    'restore\restore_manifest_latest.json',
    'page_photos'
)) {
    $path = Join-Path $root $relative
    Add-Check "required_path:$relative" (Test-Path -LiteralPath $path) $path
}

Get-ChildItem -LiteralPath $root -Recurse -Filter '*.json' -File | ForEach-Object {
    try {
        Get-Content -LiteralPath $_.FullName -Raw | ConvertFrom-Json | Out-Null
        Add-Check "json_parse:$($_.Name)" $true $_.FullName
    } catch {
        Add-Check "json_parse:$($_.Name)" $false $_.Exception.Message
    }
}

Get-ChildItem -LiteralPath (Join-Path $root 'scripts') -Filter '*.ps1' -File | ForEach-Object {
    $errors = $null
    [System.Management.Automation.PSParser]::Tokenize((Get-Content -LiteralPath $_.FullName -Raw), [ref]$errors) | Out-Null
    Add-Check "powershell_parse:$($_.Name)" (-not ($errors -and $errors.Count)) ($(if ($errors -and $errors.Count) { $errors[0].Message } else { '' }))
}

$compile = & python -m compileall -q (Join-Path $root 'app') 2>&1
Add-Check 'python_compile_app' ($LASTEXITCODE -eq 0) ($compile | Out-String)

$contract = & python (Join-Path $root 'tests\phase5_contract_check.py') 2>&1
Add-Check 'phase5_ui_contract' ($LASTEXITCODE -eq 0) ($contract | Out-String)

$scriptContract = & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $root 'tests\Test-Phase5Scripts.ps1') 2>&1
Add-Check 'phase5_script_contract' ($LASTEXITCODE -eq 0) ($scriptContract | Out-String)

$lhmContract = & python (Join-Path $root 'tests\lhm_headline_check.py') 2>&1
Add-Check 'lhm_headline_contract' ($LASTEXITCODE -eq 0) ($lhmContract | Out-String)

$mainWindowText = Get-Content -LiteralPath (Join-Path $root 'app\ui\main_window.py') -Raw
Add-Check 'status_bar_no_cpu_cpu_prefix' (-not ($mainWindowText -match 'CPU\s+\{headline\.get\(')) 'MainWindow should use status_display directly.'

$gates = Get-Content -LiteralPath (Join-Path $root 'config\apply_gate_config.json') -Raw | ConvertFrom-Json
foreach ($field in @('cpu_guarded_apply_enabled', 'active_plan_write_enabled', 'msi_profile_apply_enabled', 'fan_write_enabled', 'ec_write_enabled', 'automation_apply_enabled')) {
    Add-Check "gate_false:$field" ($gates.$field -eq $false) "$field=$($gates.$field)"
}

foreach ($field in @('active_power_plan_exported', 'current_values_snapshot_exists', 'restore_manifest_exists', 'sandbox_powercfg_write_test_passed', 'cpu_apply_requires_confirmation', 'cpu_apply_low_medium_risk_only', 'cpu_restore_available')) {
    Add-Check "gate_present:$field" ($gates.PSObject.Properties.Name -contains $field) ''
}

$screens = Get-ChildItem -LiteralPath (Join-Path $root 'page_photos') -Filter '*.png' -File -ErrorAction SilentlyContinue
Add-Check 'page_photos_count_10' (($screens | Measure-Object).Count -eq 10) "count=$(($screens | Measure-Object).Count)"

$scanRoots = @('app', 'scripts', 'tests', 'config', 'presets') | ForEach-Object { Join-Path $root $_ }
$textFiles = foreach ($scanRoot in $scanRoots) {
    if (Test-Path -LiteralPath $scanRoot) {
        Get-ChildItem -LiteralPath $scanRoot -Recurse -File -Include '*.py','*.ps1','*.json','*.md','*.txt' |
            Where-Object { $_.Name -notlike 'validate_phase*.ps1' }
    }
}
$combined = ($textFiles | ForEach-Object { Get-Content -LiteralPath $_.FullName -Raw }) -join "`n"

Add-Check 'static_no_msi_profile_execution' (-not ($combined -match 'Start-Process.*MSIAfterburner.*-Profile[1-5]|&\s*.*MSIAfterburner.*-Profile[1-5]')) ''
Add-Check 'static_no_nvidia_write_commands' (-not ($combined -match 'nvidia-smi.*(\s-pl\s|--power-limit|-lgc|-lmc|--persistence-mode|\s-pm\s)')) ''
Add-Check 'static_no_registry_writes' (-not ($combined -match 'Set-ItemProperty|New-ItemProperty|Remove-ItemProperty')) ''
Add-Check 'static_no_scheduled_tasks' (-not ($combined -match 'Register-ScheduledTask|New-ScheduledTask|Set-ScheduledTask')) ''
Add-Check 'static_no_service_control' (-not ($combined -match 'Start-Service|Stop-Service|Restart-Service')) ''
Add-Check 'static_no_fan_or_ec_writes' (-not ($combined -match 'fan\s*apply|ec\s*write')) ''
Add-Check 'static_no_shell_true' (-not ($combined -match 'shell\s*=\s*True')) ''
Add-Check 'static_no_scheme_current_powercfg_write' (-not ($combined -match '/set(ac|dc)valueindex\s+SCHEME_CURRENT')) ''

$failed = @($results | Where-Object { -not $_.passed })
$summary = [pscustomobject]@{
    timestamp_local = Get-Date -Format 's'
    phase_root = $root
    total_checks = $results.Count
    failed_checks = $failed.Count
    results = $results
}

Write-Phase5Json -Path (Join-Path $root 'raw_outputs\phase5_validation.json') -Data $summary

$lines = @(
    '# Phase 5 Validation',
    '',
    "- Timestamp: $($summary.timestamp_local)",
    "- Total checks: $($summary.total_checks)",
    "- Failed checks: $($summary.failed_checks)",
    ''
)
foreach ($row in $results) {
    $status = if ($row.passed) { 'PASS' } else { 'FAIL' }
    $lines += "- $status - $($row.name)"
    if (-not $row.passed -and $row.details) {
        $lines += "  - $($row.details)"
    }
}
$lines | Set-Content -LiteralPath (Join-Path $root 'phase5_validation.md') -Encoding UTF8

$summary | ConvertTo-Json -Depth 12
if ($failed.Count -gt 0) {
    exit 1
}
