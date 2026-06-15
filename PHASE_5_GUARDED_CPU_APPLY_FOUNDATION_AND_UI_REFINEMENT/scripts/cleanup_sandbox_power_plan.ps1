param(
    [string]$SandboxGuid
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = "Stop"
. "$PSScriptRoot\Phase4Common.ps1"

$Phase4Root = Get-Phase4Root
$Raw = Join-Path $Phase4Root "raw_outputs\sandbox_cleanup"
Ensure-Directory $Raw

if (-not $SandboxGuid) {
    throw "SandboxGuid is required."
}

$active = Get-ActivePowerSchemeCaptured -RawOutputDir $Raw
if ($active.guid -eq $SandboxGuid) {
    throw "Refusing to delete sandbox because it is active: $SandboxGuid"
}

$delete = Invoke-CapturedCommand -Name "powercfg_delete_sandbox_$SandboxGuid" -Command @("powercfg.exe", "/delete", $SandboxGuid) -RawOutputDir $Raw
$list = Invoke-CapturedCommand -Name "powercfg_list_after_cleanup" -Command @("powercfg.exe", "/list") -RawOutputDir $Raw
$existsAfter = $list.stdout -match [regex]::Escape($SandboxGuid)

$result = [pscustomobject]@{
    generated_local = (Get-Date).ToString("s")
    sandbox_guid = $SandboxGuid
    active_scheme_guid = $active.guid
    delete_exit_code = $delete.exit_code
    deleted = ($delete.exit_code -eq 0 -and -not $existsAfter)
    exists_after = $existsAfter
    warning = if ($existsAfter) { "Sandbox scheme still appears in powercfg /list." } else { $null }
    commands = @($active.command, $delete, $list)
}
$result | ConvertTo-Json -Depth 10
