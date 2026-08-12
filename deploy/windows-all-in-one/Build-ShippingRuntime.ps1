[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectPath,

    [Parameter(Mandatory = $true)]
    [string]$EngineRoot,

    [Parameter(Mandatory = $true)]
    [string]$ArchiveDirectory,

    [string]$TargetName = "ZHHZ",
    [switch]$SkipBuild
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$project = [System.IO.Path]::GetFullPath($ProjectPath)
$engine = [System.IO.Path]::GetFullPath($EngineRoot)
$archive = [System.IO.Path]::GetFullPath($ArchiveDirectory)
$uat = Join-Path $engine "Engine\Build\BatchFiles\RunUAT.bat"
$projectName = [System.IO.Path]::GetFileNameWithoutExtension($project)
$projectRoot = [System.IO.Path]::GetDirectoryName($project)
$dynamicGeometryRelativePath = "Content\AVIC_Show\Art\A03_ParkLevel\AVIC_0706\Geometries"
$dynamicGeometryCookPath = "/Game/AVIC_Show/Art/A03_ParkLevel/AVIC_0706/Geometries"
$dynamicGeometrySource = Join-Path $projectRoot $dynamicGeometryRelativePath
$packagingConfig = Join-Path $projectRoot "Config\DefaultGame.ini"
$engineConfig = Join-Path $projectRoot "Config\DefaultEngine.ini"
$sceneManagerSource = Join-Path $projectRoot "Plugins\OntoTwinSync\Source\OntoTwinSync\Private\TwinSceneManager.cpp"

if (-not (Test-Path -LiteralPath $project -PathType Leaf)) {
    throw "Unreal project was not found: $project"
}
if ($projectName -ne $TargetName) {
    throw "Unreal project identity mismatch: project '$projectName' cannot be packaged as target '$TargetName'. Select the intended .uproject instead of renaming its executable."
}
if (-not (Test-Path -LiteralPath $uat -PathType Leaf)) {
    throw "RunUAT.bat was not found: $uat"
}
if (-not (Test-Path -LiteralPath $dynamicGeometrySource -PathType Container)) {
    throw "Dynamic geometry source directory was not found: $dynamicGeometrySource"
}
if (-not (Test-Path -LiteralPath $packagingConfig -PathType Leaf)) {
    throw "Project packaging configuration was not found: $packagingConfig"
}
if (-not (Test-Path -LiteralPath $engineConfig -PathType Leaf)) {
    throw "Project engine configuration was not found: $engineConfig"
}
if (-not (Test-Path -LiteralPath $sceneManagerSource -PathType Leaf)) {
    throw "OntoTwin scene manager source was not found: $sceneManagerSource"
}
$packagingConfigText = Get-Content -LiteralPath $packagingConfig -Raw
$requiredCookSetting = "+DirectoriesToAlwaysCook=(Path=`"$dynamicGeometryCookPath`")"
if (-not $packagingConfigText.Contains($requiredCookSetting)) {
    throw "Dynamic geometry cook rule is missing from ${packagingConfig}: $requiredCookSetting"
}
$engineConfigText = Get-Content -LiteralPath $engineConfig -Raw
foreach ($requiredHttpSetting in @(
    '[HTTP]',
    'HttpConnectionTimeout=120.0',
    'HttpActivityTimeout=180.0',
    'HttpTotalTimeout=300.0'
)) {
    if (-not $engineConfigText.Contains($requiredHttpSetting)) {
        throw "Shipping HTTP readiness setting is missing from ${engineConfig}: $requiredHttpSetting"
    }
}
$sceneManagerText = Get-Content -LiteralPath $sceneManagerSource -Raw
foreach ($requiredRequestTimeout in @(
    'HttpRequest->SetTimeout(300.0f);',
    'HttpRequest->SetActivityTimeout(180.0f);'
)) {
    if (-not $sceneManagerText.Contains($requiredRequestTimeout)) {
        throw "Snapshot request timeout gate is missing from ${sceneManagerSource}: $requiredRequestTimeout"
    }
}
if (Test-Path -LiteralPath $archive) {
    if (@(Get-ChildItem -LiteralPath $archive -Force).Count -gt 0) {
        throw "ArchiveDirectory must be empty: $archive"
    }
} else {
    New-Item -ItemType Directory -Path $archive | Out-Null
}

$arguments = @(
    "BuildCookRun",
    "-project=$project",
    "-target=$TargetName",
    "-noP4",
    "-platform=Win64",
    "-clientconfig=Shipping",
    "-cook",
    "-stage",
    "-pak",
    "-iostore",
    "-prereqs",
    "-archive",
    "-archivedirectory=$archive",
    "-unattended",
    "-utf8output"
)
if (-not $SkipBuild) {
    $arguments += "-build"
}

Write-Host "Building $TargetName Win64 Shipping..."
$uatLog = Join-Path $archive "$TargetName-UAT-build.log"
& $uat @arguments 2>&1 | Tee-Object -FilePath $uatLog
if ($LASTEXITCODE -ne 0) {
    throw "Unreal BuildCookRun failed with exit code $LASTEXITCODE"
}

$runtime = Join-Path $archive "Windows"
$executable = Join-Path $runtime "$TargetName.exe"
if (-not (Test-Path -LiteralPath $executable -PathType Leaf)) {
    throw "Shipping runtime did not contain $TargetName.exe: $runtime"
}
$projectRuntime = Join-Path $runtime $projectName
if (-not (Test-Path -LiteralPath $projectRuntime -PathType Container)) {
    throw "Shipping runtime identity directory is missing: $projectRuntime"
}
$shippingExecutable = Join-Path $projectRuntime "Binaries\Win64\$TargetName-Win64-Shipping.exe"
if (-not (Test-Path -LiteralPath $shippingExecutable -PathType Leaf)) {
    throw "Shipping runtime did not contain the real UE executable: $shippingExecutable"
}
$ufsManifest = Join-Path $runtime "Manifest_UFSFiles_Win64.txt"
if (-not (Test-Path -LiteralPath $ufsManifest -PathType Leaf)) {
    throw "Shipping UFS manifest is missing: $ufsManifest"
}
$packagedPaths = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
foreach ($line in [System.IO.File]::ReadLines($ufsManifest, [System.Text.UTF8Encoding]::new($false))) {
    $manifestPath = ($line -split "`t", 2)[0].Replace('\', '/')
    if (-not [string]::IsNullOrWhiteSpace($manifestPath)) {
        [void]$packagedPaths.Add($manifestPath)
    }
}
$dynamicGeometryAssets = @(
    Get-ChildItem -LiteralPath $dynamicGeometrySource -Recurse -File -Filter "*.uasset" |
        Sort-Object FullName
)
if ($dynamicGeometryAssets.Count -eq 0) {
    throw "Dynamic geometry source directory did not contain any .uasset files: $dynamicGeometrySource"
}
$missingDynamicGeometry = @(
    foreach ($asset in $dynamicGeometryAssets) {
        $relativePath = $asset.FullName.Substring($projectRoot.Length + 1).Replace('\', '/')
        $expectedManifestPath = "$projectName/$relativePath"
        if (-not $packagedPaths.Contains($expectedManifestPath)) {
            $expectedManifestPath
        }
    }
)
$cookAudit = [ordered]@{
    schema_version = 1
    source_directory = $dynamicGeometrySource
    cook_path = $dynamicGeometryCookPath
    required_uasset_count = $dynamicGeometryAssets.Count
    packaged_uasset_count = $dynamicGeometryAssets.Count - $missingDynamicGeometry.Count
    missing_uasset_count = $missingDynamicGeometry.Count
    missing_paths = $missingDynamicGeometry
    generated_at = (Get-Date).ToString("o")
}
[System.IO.File]::WriteAllText(
    (Join-Path $runtime "ontotwin-cook-audit.json"),
    ($cookAudit | ConvertTo-Json -Depth 4),
    [System.Text.UTF8Encoding]::new($false))
if ($missingDynamicGeometry.Count -gt 0) {
    $sample = ($missingDynamicGeometry | Select-Object -First 20) -join "`n"
    throw "Shipping dynamic geometry cook audit failed: $($missingDynamicGeometry.Count) of $($dynamicGeometryAssets.Count) required .uasset files are missing from the UFS manifest. First missing paths:`n$sample"
}
Write-Host "Dynamic geometry cook audit passed: $($dynamicGeometryAssets.Count)/$($dynamicGeometryAssets.Count) assets packaged." -ForegroundColor Green
$sourceMaps = @(
    Get-ChildItem -LiteralPath (Join-Path ([System.IO.Path]::GetDirectoryName($project)) "Content") `
        -Recurse -File -Filter "*.umap" | Sort-Object FullName | ForEach-Object {
        [ordered]@{
            path = $_.FullName.Substring([System.IO.Path]::GetDirectoryName($project).Length + 1).Replace('\', '/')
            bytes = $_.Length
            sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        }
    }
)
$sourceBuildInputFiles = @(
    Get-Item -LiteralPath $project
    if (Test-Path -LiteralPath (Join-Path $projectRoot "Config") -PathType Container) {
        Get-ChildItem -LiteralPath (Join-Path $projectRoot "Config") -Recurse -File -Filter "*.ini"
    }
    if (Test-Path -LiteralPath (Join-Path $projectRoot "Source") -PathType Container) {
        Get-ChildItem -LiteralPath (Join-Path $projectRoot "Source") -Recurse -File |
            Where-Object { $_.Extension -in @(".h", ".cpp", ".cs") }
    }
    $ontoTwinPluginRoot = Join-Path $projectRoot "Plugins\OntoTwinSync"
    if (Test-Path -LiteralPath $ontoTwinPluginRoot -PathType Container) {
        Get-ChildItem -LiteralPath $ontoTwinPluginRoot -Recurse -File |
            Where-Object {
                $_.Extension -in @(".h", ".cpp", ".cs", ".uplugin") -and
                $_.FullName -notmatch '(?i)[\\/](Binaries|Intermediate|Saved)[\\/]'
            }
    }
)
$sourceBuildInputs = @(
    $sourceBuildInputFiles | Sort-Object FullName -Unique | ForEach-Object {
        [ordered]@{
            path = $_.FullName.Substring($projectRoot.Length + 1).Replace('\', '/')
            bytes = $_.Length
            sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        }
    }
)
if ($sourceBuildInputs.Count -eq 0) {
    throw "No source/config/plugin build inputs were captured for Shipping provenance."
}
$cookedArtifacts = @(
    foreach ($name in @(
        "$TargetName.exe",
        "Manifest_UFSFiles_Win64.txt",
        "Manifest_NonUFSFiles_Win64.txt"
    )) {
        $path = Join-Path $runtime $name
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
            throw "Shipping provenance input is missing: $path"
        }
        [ordered]@{
            path = $name
            bytes = (Get-Item -LiteralPath $path).Length
            sha256 = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
        }
    }
)
$runtimeIdentity = [ordered]@{
    schema_version = 3
    project_name = $projectName
    target_name = $TargetName
    source_project_path = $project
    source_project_sha256 = (Get-FileHash -LiteralPath $project -Algorithm SHA256).Hash.ToLowerInvariant()
    source_build_inputs = $sourceBuildInputs
    source_maps = $sourceMaps
    cooked_artifacts = $cookedArtifacts
    uat_log_path = $uatLog
    uat_log_sha256 = (Get-FileHash -LiteralPath $uatLog -Algorithm SHA256).Hash.ToLowerInvariant()
    generated_at = (Get-Date).ToString("o")
}
[System.IO.File]::WriteAllText(
    (Join-Path $runtime "ontotwin-runtime-manifest.json"),
    ($runtimeIdentity | ConvertTo-Json -Depth 8),
    [System.Text.UTF8Encoding]::new($false))

Write-Host "Shipping runtime created: $runtime" -ForegroundColor Green
