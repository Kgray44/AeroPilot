param(
    [string]$PhaseRoot = (Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path))
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'common_phase1.ps1')

$context = Initialize-DetectorContext -PhaseRoot $PhaseRoot -DetectorName 'gigabyte_controls'

# This detector reads installed-program metadata, running process metadata,
# service metadata, and obvious folders. It does not launch GCC utilities,
# write fan modes, write EC registers, or edit config files.
$patterns = @('(?i)GIGABYTE', '(?i)\bGCC\b', '(?i)ControlCenter', '(?i)AORUS', '(?i)Gbt\.', '(?i)GpuPowerGear', '(?i)GigabyteUpdate')

$uninstallEntries = Get-Phase1UninstallEntries -Pattern '(?i)(GIGABYTE|AORUS|Control Center|\bGCC\b)'
$processMatches = Get-Phase1ProcessMatches -Patterns $patterns

$services = New-Object System.Collections.ArrayList
try {
    $allServices = Get-CimInstance Win32_Service -ErrorAction SilentlyContinue
    foreach ($service in @($allServices)) {
        $text = (($service.Name, $service.DisplayName, $service.PathName) -join ' ')
        if ($text -match '(?i)(GIGABYTE|AORUS|Control Center|\bGCC\b|Gbt\.|GpuPowerGear|GigabyteUpdate)') {
            [void]$services.Add([pscustomobject]@{
                name         = $service.Name
                display_name = $service.DisplayName
                state        = $service.State
                start_mode   = $service.StartMode
                path_name    = $service.PathName
                process_id   = $service.ProcessId
            })
        }
    }
} catch {
    Write-Phase1Log -Context $context -Level 'WARN' -Message ("Service query failed: {0}" -f $_.Exception.Message)
}

$folderRoots = @(
    $env:ProgramFiles,
    ${env:ProgramFiles(x86)},
    $env:ProgramData,
    "$env:LOCALAPPDATA",
    "$env:APPDATA"
)

$folders = New-Object System.Collections.ArrayList
foreach ($root in @($folderRoots)) {
    if ([string]::IsNullOrWhiteSpace($root) -or -not (Test-Path -LiteralPath $root)) {
        continue
    }
    try {
        $dirs = Get-ChildItem -LiteralPath $root -Directory -ErrorAction SilentlyContinue
        foreach ($dir in @($dirs)) {
            if ($dir.Name -match '(?i)(GIGABYTE|AORUS|Control Center|\bGCC\b)') {
                [void]$folders.Add((Get-Phase1FileInfo -Path $dir.FullName))
            }
        }
    } catch { }
}

$obviousConfigFiles = New-Object System.Collections.ArrayList
foreach ($folder in @($folders)) {
    try {
        foreach ($filter in @('*.json','*.xml','*.ini','*.config','*.cfg')) {
            $files = Get-ChildItem -LiteralPath $folder.path -Recurse -File -Filter $filter -ErrorAction SilentlyContinue | Select-Object -First 80
            foreach ($file in @($files)) {
                [void]$obviousConfigFiles.Add((Get-Phase1FileInfo -Path $file.FullName))
            }
        }
    } catch { }
}

$helpProbePolicy = @(
    [pscustomobject]@{
        surface = 'GIGABYTE/GCC GUI executables'
        phase1_decision = 'Skipped'
        reason = 'Launching unknown OEM control executables for --help may open UI, initialize services, or alter config state. Treat as unsafe until manually isolated.'
    },
    [pscustomobject]@{
        surface = 'Windows services'
        phase1_decision = 'Read status only'
        reason = 'Start/stop/control commands are state changes and are out of scope for Phase 1.'
    }
)

$fanFeasibility = @(
    [pscustomobject]@{
        method = 'Official API'
        likelihood = 'Unknown'
        phase1_status = 'No official API was confirmed by read-only discovery.'
        risk = 'Unknown'
    },
    [pscustomobject]@{
        method = 'Command-line control'
        likelihood = 'Unknown'
        phase1_status = 'No safe command-line control surface was confirmed. Help probes were skipped for GUI/OEM executables.'
        risk = 'High'
    },
    [pscustomobject]@{
        method = 'Config-file control'
        likelihood = 'Unknown'
        phase1_status = 'Config-like files may exist, but Phase 1 did not read semantics or edit files.'
        risk = 'High'
    },
    [pscustomobject]@{
        method = 'UI automation'
        likelihood = 'Possible but fragile'
        phase1_status = 'Future option only; requires manual confirmation and a rollback/panic plan.'
        risk = 'High'
    },
    [pscustomobject]@{
        method = 'Embedded controller writes'
        likelihood = 'Possible on some laptops but not proven here'
        phase1_status = 'Read-only research only for now. No EC access was attempted.'
        risk = 'Dangerous / Experimental'
    }
)

$result = [pscustomobject]@{
    detector              = 'gigabyte_controls'
    timestamp_local       = (Get-Date).ToString('s')
    installed_entries     = @($uninstallEntries)
    running_processes     = @($processMatches)
    services              = @($services)
    folders               = @($folders)
    obvious_config_files  = @($obviousConfigFiles)
    command_line_help_policy = $helpProbePolicy
    fan_control_feasibility = $fanFeasibility
    conclusion            = if (@($uninstallEntries).Count -gt 0 -or @($services).Count -gt 0 -or @($processMatches).Count -gt 0) {
        'Gigabyte/GCC surfaces are present or partially present, but direct fan control is not proven safe.'
    } else {
        'No clear Gigabyte/GCC control surface was found by read-only discovery.'
    }
    future_notes          = @(
        'Keep fan control behind an Experimental tab until an official or reversible interface is proven.',
        'Never write EC registers from the main app without a dedicated research phase.',
        'If UI automation is used later, require visible confirmation and a panic restore path.'
    )
}

Write-Phase1JsonFile -Path (Join-Path $context.raw_output_dir 'gigabyte_controls_detector_result.json') -InputObject $result -Depth 12
Write-Phase1Log -Context $context -Message 'Finished detector gigabyte_controls'
$result | ConvertTo-Json -Depth 12
