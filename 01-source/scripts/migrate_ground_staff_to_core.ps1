[CmdletBinding()]
param(
    [string]$ProjectPath = "D:\SCC\DigitalFactoryBase_SCC\DigitalFactoryBase.uproject",
    [string]$EngineRoot = "D:\UE_5.6",
    [string]$DestinationContent = ""
)

$ErrorActionPreference = "Stop"
$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
$processes = @(Get-Process -ErrorAction SilentlyContinue | Where-Object {
    $_.ProcessName -in @("UnrealEditor", "UnrealEditor-Cmd")
})
if ($processes.Count -gt 0) {
    throw "Close every Unreal Editor process before migrating Ground Staff assets."
}
if (-not (Test-Path -LiteralPath $ProjectPath -PathType Leaf)) {
    throw "UE project file does not exist: $ProjectPath"
}

$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
if ([string]::IsNullOrWhiteSpace($DestinationContent)) {
    $DestinationContent = Join-Path $repoRoot "ue_project\Plugins\OntoTwinCharacterPack_Core\HostContent\Content"
}
New-Item -ItemType Directory -Path $DestinationContent -Force | Out-Null
$resolvedDestination = (Resolve-Path -LiteralPath $DestinationContent).Path
if ((Split-Path $resolvedDestination -Leaf) -ne "Content") {
    throw "Destination must be a Content directory: $resolvedDestination"
}

$resolvedProject = (Resolve-Path -LiteralPath $ProjectPath).Path
$projectRoot = Split-Path -Parent $resolvedProject
$sourceContent = Join-Path $projectRoot "Content"
$editorCmd = Join-Path $EngineRoot "Engine\Binaries\Win64\UnrealEditor-Cmd.exe"
$pythonScript = Join-Path $PSScriptRoot "ue_migrate_ground_staff_to_core.py"
$runRoot = Join-Path $projectRoot ("Saved\OntoTwinCharacterPack_Core\Migrate_" + (Get-Date -Format "yyyyMMdd_HHmmss"))
$backup = Join-Path $runRoot (Split-Path $resolvedProject -Leaf)
$manifestPath = Join-Path $runRoot "ground_staff_dependencies.json"
$log = Join-Path $runRoot "migrate.log"
New-Item -ItemType Directory -Path $runRoot -Force | Out-Null
Copy-Item -LiteralPath $resolvedProject -Destination $backup
$previousManifest = $env:ONTOTWIN_GROUND_STAFF_MANIFEST

try {
    $project = Get-Content -LiteralPath $resolvedProject -Raw -Encoding UTF8 | ConvertFrom-Json
    $plugins = @($project.Plugins)
    foreach ($pluginName in @("PythonScriptPlugin", "EditorScriptingUtilities")) {
        $entry = $plugins | Where-Object { $_.Name -eq $pluginName } | Select-Object -First 1
        if ($entry) {
            $entry.Enabled = $true
        }
        else {
            $plugins += [pscustomobject][ordered]@{
                Name = $pluginName
                Enabled = $true
                TargetAllowList = @("Editor")
            }
        }
    }
    $project.Plugins = $plugins
    [System.IO.File]::WriteAllText(
        $resolvedProject,
        ($project | ConvertTo-Json -Depth 64) + [Environment]::NewLine,
        $Utf8NoBom)
    $env:ONTOTWIN_GROUND_STAFF_MANIFEST = $manifestPath

    & $editorCmd @(
        $resolvedProject,
        "-ExecutePythonScript=$pythonScript",
        "-abslog=$log",
        "-unattended", "-nop4", "-nullrhi", "-nosplash", "-NoSound", "-UTF8Output"
    )
    if ($LASTEXITCODE -ne 0) {
        throw "Unreal dependency scan failed with exit code $LASTEXITCODE. Log: $log"
    }
}
finally {
    Copy-Item -LiteralPath $backup -Destination $resolvedProject -Force
    $env:ONTOTWIN_GROUND_STAFF_MANIFEST = $previousManifest
}

$text = Get-Content -LiteralPath $log -Raw -Encoding UTF8
if (-not $text.Contains("ONTOTWIN_GROUND_STAFF_MIGRATE_BEGIN") -or
    -not $text.Contains("ONTOTWIN_GROUND_STAFF_MIGRATE_END") -or
    -not $text.Contains('"success": true') -or
    $text.Contains("ONTOTWIN_GROUND_STAFF_MIGRATE_ERROR")) {
    throw "Ground Staff dependency scan did not produce a clean result: $log"
}
$manifest = Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
$allowedExternalPrefixes = @(
    "/Game/Art/A08_Characters/maozi/",
    "/Game/Characters/Heroes/Mannequin/"
)
$unexpectedExternal = @($manifest.external_game_dependencies | Where-Object {
    $package = $_
    -not ($allowedExternalPrefixes | Where-Object { $package.StartsWith($_) })
})
if ($unexpectedExternal.Count -gt 0) {
    $summary = $unexpectedExternal -join ", "
    throw "Ground Staff dependency closure escaped the approved paths: $summary"
}
$allowedUnresolved = @(
    "/Game/Characters/Heroes/Mannequin/Meshes/SKM_Manny",
    "/Game/Characters/Heroes/Mannequin/Meshes/SKM_Quinn"
)
$unexpectedUnresolved = @($manifest.unresolved_game_dependencies | Where-Object {
    $_ -notin $allowedUnresolved
})
if ($unexpectedUnresolved.Count -gt 0) {
    $summary = $unexpectedUnresolved -join ", "
    throw "Ground Staff contains unexpected unresolved dependencies: $summary"
}

$copied = 0
$bytes = 0L
foreach ($package in @($manifest.packages)) {
    $relativeBase = $package.Substring(6).Replace('/', '\')
    $sourceFile = Join-Path $sourceContent ($relativeBase + ".uasset")
    if (-not (Test-Path -LiteralPath $sourceFile -PathType Leaf)) {
        $sourceFile = Join-Path $sourceContent ($relativeBase + ".umap")
    }
    if (-not (Test-Path -LiteralPath $sourceFile -PathType Leaf)) {
        throw "Dependency package has no source file: $package"
    }
    $targetFile = Join-Path $resolvedDestination $sourceFile.Substring($sourceContent.Length).TrimStart('\')
    if (Test-Path -LiteralPath $targetFile -PathType Leaf) {
        $sourceHash = (Get-FileHash -LiteralPath $sourceFile -Algorithm SHA256).Hash
        $targetHash = (Get-FileHash -LiteralPath $targetFile -Algorithm SHA256).Hash
        if ($sourceHash -ne $targetHash) {
            throw "Core payload conflict; refusing to overwrite: $targetFile"
        }
        continue
    }
    New-Item -ItemType Directory -Path (Split-Path -Parent $targetFile) -Force | Out-Null
    Copy-Item -LiteralPath $sourceFile -Destination $targetFile
    $copied += 1
    $bytes += (Get-Item -LiteralPath $sourceFile).Length
}

$files = @(Get-ChildItem -LiteralPath $resolvedDestination -Recurse -File)
[pscustomobject][ordered]@{
    success = $true
    destination = $resolvedDestination
    dependency_packages = @($manifest.packages).Count
    unresolved_dependencies = @($manifest.unresolved_game_dependencies)
    files_copied = $copied
    bytes_copied = $bytes
    payload_files = $files.Count
    payload_bytes = ($files | Measure-Object -Property Length -Sum).Sum
    manifest = $manifestPath
    log = $log
    uproject_restored = $true
} | ConvertTo-Json -Depth 8
