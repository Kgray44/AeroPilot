Set-StrictMode -Version 2.0
$ErrorActionPreference = "Stop"

$Phase3Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Logs = Join-Path $Phase3Root "logs"
New-Item -ItemType Directory -Path $Logs -Force | Out-Null

$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$Target = Join-Path $Logs "phase3_control_surface_bundle_$Timestamp.zip"
$ResolvedRoot = (Resolve-Path -LiteralPath $Phase3Root).Path

Add-Type -AssemblyName System.IO.Compression.FileSystem
if (Test-Path -LiteralPath $Target) {
    Remove-Item -LiteralPath $Target -Force
}

$Temp = Join-Path $env:TEMP "aero_phase3_bundle_$Timestamp"
New-Item -ItemType Directory -Path $Temp -Force | Out-Null
try {
    foreach ($Path in Get-ChildItem -LiteralPath $Phase3Root -Recurse -File) {
        $Resolved = (Resolve-Path -LiteralPath $Path.FullName).Path
        if (-not $Resolved.StartsWith($ResolvedRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
            throw "Refusing to bundle path outside Phase 3: $Resolved"
        }
        if ($Resolved -eq $Target) { continue }
        $Relative = $Resolved.Substring($ResolvedRoot.Length).TrimStart('\')
        $Dest = Join-Path $Temp $Relative
        New-Item -ItemType Directory -Path (Split-Path -Parent $Dest) -Force | Out-Null
        Copy-Item -LiteralPath $Resolved -Destination $Dest -Force
    }
    [System.IO.Compression.ZipFile]::CreateFromDirectory($Temp, $Target)
} finally {
    if (Test-Path -LiteralPath $Temp) {
        Remove-Item -LiteralPath $Temp -Recurse -Force
    }
}

Write-Output $Target
