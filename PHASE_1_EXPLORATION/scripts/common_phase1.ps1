# Shared Phase 1 helpers. These functions only read state and write artifacts
# inside the Phase 1 project folder.

function New-Phase1Directory {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path | Out-Null
    }
}

function Initialize-DetectorContext {
    param(
        [string]$PhaseRoot,
        [string]$DetectorName
    )

    $rawOutputDir = Join-Path $PhaseRoot 'raw_outputs'
    New-Phase1Directory -Path $rawOutputDir

    $logPath = Join-Path $rawOutputDir ("{0}_log.txt" -f $DetectorName)
    $context = [pscustomobject]@{
        phase_root     = $PhaseRoot
        raw_output_dir = $rawOutputDir
        detector_name  = $DetectorName
        log_path       = $logPath
    }

    Write-Phase1Log -Context $context -Message "Starting detector $DetectorName"
    return $context
}

function Write-Phase1Log {
    param(
        [pscustomobject]$Context,
        [string]$Message,
        [string]$Level = 'INFO'
    )

    $line = "{0}`t{1}`t{2}" -f (Get-Date).ToString('s'), $Level, $Message
    Add-Content -LiteralPath $Context.log_path -Value $line -Encoding UTF8
}

function ConvertTo-Phase1SafeName {
    param([string]$Name)

    $safe = $Name -replace '[^A-Za-z0-9_.-]', '_'
    if ([string]::IsNullOrWhiteSpace($safe)) {
        return 'output'
    }
    return $safe
}

function Save-Phase1RawText {
    param(
        [pscustomobject]$Context,
        [string]$Name,
        [string]$Text
    )

    $safeName = ConvertTo-Phase1SafeName -Name $Name
    $path = Join-Path $Context.raw_output_dir ("{0}_{1}.txt" -f $Context.detector_name, $safeName)
    Set-Content -LiteralPath $path -Value $Text -Encoding UTF8
    Write-Phase1Log -Context $Context -Message "Wrote raw text $path"
    return $path
}

function Join-Phase1CommandArguments {
    param([string[]]$Arguments)

    $joined = New-Object System.Collections.ArrayList
    foreach ($arg in @($Arguments)) {
        if ($null -eq $arg) {
            continue
        }
        $text = [string]$arg
        if ($text -match '[\s"]') {
            $text = '"' + ($text -replace '"', '\"') + '"'
        }
        [void]$joined.Add($text)
    }
    return (@($joined) -join ' ')
}

function Invoke-Phase1ReadOnlyCommand {
    param(
        [pscustomobject]$Context,
        [string]$Name,
        [string]$FilePath,
        [string[]]$Arguments = @(),
        [int]$TimeoutSeconds = 30
    )

    $safeName = ConvertTo-Phase1SafeName -Name $Name
    $stdoutPath = Join-Path $Context.raw_output_dir ("{0}_{1}_stdout.txt" -f $Context.detector_name, $safeName)
    $stderrPath = Join-Path $Context.raw_output_dir ("{0}_{1}_stderr.txt" -f $Context.detector_name, $safeName)

    Remove-Item -LiteralPath $stdoutPath, $stderrPath -ErrorAction SilentlyContinue
    Write-Phase1Log -Context $Context -Message ("Running read-only command: {0} {1}" -f $FilePath, (Join-Phase1CommandArguments -Arguments $Arguments))

    $result = [ordered]@{
        name            = $Name
        file_path       = $FilePath
        arguments       = @($Arguments)
        command_line    = ("{0} {1}" -f $FilePath, (Join-Phase1CommandArguments -Arguments $Arguments)).Trim()
        timeout_seconds = $TimeoutSeconds
        started_local   = (Get-Date).ToString('s')
        exit_code       = $null
        timed_out       = $false
        succeeded       = $false
        stdout_path     = $stdoutPath
        stderr_path     = $stderrPath
        stdout          = ''
        stderr          = ''
        error           = $null
    }

    try {
        if (-not (Test-Path -LiteralPath $FilePath)) {
            $cmd = Get-Command $FilePath -ErrorAction SilentlyContinue
            if ($cmd) {
                $FilePath = $cmd.Source
                $result.file_path = $FilePath
            }
        }

        $psi = New-Object System.Diagnostics.ProcessStartInfo
        $psi.FileName = $FilePath
        $psi.Arguments = Join-Phase1CommandArguments -Arguments $Arguments
        $psi.UseShellExecute = $false
        $psi.RedirectStandardOutput = $true
        $psi.RedirectStandardError = $true
        $psi.CreateNoWindow = $true

        $process = New-Object System.Diagnostics.Process
        $process.StartInfo = $psi
        [void]$process.Start()

        $stdoutTask = $process.StandardOutput.ReadToEndAsync()
        $stderrTask = $process.StandardError.ReadToEndAsync()

        $exited = $process.WaitForExit($TimeoutSeconds * 1000)
        if (-not $exited) {
            $result.timed_out = $true
            try { $process.Kill() } catch { }
            Write-Phase1Log -Context $Context -Level 'WARN' -Message "Command timed out: $Name"
        } else {
            $process.WaitForExit()
            $result.exit_code = $process.ExitCode
        }

        try { $result.stdout = $stdoutTask.Result } catch { $result.stdout = '' }
        try { $result.stderr = $stderrTask.Result } catch { $result.stderr = '' }

        Set-Content -LiteralPath $stdoutPath -Value $result.stdout -Encoding UTF8
        Set-Content -LiteralPath $stderrPath -Value $result.stderr -Encoding UTF8

        $result.succeeded = (($result.exit_code -eq 0) -and (-not $result.timed_out))
    } catch {
        $result.error = $_.Exception.Message
        Write-Phase1Log -Context $Context -Level 'WARN' -Message ("Command failed: {0}: {1}" -f $Name, $_.Exception.Message)
    }

    $result.finished_local = (Get-Date).ToString('s')
    return [pscustomobject]$result
}

function Get-Phase1FileInfo {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        return $null
    }

    $item = Get-Item -LiteralPath $Path -ErrorAction SilentlyContinue
    if (-not $item) {
        return $null
    }

    $version = $null
    try {
        if ($item.VersionInfo) {
            $version = $item.VersionInfo.FileVersion
        }
    } catch { }

    return [pscustomobject]@{
        path             = $item.FullName
        name             = $item.Name
        exists           = $true
        length_bytes     = if ($item.PSIsContainer) { $null } else { $item.Length }
        last_write_local = $item.LastWriteTime.ToString('s')
        file_version     = $version
        is_directory     = [bool]$item.PSIsContainer
    }
}

function Get-Phase1UninstallEntries {
    param([string]$Pattern)

    $roots = @(
        'HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*',
        'HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*',
        'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*'
    )

    $entries = New-Object System.Collections.ArrayList
    foreach ($root in $roots) {
        $items = Get-ItemProperty -Path $root -ErrorAction SilentlyContinue
        foreach ($item in @($items)) {
            $displayName = [string]$item.DisplayName
            if ([string]::IsNullOrWhiteSpace($displayName)) {
                continue
            }
            if ($displayName -match $Pattern) {
                [void]$entries.Add([pscustomobject]@{
                    display_name     = $displayName
                    display_version  = $item.DisplayVersion
                    publisher        = $item.Publisher
                    install_location = $item.InstallLocation
                    uninstall_string = $item.UninstallString
                    registry_path    = $item.PSPath
                })
            }
        }
    }

    return @($entries)
}

function Find-Phase1Files {
    param(
        [string[]]$Roots,
        [string[]]$Filters,
        [int]$MaxResults = 80
    )

    $results = New-Object System.Collections.ArrayList
    $seen = @{}

    foreach ($root in @($Roots)) {
        if ([string]::IsNullOrWhiteSpace($root) -or -not (Test-Path -LiteralPath $root)) {
            continue
        }

        foreach ($filter in @($Filters)) {
            try {
                $files = Get-ChildItem -LiteralPath $root -Recurse -File -Filter $filter -ErrorAction SilentlyContinue
                foreach ($file in @($files)) {
                    if ($seen.ContainsKey($file.FullName)) {
                        continue
                    }
                    $seen[$file.FullName] = $true
                    [void]$results.Add((Get-Phase1FileInfo -Path $file.FullName))
                    if (@($results).Count -ge $MaxResults) {
                        return @($results)
                    }
                }
            } catch { }
        }
    }

    return @($results)
}

function Get-Phase1ShortcutInfo {
    param([string[]]$NamePatterns)

    $roots = @(
        "$env:ProgramData\Microsoft\Windows\Start Menu",
        "$env:AppData\Microsoft\Windows\Start Menu"
    )

    $shortcuts = New-Object System.Collections.ArrayList
    $shell = $null
    try { $shell = New-Object -ComObject WScript.Shell } catch { }

    foreach ($root in $roots) {
        if (-not (Test-Path -LiteralPath $root)) {
            continue
        }

        $lnks = Get-ChildItem -LiteralPath $root -Recurse -File -Filter '*.lnk' -ErrorAction SilentlyContinue
        foreach ($lnk in @($lnks)) {
            $matchesPattern = $false
            foreach ($pattern in @($NamePatterns)) {
                if ($lnk.Name -match $pattern -or $lnk.FullName -match $pattern) {
                    $matchesPattern = $true
                    break
                }
            }
            if (-not $matchesPattern) {
                continue
            }

            $target = $null
            $arguments = $null
            if ($shell) {
                try {
                    $shortcut = $shell.CreateShortcut($lnk.FullName)
                    $target = $shortcut.TargetPath
                    $arguments = $shortcut.Arguments
                } catch { }
            }

            [void]$shortcuts.Add([pscustomobject]@{
                path             = $lnk.FullName
                name             = $lnk.Name
                target_path      = $target
                arguments        = $arguments
                last_write_local = $lnk.LastWriteTime.ToString('s')
            })
        }
    }

    return @($shortcuts)
}

function Get-Phase1ProcessMatches {
    param([string[]]$Patterns)

    $processes = New-Object System.Collections.ArrayList
    foreach ($process in @(Get-Process -ErrorAction SilentlyContinue)) {
        $matched = New-Object System.Collections.ArrayList
        foreach ($pattern in @($Patterns)) {
            if ($process.ProcessName -match $pattern) {
                [void]$matched.Add($pattern)
            }
        }
        if (@($matched).Count -eq 0) {
            continue
        }

        $path = $null
        try { $path = $process.Path } catch { }
        [void]$processes.Add([pscustomobject]@{
            process_name = $process.ProcessName
            id           = $process.Id
            path         = $path
            cpu_seconds  = $process.CPU
            matched      = @($matched)
        })
    }

    return @($processes)
}

function Write-Phase1JsonFile {
    param(
        [string]$Path,
        [object]$InputObject,
        [int]$Depth = 12
    )

    $json = $InputObject | ConvertTo-Json -Depth $Depth
    Set-Content -LiteralPath $Path -Value $json -Encoding UTF8
}

function Get-Phase1KnownSearchRoots {
    param([string]$PhaseRoot)

    $roots = New-Object System.Collections.ArrayList
    foreach ($candidate in @(
        $env:ProgramFiles,
        ${env:ProgramFiles(x86)},
        "$env:USERPROFILE\Downloads",
        (Split-Path -Parent (Split-Path -Parent $PhaseRoot)),
        $PhaseRoot
    )) {
        if (-not [string]::IsNullOrWhiteSpace($candidate) -and (Test-Path -LiteralPath $candidate)) {
            [void]$roots.Add($candidate)
        }
    }

    return @($roots | Select-Object -Unique)
}
