param(
    [Parameter(Mandatory=$true)]
    [string]$DllPath,
    [int]$MaxSensors = 240
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = "Stop"

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
        sensors = @($Sensors)
        sensor_count = @($Sensors).Count
        error = $ErrorMessage
        read_only = $true
    } | ConvertTo-Json -Depth 8
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

    $rows = New-Object System.Collections.ArrayList
    foreach ($hardware in $computer.Hardware) {
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
    $computer.Close()
    New-Result -Ok $true -Sensors $rows -ErrorMessage $null
} catch {
    New-Result -Ok $false -Sensors @() -ErrorMessage $_.Exception.Message
    exit 1
}
