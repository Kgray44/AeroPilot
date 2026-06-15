Set-StrictMode -Version 2.0

function Get-Phase4Root {
    return (Split-Path -Parent $PSScriptRoot)
}

function Ensure-Directory {
    param([string]$Path)
    New-Item -ItemType Directory -Path $Path -Force | Out-Null
}

function Write-JsonFile {
    param(
        [string]$Path,
        [object]$Data,
        [int]$Depth = 12
    )
    Ensure-Directory -Path (Split-Path -Parent $Path)
    $Data | ConvertTo-Json -Depth $Depth | Set-Content -LiteralPath $Path -Encoding UTF8
    return $Path
}

function Invoke-CapturedCommand {
    param(
        [string]$Name,
        [string[]]$Command,
        [string]$RawOutputDir
    )
    Ensure-Directory -Path $RawOutputDir
    $stdoutPath = Join-Path $RawOutputDir "$Name`_stdout.txt"
    $stderrPath = Join-Path $RawOutputDir "$Name`_stderr.txt"
    $started = Get-Date
    $stdout = $null
    $stderr = $null
    $exitCode = $null
    $errorText = $null
    try {
        $stdout = & $Command[0] @($Command[1..($Command.Count - 1)]) 2> $stderrPath
        $exitCode = $LASTEXITCODE
        ($stdout -join "`r`n") | Set-Content -LiteralPath $stdoutPath -Encoding UTF8
        $stderr = Get-Content -LiteralPath $stderrPath -Raw -ErrorAction SilentlyContinue
    } catch {
        $errorText = $_.Exception.Message
        $exitCode = -1
        "" | Set-Content -LiteralPath $stdoutPath -Encoding UTF8
        $errorText | Set-Content -LiteralPath $stderrPath -Encoding UTF8
    }
    return [pscustomobject]@{
        name = $Name
        command = $Command
        exit_code = $exitCode
        stdout_path = $stdoutPath
        stderr_path = $stderrPath
        stdout = (($stdout | Out-String).Trim())
        stderr = ($stderr | Out-String).Trim()
        error = $errorText
        started_at = $started.ToString("s")
        completed_at = (Get-Date).ToString("s")
    }
}

function Parse-ActivePowerScheme {
    param([string]$Text)
    $match = [regex]::Match($Text, "Power Scheme GUID:\s*([a-fA-F0-9-]+)\s*\((.+?)\)")
    if (-not $match.Success) {
        return [pscustomobject]@{ guid = $null; name = $null; raw = $Text }
    }
    return [pscustomobject]@{
        guid = $match.Groups[1].Value
        name = $match.Groups[2].Value
        raw = $Text
    }
}

function Get-ActivePowerSchemeCaptured {
    param([string]$RawOutputDir)
    $result = Invoke-CapturedCommand -Name "powercfg_get_active_scheme" -Command @("powercfg.exe", "/getactivescheme") -RawOutputDir $RawOutputDir
    $scheme = Parse-ActivePowerScheme -Text $result.stdout
    return [pscustomobject]@{
        command = $result
        guid = $scheme.guid
        name = $scheme.name
        raw = $scheme.raw
    }
}

function Parse-PowerCfgSettingValues {
    param([string]$Text)
    $ac = $null
    $dc = $null
    $acMatch = [regex]::Match($Text, "Current AC Power Setting Index:\s*0x([0-9a-fA-F]+)")
    $dcMatch = [regex]::Match($Text, "Current DC Power Setting Index:\s*0x([0-9a-fA-F]+)")
    if ($acMatch.Success) { $ac = [Convert]::ToInt64($acMatch.Groups[1].Value, 16) }
    if ($dcMatch.Success) { $dc = [Convert]::ToInt64($dcMatch.Groups[1].Value, 16) }
    return [pscustomobject]@{
        ac_value = $ac
        dc_value = $dc
        ac_hex = if ($acMatch.Success) { "0x$($acMatch.Groups[1].Value)" } else { $null }
        dc_hex = if ($dcMatch.Success) { "0x$($dcMatch.Groups[1].Value)" } else { $null }
    }
}

function Get-FileHashRecord {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) { return $null }
    $item = Get-Item -LiteralPath $Path
    $hash = Get-FileHash -LiteralPath $Path -Algorithm SHA256
    return [pscustomobject]@{
        path = $Path
        name = $item.Name
        length_bytes = $item.Length
        last_write_local = $item.LastWriteTime.ToString("s")
        sha256 = $hash.Hash
    }
}
