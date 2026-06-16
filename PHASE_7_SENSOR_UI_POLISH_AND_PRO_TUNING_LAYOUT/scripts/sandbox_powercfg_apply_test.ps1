Set-StrictMode -Version 2.0
$ErrorActionPreference = "Stop"
. "$PSScriptRoot\Phase4Common.ps1"

$Phase4Root = Get-Phase4Root
$Raw = Join-Path $Phase4Root "raw_outputs\sandbox_powercfg"
$SandboxDir = Join-Path $Phase4Root "sandbox"
Ensure-Directory $Raw
Ensure-Directory $SandboxDir

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$sandboxName = "AERO_X16_CC_SANDBOX_DO_NOT_USE_$timestamp"
$resultPath = Join-Path $SandboxDir "sandbox_powercfg_test_result.json"
$logPath = Join-Path $SandboxDir "sandbox_powercfg_test_log.md"

$commands = New-Object System.Collections.ArrayList
$writes = New-Object System.Collections.ArrayList
$sandboxGuid = $null
$safety = [pscustomobject]@{
    write_targeted_active_scheme = $false
    write_used_scheme_current = $false
    setactive_executed = $false
}

function Finish-Result {
    param([object]$Result)
    Write-JsonFile -Path $resultPath -Data $Result | Out-Null
    $lines = New-Object System.Collections.ArrayList
    [void]$lines.Add("# Sandbox Powercfg Apply Test")
    [void]$lines.Add("")
    [void]$lines.Add("- Ran: $($Result.ran)")
    [void]$lines.Add("- Passed: $($Result.passed)")
    [void]$lines.Add("- Sandbox GUID: $($Result.sandbox_guid)")
    [void]$lines.Add("- Active before: $($Result.active_scheme_before.guid)")
    [void]$lines.Add("- Active after: $($Result.active_scheme_after.guid)")
    [void]$lines.Add("- Cleanup deleted: $($Result.cleanup.deleted)")
    if ($Result.skip_reason) { [void]$lines.Add("- Skip reason: $($Result.skip_reason)") }
    if ($Result.failure) { [void]$lines.Add("- Failure: $($Result.failure)") }
    if ($Result.cleanup.warning) { [void]$lines.Add("- Cleanup warning: $($Result.cleanup.warning)") }
    $lines | Set-Content -LiteralPath $logPath -Encoding UTF8
    $Result | ConvertTo-Json -Depth 12
}

try {
    $activeBefore = Get-ActivePowerSchemeCaptured -RawOutputDir $Raw
    [void]$commands.Add($activeBefore.command)
    if (-not $activeBefore.guid) { throw "Unable to parse active power plan before sandbox test." }

    $duplicate = Invoke-CapturedCommand -Name "powercfg_duplicate_active_to_sandbox" -Command @("powercfg.exe", "/duplicatescheme", $activeBefore.guid) -RawOutputDir $Raw
    [void]$commands.Add($duplicate)
    if ($duplicate.exit_code -ne 0) { throw "powercfg /duplicatescheme failed. No writes were attempted." }

    $dupMatch = [regex]::Match($duplicate.stdout, "([a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12})")
    if (-not $dupMatch.Success) { throw "Could not parse sandbox scheme GUID from duplicate output: $($duplicate.stdout)" }
    $sandboxGuid = $dupMatch.Groups[1].Value

    $rename = Invoke-CapturedCommand -Name "powercfg_rename_sandbox" -Command @("powercfg.exe", "/changename", $sandboxGuid, $sandboxName) -RawOutputDir $Raw
    [void]$commands.Add($rename)

    $activeCheck = Get-ActivePowerSchemeCaptured -RawOutputDir $Raw
    [void]$commands.Add($activeCheck.command)
    $sandboxWasActive = ($activeCheck.guid -eq $sandboxGuid)
    if ($sandboxWasActive) { throw "Sandbox scheme unexpectedly became active. Refusing writes." }

    $eppGuid = "36687f9e-e3a5-4dbf-b1dc-15eb381c6863"
    $coolGuid = "94d3a615-a899-4ac5-ae2b-e4d8f634367f"
    $subProcessor = "54533251-82be-4824-96c1-47b60b740d00"

    $beforeEppCmd = Invoke-CapturedCommand -Name "sandbox_query_epp_before" -Command @("powercfg.exe", "/query", $sandboxGuid, $subProcessor, $eppGuid) -RawOutputDir $Raw
    $beforeCoolCmd = Invoke-CapturedCommand -Name "sandbox_query_cooling_before" -Command @("powercfg.exe", "/query", $sandboxGuid, $subProcessor, $coolGuid) -RawOutputDir $Raw
    [void]$commands.Add($beforeEppCmd)
    [void]$commands.Add($beforeCoolCmd)
    $beforeEpp = Parse-PowerCfgSettingValues -Text $beforeEppCmd.stdout
    $beforeCool = Parse-PowerCfgSettingValues -Text $beforeCoolCmd.stdout
    if ($beforeEpp.ac_value -eq $null -or $beforeCool.ac_value -eq $null) {
        throw "Sandbox setting values could not be read before writes. No writes were attempted."
    }

    $eppTest = if ($beforeEpp.ac_value -eq 44) { 55 } else { 44 }
    $coolTest = if ($beforeCool.ac_value -eq 0) { 1 } else { 0 }

    foreach ($write in @(
        @{ name = "sandbox_write_epp_ac"; guid = $eppGuid; value = $eppTest },
        @{ name = "sandbox_write_cooling_ac"; guid = $coolGuid; value = $coolTest }
    )) {
        if ($sandboxGuid -eq $activeBefore.guid) { $safety.write_targeted_active_scheme = $true; throw "Write target equals active scheme." }
        $cmd = @("powercfg.exe", "/setacvalueindex", $sandboxGuid, $subProcessor, [string]$write.guid, [string]$write.value)
        [void]$writes.Add([pscustomobject]@{ command = $cmd; target_guid = $sandboxGuid; setting_guid = $write.guid; value = $write.value })
        $writeResult = Invoke-CapturedCommand -Name $write.name -Command $cmd -RawOutputDir $Raw
        [void]$commands.Add($writeResult)
        if ($writeResult.exit_code -ne 0) { throw "Sandbox write failed: $($write.name)" }
    }

    $afterEppCmd = Invoke-CapturedCommand -Name "sandbox_query_epp_after" -Command @("powercfg.exe", "/query", $sandboxGuid, $subProcessor, $eppGuid) -RawOutputDir $Raw
    $afterCoolCmd = Invoke-CapturedCommand -Name "sandbox_query_cooling_after" -Command @("powercfg.exe", "/query", $sandboxGuid, $subProcessor, $coolGuid) -RawOutputDir $Raw
    [void]$commands.Add($afterEppCmd)
    [void]$commands.Add($afterCoolCmd)
    $afterEpp = Parse-PowerCfgSettingValues -Text $afterEppCmd.stdout
    $afterCool = Parse-PowerCfgSettingValues -Text $afterCoolCmd.stdout
    $verified = ($afterEpp.ac_value -eq $eppTest -and $afterCool.ac_value -eq $coolTest)

    $restoreEpp = Invoke-CapturedCommand -Name "sandbox_restore_epp_ac_inside_clone" -Command @("powercfg.exe", "/setacvalueindex", $sandboxGuid, $subProcessor, $eppGuid, [string]$beforeEpp.ac_value) -RawOutputDir $Raw
    $restoreCool = Invoke-CapturedCommand -Name "sandbox_restore_cooling_ac_inside_clone" -Command @("powercfg.exe", "/setacvalueindex", $sandboxGuid, $subProcessor, $coolGuid, [string]$beforeCool.ac_value) -RawOutputDir $Raw
    [void]$commands.Add($restoreEpp)
    [void]$commands.Add($restoreCool)

    $cleanup = powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "cleanup_sandbox_power_plan.ps1") -SandboxGuid $sandboxGuid | ConvertFrom-Json
    $activeAfter = Get-ActivePowerSchemeCaptured -RawOutputDir $Raw
    [void]$commands.Add($activeAfter.command)

    $passed = ($verified -and $cleanup.deleted -eq $true -and $activeBefore.guid -eq $activeAfter.guid -and -not $safety.write_targeted_active_scheme -and -not $safety.write_used_scheme_current -and -not $safety.setactive_executed)
    $result = [pscustomobject]@{
        generated_local = (Get-Date).ToString("s")
        ran = $true
        passed = $passed
        sandbox_name = $sandboxName
        sandbox_guid = $sandboxGuid
        sandbox_was_active = $sandboxWasActive
        active_scheme_before = [pscustomobject]@{ guid = $activeBefore.guid; name = $activeBefore.name }
        active_scheme_after = [pscustomobject]@{ guid = $activeAfter.guid; name = $activeAfter.name }
        writes = $writes
        before_values = [pscustomobject]@{ epp_ac = $beforeEpp.ac_value; cooling_ac = $beforeCool.ac_value }
        test_values = [pscustomobject]@{ epp_ac = $eppTest; cooling_ac = $coolTest }
        after_values = [pscustomobject]@{ epp_ac = $afterEpp.ac_value; cooling_ac = $afterCool.ac_value }
        verified_expected_values = $verified
        cleanup = $cleanup
        safety = $safety
        commands = $commands
        failure = if ($passed) { $null } else { "One or more sandbox verification checks failed." }
        skip_reason = $null
    }
    Finish-Result -Result $result
} catch {
    $activeAfterCatch = Get-ActivePowerSchemeCaptured -RawOutputDir $Raw
    $cleanupResult = [pscustomobject]@{ deleted = $false; warning = "Cleanup not needed or not attempted."; attempted = $false }
    if ($sandboxGuid) {
        try {
            $cleanupResult = powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "cleanup_sandbox_power_plan.ps1") -SandboxGuid $sandboxGuid | ConvertFrom-Json
            if ($cleanupResult.deleted -ne $true -and -not $cleanupResult.warning) {
                $cleanupResult.warning = "Cleanup command completed but did not confirm deletion."
            }
        } catch {
            $cleanupResult = [pscustomobject]@{
                deleted = $false
                warning = "Cleanup attempt failed: $($_.Exception.Message). If sandbox_guid is present, run cleanup_sandbox_power_plan.ps1 manually."
                attempted = $true
            }
        }
    }
    $result = [pscustomobject]@{
        generated_local = (Get-Date).ToString("s")
        ran = $false
        passed = $false
        sandbox_name = $sandboxName
        sandbox_guid = $sandboxGuid
        sandbox_was_active = $false
        active_scheme_before = if (Get-Variable -Name activeBefore -Scope Local -ErrorAction SilentlyContinue) { [pscustomobject]@{ guid = $activeBefore.guid; name = $activeBefore.name } } else { [pscustomobject]@{ guid = $null; name = $null } }
        active_scheme_after = [pscustomobject]@{ guid = $activeAfterCatch.guid; name = $activeAfterCatch.name }
        writes = $writes
        cleanup = $cleanupResult
        safety = $safety
        commands = $commands
        failure = $_.Exception.Message
        skip_reason = $_.Exception.Message
    }
    Finish-Result -Result $result
    exit 1
}
