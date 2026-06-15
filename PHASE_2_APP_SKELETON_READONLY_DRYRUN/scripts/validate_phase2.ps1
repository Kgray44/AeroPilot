param(
    [string]$PhaseRoot = (Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path))
)

$ErrorActionPreference = 'Stop'

function Add-Result {
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

function Test-PathExists {
    param(
        [System.Collections.ArrayList]$Results,
        [string]$Base,
        [string]$RelativePath
    )

    $path = Join-Path $Base $RelativePath
    Add-Result -Results $Results -Name "required_path:$RelativePath" -Passed (Test-Path -LiteralPath $path) -Details $path
}

function Test-Json {
    param(
        [System.Collections.ArrayList]$Results,
        [string]$Path
    )

    try {
        $null = Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json -ErrorAction Stop
        Add-Result -Results $Results -Name "json_parse:$([IO.Path]::GetFileName($Path))" -Passed $true -Details $Path
    } catch {
        Add-Result -Results $Results -Name "json_parse:$([IO.Path]::GetFileName($Path))" -Passed $false -Details $_.Exception.Message
    }
}

function Invoke-ValidationCommand {
    param(
        [string]$FilePath,
        [string[]]$Arguments,
        [int]$TimeoutSeconds = 60
    )

    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $FilePath
    $psi.Arguments = ($Arguments | ForEach-Object {
        if ($_ -match '[\s"]') { '"' + ($_ -replace '"', '\"') + '"' } else { $_ }
    }) -join ' '
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.CreateNoWindow = $true

    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $psi
    [void]$process.Start()
    $stdoutTask = $process.StandardOutput.ReadToEndAsync()
    $stderrTask = $process.StandardError.ReadToEndAsync()
    $exited = $process.WaitForExit($TimeoutSeconds * 1000)
    if (-not $exited) {
        try { $process.Kill() } catch { }
    } else {
        $process.WaitForExit()
    }

    $stdoutText = ''
    $stderrText = ''
    try { $stdoutText = $stdoutTask.Result } catch { $stdoutText = '' }
    try { $stderrText = $stderrTask.Result } catch { $stderrText = '' }

    return [pscustomobject]@{
        exit_code = if ($exited) { $process.ExitCode } else { $null }
        timed_out = -not $exited
        stdout    = $stdoutText
        stderr    = $stderrText
    }
}

$appRoot = Split-Path -Parent $PhaseRoot
$phase1Root = Join-Path $appRoot 'PHASE_1_EXPLORATION'
$results = New-Object System.Collections.ArrayList

$requiredDirs = @(
    'raw_outputs',
    'screenshots',
    'logs',
    'tests',
    'scripts',
    'docs',
    'app',
    'app\core',
    'app\adapters',
    'app\ui',
    'app\resources',
    'config',
    'presets',
    'restore'
)

foreach ($dir in $requiredDirs) {
    Test-PathExists -Results $results -Base $PhaseRoot -RelativePath $dir
}

$requiredFiles = @(
    'phase2_report.md',
    'phase2_report.json',
    'phase2_validation.md',
    'requirements.txt',
    'scripts\run_app.ps1',
    'scripts\validate_phase2.ps1',
    'scripts\collect_readonly_snapshot.ps1',
    'docs\app_architecture_cleaned.md',
    'docs\safety_model.md',
    'docs\phase3_recommendation.md',
    'docs\presentmon_candidate_notes.md',
    'docs\msi_profile_slot_mapping_notes.md',
    'app\__init__.py',
    'app\main.py',
    'app\core\__init__.py',
    'app\core\app_paths.py',
    'app\core\config_loader.py',
    'app\core\risk_model.py',
    'app\core\preset_schema.py',
    'app\core\state_snapshot.py',
    'app\core\command_runner.py',
    'app\core\dryrun.py',
    'app\core\logging_setup.py',
    'app\adapters\__init__.py',
    'app\adapters\phase1_data_adapter.py',
    'app\adapters\powercfg_adapter.py',
    'app\adapters\nvidia_smi_adapter.py',
    'app\adapters\msi_afterburner_adapter.py',
    'app\adapters\presentmon_adapter.py',
    'app\adapters\process_adapter.py',
    'app\adapters\librehardwaremonitor_adapter.py',
    'app\adapters\gigabyte_adapter.py',
    'app\ui\__init__.py',
    'app\ui\main_window.py',
    'app\ui\dashboard_tab.py',
    'app\ui\cpu_tab.py',
    'app\ui\gpu_tab.py',
    'app\ui\telemetry_tab.py',
    'app\ui\game_automation_tab.py',
    'app\ui\autotuning_tab.py',
    'app\ui\fan_experimental_tab.py',
    'app\ui\logs_tab.py',
    'app\ui\settings_safety_tab.py',
    'app\resources\app_styles.qss',
    'config\app_config.json',
    'config\tool_paths.json',
    'config\capability_cache.json',
    'presets\README.md',
    'presets\preset_schema.example.json',
    'presets\cpu_presets.example.json',
    'presets\gpu_profiles.example.json',
    'presets\game_rules.example.json',
    'restore\README.md',
    'restore\no_restore_manifests_yet.txt'
)

foreach ($file in $requiredFiles) {
    Test-PathExists -Results $results -Base $PhaseRoot -RelativePath $file
}

$phase1Files = @(
    'phase1_exploration_report.json',
    'discovered_paths.json',
    'discovered_capabilities.json',
    'risk_catalog.json',
    'app_probe\process_targets_seed.json'
)

foreach ($file in $phase1Files) {
    $path = Join-Path $phase1Root $file
    Add-Result -Results $results -Name "phase1_source:$file" -Passed (Test-Path -LiteralPath $path) -Details $path
    if (Test-Path -LiteralPath $path) {
        Test-Json -Results $results -Path $path
    }
}

Get-ChildItem -LiteralPath $PhaseRoot -Recurse -Filter '*.json' -File -ErrorAction SilentlyContinue | ForEach-Object {
    Test-Json -Results $results -Path $_.FullName
}

$python = Get-Command python -ErrorAction SilentlyContinue
if ($python) {
    $compile = Invoke-ValidationCommand -FilePath $python.Source -Arguments @('-m','compileall','-q',(Join-Path $PhaseRoot 'app')) -TimeoutSeconds 60
    Add-Result -Results $results -Name 'python_compile_app' -Passed (($compile.exit_code -eq 0) -and (-not $compile.timed_out)) -Details (($compile.stdout + $compile.stderr).Trim())

    $importCheck = Join-Path $PhaseRoot 'tests\phase2_import_check.py'
    if (Test-Path -LiteralPath $importCheck) {
        $env:PYTHONPATH = $PhaseRoot
        $import = Invoke-ValidationCommand -FilePath $python.Source -Arguments @($importCheck) -TimeoutSeconds 60
        Add-Result -Results $results -Name 'python_import_check' -Passed (($import.exit_code -eq 0) -and (-not $import.timed_out)) -Details (($import.stdout + $import.stderr).Trim())
    } else {
        Add-Result -Results $results -Name 'python_import_check' -Passed $false -Details 'tests\phase2_import_check.py missing'
    }

    $pyside = Invoke-ValidationCommand -FilePath $python.Source -Arguments @('-c','import importlib.util; raise SystemExit(0 if importlib.util.find_spec("PySide6") else 2)') -TimeoutSeconds 20
    Add-Result -Results $results -Name 'pyside6_available' -Passed ($pyside.exit_code -eq 0) -Details "exit=$($pyside.exit_code)"
} else {
    Add-Result -Results $results -Name 'python_available' -Passed $false -Details 'python command not found'
}

$validatorPath = (Get-Item -LiteralPath $MyInvocation.MyCommand.Path).FullName
$codeFiles = Get-ChildItem -LiteralPath $PhaseRoot -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object { @('.py', '.ps1') -contains $_.Extension.ToLowerInvariant() } |
    Where-Object { $_.FullName -ne $validatorPath }
$hardBlockedPatterns = @(
    'Register-ScheduledTask',
    'New-ScheduledTask',
    'Start-Service',
    'Stop-Service',
    'Restart-Service',
    'Set-ItemProperty',
    'New-ItemProperty',
    'Remove-ItemProperty',
    'powercfg\s+/(setacvalueindex|setdcvalueindex|setactive)',
    'nvidia-smi.*(\s-pl\s|--power-limit|-lgc|-lmc|--persistence-mode|\s-pm\s)',
    'shell\s*=\s*True'
)

foreach ($pattern in $hardBlockedPatterns) {
    $hits = @($codeFiles | Select-String -Pattern $pattern -ErrorAction SilentlyContinue)
    Add-Result -Results $results -Name "static_no_hard_blocked:$pattern" -Passed (@($hits).Count -eq 0) -Details ((@($hits) | ForEach-Object { "$($_.Path):$($_.LineNumber):$($_.Line.Trim())" }) -join "`n")
}

$profileHits = @($codeFiles | Select-String -Pattern 'MSIAfterburner\.exe.*-Profile[1-5]|-Profile[1-5].*MSIAfterburner\.exe' -ErrorAction SilentlyContinue)
$unsafeProfileHits = @($profileHits | Where-Object { $_.Line -notmatch '(dry|preview|template|not executed|refuse|DRY)' })
Add-Result -Results $results -Name 'static_msi_profile_commands_are_dryrun_only' -Passed (@($unsafeProfileHits).Count -eq 0) -Details ((@($profileHits) | ForEach-Object { "$($_.Path):$($_.LineNumber):$($_.Line.Trim())" }) -join "`n")

$failed = @($results | Where-Object { -not $_.passed })
$timestamp = (Get-Date).ToString('s')
$validation = [pscustomobject]@{
    timestamp_local = $timestamp
    phase_root      = $PhaseRoot
    total_checks    = @($results).Count
    failed_checks   = @($failed).Count
    results         = @($results)
}

$rawPath = Join-Path $PhaseRoot 'raw_outputs\phase2_validation.json'
$validation | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $rawPath -Encoding UTF8

$md = New-Object System.Collections.ArrayList
[void]$md.Add('# Phase 2 Validation')
[void]$md.Add('')
[void]$md.Add('- Timestamp: ' + $timestamp)
[void]$md.Add('- Phase root: `' + $PhaseRoot + '`')
[void]$md.Add('- Total checks: ' + @($results).Count)
[void]$md.Add('- Failed checks: ' + @($failed).Count)
[void]$md.Add('')
[void]$md.Add('## Failed Checks')
[void]$md.Add('')
if (@($failed).Count -eq 0) {
    [void]$md.Add('None.')
} else {
    foreach ($item in @($failed)) {
        [void]$md.Add('- ' + $item.name + ': ' + $item.details)
    }
}
[void]$md.Add('')
[void]$md.Add('## All Checks')
[void]$md.Add('')
foreach ($item in @($results)) {
    $mark = if ($item.passed) { 'PASS' } else { 'FAIL' }
    [void]$md.Add('- ' + $mark + ' - ' + $item.name)
}

Set-Content -LiteralPath (Join-Path $PhaseRoot 'phase2_validation.md') -Value @($md) -Encoding UTF8

$validation | ConvertTo-Json -Depth 8
if (@($failed).Count -gt 0) {
    exit 1
}
