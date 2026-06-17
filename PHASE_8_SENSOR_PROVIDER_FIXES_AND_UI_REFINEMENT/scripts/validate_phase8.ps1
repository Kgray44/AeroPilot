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

function Write-Phase8Json {
    param([string]$Path, $Data)
    $parent = Split-Path -Parent $Path
    if (-not (Test-Path -LiteralPath $parent)) {
        New-Item -ItemType Directory -Path $parent | Out-Null
    }
    $Data | ConvertTo-Json -Depth 18 | Set-Content -LiteralPath $Path -Encoding UTF8
}

foreach ($relative in @(
    'phase8_report.md',
    'phase8_report.json',
    'docs\phase8_safety_boundary.md',
    'docs\cpu_sensor_provider_diagnostics.md',
    'docs\sensor_validity_model.md',
    'docs\gpu_sensor_classification_fix.md',
    'docs\sensors_ui_refinement.md',
    'docs\telemetry_provider_ladder.md',
    'docs\phase9_recommendation.md',
    'app\core\sensor_normalizer.py',
    'app\core\sensor_presentation.py',
    'app\core\telemetry_provider_registry.py',
    'app\adapters\cpu_telemetry_adapter.py',
    'app\adapters\librehardwaremonitor_adapter.py',
    'app\ui\telemetry_tab.py',
    'app\ui\telemetry_widgets.py',
    'config\sensor_favorites.json',
    'scripts\read_librehardwaremonitor_sensors.ps1',
    'scripts\capture_page_photos.py',
    'scripts\validate_phase8.ps1',
    'tests\phase8_sensor_validity_check.py',
    'tests\phase8_provider_pipeline_check.py',
    'tests\phase8_ui_contract_check.py',
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

$phase8Sensor = & python (Join-Path $root 'tests\phase8_sensor_validity_check.py') 2>&1
Add-Check 'phase8_sensor_validity_contract' ($LASTEXITCODE -eq 0) ($phase8Sensor | Out-String)

$providerPipeline = & python (Join-Path $root 'tests\phase8_provider_pipeline_check.py') 2>&1
Add-Check 'phase8_provider_pipeline_contract' ($LASTEXITCODE -eq 0) ($providerPipeline | Out-String)

$lhm = & python (Join-Path $root 'tests\lhm_headline_check.py') 2>&1
Add-Check 'lhm_headline_phase8_contract' ($LASTEXITCODE -eq 0) ($lhm | Out-String)

$env:QT_QPA_PLATFORM = 'offscreen'
$ui = & python (Join-Path $root 'tests\phase8_ui_contract_check.py') 2>&1
Add-Check 'phase8_ui_contract_offscreen' ($LASTEXITCODE -eq 0) ($ui | Out-String)

$expectedScreens = @(
    '01_dashboard.png',
    '02_cpu_presets_ac.png',
    '03_cpu_presets_dc.png',
    '04_gpu_profiles.png',
    '05_sensors_overview_refined.png',
    '06_sensors_cpu_partial_provider.png',
    '07_sensors_gpu_panels.png',
    '08_sensors_all_raw_validity.png',
    '09_sensors_cpu_diagnostics.png',
    '10_game_automation.png',
    '11_auto_tuning.png',
    '12_fan_experimental.png',
    '13_logs.png',
    '14_settings.png'
)
foreach ($screen in $expectedScreens) {
    $screenPath = Join-Path $root "page_photos\$screen"
    Add-Check "screenshot_exists:$screen" (Test-Path -LiteralPath $screenPath) $screenPath
}
$screenCount = (Get-ChildItem -LiteralPath (Join-Path $root 'page_photos') -Filter '*.png' -File -ErrorAction SilentlyContinue | Measure-Object).Count
Add-Check 'page_photos_count_14' ($screenCount -eq 14) "count=$screenCount"

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
$normalizerText = Get-Content -LiteralPath (Join-Path $root 'app\core\sensor_normalizer.py') -Raw
$presentationText = Get-Content -LiteralPath (Join-Path $root 'app\core\sensor_presentation.py') -Raw
$mainWindowText = Get-Content -LiteralPath (Join-Path $root 'app\ui\main_window.py') -Raw
$presentmonText = Get-Content -LiteralPath (Join-Path $root 'app\adapters\presentmon_adapter.py') -Raw
$registryText = Get-Content -LiteralPath (Join-Path $root 'app\core\telemetry_provider_registry.py') -Raw
$cpuTelemetryText = Get-Content -LiteralPath (Join-Path $root 'app\adapters\cpu_telemetry_adapter.py') -Raw

Add-Check 'sensors_tab_has_provider_status_section' ($sensorText -match 'sensor_provider_status_section') ''
Add-Check 'sensors_tab_has_validity_raw_columns' ($sensorText -match 'Validity reason' -and $sensorText -match 'Subcategory' -and $sensorText -match 'Provider') ''
Add-Check 'sensors_tab_has_cpu_diagnostics_export' ($sensorText -match 'sensor_export_cpu_diagnostics_button') ''
Add-Check 'telemetry_provider_registry_present' ($registryText -match 'class TelemetryProviderRegistry' -and $registryText -match 'ProviderStatus') ''
Add-Check 'refresh_attempts_registered_providers' ($mainWindowText -match 'register_static_provider\("hwinfo"' -and $mainWindowText -match 'register_static_provider\("windows_counters"' -and $mainWindowText -match 'refresh_provider_snapshots') ''
Add-Check 'hwinfo_shared_memory_probe_present' ($cpuTelemetryText -match 'OpenFileMappingW' -and $cpuTelemetryText -match 'HWiNFO_SENS_SM') ''
Add-Check 'windows_counter_provider_present' ($cpuTelemetryText -match 'Get-Counter' -and $cpuTelemetryText -match 'Processor Utility') ''
Add-Check 'wmi_acpi_provider_present' ($cpuTelemetryText -match 'Win32_TemperatureProbe' -and $cpuTelemetryText -match 'MSAcpi_ThermalZoneTemperature') ''
Add-Check 'cpu_diagnostics_exports_provider_sections' ($normalizerText -match 'provider_statuses' -and $normalizerText -match 'all_provider_sensors' -and $normalizerText -match 'fallback_chain_used' -and $normalizerText -match 'unavailable_reasons_by_metric') ''
Add-Check 'cpu_diagnostics_exports_next_recommended_action' ($normalizerText -match 'next_recommended_action' -and $normalizerText -match 'Start HWiNFO64 Sensors with shared memory enabled') ''
Add-Check 'sensors_tab_has_cpu_temp_guidance_block' ($sensorText -match 'sensor_cpu_temp_guidance_block' -and $sensorText -match 'Start HWiNFO64 Sensors and enable shared memory, then refresh') ''
Add-Check 'sensor_validity_states_present' ($normalizerText -match 'stale_zero' -and $normalizerText -match 'invalid_value' -and $normalizerText -match 'can_use_for_headline') ''
Add-Check 'cpu_zero_power_clock_marked_stale' ($normalizerText -match 'CPU power reported 0 W' -and $normalizerText -match 'CPU clock reported 0 MHz') ''
Add-Check 'cpu_card_can_use_load_primary' ($presentationText -match 'CPU load' -and $presentationText -match 'Temp.*unavailable' -and $presentationText -match 'VID') ''
Add-Check 'gpu_hw_types_categorized' ($normalizerText -match 'hw\.startswith\("gpu"\)' -and $normalizerText -match 'GpuNvidia|nvidia') ''
Add-Check 'gpu_255_junction_invalid' ($normalizerText -match 'reported \{value:g\} C, which is outside the trusted range') ''
Add-Check 'generic_memory_unit_gb' ($normalizerText -match 'generic memory' -and $normalizerText -match 'return "GB"') ''
Add-Check 'presentmon_no_csv_not_scary_ui_error' ($normalizerText -match 'No PresentMon CSV' -and $presentationText -match 'Start capture for FPS/frame-time') ''
Add-Check 'status_bar_uses_normalized_cpu_status' ($mainWindowText -match 'status_display' -and -not ($mainWindowText -match 'CPU CPU')) ''
Add-Check 'presentmon_not_started_in_main_window' (-not ($mainWindowText -match 'start_capture\s*\(')) ''
Add-Check 'presentmon_cleanup_on_close_present' ($mainWindowText -match 'cleanup_on_close' -and $presentmonText -match 'cleanup_on_close') ''

$scanRoots = @('app', 'scripts', 'tests', 'config', 'presets') | ForEach-Object { Join-Path $root $_ }
$textFiles = foreach ($scanRoot in $scanRoots) {
    if (Test-Path -LiteralPath $scanRoot) {
        Get-ChildItem -LiteralPath $scanRoot -Recurse -File -Include '*.py','*.ps1','*.json','*.md','*.txt' |
            Where-Object { $_.Name -notlike 'validate_phase*.ps1' -and $_.Name -notlike 'sandbox_powercfg_apply_test.ps1' -and $_.Name -notlike 'cleanup_sandbox_power_plan.ps1' }
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
Add-Check 'static_no_automatic_game_apply' (-not ($combined -match 'auto_apply"\s*:\s*true|automation_apply_enabled"\s*:\s*true')) ''

$failed = @($results | Where-Object { -not $_.passed })
$summary = [pscustomobject]@{
    timestamp_local = Get-Date -Format 's'
    phase_root = $root
    total_checks = $results.Count
    failed_checks = $failed.Count
    results = $results
}

Write-Phase8Json -Path (Join-Path $root 'raw_outputs\phase8_validation.json') -Data $summary

$lines = @(
    '# Phase 8 Validation',
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
$lines | Set-Content -LiteralPath (Join-Path $root 'phase8_validation.md') -Encoding UTF8

$summary | ConvertTo-Json -Depth 18
if ($failed.Count -gt 0) {
    exit 1
}
