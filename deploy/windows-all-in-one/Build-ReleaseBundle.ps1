[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$RuntimeDirectory,

    [Parameter(Mandatory = $true)]
    [string]$ModelsDirectory,

    [Parameter(Mandatory = $true)]
    [string]$OutputDirectory,

    [string]$ReleaseVersion = "3.7.1-r1",
    [string]$ProjectId = "ds_1784694647848",
    [switch]$SkipDockerImages,
    [switch]$SkipLauncher
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repositoryRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot "..\.."))
$runtimeRoot = [System.IO.Path]::GetFullPath($RuntimeDirectory)
$modelsRoot = [System.IO.Path]::GetFullPath($ModelsDirectory)
$outputRoot = [System.IO.Path]::GetFullPath($OutputDirectory)

if (-not (Test-Path -LiteralPath (Join-Path $runtimeRoot "ZHHZ.exe") -PathType Leaf)) {
    throw "ZHHZ.exe was not found in RuntimeDirectory: $runtimeRoot"
}
$runtimeIdentityPath = Join-Path $runtimeRoot "ontotwin-runtime-manifest.json"
if (-not (Test-Path -LiteralPath $runtimeIdentityPath -PathType Leaf)) {
    throw "Runtime identity manifest was not found: $runtimeIdentityPath"
}
$runtimeIdentity = Get-Content -Raw -LiteralPath $runtimeIdentityPath | ConvertFrom-Json
if ($runtimeIdentity.project_name -ne "ZHHZ" -or $runtimeIdentity.target_name -ne "ZHHZ") {
    throw "Runtime identity mismatch: project='$($runtimeIdentity.project_name)', target='$($runtimeIdentity.target_name)'."
}
if (-not (Test-Path -LiteralPath (Join-Path $runtimeRoot "ZHHZ") -PathType Container)) {
    throw "The packaged runtime does not contain the ZHHZ project directory."
}
if (Test-Path -LiteralPath (Join-Path $runtimeRoot "test0316")) {
    throw "The packaged runtime contains the forbidden test0316 project directory."
}
$ufsManifestPath = Join-Path $runtimeRoot "Manifest_UFSFiles_Win64.txt"
$nonUfsManifestPath = Join-Path $runtimeRoot "Manifest_NonUFSFiles_Win64.txt"
if (-not (Test-Path -LiteralPath $ufsManifestPath -PathType Leaf)) {
    throw "Shipping UFS manifest was not found: $ufsManifestPath"
}
$ufsManifest = Get-Content -Raw -LiteralPath $ufsManifestPath
if ($ufsManifest -notmatch "(?i)glTFRuntime[^/\\]*[/\\]Content[/\\]") {
    throw "glTFRuntime Content was not cooked into this Shipping build. Rebuild ZHHZ after adding /glTFRuntime to DirectoriesToAlwaysCook."
}
$runtimeManifestText = $ufsManifest
if (Test-Path -LiteralPath $nonUfsManifestPath -PathType Leaf) {
    $runtimeManifestText += [Environment]::NewLine + (Get-Content -Raw -LiteralPath $nonUfsManifestPath)
}
if ($runtimeManifestText -match "(?i)PixelStreaming") {
    throw "Pixel Streaming content is present in this Shipping build. Disable the PixelStreaming plugin and rebuild the v1 runtime."
}
if ($runtimeManifestText -match "(?i)(^|[/\\])test0316([/\\]|$)") {
    throw "The Shipping manifests contain the forbidden test0316 project identity."
}
if (@(Get-ChildItem -LiteralPath $modelsRoot -Filter "*.glb" -File -ErrorAction SilentlyContinue).Count -eq 0) {
    throw "No GLB files were found in ModelsDirectory: $modelsRoot"
}

if (Test-Path -LiteralPath $outputRoot) {
    if (@(Get-ChildItem -LiteralPath $outputRoot -Force).Count -gt 0) {
        throw "OutputDirectory must be empty: $outputRoot"
    }
} else {
    New-Item -ItemType Directory -Path $outputRoot | Out-Null
}

$paths = [ordered]@{
    Deploy = Join-Path $outputRoot "Deploy"
    Runtime = Join-Path $outputRoot "ZHHZ"
    Models = Join-Path $outputRoot "Models"
    Database = Join-Path $outputRoot "Database"
    Data = Join-Path $outputRoot "Data"
    Images = Join-Path $outputRoot "Images"
    Backups = Join-Path $outputRoot "Backups"
}
foreach ($path in $paths.Values) {
    New-Item -ItemType Directory -Path $path | Out-Null
}
New-Item -ItemType Directory -Path (Join-Path $paths.Data "project_assets") | Out-Null
New-Item -ItemType Directory -Path (Join-Path $paths.Data "exports") | Out-Null

Write-Host "Copying ZHHZ Shipping runtime..."
Copy-Item -Path (Join-Path $runtimeRoot "*") -Destination $paths.Runtime -Recurse -Force
Write-Host "Copying GLB models..."
Copy-Item -Path (Join-Path $modelsRoot "*.glb") -Destination $paths.Models -Force

Copy-Item -LiteralPath (Join-Path $PSScriptRoot "docker-compose.release.yml") -Destination $paths.Deploy
Copy-Item -LiteralPath (Join-Path $PSScriptRoot "customer.env.example") -Destination $paths.Deploy
Copy-Item -LiteralPath (Join-Path $PSScriptRoot "Start.cmd") -Destination $paths.Deploy
Copy-Item -LiteralPath (Join-Path $PSScriptRoot "Stop.cmd") -Destination $paths.Deploy
Copy-Item -LiteralPath (Join-Path $PSScriptRoot "Status.cmd") -Destination $paths.Deploy
Copy-Item -LiteralPath (Join-Path $PSScriptRoot "Preflight.cmd") -Destination $paths.Deploy
$customerScriptsDirectory = Join-Path $paths.Deploy "scripts"
New-Item -ItemType Directory -Path $customerScriptsDirectory | Out-Null
foreach ($scriptName in @(
    "Common.ps1",
    "Initialize-Release.ps1",
    "Start-OntoTwinZHHZ.ps1",
    "Stop-OntoTwinZHHZ.ps1",
    "Get-OntoTwinZHHZStatus.ps1",
    "Backup-OntoTwinZHHZ.ps1",
    "Restore-OntoTwinZHHZ.ps1",
    "Test-DeploymentEnvironment.ps1",
    "Test-ReleaseIntegrity.ps1"
)) {
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot "scripts\$scriptName") -Destination $customerScriptsDirectory
}
Copy-Item -LiteralPath (Join-Path $PSScriptRoot "CUSTOMER-README.md") -Destination (Join-Path $outputRoot "Deployment-Guide.md")

if (-not $SkipLauncher) {
    $launcherOutput = Join-Path $paths.Deploy "Launcher"
    & (Join-Path $PSScriptRoot "Publish-Launcher.ps1") -OutputDirectory $launcherOutput
}

$postgresSeedDir = Join-Path $paths.Database "postgres"
New-Item -ItemType Directory -Path $postgresSeedDir | Out-Null
Copy-Item -LiteralPath (Join-Path $PSScriptRoot "database\postgres\01-restore.sh") -Destination $postgresSeedDir

$exportScript = Join-Path $PSScriptRoot "scripts\Export-ZHHZReleaseData.ps1"
& $exportScript -OutputDirectory $paths.Database -ProjectId $ProjectId

$exportedAssets = Join-Path $paths.Database "project_assets\$ProjectId"
if (Test-Path -LiteralPath $exportedAssets -PathType Container) {
    Copy-Item -LiteralPath $exportedAssets -Destination (Join-Path $paths.Data "project_assets") -Recurse -Force
}

$dataManifest = Get-Content -Raw -LiteralPath (Join-Path $paths.Database "data-manifest.json") | ConvertFrom-Json
$dataVersion = "zhhz-" + (Get-Date -Format "yyyyMMdd-HHmmss")

if (-not $SkipDockerImages) {
    $backendImage = "ontotwin-zhhz/backend:$ReleaseVersion"
    $postgresImage = "ontotwin-zhhz/postgres:16-20260724"
    $neo4jImage = "ontotwin-zhhz/neo4j:5-20260724"

    Push-Location $repositoryRoot
    try {
        & docker build -f (Join-Path $PSScriptRoot "Dockerfile.backend") -t $backendImage .
        if ($LASTEXITCODE -ne 0) { throw "Backend release image build failed." }
        & docker tag postgres:16 $postgresImage
        if ($LASTEXITCODE -ne 0) { throw "PostgreSQL release image tag failed." }
        & docker tag neo4j:5 $neo4jImage
        if ($LASTEXITCODE -ne 0) { throw "Neo4j release image tag failed." }
    } finally {
        Pop-Location
    }

    & docker save --output (Join-Path $paths.Images "ontotwin-backend.tar") $backendImage
    if ($LASTEXITCODE -ne 0) { throw "Backend image export failed." }
    & docker save --output (Join-Path $paths.Images "postgres.tar") $postgresImage
    if ($LASTEXITCODE -ne 0) { throw "PostgreSQL image export failed." }
    & docker save --output (Join-Path $paths.Images "neo4j.tar") $neo4jImage
    if ($LASTEXITCODE -ne 0) { throw "Neo4j image export failed." }
}

$envTemplatePath = Join-Path $paths.Deploy "customer.env.example"
$envTemplate = Get-Content -Raw -LiteralPath $envTemplatePath
$envTemplate = $envTemplate.Replace("__RELEASE_VERSION__", $ReleaseVersion)
$envTemplate = $envTemplate.Replace("__DATA_VERSION__", $dataVersion)
$encoding = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($envTemplatePath, $envTemplate, $encoding)

$immutableFiles = @(
    foreach ($immutableRoot in @($paths.Deploy, $paths.Runtime, $paths.Models, $paths.Database, $paths.Images)) {
        Get-ChildItem -Recurse -File -LiteralPath $immutableRoot
    }
    Get-Item -LiteralPath (Join-Path $outputRoot "Deployment-Guide.md")
) | Sort-Object FullName -Unique

$manifestFiles = @($immutableFiles | ForEach-Object {
    $item = $_
    [ordered]@{
        path = $item.FullName.Substring($outputRoot.Length + 1).Replace('\', '/')
        bytes = $item.Length
        sha256 = (Get-FileHash -LiteralPath $item.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    }
})

$releaseManifest = [ordered]@{
    product = "OntoTwin ZHHZ"
    release_version = $ReleaseVersion
    data_version = $dataVersion
    project_id = $ProjectId
    generated_at = (Get-Date).ToString("o")
    realtime_websocket_enabled = $false
    pixel_streaming_included = $false
    artstudio_enabled_by_default = $true
    postgres_counts = $dataManifest.postgres
    files = $manifestFiles
}
[System.IO.File]::WriteAllText(
    (Join-Path $outputRoot "release-manifest.json"),
    ($releaseManifest | ConvertTo-Json -Depth 8),
    $encoding
)

Write-Host "Release bundle created: $outputRoot" -ForegroundColor Green
