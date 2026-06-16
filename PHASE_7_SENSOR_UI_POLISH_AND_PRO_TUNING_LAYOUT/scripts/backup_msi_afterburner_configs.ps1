Set-StrictMode -Version 2.0
$ErrorActionPreference = "Stop"
. "$PSScriptRoot\Phase4Common.ps1"

$Phase4Root = Get-Phase4Root
$AppRoot = Split-Path -Parent $Phase4Root
$Phase1Root = Join-Path $AppRoot "PHASE_1_EXPLORATION"
$Raw = Join-Path $Phase4Root "raw_outputs\msi_backup"
$BackupDir = Join-Path $Phase4Root "backups\msi_afterburner"
$FilesDir = Join-Path $BackupDir "files"
Ensure-Directory $Raw
Ensure-Directory $FilesDir

$phase1MsiPath = Join-Path $Phase1Root "raw_outputs\msi_afterburner_detector_result.json"
if (-not (Test-Path -LiteralPath $phase1MsiPath)) {
    throw "Missing Phase 1 MSI detector result: $phase1MsiPath"
}
$msi = Get-Content -LiteralPath $phase1MsiPath -Raw | ConvertFrom-Json
$sourceFiles = New-Object System.Collections.ArrayList
foreach ($collectionName in @("config_files", "profile_files")) {
    foreach ($file in @($msi.$collectionName)) {
        if ($file.path) { [void]$sourceFiles.Add([pscustomobject]@{ collection = $collectionName; path = [string]$file.path }) }
    }
}
if ($msi.msi_afterburner_cfg -and $msi.msi_afterburner_cfg.path) {
    [void]$sourceFiles.Add([pscustomobject]@{ collection = "main_cfg"; path = [string]$msi.msi_afterburner_cfg.path })
}

$copied = New-Object System.Collections.ArrayList
$skipped = New-Object System.Collections.ArrayList
$seen = @{}
foreach ($entry in $sourceFiles) {
    $src = $entry.path
    if ($seen.ContainsKey($src)) { continue }
    $seen[$src] = $true
    if (-not (Test-Path -LiteralPath $src)) {
        [void]$skipped.Add([pscustomobject]@{ source_path = $src; reason = "missing_at_backup_time" })
        continue
    }
    $sha = [System.Security.Cryptography.SHA256]::Create()
    $sourceHashName = ([System.BitConverter]::ToString($sha.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($src))).Replace("-", "")).Substring(0, 12)
    $leafSafe = ([IO.Path]::GetFileName($src) -replace "[\\/:*?`"<>|&]", "_")
    $dest = Join-Path $FilesDir "$sourceHashName`_$leafSafe"
    Ensure-Directory (Split-Path -Parent $dest)
    Copy-Item -LiteralPath $src -Destination $dest -Force
    $srcHash = Get-FileHashRecord -Path $src
    $destHash = Get-FileHashRecord -Path $dest
    [void]$copied.Add([pscustomobject]@{
        collection = $entry.collection
        source_path = $src
        destination_path = $dest
        source_hash = $srcHash
        destination_hash = $destHash
        copied = $true
    })
}

$manifest = [pscustomobject]@{
    generated_local = (Get-Date).ToString("s")
    msi_afterburner_executable_path = if ($msi.executable_paths) { $msi.executable_paths[0].path } else { $null }
    rtss_executable_path = if ($msi.rtss_executable_paths) { $msi.rtss_executable_paths[0].path } else { $null }
    install_folder = $msi.install_folder
    profiles_folder = if ($msi.profiles_folder) { $msi.profiles_folder.path } else { $null }
    copied_files = $copied
    skipped_items = $skipped
    original_files_modified = $false
}

$manifestPath = Join-Path $BackupDir "msi_backup_manifest.json"
Write-JsonFile -Path $manifestPath -Data $manifest | Out-Null
Write-JsonFile -Path (Join-Path $Raw "backup_msi_afterburner_configs_result.json") -Data $manifest | Out-Null
$manifest | ConvertTo-Json -Depth 12
