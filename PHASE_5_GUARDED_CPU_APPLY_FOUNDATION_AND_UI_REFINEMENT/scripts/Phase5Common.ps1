Set-StrictMode -Version Latest

function Get-Phase5Root {
    Split-Path -Parent $PSScriptRoot
}

function New-Phase5Directory {
    param([Parameter(Mandatory = $true)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path | Out-Null
    }
}

function Get-Phase5Timestamp {
    Get-Date -Format 'yyyyMMdd-HHmmss'
}

function Test-Phase5Elevated {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Write-Phase5Json {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)]$Data
    )
    $parent = Split-Path -Parent $Path
    New-Phase5Directory -Path $parent
    $Data | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $Path -Encoding UTF8
}

function Get-Phase5Property {
    param(
        $Object,
        [Parameter(Mandatory = $true)][string]$Name,
        $Default = $null
    )
    if ($null -eq $Object) {
        return $Default
    }
    if ($Object.PSObject.Properties.Name -contains $Name) {
        return $Object.$Name
    }
    return $Default
}

function ConvertTo-Phase5CommandSummary {
    param($Result)
    if ($null -eq $Result) {
        return $null
    }
    [pscustomobject]@{
        command = Get-Phase5Property -Object $Result -Name 'command' -Default @()
        exit_code = Get-Phase5Property -Object $Result -Name 'exit_code' -Default $null
        stdout_path = Get-Phase5Property -Object $Result -Name 'stdout_path' -Default $null
        stderr_path = Get-Phase5Property -Object $Result -Name 'stderr_path' -Default $null
        error = Get-Phase5Property -Object $Result -Name 'error' -Default $null
    }
}

function Invoke-Phase5Command {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][string[]]$Command,
        [Parameter(Mandatory = $true)][string]$OutputDirectory
    )
    New-Phase5Directory -Path $OutputDirectory
    $stdoutPath = Join-Path $OutputDirectory "$Name`_stdout.txt"
    $stderrPath = Join-Path $OutputDirectory "$Name`_stderr.txt"
    $started = Get-Date -Format 's'
    $errorText = $null
    $exitCode = $null
    try {
        $exe = $Command[0]
        $args = @()
        if ($Command.Count -gt 1) {
            $args = $Command[1..($Command.Count - 1)]
        }
        & $exe @args > $stdoutPath 2> $stderrPath
        $exitCode = $LASTEXITCODE
    } catch {
        $errorText = $_.Exception.Message
        $exitCode = -1
        $errorText | Set-Content -LiteralPath $stderrPath -Encoding UTF8
        '' | Set-Content -LiteralPath $stdoutPath -Encoding UTF8
    }
    $completed = Get-Date -Format 's'
    $stdout = ''
    $stderr = ''
    if (Test-Path -LiteralPath $stdoutPath) { $stdout = Get-Content -LiteralPath $stdoutPath -Raw }
    if (Test-Path -LiteralPath $stderrPath) { $stderr = Get-Content -LiteralPath $stderrPath -Raw }
    [pscustomobject]@{
        name = $Name
        command = $Command
        exit_code = $exitCode
        stdout_path = $stdoutPath
        stderr_path = $stderrPath
        stdout = $stdout
        stderr = $stderr
        error = $errorText
        started_at = $started
        completed_at = $completed
    }
}

function Get-Phase5ActiveScheme {
    param([Parameter(Mandatory = $true)][string]$RawText)
    $guid = $null
    $name = $null
    if ($RawText -match 'Power Scheme GUID:\s*([a-fA-F0-9-]+)\s*\((.*?)\)') {
        $guid = $Matches[1]
        $name = $Matches[2]
    }
    [pscustomobject]@{
        guid = $guid
        name = $name
        raw = $RawText
    }
}
