param(
    [string]$PhaseRoot = (Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path))
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'common_phase1.ps1')

$context = Initialize-DetectorContext -PhaseRoot $PhaseRoot -DetectorName 'msi_afterburner'

# This detector only reads common install locations, registry uninstall metadata,
# Start Menu shortcuts, config/profile file metadata, and running processes.
$commonAfterburnerPaths = @(
    'C:\Program Files (x86)\MSI Afterburner\MSIAfterburner.exe',
    'C:\Program Files\MSI Afterburner\MSIAfterburner.exe'
)
$commonRtssPaths = @(
    'C:\Program Files (x86)\RivaTuner Statistics Server\RTSS.exe',
    'C:\Program Files\RivaTuner Statistics Server\RTSS.exe',
    'C:\Program Files (x86)\MSI Afterburner\Bundle\OSDServer\RTSS.exe'
)

$afterburnerExecutables = New-Object System.Collections.ArrayList
foreach ($path in $commonAfterburnerPaths) {
    $info = Get-Phase1FileInfo -Path $path
    if ($info) { [void]$afterburnerExecutables.Add($info) }
}

$rtssExecutables = New-Object System.Collections.ArrayList
foreach ($path in $commonRtssPaths) {
    $info = Get-Phase1FileInfo -Path $path
    if ($info) { [void]$rtssExecutables.Add($info) }
}

$uninstallEntries = Get-Phase1UninstallEntries -Pattern '(?i)(MSI Afterburner|RivaTuner|RTSS)'
foreach ($entry in @($uninstallEntries)) {
    if (-not [string]::IsNullOrWhiteSpace($entry.install_location)) {
        $candidate = Join-Path $entry.install_location 'MSIAfterburner.exe'
        $info = Get-Phase1FileInfo -Path $candidate
        if ($info -and -not (@($afterburnerExecutables).path -contains $info.path)) {
            [void]$afterburnerExecutables.Add($info)
        }

        $rtssCandidate = Join-Path $entry.install_location 'RTSS.exe'
        $rtssInfo = Get-Phase1FileInfo -Path $rtssCandidate
        if ($rtssInfo -and -not (@($rtssExecutables).path -contains $rtssInfo.path)) {
            [void]$rtssExecutables.Add($rtssInfo)
        }
    }
}

$shortcuts = Get-Phase1ShortcutInfo -NamePatterns @('(?i)Afterburner', '(?i)RivaTuner', '(?i)RTSS')
foreach ($shortcut in @($shortcuts)) {
    if ($shortcut.target_path -match '(?i)MSIAfterburner\.exe$') {
        $info = Get-Phase1FileInfo -Path $shortcut.target_path
        if ($info -and -not (@($afterburnerExecutables).path -contains $info.path)) {
            [void]$afterburnerExecutables.Add($info)
        }
    }
    if ($shortcut.target_path -match '(?i)RTSS\.exe$') {
        $info = Get-Phase1FileInfo -Path $shortcut.target_path
        if ($info -and -not (@($rtssExecutables).path -contains $info.path)) {
            [void]$rtssExecutables.Add($info)
        }
    }
}

$installFolder = $null
if (@($afterburnerExecutables).Count -gt 0) {
    $installFolder = Split-Path -Parent @($afterburnerExecutables)[0].path
}

$configFiles = New-Object System.Collections.ArrayList
$profileFiles = New-Object System.Collections.ArrayList
$profilesFolder = $null
$msiConfig = $null

if ($installFolder -and (Test-Path -LiteralPath $installFolder)) {
    $msiConfig = Get-Phase1FileInfo -Path (Join-Path $installFolder 'MSIAfterburner.cfg')
    if ($msiConfig) { [void]$configFiles.Add($msiConfig) }

    foreach ($filter in @('*.cfg','*.ini','*.dat','*.oem','*.oem*')) {
        foreach ($file in @(Get-ChildItem -LiteralPath $installFolder -File -Filter $filter -ErrorAction SilentlyContinue)) {
            $info = Get-Phase1FileInfo -Path $file.FullName
            if ($info -and -not (@($configFiles).path -contains $info.path)) {
                [void]$configFiles.Add($info)
            }
        }
    }

    $profilesFolderPath = Join-Path $installFolder 'Profiles'
    if (Test-Path -LiteralPath $profilesFolderPath) {
        $profilesFolder = Get-Phase1FileInfo -Path $profilesFolderPath
        foreach ($file in @(Get-ChildItem -LiteralPath $profilesFolderPath -File -ErrorAction SilentlyContinue)) {
            [void]$profileFiles.Add((Get-Phase1FileInfo -Path $file.FullName))
        }
    }
}

$processMatches = Get-Phase1ProcessMatches -Patterns @('(?i)^MSIAfterburner$', '(?i)^RTSS$', '(?i)RTSS', '(?i)Afterburner')

$dryRunCommands = New-Object System.Collections.ArrayList
if (@($afterburnerExecutables).Count -gt 0) {
    $exe = @($afterburnerExecutables)[0].path
} else {
    $exe = 'MSIAfterburner.exe'
}
foreach ($slot in 1..5) {
    [void]$dryRunCommands.Add([pscustomobject]@{
        profile_slot = $slot
        command      = ('"{0}" -Profile{1}' -f $exe, $slot)
        phase1_state = 'Template only. Not executed in Phase 1.'
        risk_label   = 'Medium'
    })
}

$result = [pscustomobject]@{
    detector              = 'msi_afterburner'
    timestamp_local       = (Get-Date).ToString('s')
    installed             = (@($afterburnerExecutables).Count -gt 0)
    executable_paths      = @($afterburnerExecutables)
    rtss_executable_paths = @($rtssExecutables)
    install_folder        = $installFolder
    uninstall_entries     = @($uninstallEntries)
    shortcuts             = @($shortcuts)
    profiles_folder       = $profilesFolder
    profiles_folder_exists = [bool]$profilesFolder
    msi_afterburner_cfg   = $msiConfig
    config_files          = @($configFiles)
    profile_files         = @($profileFiles)
    appears_running       = (@($processMatches).Count -gt 0)
    process_matches       = @($processMatches)
    future_profile_commands = @($dryRunCommands)
    conclusion            = if (@($afterburnerExecutables).Count -gt 0) {
        'MSI Afterburner profile commands are likely launchable later, but Phase 1 did not run them.'
    } else {
        'MSI Afterburner executable was not found in common paths or shortcut targets.'
    }
    manual_verification_needed = @(
        'Confirm profile slots match friendly preset names before any apply phase.',
        'Confirm MSI Afterburner command-line profile loading behavior manually before GUI integration.',
        'Back up MSIAfterburner.cfg and Profiles before any future write or profile launch test.'
    )
}

Write-Phase1JsonFile -Path (Join-Path $context.raw_output_dir 'msi_afterburner_detector_result.json') -InputObject $result -Depth 12
Write-Phase1Log -Context $context -Message 'Finished detector msi_afterburner'
$result | ConvertTo-Json -Depth 12
