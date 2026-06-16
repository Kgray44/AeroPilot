param(
    [Parameter(Mandatory=$true)]
    [string]$DllPath,
    [int]$MaxSensors = 240,
    [int]$Samples = 3,
    [int]$SampleDelayMs = 500
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = "Stop"
$computer = $null

function New-Result {
    param(
        [bool]$Ok,
        [object[]]$Sensors,
        [string]$ErrorMessage = $null
    )
    [pscustomobject]@{
        ok = $Ok
        generated_local = (Get-Date).ToString("s")
        dll_path = $DllPath
        samples = [Math]::Max(1, $Samples)
        sample_delay_ms = [Math]::Max(0, $SampleDelayMs)
        sensors = @($Sensors)
        sensor_count = @($Sensors).Count
        error = $ErrorMessage
        read_only = $true
    } | ConvertTo-Json -Depth 10
}

function Get-SensorRows {
    param($Computer)

    $rows = New-Object System.Collections.ArrayList
    foreach ($hardware in $Computer.Hardware) {
        $hardware.Update()
        foreach ($subhardware in $hardware.SubHardware) {
            $subhardware.Update()
        }
        foreach ($sensor in @($hardware.Sensors) + @($hardware.SubHardware | ForEach-Object { $_.Sensors })) {
            if ($null -eq $sensor -or $null -eq $sensor.Value) { continue }
            [void]$rows.Add([pscustomobject]@{
                hardware = $hardware.Name
                hardware_type = [string]$hardware.HardwareType
                name = $sensor.Name
                sensor_type = [string]$sensor.SensorType
                value = [double]$sensor.Value
                min = if ($null -ne $sensor.Min) { [double]$sensor.Min } else { $null }
                max = if ($null -ne $sensor.Max) { [double]$sensor.Max } else { $null }
            })
            if ($rows.Count -ge $MaxSensors) { break }
        }
        if ($rows.Count -ge $MaxSensors) { break }
    }
    return @($rows)
}

try {
    if (-not (Test-Path -LiteralPath $DllPath)) {
        New-Result -Ok $false -Sensors @() -ErrorMessage "LibreHardwareMonitorLib.dll not found at supplied path."
        exit 2
    }

    Add-Type -LiteralPath $DllPath
    $computer = New-Object LibreHardwareMonitor.Hardware.Computer
    $computer.IsCpuEnabled = $true
    $computer.IsGpuEnabled = $true
    $computer.IsMemoryEnabled = $true
    $computer.IsMotherboardEnabled = $true
    $computer.IsStorageEnabled = $true
    $computer.IsNetworkEnabled = $true
    $computer.IsControllerEnabled = $true
    $computer.Open()

    $accum = @{}
    $sampleCount = [Math]::Max(1, $Samples)
    for ($sampleIndex = 0; $sampleIndex -lt $sampleCount; $sampleIndex++) {
        $rows = Get-SensorRows -Computer $computer
        foreach ($row in $rows) {
            $key = "$($row.hardware)|$($row.hardware_type)|$($row.sensor_type)|$($row.name)"
            if (-not $accum.ContainsKey($key)) {
                $accum[$key] = [pscustomobject]@{
                    hardware = $row.hardware
                    hardware_type = $row.hardware_type
                    name = $row.name
                    sensor_type = $row.sensor_type
                    value = $row.value
                    min = $row.min
                    max = $row.max
                    sample_values = New-Object System.Collections.ArrayList
                    nonzero_latest = $null
                    sample_nonzero_count = 0
                }
            }
            $entry = $accum[$key]
            $entry.value = $row.value
            $entry.min = $row.min
            $entry.max = $row.max
            [void]$entry.sample_values.Add($row.value)
            if ([Math]::Abs([double]$row.value) -gt 0.0001) {
                $entry.nonzero_latest = $row.value
                $entry.sample_nonzero_count = [int]$entry.sample_nonzero_count + 1
            }
        }
        if ($sampleIndex -lt ($sampleCount - 1) -and $SampleDelayMs -gt 0) {
            Start-Sleep -Milliseconds $SampleDelayMs
        }
    }
    $computer.Close()

    $finalRows = New-Object System.Collections.ArrayList
    foreach ($entry in $accum.Values) {
        $values = @($entry.sample_values)
        $entry | Add-Member -NotePropertyName sample_min -NotePropertyValue (($values | Measure-Object -Minimum).Minimum) -Force
        $entry | Add-Member -NotePropertyName sample_max -NotePropertyValue (($values | Measure-Object -Maximum).Maximum) -Force
        $entry | Add-Member -NotePropertyName stale_zero -NotePropertyValue (($values.Count -gt 1) -and ($entry.sample_nonzero_count -eq 0) -and ([double]$entry.value -eq 0.0)) -Force
        [void]$finalRows.Add($entry)
        if ($finalRows.Count -ge $MaxSensors) { break }
    }
    New-Result -Ok $true -Sensors $finalRows -ErrorMessage $null
} catch {
    try {
        if ($null -ne $computer) { $computer.Close() }
    } catch { }
    New-Result -Ok $false -Sensors @() -ErrorMessage $_.Exception.Message
    exit 1
}
