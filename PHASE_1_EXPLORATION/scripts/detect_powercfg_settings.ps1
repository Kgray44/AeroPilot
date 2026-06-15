param(
    [string]$PhaseRoot = (Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path))
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'common_phase1.ps1')

$context = Initialize-DetectorContext -PhaseRoot $PhaseRoot -DetectorName 'powercfg'

function Get-SettingVisibility {
    param(
        [string]$SubgroupGuid,
        [string]$SettingGuid
    )

    $path = "HKLM:\SYSTEM\CurrentControlSet\Control\Power\PowerSettings\$SubgroupGuid\$SettingGuid"
    $attributes = $null
    $visible = 'Unknown'
    try {
        $item = Get-ItemProperty -LiteralPath $path -ErrorAction Stop
        $attributes = $item.Attributes
        if ($null -eq $attributes) {
            $visible = 'Likely visible or default visibility'
        } elseif (($attributes -band 1) -eq 1) {
            $visible = 'Hidden by Attributes bit 0'
        } else {
            $visible = 'Likely visible'
        }
    } catch {
        $visible = 'Unknown: registry key not readable or not present'
    }

    return [pscustomobject]@{
        registry_path = $path
        attributes    = $attributes
        ui_visibility = $visible
    }
}

function Parse-PowerCfgSettingOutput {
    param(
        [string]$Text,
        [string]$FriendlyName,
        [string]$Guid
    )

    $acHex = $null
    $dcHex = $null
    $possible = New-Object System.Collections.ArrayList
    $currentPossibleIndex = $null

    foreach ($line in @($Text -split "`r?`n")) {
        if ($line -match 'Current AC Power Setting Index:\s*(0x[0-9a-fA-F]+)') {
            $acHex = $matches[1]
        } elseif ($line -match 'Current DC Power Setting Index:\s*(0x[0-9a-fA-F]+)') {
            $dcHex = $matches[1]
        } elseif ($line -match 'Possible Setting Index:\s*(0x[0-9a-fA-F]+|[0-9]+)') {
            $currentPossibleIndex = $matches[1]
        } elseif ($line -match 'Possible Setting Friendly Name:\s*(.+)$') {
            [void]$possible.Add([pscustomobject]@{
                index = $currentPossibleIndex
                name  = $matches[1].Trim()
            })
            $currentPossibleIndex = $null
        }
    }

    $acDecimal = $null
    $dcDecimal = $null
    try { if ($acHex) { $acDecimal = [Convert]::ToInt64(($acHex -replace '^0x',''), 16) } } catch { }
    try { if ($dcHex) { $dcDecimal = [Convert]::ToInt64(($dcHex -replace '^0x',''), 16) } } catch { }

    return [pscustomobject]@{
        friendly_name   = $FriendlyName
        guid            = $Guid
        current_ac_hex  = $acHex
        current_ac_value = $acDecimal
        current_dc_hex  = $dcHex
        current_dc_value = $dcDecimal
        possible_values = @($possible)
        powercfg_can_read = [bool]($acHex -or $dcHex -or @($possible).Count -gt 0)
    }
}

$subProcessor = '54533251-82be-4824-96c1-47b60b740d00'
$settings = @(
    [pscustomobject]@{ friendly='Processor performance boost mode'; alias='PERFBOOSTMODE'; guid='be337238-0d82-4146-a960-4f3749d470c7'; risk='Medium'; category='CPU boost behavior'; gui='Boost mode'; tooltip='Changes CPU boost behavior. Can affect heat, fan noise, battery life, and stability.' },
    [pscustomobject]@{ friendly='Processor performance boost policy'; alias='PERFBOOSTPOL'; guid='45bcc044-d885-43e2-8605-ee0ec6e96b59'; risk='Medium'; category='CPU boost behavior'; gui='Boost policy'; tooltip='Advanced boost policy. Treat as experimental until values are verified on this laptop.' },
    [pscustomobject]@{ friendly='Processor energy performance preference / EPP'; alias='PERFEPP'; guid='36687f9e-e3a5-4dbf-b1dc-15eb381c6863'; risk='Low'; category='CPU power behavior'; gui='Energy preference'; tooltip='Lower values favor performance. Higher values favor efficiency. Can change heat and battery use.' },
    [pscustomobject]@{ friendly='Minimum processor state'; alias='PROCTHROTTLEMIN'; guid='893dee8e-2bef-41e0-89c6-b55d0929964c'; risk='Medium'; category='CPU frequency limits'; gui='Minimum CPU state'; tooltip='Raising this can increase idle power and heat. Use conservative defaults.' },
    [pscustomobject]@{ friendly='Maximum processor state'; alias='PROCTHROTTLEMAX'; guid='bc5038f7-23e0-4960-96da-33abaf5935ec'; risk='Medium'; category='CPU frequency limits'; gui='Maximum CPU state'; tooltip='Lowering this can cap CPU performance. Changing it affects all workloads on the selected power plan.' },
    [pscustomobject]@{ friendly='System cooling policy'; alias='SYSCOOLPOL'; guid='94d3a615-a899-4ac5-ae2b-e4d8f634367f'; risk='Low'; category='Fan control'; gui='Cooling policy'; tooltip='Controls passive versus active cooling behavior where supported. May not override OEM fan firmware.' },
    [pscustomobject]@{ friendly='Maximum processor frequency'; alias='PROCFREQMAX'; guid='75b0ae3f-bce0-45a7-8c89-c9611c25e100'; risk='High'; category='CPU frequency limits'; gui='CPU frequency cap'; tooltip='Frequency caps can sharply limit performance or create confusing benchmark results.' },
    [pscustomobject]@{ friendly='Processor performance core parking min cores'; alias='CPMINCORES'; guid='0cc5b647-c1df-4637-891a-dec35c318583'; risk='High'; category='CPU scheduling/core parking'; gui='Core parking minimum'; tooltip='Core parking changes can affect latency, heat, and scheduler behavior. Advanced users only.' },
    [pscustomobject]@{ friendly='Processor performance core parking max cores'; alias='CPMAXCORES'; guid='ea062031-0e34-4ff1-9b6d-eb1059334028'; risk='High'; category='CPU scheduling/core parking'; gui='Core parking maximum'; tooltip='Core parking changes can affect latency, heat, and scheduler behavior. Advanced users only.' },
    [pscustomobject]@{ friendly='Processor idle disable'; alias='IDLEDISABLE'; guid='5d76a2ca-e8c0-402f-a133-2158492d58ad'; risk='Dangerous / Experimental'; category='CPU scheduling/core parking'; gui='Disable CPU idle states'; tooltip='Can greatly increase heat and power use. Keep read-only until a restore path is proven.' },
    [pscustomobject]@{ friendly='Heterogeneous policy in effect'; alias='HETEROPOLICY'; guid='7f2f5cfa-f10c-4823-b5e1-e93ae85f46b5'; risk='Unknown'; category='CPU scheduling/core parking'; gui='Hybrid CPU policy'; tooltip='Hybrid scheduling behavior is platform-specific. Treat as advanced and verify before writes.' },
    [pscustomobject]@{ friendly='Processor performance increase threshold'; alias='PERFINCTHRESHOLD'; guid='06cadf0e-64ed-448a-8927-ce7bf90eb35d'; risk='High'; category='CPU boost behavior'; gui='Performance increase threshold'; tooltip='Advanced boost response tuning. Can cause erratic performance or heat behavior if misused.' },
    [pscustomobject]@{ friendly='Processor performance decrease threshold'; alias='PERFDECTHRESHOLD'; guid='12a0ab44-fe28-4fa9-b3bd-4b64f44960a6'; risk='High'; category='CPU boost behavior'; gui='Performance decrease threshold'; tooltip='Advanced boost response tuning. Can cause erratic performance or heat behavior if misused.' }
)

$commands = New-Object System.Collections.ArrayList
[void]$commands.Add((Invoke-Phase1ReadOnlyCommand -Context $context -Name 'powercfg_get_active_scheme' -FilePath 'powercfg.exe' -Arguments @('/getactivescheme') -TimeoutSeconds 15))
[void]$commands.Add((Invoke-Phase1ReadOnlyCommand -Context $context -Name 'powercfg_list_schemes' -FilePath 'powercfg.exe' -Arguments @('/list') -TimeoutSeconds 15))
[void]$commands.Add((Invoke-Phase1ReadOnlyCommand -Context $context -Name 'powercfg_query_current_full' -FilePath 'powercfg.exe' -Arguments @('/query','SCHEME_CURRENT') -TimeoutSeconds 30))
[void]$commands.Add((Invoke-Phase1ReadOnlyCommand -Context $context -Name 'powercfg_query_current_processor' -FilePath 'powercfg.exe' -Arguments @('/query','SCHEME_CURRENT','SUB_PROCESSOR') -TimeoutSeconds 30))
[void]$commands.Add((Invoke-Phase1ReadOnlyCommand -Context $context -Name 'powercfg_query_hidden_current_processor' -FilePath 'powercfg.exe' -Arguments @('/qh','SCHEME_CURRENT','SUB_PROCESSOR') -TimeoutSeconds 30))
[void]$commands.Add((Invoke-Phase1ReadOnlyCommand -Context $context -Name 'powercfg_aliases' -FilePath 'powercfg.exe' -Arguments @('/aliases') -TimeoutSeconds 20))

$settingResults = New-Object System.Collections.ArrayList
foreach ($setting in $settings) {
    $commandName = 'setting_' + ($setting.alias.ToLowerInvariant())
    $cmd = Invoke-Phase1ReadOnlyCommand -Context $context -Name $commandName -FilePath 'powercfg.exe' -Arguments @('/query','SCHEME_CURRENT',$subProcessor,$setting.guid) -TimeoutSeconds 20
    [void]$commands.Add($cmd)

    $parsed = Parse-PowerCfgSettingOutput -Text $cmd.stdout -FriendlyName $setting.friendly -Guid $setting.guid
    $visibility = Get-SettingVisibility -SubgroupGuid $subProcessor -SettingGuid $setting.guid
    [void]$settingResults.Add([pscustomobject]@{
        friendly_name        = $setting.friendly
        alias                = $setting.alias
        subgroup_guid        = $subProcessor
        setting_guid         = $setting.guid
        category             = $setting.category
        current_ac_hex       = $parsed.current_ac_hex
        current_ac_value     = $parsed.current_ac_value
        current_dc_hex       = $parsed.current_dc_hex
        current_dc_value     = $parsed.current_dc_value
        possible_values      = $parsed.possible_values
        visible_in_windows_ui = $visibility.ui_visibility
        registry_attributes  = $visibility.attributes
        powercfg_can_read    = $parsed.powercfg_can_read
        powercfg_can_likely_write_later = $parsed.powercfg_can_read
        risk_level           = $setting.risk
        suggested_future_gui_label = $setting.gui
        suggested_future_tooltip_warning = $setting.tooltip
        notes                = if ($parsed.powercfg_can_read) { 'Read successfully through powercfg in Phase 1.' } else { 'Not readable through direct powercfg query in Phase 1; may be unsupported, hidden, OEM-blocked, or absent.' }
    })
}

$activeSchemeText = (@($commands) | Where-Object { $_.name -eq 'powercfg_get_active_scheme' } | Select-Object -First 1).stdout
$activeSchemeGuid = $null
$activeSchemeName = $null
if ($activeSchemeText -match 'Power Scheme GUID:\s*([a-fA-F0-9-]+)\s*\((.+?)\)') {
    $activeSchemeGuid = $matches[1]
    $activeSchemeName = $matches[2]
}

$result = [pscustomobject]@{
    detector             = 'powercfg'
    timestamp_local      = (Get-Date).ToString('s')
    active_scheme_guid   = $activeSchemeGuid
    active_scheme_name   = $activeSchemeName
    sub_processor_guid   = $subProcessor
    read_only_commands   = @($commands | ForEach-Object {
        [pscustomobject]@{
            name          = $_.name
            command_line  = $_.command_line
            exit_code     = $_.exit_code
            timed_out     = $_.timed_out
            succeeded     = $_.succeeded
            stdout_path   = $_.stdout_path
            stderr_path   = $_.stderr_path
            error         = $_.error
        }
    })
    processor_settings   = @($settingResults)
    future_safety_notes  = @(
        'Phase 1 only queried powercfg values and read visibility attributes.',
        'Future writes should clone or export the active plan first, then require explicit confirmation.',
        'Admin privileges may be required for some powercfg writes and hidden-setting visibility changes.',
        'Hidden setting visibility was detected by reading Attributes only; Phase 1 did not modify Attributes.'
    )
}

Write-Phase1JsonFile -Path (Join-Path $context.raw_output_dir 'powercfg_detector_result.json') -InputObject $result -Depth 14
Write-Phase1Log -Context $context -Message 'Finished detector powercfg'
$result | ConvertTo-Json -Depth 14
