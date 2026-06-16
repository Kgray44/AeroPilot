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

function Write-Phase7Json {
    param([string]$Path, $Data)
    $parent = Split-Path -Parent $Path
    if (-not (Test-Path -LiteralPath $parent)) {
        New-Item -ItemType Directory -Path $parent | Out-Null
    }
    $Data | ConvertTo-Json -Depth 16 | Set-Content -LiteralPath $Path -Encoding UTF8
}

foreach ($relative in @(
    'phase7_report.md',
    'phase7_report.json',
    'docs\phase7_safety_boundary.md',
    'docs\sensors_ui_polish_design.md',
    'docs\hero_metric_cards_design.md',
    'docs\hardware_panels_design.md',
    'docs\all_sensors_explorer_design.md',
    'docs\cpu_diagnostics_ui_design.md',
    'docs\phase8_recommendation.md',
    'app\core\sensor_presentation.py',
    'app\core\sensor_normalizer.py',
    'app\core\sensor_history.py',
    'app\ui\telemetry_widgets.py',
    'app\ui\telemetry_tab.py',
    'config\sensor_favorites.json',
    'scripts\capture_page_photos.py',
    'scripts\validate_phase7.ps1',
    'tests\phase7_sensor_presentation_check.py',
    'tests\phase7_ui_contract_check.py',
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

$phase6Normalizer = & python (Join-Path $root 'tests\phase6_sensor_normalizer_check.py') 2>&1
Add-Check 'phase6_sensor_normalizer_contract' ($LASTEXITCODE -eq 0) ($phase6Normalizer | Out-String)

$lhm = & python (Join-Path $root 'tests\lhm_headline_check.py') 2>&1
Add-Check 'lhm_headline_contract' ($LASTEXITCODE -eq 0) ($lhm | Out-String)

$presentation = & python (Join-Path $root 'tests\phase7_sensor_presentation_check.py') 2>&1
Add-Check 'phase7_sensor_presentation_contract' ($LASTEXITCODE -eq 0) ($presentation | Out-String)

$env:QT_QPA_PLATFORM = 'offscreen'
$ui = & python (Join-Path $root 'tests\phase7_ui_contract_check.py') 2>&1
Add-Check 'phase7_ui_contract_offscreen' ($LASTEXITCODE -eq 0) ($ui | Out-String)

$expectedScreens = @(
    '01_dashboard.png',
    '02_cpu_presets_ac.png',
    '03_cpu_presets_dc.png',
    '04_gpu_profiles.png',
    '05_sensors_overview_polished.png',
    '06_sensors_hardware_panels.png',
    '07_sensors_all_raw_explorer.png',
    '08_sensors_cpu_diagnostics.png',
    '09_game_automation.png',
    '10_auto_tuning.png',
    '11_fan_experimental.png',
    '12_logs.png',
    '13_settings.png'
)
foreach ($screen in $expectedScreens) {
    $screenPath = Join-Path $root "page_photos\$screen"
    Add-Check "screenshot_exists:$screen" (Test-Path -LiteralPath $screenPath) $screenPath
}
$screenCount = (Get-ChildItem -LiteralPath (Join-Path $root 'page_photos') -Filter '*.png' -File -ErrorAction SilentlyContinue | Measure-Object).Count
Add-Check 'page_photos_count_13' ($screenCount -eq 13) "count=$screenCount"

$gatesPath = Join-Path $root 'config\apply_gate_config.json'
if (Test-Path -LiteralPath $gatesPath) {
    $gates = Get-Content -LiteralPath $gatesPath -Raw | ConvertFrom-Json
    foreach ($field in @('active_plan_write_enabled', 'msi_profile_apply_enabled', 'fan_write_enabled', 'ec_write_enabled', 'automation_apply_enabled')) {
        Add-Check "gate_false:$field" ($gates.$field -eq $false) "$field=$($gates.$field)"
    }
} else {
    Add-Check 'apply_gate_config_present' $false $gatesPath
}

$sensorText = Get-Content -LiteralPath (Join-Path $root 'app\ui\telemetry_tab.py') -Raw
$widgetText = Get-Content -LiteralPath (Join-Path $root 'app\ui\telemetry_widgets.py') -Raw
$presentationText = Get-Content -LiteralPath (Join-Path $root 'app\core\sensor_presentation.py') -Raw
$mainWindowText = Get-Content -LiteralPath (Join-Path $root 'app\ui\main_window.py') -Raw

Add-Check 'sensors_tab_has_hero_metric_cards' ($sensorText -match 'sensor_hero_strip' -and $widgetText -match 'class HeroMetricCard') ''
Add-Check 'sensors_tab_has_status_pills' ($sensorText -match 'sensor_status_pills' -and $widgetText -match 'class StatusPill') ''
Add-Check 'sensors_tab_has_hardware_panels' ($sensorText -match 'sensor_hardware_panels' -and $widgetText -match 'class HardwarePanel') ''
Add-Check 'sensors_tab_has_raw_explorer' ($sensorText -match 'sensor_all_raw_explorer_table') ''
Add-Check 'sensors_tab_has_cpu_diagnostics' ($sensorText -match 'sensor_cpu_diagnostics_panel') ''
Add-Check 'top_overview_not_count_status_hero_cards' ($presentationText -match 'Memory / VRAM' -and -not ($presentationText -match '"Sensor Count"|"Read Status"')) ''
Add-Check 'hero_metric_dedupes_value_subtitle' ($widgetText -match 'subtitle\.strip\(\)\.lower\(\) == self\.value_label\.text\(\)\.strip\(\)\.lower\(\)') ''
Add-Check 'grouped_overview_not_table_first' (-not ($sensorText -match 'group_tables') -and ($sensorText -match 'HardwarePanel')) ''
Add-Check 'cpu_diagnostics_accepted_not_tiny' ($sensorText -match 'setMinimumHeight\(200\)' -and -not ($sensorText -match 'setFixedHeight\(92\)')) ''
Add-Check 'status_bar_uses_normalized_display' ($mainWindowText -match 'status_display' -and -not ($mainWindowText -match 'CPU\s+\{headline')) ''
Add-Check 'presentmon_not_started_in_main_window' (-not ($mainWindowText -match 'start_capture\s*\(')) ''

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
Add-Check 'static_no_automatic_game_apply' (-not ($combined -match 'auto_apply"\s*:\s*true|automation_apply_enabled"\s*:\s*true')) ''

$failed = @($results | Where-Object { -not $_.passed })
$summary = [pscustomobject]@{
    timestamp_local = Get-Date -Format 's'
    phase_root = $root
    total_checks = $results.Count
    failed_checks = $failed.Count
    results = $results
}

Write-Phase7Json -Path (Join-Path $root 'raw_outputs\phase7_validation.json') -Data $summary

$lines = @(
    '# Phase 7 Validation',
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
$lines | Set-Content -LiteralPath (Join-Path $root 'phase7_validation.md') -Encoding UTF8

$summary | ConvertTo-Json -Depth 16
if ($failed.Count -gt 0) {
    exit 1
}
