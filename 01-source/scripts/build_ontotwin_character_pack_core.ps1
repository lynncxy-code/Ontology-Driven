[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectPath,

    [string]$EngineRoot = "D:\UE_5.6"
)

$ErrorActionPreference = "Stop"
$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)

function Assert-UnrealEditorClosed {
    $processes = @(Get-Process -ErrorAction SilentlyContinue | Where-Object {
        $_.ProcessName -in @("UnrealEditor", "UnrealEditor-Cmd")
    })
    if ($processes.Count -gt 0) {
        $summary = ($processes | ForEach-Object { "$($_.ProcessName) PID=$($_.Id)" }) -join ", "
        throw "Close every Unreal Editor process before building: $summary"
    }
}

function Enable-EditorPlugin([string]$Path, [string]$PluginName) {
    $project = Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json
    $plugins = @($project.Plugins)
    $entry = $plugins | Where-Object { $_.Name -eq $PluginName } | Select-Object -First 1
    if ($entry) {
        $entry.Enabled = $true
    }
    else {
        $plugins += [pscustomobject][ordered]@{
            Name = $PluginName
            Enabled = $true
            TargetAllowList = @("Editor")
        }
    }
    $project.Plugins = $plugins
    $json = $project | ConvertTo-Json -Depth 64
    [System.IO.File]::WriteAllText($Path, $json + [Environment]::NewLine, $Utf8NoBom)
}

function Invoke-UnrealPython([string]$EditorCmd, [string]$Project, [string]$Script, [string]$LogFile) {
    $arguments = @(
        $Project,
        "-ExecutePythonScript=$Script",
        "-abslog=$LogFile",
        "-unattended",
        "-nop4",
        "-nullrhi",
        "-nosplash",
        "-NoSound",
        "-UTF8Output"
    )
    & $EditorCmd @arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Unreal Python failed with exit code $LASTEXITCODE. Log: $LogFile"
    }
}

function Assert-UnrealLogSuccess([string]$LogFile, [string]$BeginMarker, [string]$EndMarker) {
    if (-not (Test-Path -LiteralPath $LogFile -PathType Leaf)) {
        throw "Unreal did not create the expected log: $LogFile"
    }
    $logText = Get-Content -LiteralPath $LogFile -Raw -Encoding UTF8
    if (-not $logText.Contains($BeginMarker) -or
        -not $logText.Contains($EndMarker) -or
        -not $logText.Contains('"success": true') -or
        $logText.Contains("LogPython: Error:")) {
        throw "Unreal log does not contain a clean success result: $LogFile"
    }
}

function Assert-AssetManagerSummary([string]$LogFile) {
    $logText = Get-Content -LiteralPath $LogFile -Raw -Encoding UTF8
    if ($logText -notmatch 'TwinCharacter:\s+Class TwinCharacterAsset, Count 2' -or
        $logText -notmatch 'TwinSkin:\s+Class TwinSkinAsset, Count 3') {
        throw "Asset Manager did not scan the expected Core assets: $LogFile"
    }
}

Assert-UnrealEditorClosed
if (-not (Test-Path -LiteralPath $ProjectPath -PathType Leaf)) {
    throw "UE project file does not exist: $ProjectPath"
}
$resolvedProject = (Resolve-Path -LiteralPath $ProjectPath).Path
$projectRoot = Split-Path -Parent $resolvedProject
$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
$masterPlugin = Join-Path $repoRoot "ue_project\Plugins\OntoTwinCharacterPack_Core"
$editorCmd = Join-Path $EngineRoot "Engine\Binaries\Win64\UnrealEditor-Cmd.exe"
$buildPython = Join-Path $PSScriptRoot "ue_build_ontotwin_character_pack_core.py"
$verifyPython = Join-Path $PSScriptRoot "ue_verify_ontotwin_character_pack_core.py"

foreach ($requiredFile in @($editorCmd, $buildPython, $verifyPython)) {
    if (-not (Test-Path -LiteralPath $requiredFile -PathType Leaf)) {
        throw "Build dependency does not exist: $requiredFile"
    }
}
& (Join-Path $PSScriptRoot "install_ontotwin_character_pack_core.ps1") `
    -ProjectPath $resolvedProject `
    -SourcePluginPath $masterPlugin `
    -AllowEmptyContent `
    -UseExistingHostContent | Out-Host

$targetPlugin = Join-Path $projectRoot "Plugins\OntoTwinCharacterPack_Core"
$builderBackupRoot = Join-Path $projectRoot ("Saved\OntoTwinCharacterPack_Core\Builder_" + (Get-Date -Format "yyyyMMdd_HHmmss"))
New-Item -ItemType Directory -Path $builderBackupRoot -Force | Out-Null
$uProjectAfterInstall = Join-Path $builderBackupRoot (Split-Path $resolvedProject -Leaf)
Copy-Item -LiteralPath $resolvedProject -Destination $uProjectAfterInstall

$buildLog = Join-Path $builderBackupRoot "build.log"
$verifyLog = Join-Path $builderBackupRoot "verify.log"
$buildSucceeded = $false

try {
    Enable-EditorPlugin $resolvedProject "PythonScriptPlugin"
    Enable-EditorPlugin $resolvedProject "EditorScriptingUtilities"

    Invoke-UnrealPython $editorCmd $resolvedProject $buildPython $buildLog
    Assert-UnrealLogSuccess $buildLog "ONTOTWIN_CORE_BUILD_BEGIN" "ONTOTWIN_CORE_BUILD_END"

    $expectedTargetAssets = @(
        "Content\Characters\ObserverBase.uasset",
        "Content\Characters\MannyRobot.uasset",
        "Content\Skins\ObserverGray.uasset",
        "Content\Skins\ObserverGreen.uasset",
        "Content\Skins\MannyRobotDefault.uasset"
    )
    foreach ($relativeAsset in $expectedTargetAssets) {
        $targetAsset = Join-Path $targetPlugin $relativeAsset
        if (-not (Test-Path -LiteralPath $targetAsset -PathType Leaf)) {
            throw "The Core build did not produce the expected asset: $targetAsset"
        }
    }

    $targetContent = Join-Path $targetPlugin "Content"
    $masterContent = Join-Path $masterPlugin "Content"
    New-Item -ItemType Directory -Path $masterContent -Force | Out-Null
    Get-ChildItem -LiteralPath $targetContent -Force | ForEach-Object {
        Copy-Item -LiteralPath $_.FullName -Destination $masterContent -Recurse -Force
    }

    Invoke-UnrealPython $editorCmd $resolvedProject $verifyPython $verifyLog
    Assert-UnrealLogSuccess $verifyLog "ONTOTWIN_CORE_VERIFY_BEGIN" "ONTOTWIN_CORE_VERIFY_END"
    Assert-AssetManagerSummary $verifyLog
    $buildSucceeded = $true
}
finally {
    Copy-Item -LiteralPath $uProjectAfterInstall -Destination $resolvedProject -Force
}

if (-not $buildSucceeded) {
    throw "OntoTwinCharacterPack_Core build did not complete"
}

$masterFiles = Get-ChildItem -LiteralPath (Join-Path $masterPlugin "Content") -Recurse -File
$masterHostFiles = Get-ChildItem -LiteralPath (Join-Path $masterPlugin "HostContent") -Recurse -File
$targetFiles = Get-ChildItem -LiteralPath (Join-Path $targetPlugin "Content") -Recurse -File
[pscustomobject][ordered]@{
    success = $true
    project = $resolvedProject
    master_plugin = $masterPlugin
    installed_plugin = $targetPlugin
    master_content_files = $masterFiles.Count
    master_content_bytes = ($masterFiles | Measure-Object -Property Length -Sum).Sum
    master_host_content_files = $masterHostFiles.Count
    master_host_content_bytes = ($masterHostFiles | Measure-Object -Property Length -Sum).Sum
    installed_content_files = $targetFiles.Count
    build_log = $buildLog
    verify_log = $verifyLog
} | ConvertTo-Json -Depth 8
