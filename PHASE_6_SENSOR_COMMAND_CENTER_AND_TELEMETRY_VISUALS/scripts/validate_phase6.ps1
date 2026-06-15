[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
$results = New-Object System.Collections.Generic.List[object]

function Add-Check {
    param([string]$Name, [bool]$Passed, [string]$Details = '')
    $script:results.Add([pscustomobject]@{ name = $Name; passed = $Passed; details = $Details }) | Out-Null
}

function Write-Phase6Json {
    param([string]$Path, $Data)
    $parent = Split-Path -Parent $Path
    if (-not (Test-Path -LiteralPath $parent)) {
        New-Item -ItemType Directory -Path $parent | Out-Null
    }
    $Data | ConvertTo-Json -Depth 16 | Set-Content -LiteralPath $Path -Encoding UTF8
}

foreach ($relative in @(
    'phase6_report.md',
    'phase6_report.json',
    'docs\phase6_safety_boundary.md',
    'docs\sensor_command_center_design.md',
    'docs\sensor_normalization_model.md',
    'docs\cpu_temperature_detection_debugging.md',
    'docs\sensor_cards_and_visuals.md',
    'docs\presentmon_sensor_integration.md',
    'docs\phase7_recommendation.md',
    'app\core\sensor_normalizer.py',
    'app\core\sensor_history.py',
    'app\ui\telemetry_widgets.py',
    'app\ui\telemetry_tab.py',
    'config\sensor_favorites.json',
    'scripts\capture_page_photos.py',
    'scripts\validate_phase6.ps1',
    'tests\phase6_sensor_normalizer_check.py',
    'tests\phase6_ui_contract_check.py',
    'page_photos\README.md'
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

$compile = & python -m compileall -q (Join-Path $root 'app') (Join-Path $root 'tests') 2>&1
Add-Check 'python_compile_app_and_tests' ($LASTEXITCODE -eq 0) ($compile | Out-String)

$normalizer = & python (Join-Path $root 'tests\phase6_sensor_normalizer_check.py') 2>&1
Add-Check 'phase6_sensor_normalizer_contract' ($LASTEXITCODE -eq 0) ($normalizer | Out-String)

$lhm = & python (Join-Path $root 'tests\lhm_headline_check.py') 2>&1
Add-Check 'lhm_headline_contract' ($LASTEXITCODE -eq 0) ($lhm | Out-String)

$env:QT_QPA_PLATFORM = 'offscreen'
$ui = & python (Join-Path $root 'tests\phase6_ui_contract_check.py') 2>&1
Add-Check 'phase6_ui_contract_offscreen' ($LASTEXITCODE -eq 0) ($ui | Out-String)

$expectedScreens = @(
    '01_dashboard.png',
    '02_cpu_presets_ac.png',
    '03_cpu_presets_dc.png',
    '04_gpu_profiles.png',
    '05_sensors_overview.png',
    '06_sensors_all_raw.png',
    '07_sensors_cpu_diagnostics.png',
    '08_game_automation.png',
    '09_auto_tuning.png',
    '10_fan_experimental.png',
    '11_logs.png',
    '12_settings.png'
)
foreach ($screen in $expectedScreens) {
    $screenPath = Join-Path $root "page_photos\$screen"
    Add-Check "screenshot_exists:$screen" (Test-Path -LiteralPath $screenPath) $screenPath
}
$screenCount = (Get-ChildItem -LiteralPath (Join-Path $root 'page_photos') -Filter '*.png' -File -ErrorAction SilentlyContinue | Measure-Object).Count
Add-Check 'page_photos_count_12' ($screenCount -eq 12) "count=$screenCount"

$gatesPath = Join-Path $root 'config\apply_gate_config.json'
if (Test-Path -LiteralPath $gatesPath) {
    $gates = Get-Content -LiteralPath $gatesPath -Raw | ConvertFrom-Json
    foreach ($field in @('active_plan_write_enabled', 'msi_profile_apply_enabled', 'fan_write_enabled', 'ec_write_enabled', 'automation_apply_enabled')) {
        Add-Check "gate_false:$field" ($gates.$field -eq $false) "$field=$($gates.$field)"
    }
} else {
    Add-Check 'apply_gate_config_present' $false $gatesPath
}

$mainWindowText = Get-Content -LiteralPath (Join-Path $root 'app\ui\main_window.py') -Raw
Add-Check 'status_bar_uses_normalized_display' ($mainWindowText -match 'status_display' -and -not ($mainWindowText -match 'CPU\s+\{headline')) ''
Add-Check 'presentmon_not_started_in_main_window' (-not ($mainWindowText -match 'start_capture\s*\(')) ''

$sensorText = Get-Content -LiteralPath (Join-Path $root 'app\ui\telemetry_tab.py') -Raw
Add-Check 'sensors_tab_has_overview_cards' ($sensorText -match 'sensor_overview_cards' -and $sensorText -match 'MetricCard') ''
Add-Check 'sensors_tab_has_raw_explorer' ($sensorText -match 'sensor_raw_explorer_table') ''
Add-Check 'sensors_tab_has_cpu_diagnostics' ($sensorText -match 'sensor_cpu_diagnostics_table') ''

$normalizerText = Get-Content -LiteralPath (Join-Path $root 'app\core\sensor_normalizer.py') -Raw
foreach ($term in @('CPU Package', 'Core Max', 'P-Core Max', 'Tctl/Tdie')) {
    Add-Check "cpu_temp_priority_present:$term" ($normalizerText -match [regex]::Escape($term.ToLower())) ''
}

$scanRoots = @('app', 'scripts', 'tests', 'config', 'presets') | ForEach-Object { Join-Path $root $_ }
$textFiles = foreach ($scanRoot in $scanRoots) {
    if (Test-Path -LiteralPath $scanRoot) {
        Get-ChildItem -LiteralPath $scanRoot -Recurse -File -Include '*.py','*.ps1','*.json','*.md','*.txt' |
            Where-Object { $_.Name -notlike 'validate_phase*.ps1' }
    }
}
$combined = ($textFiles | ForEach-Object { Get-Content -LiteralPath $_.FullName -Raw }) -join "`n"

Add-Check 'static_no_msi_profile_execution' (-not ($combined -match '(Start-Process|subprocess|runner\.run|&\s*).*MSIAfterburner.*-Profile[1-5]')) ''
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

Write-Phase6Json -Path (Join-Path $root 'raw_outputs\phase6_validation.json') -Data $summary

$lines = @(
    '# Phase 6 Validation',
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
$lines | Set-Content -LiteralPath (Join-Path $root 'phase6_validation.md') -Encoding UTF8

$summary | ConvertTo-Json -Depth 16
if ($failed.Count -gt 0) {
    exit 1
}
