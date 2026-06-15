param(
    [string]$PhaseRoot = (Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path))
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'common_phase1.ps1')

$context = Initialize-DetectorContext -PhaseRoot $PhaseRoot -DetectorName 'nvidia_telemetry'

function Convert-CsvLineToObject {
    param(
        [string]$Header,
        [string]$Line
    )

    if ([string]::IsNullOrWhiteSpace($Line)) {
        return $null
    }

    $headers = $Header -split ','
    $values = $Line -split ','
    $obj = [ordered]@{}
    for ($i = 0; $i -lt $headers.Count; $i++) {
        $key = $headers[$i].Trim()
        $value = if ($i -lt $values.Count) { $values[$i].Trim() } else { $null }
        $obj[$key] = $value
    }

    return [pscustomobject]$obj
}

$candidates = New-Object System.Collections.ArrayList
$cmd = Get-Command 'nvidia-smi.exe' -ErrorAction SilentlyContinue
if ($cmd) { [void]$candidates.Add($cmd.Source) }
foreach ($path in @(
    'C:\Windows\System32\nvidia-smi.exe',
    'C:\Program Files\NVIDIA Corporation\NVSMI\nvidia-smi.exe'
)) {
    if ((Test-Path -LiteralPath $path) -and -not (@($candidates) -contains $path)) {
        [void]$candidates.Add($path)
    }
}

$nvidiaSmiPath = $null
if (@($candidates).Count -gt 0) {
    $nvidiaSmiPath = @($candidates)[0]
}

$commands = New-Object System.Collections.ArrayList
$gpuSummary = $null
$supportedQueryText = $null
$processText = $null

if ($nvidiaSmiPath) {
    [void]$commands.Add((Invoke-Phase1ReadOnlyCommand -Context $context -Name 'nvidia_smi_plain' -FilePath $nvidiaSmiPath -Arguments @() -TimeoutSeconds 20))
    [void]$commands.Add((Invoke-Phase1ReadOnlyCommand -Context $context -Name 'nvidia_smi_help_query_gpu' -FilePath $nvidiaSmiPath -Arguments @('--help-query-gpu') -TimeoutSeconds 20))

    $fields = 'name,driver_version,cuda_version,utilization.gpu,utilization.memory,memory.total,memory.used,memory.free,temperature.gpu,power.draw,power.limit,clocks.current.graphics,clocks.current.memory'
    $query = Invoke-Phase1ReadOnlyCommand -Context $context -Name 'nvidia_smi_query_gpu_full' -FilePath $nvidiaSmiPath -Arguments @("--query-gpu=$fields",'--format=csv,noheader,nounits') -TimeoutSeconds 20
    [void]$commands.Add($query)

    if (-not $query.succeeded) {
        $fields = 'name,driver_version,utilization.gpu,utilization.memory,memory.total,memory.used,memory.free,temperature.gpu,power.draw,power.limit,clocks.current.graphics,clocks.current.memory'
        $query = Invoke-Phase1ReadOnlyCommand -Context $context -Name 'nvidia_smi_query_gpu_fallback' -FilePath $nvidiaSmiPath -Arguments @("--query-gpu=$fields",'--format=csv,noheader,nounits') -TimeoutSeconds 20
        [void]$commands.Add($query)
    }

    if ($query.succeeded) {
        $line = (@($query.stdout -split "`r?`n") | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Select-Object -First 1)
        $gpuSummary = Convert-CsvLineToObject -Header $fields -Line $line
    }

    $computeApps = Invoke-Phase1ReadOnlyCommand -Context $context -Name 'nvidia_smi_query_compute_apps' -FilePath $nvidiaSmiPath -Arguments @('--query-compute-apps=pid,process_name,used_memory','--format=csv') -TimeoutSeconds 20
    [void]$commands.Add($computeApps)

    $pmon = Invoke-Phase1ReadOnlyCommand -Context $context -Name 'nvidia_smi_pmon_once' -FilePath $nvidiaSmiPath -Arguments @('pmon','-c','1') -TimeoutSeconds 20
    [void]$commands.Add($pmon)

    $supportedQueryText = (@($commands) | Where-Object { $_.name -eq 'nvidia_smi_help_query_gpu' } | Select-Object -First 1).stdout
    $processText = (($computeApps.stdout, $pmon.stdout) -join "`r`n")
}

$result = [pscustomobject]@{
    detector              = 'nvidia_telemetry'
    timestamp_local       = (Get-Date).ToString('s')
    nvidia_smi_available  = [bool]$nvidiaSmiPath
    nvidia_smi_path       = $nvidiaSmiPath
    candidate_paths       = @($candidates)
    nvidia_smi_file_info  = if ($nvidiaSmiPath) { Get-Phase1FileInfo -Path $nvidiaSmiPath } else { $null }
    gpu_summary           = $gpuSummary
    supported_query_fields_raw_path = (@($commands) | Where-Object { $_.name -eq 'nvidia_smi_help_query_gpu' } | Select-Object -First 1).stdout_path
    current_gpu_processes_raw = $processText
    read_only_commands    = @($commands | ForEach-Object {
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
    future_integration    = [pscustomobject]@{
        nvidia_smi_polling = if ($nvidiaSmiPath) { 'Practical for MVP read-only telemetry polling.' } else { 'Not available until nvidia-smi is found.' }
        nvml_python        = 'Recommended later for lower-overhead polling and structured GPU telemetry if Python NVML bindings are installed or vendored.'
        enough_for_mvp     = [bool]$gpuSummary
        notes              = @(
            'Phase 1 did not set clocks, power limits, persistence mode, or driver settings.',
            'nvidia-smi is suitable for MVP dashboards if polling interval is conservative.',
            'NVML may become useful for cleaner process and telemetry APIs later.'
        )
    }
}

Write-Phase1JsonFile -Path (Join-Path $context.raw_output_dir 'nvidia_telemetry_detector_result.json') -InputObject $result -Depth 12
Write-Phase1Log -Context $context -Message 'Finished detector nvidia_telemetry'
$result | ConvertTo-Json -Depth 12
