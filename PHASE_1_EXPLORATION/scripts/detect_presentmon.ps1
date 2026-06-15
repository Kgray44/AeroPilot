param(
    [string]$PhaseRoot = (Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path))
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'common_phase1.ps1')

$context = Initialize-DetectorContext -PhaseRoot $PhaseRoot -DetectorName 'presentmon'

# PresentMon is optional for Phase 1. This detector searches likely local paths
# and only invokes help/version commands with short timeouts if an executable is found.
$roots = Get-Phase1KnownSearchRoots -PhaseRoot $PhaseRoot
$foundExecutables = Find-Phase1Files -Roots $roots -Filters @('PresentMon.exe','PresentMon*.exe') -MaxResults 40

$commands = New-Object System.Collections.ArrayList
$primary = $null
if (@($foundExecutables).Count -gt 0) {
    $primary = @($foundExecutables)[0].path
    [void]$commands.Add((Invoke-Phase1ReadOnlyCommand -Context $context -Name 'presentmon_help_long' -FilePath $primary -Arguments @('--help') -TimeoutSeconds 10))
    if (-not (@($commands)[0]).succeeded) {
        [void]$commands.Add((Invoke-Phase1ReadOnlyCommand -Context $context -Name 'presentmon_help_short' -FilePath $primary -Arguments @('-h') -TimeoutSeconds 10))
    }
    [void]$commands.Add((Invoke-Phase1ReadOnlyCommand -Context $context -Name 'presentmon_version' -FilePath $primary -Arguments @('--version') -TimeoutSeconds 10))
}

$helpText = (@($commands) | Where-Object { $_.name -match 'help' -and -not [string]::IsNullOrWhiteSpace($_.stdout) } | Select-Object -First 1).stdout
$csvSupported = $false
$processTargetSupported = $false
if ($helpText) {
    $csvSupported = ($helpText -match '(?i)csv')
    $processTargetSupported = ($helpText -match '(?i)(process|process_name|process-name|capture_process)')
}

$templates = @(
    [pscustomobject]@{
        label        = 'Read-only capability check'
        command      = if ($primary) { ('"{0}" --help' -f $primary) } else { 'PresentMon.exe --help' }
        phase1_state = if ($primary) { 'Help command attempted with timeout.' } else { 'Template only; PresentMon not found.' }
    },
    [pscustomobject]@{
        label        = 'Future CSV capture by process'
        command      = if ($primary) { ('"{0}" --process_name <game.exe> --output_file "<session.csv>"' -f $primary) } else { 'PresentMon.exe --process_name <game.exe> --output_file "<session.csv>"' }
        phase1_state = 'Template only. Not executed in Phase 1.'
    },
    [pscustomobject]@{
        label        = 'Future timed capture'
        command      = if ($primary) { ('"{0}" --process_name <game.exe> --timed 60 --output_file "<session.csv>"' -f $primary) } else { 'PresentMon.exe --process_name <game.exe> --timed 60 --output_file "<session.csv>"' }
        phase1_state = 'Template only. Syntax must be verified against installed PresentMon version.'
    }
)

$result = [pscustomobject]@{
    detector                 = 'presentmon'
    timestamp_local          = (Get-Date).ToString('s')
    search_roots             = @($roots)
    presentmon_found         = (@($foundExecutables).Count -gt 0)
    primary_executable_path  = $primary
    executable_paths         = @($foundExecutables)
    help_output_available    = [bool]$helpText
    csv_output_appears_supported = $csvSupported
    process_targeting_appears_supported = $processTargetSupported
    read_only_commands       = @($commands | ForEach-Object {
        [pscustomobject]@{
            name         = $_.name
            command_line = $_.command_line
            exit_code    = $_.exit_code
            timed_out    = $_.timed_out
            succeeded    = $_.succeeded
            stdout_path  = $_.stdout_path
            stderr_path  = $_.stderr_path
            error        = $_.error
        }
    })
    command_templates        = $templates
    missing_optional_tool    = -not (@($foundExecutables).Count -gt 0)
    future_integration_plan  = @(
        'Treat PresentMon as optional but strongly recommended for FPS and frame-time capture.',
        'Add a configured executable path setting in the future app.',
        'Use process-name targeting for game sessions after syntax is verified on the installed build.',
        'Write PresentMon CSV files under timestamped session folders and link them to preset metadata.',
        'Do not install PresentMon automatically in Phase 1.'
    )
}

Write-Phase1JsonFile -Path (Join-Path $context.raw_output_dir 'presentmon_detector_result.json') -InputObject $result -Depth 12
Write-Phase1Log -Context $context -Message 'Finished detector presentmon'
$result | ConvertTo-Json -Depth 12
