param(
    [string]$PhaseRoot = (Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path))
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'common_phase1.ps1')

$context = Initialize-DetectorContext -PhaseRoot $PhaseRoot -DetectorName 'librehardwaremonitor'

# LibreHardwareMonitor is optional in Phase 1. This detector does not launch it;
# launching the GUI can create config state and may require admin for sensors.
$roots = Get-Phase1KnownSearchRoots -PhaseRoot $PhaseRoot
$exeFiles = Find-Phase1Files -Roots $roots -Filters @('LibreHardwareMonitor.exe') -MaxResults 40
$dllFiles = Find-Phase1Files -Roots $roots -Filters @('LibreHardwareMonitorLib.dll') -MaxResults 40
$relatedFiles = Find-Phase1Files -Roots $roots -Filters @('LibreHardwareMonitor*.dll','LibreHardwareMonitor*.config') -MaxResults 80

$primaryExe = $null
if (@($exeFiles).Count -gt 0) {
    $primaryExe = @($exeFiles)[0].path
}

$primaryDll = $null
if (@($dllFiles).Count -gt 0) {
    $primaryDll = @($dllFiles)[0].path
}

$result = [pscustomobject]@{
    detector                = 'librehardwaremonitor'
    timestamp_local         = (Get-Date).ToString('s')
    search_roots            = @($roots)
    found                   = ((@($exeFiles).Count + @($dllFiles).Count) -gt 0)
    primary_executable_path = $primaryExe
    primary_library_path    = $primaryDll
    executable_paths        = @($exeFiles)
    library_paths           = @($dllFiles)
    related_files           = @($relatedFiles)
    launched_in_phase1      = $false
    can_be_used_as_library_later = [bool]$primaryDll
    admin_privilege_expectation = if ($primaryExe -or $primaryDll) {
        'Unknown on this machine until tested. Many low-level sensors may require admin or driver access.'
    } else {
        'Not testable because LibreHardwareMonitor was not found.'
    }
    likely_sensor_domains_inferred = @(
        'CPU temperatures',
        'CPU clocks',
        'GPU temperatures and clocks when supported',
        'Fan speeds when exposed by motherboard or EC interfaces',
        'Voltages when exposed by motherboard sensors',
        'Battery and storage sensors when exposed'
    )
    missing_optional_tool   = -not ((@($exeFiles).Count + @($dllFiles).Count) -gt 0)
    future_integration_plan = @(
        'Treat LibreHardwareMonitor as optional but useful for broader sensors.',
        'Prefer using LibreHardwareMonitorLib.dll from Python only after a controlled proof of concept.',
        'Keep all sensor reads read-only and label fan/voltage fields as hardware-dependent.',
        'Add an admin-required marker if a future probe proves elevated access is needed.',
        'Do not install or launch LibreHardwareMonitor in Phase 1.'
    )
}

Write-Phase1JsonFile -Path (Join-Path $context.raw_output_dir 'librehardwaremonitor_detector_result.json') -InputObject $result -Depth 12
Write-Phase1Log -Context $context -Message 'Finished detector librehardwaremonitor'
$result | ConvertTo-Json -Depth 12
