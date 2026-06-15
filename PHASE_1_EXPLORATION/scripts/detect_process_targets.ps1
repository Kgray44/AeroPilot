param(
    [string]$PhaseRoot = (Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path))
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'common_phase1.ps1')

$context = Initialize-DetectorContext -PhaseRoot $PhaseRoot -DetectorName 'process_targets'

# Future GUI game/tool detection starts from a configurable seed list.
# Phase 1 only enumerates processes. It never kills, suspends, or modifies them.
$targets = @(
    [pscustomobject]@{ id='battlefield_6'; friendly='Battlefield 6 / BF6'; category='Game'; process_names=@('BF6','Battlefield6','Battlefield 6','bf6game'); match_notes='Names are seed guesses and need confirmation from an active BF6 session.' },
    [pscustomobject]@{ id='steam'; friendly='Steam'; category='Launcher'; process_names=@('steam','steamwebhelper'); match_notes='Steam client and web helper.' },
    [pscustomobject]@{ id='ea_app'; friendly='EA App'; category='Launcher'; process_names=@('EADesktop','EALauncher','EABackgroundService','EACefSubProcess','Origin'); match_notes='EA App background and launcher processes.' },
    [pscustomobject]@{ id='epic_games'; friendly='Epic Games Launcher'; category='Launcher'; process_names=@('EpicGamesLauncher','EpicWebHelper'); match_notes='Epic launcher and helpers.' },
    [pscustomobject]@{ id='sea_of_thieves'; friendly='Sea of Thieves'; category='Game'; process_names=@('SoTGame','SeaOfThieves'); match_notes='Common Sea of Thieves executable names.' },
    [pscustomobject]@{ id='minecraft'; friendly='Minecraft'; category='Game'; process_names=@('Minecraft','Minecraft.Windows','javaw','java'); match_notes='java/javaw are broad and require command-line filtering later.' },
    [pscustomobject]@{ id='msi_afterburner'; friendly='MSI Afterburner'; category='Tool'; process_names=@('MSIAfterburner'); match_notes='GPU profile tool.' },
    [pscustomobject]@{ id='rtss'; friendly='RivaTuner Statistics Server'; category='Tool'; process_names=@('RTSS','RTSSHooksLoader64','RTSSHooksLoader'); match_notes='OSD/frame limiter support tool.' },
    [pscustomobject]@{ id='presentmon'; friendly='PresentMon'; category='Tool'; process_names=@('PresentMon'); match_notes='Future frame-time capture tool.' },
    [pscustomobject]@{ id='hwinfo'; friendly='HWiNFO'; category='Tool'; process_names=@('HWiNFO64','HWiNFO32','HWiNFO'); match_notes='Optional sensor tool.' },
    [pscustomobject]@{ id='gigabyte_control_center'; friendly='GIGABYTE Control Center'; category='OEM control'; process_names=@('GCC','ControlCenter','GIGABYTE','GService','GigabyteUpdateService'); match_notes='Names vary by GCC version.' },
    [pscustomobject]@{ id='nvidia_app'; friendly='NVIDIA App / NVIDIA services'; category='GPU tool'; process_names=@('NVIDIA App','NVIDIA Overlay','NVIDIA Share','NVIDIA Web Helper','nvcontainer','NVIDIA GeForce Experience'); match_notes='NVIDIA App components and service containers.' }
)

$allProcesses = New-Object System.Collections.ArrayList
foreach ($process in @(Get-Process -ErrorAction SilentlyContinue)) {
    $path = $null
    try { $path = $process.Path } catch { }
    [void]$allProcesses.Add([pscustomobject]@{
        process_name = $process.ProcessName
        id           = $process.Id
        path         = $path
        cpu_seconds  = $process.CPU
        start_time   = try { $process.StartTime.ToString('s') } catch { $null }
    })
}

$csvPath = Join-Path $context.raw_output_dir 'process_targets_all_running_processes.csv'
@($allProcesses) | Sort-Object process_name, id | Export-Csv -LiteralPath $csvPath -NoTypeInformation -Encoding UTF8
Write-Phase1Log -Context $context -Message "Wrote running process CSV $csvPath"

$matches = New-Object System.Collections.ArrayList
foreach ($target in $targets) {
    $targetMatches = New-Object System.Collections.ArrayList
    foreach ($process in @($allProcesses)) {
        foreach ($name in @($target.process_names)) {
            if ($process.process_name -ieq $name -or $process.process_name -like "$name*") {
                [void]$targetMatches.Add([pscustomobject]@{
                    process_name = $process.process_name
                    id           = $process.id
                    path         = $process.path
                    matched_seed = $name
                })
                break
            }
        }
    }

    [void]$matches.Add([pscustomobject]@{
        id             = $target.id
        friendly       = $target.friendly
        category       = $target.category
        configured_process_names = $target.process_names
        running_now    = (@($targetMatches).Count -gt 0)
        matches        = @($targetMatches)
        match_notes    = $target.match_notes
    })
}

$appProbeDir = Join-Path $PhaseRoot 'app_probe'
New-Phase1Directory -Path $appProbeDir
$seedPath = Join-Path $appProbeDir 'process_targets_seed.json'
Write-Phase1JsonFile -Path $seedPath -InputObject ([pscustomobject]@{
    generated_local = (Get-Date).ToString('s')
    description     = 'Editable seed list for future game/tool detection. Phase 1 did not modify running processes.'
    targets         = $targets
}) -Depth 10

$result = [pscustomobject]@{
    detector          = 'process_targets'
    timestamp_local   = (Get-Date).ToString('s')
    process_count     = @($allProcesses).Count
    all_processes_csv = $csvPath
    seed_list_path    = $seedPath
    targets           = @($matches)
    phase1_safety     = @(
        'Enumerated running processes only.',
        'No process was killed, suspended, deprioritized, or modified.',
        'Future app should let users edit process names and require confirmation for automation.'
    )
}

Write-Phase1JsonFile -Path (Join-Path $context.raw_output_dir 'process_targets_detector_result.json') -InputObject $result -Depth 12
Write-Phase1Log -Context $context -Message 'Finished detector process_targets'
$result | ConvertTo-Json -Depth 12
