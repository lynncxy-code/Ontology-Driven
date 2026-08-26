[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectPath,

    [string]$SourcePluginPath = "",

    [switch]$AllowEmptyContent,

    [switch]$UseExistingHostContent
)

$ErrorActionPreference = "Stop"
$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
$RuleBegin = "; BEGIN OntoTwinCharacterPack_Core"
$RuleEnd = "; END OntoTwinCharacterPack_Core"

function Assert-UnrealEditorClosed {
    $processes = @(Get-Process -ErrorAction SilentlyContinue | Where-Object {
        $_.ProcessName -in @("UnrealEditor", "UnrealEditor-Cmd")
    })
    if ($processes.Count -gt 0) {
        $summary = ($processes | ForEach-Object { "$($_.ProcessName) PID=$($_.Id)" }) -join ", "
        throw "Close every Unreal Editor process before installing: $summary"
    }
}

function Resolve-ExistingFile([string]$Path, [string]$Label) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "$Label does not exist: $Path"
    }
    return (Resolve-Path -LiteralPath $Path).Path
}

function Enable-UProjectPlugin([string]$Path, [string]$PluginName) {
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
        }
    }
    $project.Plugins = $plugins
    $json = $project | ConvertTo-Json -Depth 64
    [System.IO.File]::WriteAllText($Path, $json + [Environment]::NewLine, $Utf8NoBom)
}

function Get-CleanAssetManagerConfig([string]$Text) {
    $escapedBegin = [Regex]::Escape($RuleBegin)
    $escapedEnd = [Regex]::Escape($RuleEnd)
    $pattern = "(?ms)^\s*$escapedBegin\s*\r?\n.*?^\s*$escapedEnd\s*\r?\n?"
    return [Regex]::Replace($Text, $pattern, "")
}

Assert-UnrealEditorClosed
$resolvedProject = Resolve-ExistingFile $ProjectPath "UE project file"
$projectRoot = Split-Path -Parent $resolvedProject

if ([string]::IsNullOrWhiteSpace($SourcePluginPath)) {
    $repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
    $SourcePluginPath = Join-Path $repoRoot "ue_project\Plugins\OntoTwinCharacterPack_Core"
}
if (-not (Test-Path -LiteralPath $SourcePluginPath -PathType Container)) {
    throw "The master character plugin does not exist: $SourcePluginPath"
}
$resolvedSource = (Resolve-Path -LiteralPath $SourcePluginPath).Path
$sourceDescriptor = Join-Path $resolvedSource "OntoTwinCharacterPack_Core.uplugin"
Resolve-ExistingFile $sourceDescriptor "Character plugin descriptor" | Out-Null

if (-not $AllowEmptyContent) {
    $requiredAssets = @(
        "Content\Characters\ObserverBase.uasset",
        "Content\Characters\MannyRobot.uasset",
        "Content\Skins\ObserverGray.uasset",
        "Content\Skins\ObserverGreen.uasset",
        "Content\Skins\MannyRobotDefault.uasset",
        "HostContent\Content\Characters\Mannequins\Meshes\SKM_Manny_Simple.uasset",
        "HostContent\Content\Art\A08_Characters\00_Ground_Staff\ThirdPerson\SkeletonIK\SK_Charactor.uasset",
        "HostContent\Content\Art\A08_Characters\00_Ground_Staff\ThirdPerson\SkeletonIK\myAnimBlueprint.uasset"
    )
    foreach ($relativeAsset in $requiredAssets) {
        Resolve-ExistingFile (Join-Path $resolvedSource $relativeAsset) "Core character asset" | Out-Null
    }
}

$ontoTwinSyncDescriptor = Join-Path $projectRoot "Plugins\OntoTwinSync\OntoTwinSync.uplugin"
Resolve-ExistingFile $ontoTwinSyncDescriptor "Host OntoTwinSync plugin" | Out-Null

$defaultGame = Join-Path $projectRoot "Config\DefaultGame.ini"
$currentConfig = if (Test-Path -LiteralPath $defaultGame) {
    Get-Content -LiteralPath $defaultGame -Raw -Encoding UTF8
}
else {
    ""
}
$cleanConfig = Get-CleanAssetManagerConfig $currentConfig
if ($cleanConfig -match 'PrimaryAssetType\s*=\s*"TwinCharacter"' -or
    $cleanConfig -match 'PrimaryAssetType\s*=\s*"TwinSkin"') {
    throw "DefaultGame.ini already contains TwinCharacter/TwinSkin scan rules. Merge each type into one rule that includes /OntoTwinCharacterPack_Core before installing."
}

$payloadContent = Join-Path $resolvedSource "HostContent\Content"
$projectContent = Join-Path $projectRoot "Content"
$payloadFiles = @()
$hostContentConflicts = @()
if (Test-Path -LiteralPath $payloadContent -PathType Container) {
    $payloadFiles = @(Get-ChildItem -LiteralPath $payloadContent -Recurse -File)
    foreach ($payloadFile in $payloadFiles) {
        $relativePath = $payloadFile.FullName.Substring($payloadContent.Length).TrimStart('\')
        $targetFile = Join-Path $projectContent $relativePath
        if (Test-Path -LiteralPath $targetFile -PathType Leaf) {
            $sourceHash = (Get-FileHash -LiteralPath $payloadFile.FullName -Algorithm SHA256).Hash
            $targetHash = (Get-FileHash -LiteralPath $targetFile -Algorithm SHA256).Hash
            if ($sourceHash -ne $targetHash) {
                if (-not $UseExistingHostContent) {
                    throw "Host content conflict; refusing to overwrite: $targetFile"
                }
                $hostContentConflicts += $targetFile
            }
        }
    }
}

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupRoot = Join-Path $projectRoot "Saved\OntoTwinCharacterPack_Core\InstallBackups\$timestamp"
New-Item -ItemType Directory -Path $backupRoot -Force | Out-Null
Copy-Item -LiteralPath $resolvedProject -Destination (Join-Path $backupRoot (Split-Path $resolvedProject -Leaf))
if (Test-Path -LiteralPath $defaultGame) {
    Copy-Item -LiteralPath $defaultGame -Destination (Join-Path $backupRoot "DefaultGame.ini")
}

$targetPlugin = Join-Path $projectRoot "Plugins\OntoTwinCharacterPack_Core"
New-Item -ItemType Directory -Path $targetPlugin -Force | Out-Null
Get-ChildItem -LiteralPath $resolvedSource -Force | Where-Object {
    $_.Name -ne "HostContent"
} | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination $targetPlugin -Recurse -Force
}

if (Test-Path -LiteralPath $payloadContent -PathType Container) {
    New-Item -ItemType Directory -Path $projectContent -Force | Out-Null
    foreach ($payloadFile in $payloadFiles) {
        $relativePath = $payloadFile.FullName.Substring($payloadContent.Length).TrimStart('\')
        $targetFile = Join-Path $projectContent $relativePath
        if (Test-Path -LiteralPath $targetFile -PathType Leaf) {
            continue
        }
        New-Item -ItemType Directory -Path (Split-Path -Parent $targetFile) -Force | Out-Null
        Copy-Item -LiteralPath $payloadFile.FullName -Destination $targetFile
    }
}

Enable-UProjectPlugin $resolvedProject "OntoTwinCharacterPack_Core"

$rules = @"
$RuleBegin
[/Script/Engine.AssetManagerSettings]
+PrimaryAssetTypesToScan=(PrimaryAssetType="TwinCharacter",AssetBaseClass=/Script/OntoTwinSync.TwinCharacterAsset,bHasBlueprintClasses=False,bIsEditorOnly=False,Directories=((Path="/OntoTwinCharacterPack_Core/Characters")),Rules=(Priority=0,ChunkId=-1,bApplyRecursively=True,CookRule=AlwaysCook))
+PrimaryAssetTypesToScan=(PrimaryAssetType="TwinSkin",AssetBaseClass=/Script/OntoTwinSync.TwinSkinAsset,bHasBlueprintClasses=False,bIsEditorOnly=False,Directories=((Path="/OntoTwinCharacterPack_Core/Skins")),Rules=(Priority=0,ChunkId=-1,bApplyRecursively=True,CookRule=AlwaysCook))
$RuleEnd
"@
$newConfig = $cleanConfig.TrimEnd() + [Environment]::NewLine + [Environment]::NewLine + $rules.Trim() + [Environment]::NewLine
$configDirectory = Split-Path -Parent $defaultGame
New-Item -ItemType Directory -Path $configDirectory -Force | Out-Null
[System.IO.File]::WriteAllText($defaultGame, $newConfig, $Utf8NoBom)

[pscustomobject][ordered]@{
    success = $true
    project = $resolvedProject
    source_plugin = $resolvedSource
    installed_plugin = $targetPlugin
    asset_manager_config = $defaultGame
    backup = $backupRoot
    content_required = -not $AllowEmptyContent
    host_payload = if (Test-Path -LiteralPath $payloadContent) { $payloadContent } else { $null }
    existing_host_content_kept = [bool]$UseExistingHostContent
    host_content_conflicts_kept = $hostContentConflicts.Count
} | ConvertTo-Json -Depth 8
