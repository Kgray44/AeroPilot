param(
    [string]$PhaseRoot = (Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path))
)

$ErrorActionPreference = 'Stop'

function Add-ValidationResult {
    param(
        [System.Collections.ArrayList]$Results,
        [string]$Name,
        [bool]$Passed,
        [string]$Details
    )

    [void]$Results.Add([pscustomobject]@{
        name    = $Name
        passed  = $Passed
        details = $Details
    })
}

function Test-RequiredPath {
    param(
        [System.Collections.ArrayList]$Results,
        [string]$BasePath,
        [string]$RelativePath
    )

    $path = Join-Path $BasePath $RelativePath
    Add-ValidationResult -Results $Results -Name "required_path:$RelativePath" -Passed (Test-Path -LiteralPath $path) -Details $path
}

function Test-JsonFile {
    param(
        [System.Collections.ArrayList]$Results,
        [string]$Path
    )

    try {
        $raw = Get-Content -LiteralPath $Path -Raw
        $null = $raw | ConvertFrom-Json
        Add-ValidationResult -Results $Results -Name "json_parse:$([IO.Path]::GetFileName($Path))" -Passed $true -Details $Path
    } catch {
        Add-ValidationResult -Results $Results -Name "json_parse:$([IO.Path]::GetFileName($Path))" -Passed $false -Details $_.Exception.Message
    }
}

function Test-PowerShellParse {
    param(
        [System.Collections.ArrayList]$Results,
        [string]$Path
    )

    $tokens = $null
    $parseErrors = $null
    [void][System.Management.Automation.Language.Parser]::ParseFile($Path, [ref]$tokens, [ref]$parseErrors)
    $passed = (@($parseErrors).Count -eq 0)
    $details = if ($passed) { $Path } else { (@($parseErrors) | ForEach-Object { $_.Message }) -join '; ' }
    Add-ValidationResult -Results $Results -Name "ps_parse:$([IO.Path]::GetFileName($Path))" -Passed $passed -Details $details
}

$results = New-Object System.Collections.ArrayList
$appRoot = Split-Path -Parent $PhaseRoot

$requiredPaths = @(
    'run_phase1_exploration.ps1',
    'phase1_exploration_report.md',
    'phase1_exploration_report.json',
    'discovered_paths.json',
    'discovered_capabilities.json',
    'risk_catalog.json',
    'command_inventory.md',
    'future_architecture_notes.md',
    'raw_outputs',
    'scripts\detect_msi_afterburner.ps1',
    'scripts\detect_powercfg_settings.ps1',
    'scripts\detect_nvidia_telemetry.ps1',
    'scripts\detect_presentmon.ps1',
    'scripts\detect_librehardwaremonitor.ps1',
    'scripts\detect_gigabyte_controls.ps1',
    'scripts\detect_process_targets.ps1',
    'app_probe\README.md'
)

foreach ($relativePath in $requiredPaths) {
    Test-RequiredPath -Results $results -BasePath $PhaseRoot -RelativePath $relativePath
}

Test-RequiredPath -Results $results -BasePath $appRoot -RelativePath 'README.md'

$scriptFiles = Get-ChildItem -LiteralPath $PhaseRoot -Filter '*.ps1' -Recurse -File -ErrorAction SilentlyContinue
foreach ($scriptFile in $scriptFiles) {
    Test-PowerShellParse -Results $results -Path $scriptFile.FullName
}

$jsonFiles = @(
    'phase1_exploration_report.json',
    'discovered_paths.json',
    'discovered_capabilities.json',
    'risk_catalog.json'
)

foreach ($relativePath in $jsonFiles) {
    $jsonPath = Join-Path $PhaseRoot $relativePath
    if (Test-Path -LiteralPath $jsonPath) {
        Test-JsonFile -Results $results -Path $jsonPath
    }
}

$reportPath = Join-Path $PhaseRoot 'phase1_exploration_report.md'
if (Test-Path -LiteralPath $reportPath) {
    $report = Get-Content -LiteralPath $reportPath -Raw
    $sections = @(
        'Summary',
        'What Was Discovered',
        'Reachability Matrix',
        'Risk Catalog Summary',
        'Recommended Phase 2',
        'Exact Files Created'
    )
    foreach ($section in $sections) {
        Add-ValidationResult -Results $results -Name "report_section:$section" -Passed ($report -match [regex]::Escape($section)) -Details $section
    }
}

$failed = @($results | Where-Object { -not $_.passed })
$summary = [pscustomobject]@{
    timestamp_local = (Get-Date).ToString('s')
    phase_root      = $PhaseRoot
    total_checks    = @($results).Count
    failed_checks   = @($failed).Count
    results         = @($results)
}

$summary | ConvertTo-Json -Depth 8

if (@($failed).Count -gt 0) {
    exit 1
}

exit 0
