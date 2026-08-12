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
    [switch]$ResetBackendBaselineOnUpgrade,
    [switch]$SkipDockerImages,
    [switch]$SkipLauncher
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-ReleaseDescriptor {
    param([Parameter(Mandatory = $true)][string]$Version)

    if ($Version -cnotmatch '^(?<product>\d+\.\d+\.\d+)-r(?<release>\d+)-rc(?<candidateMajor>\d+)(?:\.(?<candidateMinor>\d+))?$') {
        throw "Release version is not canonical: $Version"
    }
    $productVersion = $Matches.product
    $candidateMajor = [int]$Matches.candidateMajor
    $candidateMinor = if ($Matches.ContainsKey('candidateMinor') -and
        -not [string]::IsNullOrWhiteSpace([string]$Matches['candidateMinor'])) {
        [int]$Matches.candidateMinor
    } else {
        0
    }
    if ($candidateMinor -gt 99) { throw "The RC minor revision must be between 0 and 99: $Version" }
    $numericRevision = ($candidateMajor * 100) + $candidateMinor
    if ($numericRevision -gt 65535) { throw "The RC revision is too large for a Windows binary version: $Version" }
    $msiParts = $productVersion.Split('.')
    return [pscustomobject]@{
        BinaryVersion = "$productVersion.$numericRevision"
        BundleVersion = "$productVersion.$numericRevision"
        MsiVersion = "$($msiParts[0]).$($msiParts[1]).$numericRevision"
    }
}

function Set-EnvironmentValue {
    param(
        [Parameter(Mandatory = $true)][string]$Content,
        [Parameter(Mandatory = $true)][string]$Key,
        [Parameter(Mandatory = $true)][string]$Value
    )

    $pattern = '(?m)^' + [regex]::Escape($Key) + '=.*$'
    $matches = [regex]::Matches($Content, $pattern)
    if ($matches.Count -ne 1) { throw "Expected exactly one $Key entry in customer.env.example; found $($matches.Count)." }
    return [regex]::Replace($Content, $pattern, "$Key=$Value", 1)
}

function Test-PostgresReleaseSeed {
    param(
        [Parameter(Mandatory = $true)][string]$SeedDirectory,
        [Parameter(Mandatory = $true)][string]$PostgresImage,
        [Parameter(Mandatory = $true)][object]$ExpectedCounts,
        [Parameter(Mandatory = $true)][string]$ExpectedProjectId
    )

    $restoreScript = Join-Path $SeedDirectory "01-restore.sh"
    $dumpFile = Join-Path $SeedDirectory "zhhz.dump"
    if (-not (Test-Path -LiteralPath $restoreScript -PathType Leaf) -or
        -not (Test-Path -LiteralPath $dumpFile -PathType Leaf)) {
        throw "PostgreSQL release seed is incomplete: $SeedDirectory"
    }

    $restoreBytes = [System.IO.File]::ReadAllBytes($restoreScript)
    if ($restoreBytes -contains 13) {
        throw "PostgreSQL restore script contains CR characters; Linux requires LF line endings: $restoreScript"
    }

    $containerName = "ontotwin-zhhz-seed-test-" + [Guid]::NewGuid().ToString("N").Substring(0, 12)
    $password = "Seed" + [Guid]::NewGuid().ToString("N")
    $expectedRow = @(
        [int]$ExpectedCounts.projects,
        [int]$ExpectedCounts.object_types,
        [int]$ExpectedCounts.instances,
        [int]$ExpectedCounts.zones,
        $ExpectedProjectId
    ) -join ","
    $query = @"
SELECT
  (SELECT count(*) FROM project),
  (SELECT count(*) FROM object_type WHERE deleted_at IS NULL),
  (SELECT count(*) FROM instance WHERE deleted_at IS NULL),
  (SELECT count(*) FROM zone WHERE deleted_at IS NULL),
  COALESCE((SELECT v FROM app_singleton WHERE k='active_project_id'), '');
"@

    Write-Host "Smoke-testing the packaged PostgreSQL seed in a disposable container..."
    $containerOutput = & docker run -d --name $containerName `
        -e "POSTGRES_USER=ontotwin" `
        -e "POSTGRES_PASSWORD=$password" `
        -e "POSTGRES_DB=ontotwin" `
        -v "${SeedDirectory}:/release-seed:ro" `
        -v "${restoreScript}:/docker-entrypoint-initdb.d/01-restore.sh:ro" `
        $PostgresImage 2>&1
    $runExitCode = $LASTEXITCODE
    if ($runExitCode -ne 0) {
        throw "Could not start the PostgreSQL seed smoke test: $($containerOutput -join [Environment]::NewLine)"
    }

    try {
        $deadline = (Get-Date).AddMinutes(3)
        $lastResult = ""
        do {
            $running = (& docker inspect --format "{{.State.Running}}" $containerName 2>$null) -join ""
            if ($LASTEXITCODE -ne 0 -or $running.Trim() -ne "true") {
                $logs = (& docker logs $containerName 2>&1) -join [Environment]::NewLine
                throw "PostgreSQL seed initialization stopped before validation. Logs:`n$logs"
            }

            $previousErrorActionPreference = $ErrorActionPreference
            $ErrorActionPreference = "Continue"
            try {
                $queryOutput = & docker exec $containerName psql -U ontotwin -d ontotwin -At -F "," -c $query 2>$null
                $queryExitCode = $LASTEXITCODE
            } finally {
                $ErrorActionPreference = $previousErrorActionPreference
            }
            if ($queryExitCode -eq 0) {
                $lastResult = (($queryOutput | ForEach-Object { [string]$_ }) -join "").Trim()
                if ($lastResult -eq $expectedRow) {
                    Write-Host "PostgreSQL seed smoke test passed: $lastResult"
                    return
                }
            }
            Start-Sleep -Seconds 2
        } while ((Get-Date) -lt $deadline)

        $logs = (& docker logs $containerName 2>&1) -join [Environment]::NewLine
        throw "PostgreSQL seed did not restore the expected data. Expected='$expectedRow'; Actual='$lastResult'. Logs:`n$logs"
    } finally {
        & docker rm -f $containerName *> $null
    }
}

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
if ([string]$runtimeIdentity.source_project_path -notmatch '(?i)(^|[/\\])ZHHZ\.uproject$' -or
    [string]$runtimeIdentity.source_project_sha256 -cnotmatch '^[0-9a-f]{64}$' -or
    [int]$runtimeIdentity.schema_version -lt 3 -or
    @($runtimeIdentity.source_build_inputs).Count -eq 0 -or
    @($runtimeIdentity.source_maps).Count -eq 0) {
    throw "Runtime identity does not contain fresh ZHHZ source evidence."
}
$sourceProjectPath = [System.IO.Path]::GetFullPath([string]$runtimeIdentity.source_project_path)
$sourceProjectRoot = [System.IO.Path]::GetDirectoryName($sourceProjectPath)
$sourceProjectPrefix = $sourceProjectRoot.TrimEnd('\') + '\'
if (-not (Test-Path -LiteralPath $sourceProjectPath -PathType Leaf) -or
    (Get-FileHash -LiteralPath $sourceProjectPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne [string]$runtimeIdentity.source_project_sha256) {
    throw "The Shipping runtime was not built from the current ZHHZ.uproject. Run a fresh Cook."
}
foreach ($inputEntry in @($runtimeIdentity.source_build_inputs)) {
    $relativeInput = [string]$inputEntry.path
    if ([string]::IsNullOrWhiteSpace($relativeInput) -or [System.IO.Path]::IsPathRooted($relativeInput)) {
        throw "Unsafe source build input path in runtime manifest: $relativeInput"
    }
    $currentInput = [System.IO.Path]::GetFullPath((Join-Path $sourceProjectRoot $relativeInput.Replace('/', '\')))
    if (-not $currentInput.StartsWith($sourceProjectPrefix, [System.StringComparison]::OrdinalIgnoreCase) -or
        -not (Test-Path -LiteralPath $currentInput -PathType Leaf) -or
        (Get-Item -LiteralPath $currentInput).Length -ne [long]$inputEntry.bytes -or
        (Get-FileHash -LiteralPath $currentInput -Algorithm SHA256).Hash.ToLowerInvariant() -ne [string]$inputEntry.sha256) {
        throw "A source/config/plugin build input changed after Cook and must be recooked: $relativeInput"
    }
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
$restoreScriptSource = Join-Path $PSScriptRoot "database\postgres\01-restore.sh"
$restoreScriptDestination = Join-Path $postgresSeedDir "01-restore.sh"
$restoreScriptContent = [System.IO.File]::ReadAllText($restoreScriptSource)
$restoreScriptContent = $restoreScriptContent.Replace("`r`n", "`n").Replace("`r", "`n")
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($restoreScriptDestination, $restoreScriptContent, $utf8NoBom)
if ([System.IO.File]::ReadAllBytes($restoreScriptDestination) -contains 13) {
    throw "PostgreSQL restore script normalization failed: $restoreScriptDestination"
}

$exportScript = Join-Path $PSScriptRoot "scripts\Export-ZHHZReleaseData.ps1"
& $exportScript -OutputDirectory $paths.Database -ProjectId $ProjectId

$exportedAssets = Join-Path $paths.Database "project_assets\$ProjectId"
if (Test-Path -LiteralPath $exportedAssets -PathType Container) {
    Copy-Item -LiteralPath $exportedAssets -Destination (Join-Path $paths.Data "project_assets") -Recurse -Force
}

$dataManifest = Get-Content -Raw -LiteralPath (Join-Path $paths.Database "data-manifest.json") | ConvertFrom-Json
$dataVersion = "zhhz-" + (Get-Date -Format "yyyyMMdd-HHmmss")
$releaseDescriptor = Get-ReleaseDescriptor -Version $ReleaseVersion
$backendImage = "ontotwin-zhhz/backend:$ReleaseVersion"
$postgresImage = "ontotwin-zhhz/postgres:16-20260724"
$neo4jImage = "ontotwin-zhhz/neo4j:5-20260724"

Test-PostgresReleaseSeed `
    -SeedDirectory $postgresSeedDir `
    -PostgresImage $postgresImage `
    -ExpectedCounts $dataManifest.postgres `
    -ExpectedProjectId $ProjectId

if (-not $SkipDockerImages) {
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
$envTemplate = Set-EnvironmentValue -Content $envTemplate -Key "BACKEND_IMAGE" -Value $backendImage
$envTemplate = Set-EnvironmentValue -Content $envTemplate -Key "POSTGRES_IMAGE" -Value $postgresImage
$envTemplate = Set-EnvironmentValue -Content $envTemplate -Key "NEO4J_IMAGE" -Value $neo4jImage
$envTemplate = Set-EnvironmentValue -Content $envTemplate -Key "ONTOTWIN_RELEASE_VERSION" -Value $ReleaseVersion
$envTemplate = Set-EnvironmentValue -Content $envTemplate -Key "ONTOTWIN_DATA_VERSION" -Value $dataVersion
$encoding = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($envTemplatePath, $envTemplate, $encoding)

$runtimePackagePaths = @(
    "ZHHZ.exe",
    "ZHHZ\Binaries\Win64\ZHHZ-Win64-Shipping.exe",
    "ZHHZ\Content\Paks\ZHHZ-Windows.pak",
    "ZHHZ\Content\Paks\ZHHZ-Windows.ucas",
    "ZHHZ\Content\Paks\ZHHZ-Windows.utoc"
)
$runtimePackageHashes = @($runtimePackagePaths | ForEach-Object {
    $packagePath = Join-Path $paths.Runtime $_
    if (-not (Test-Path -LiteralPath $packagePath -PathType Leaf)) { throw "Required runtime package is missing: $packagePath" }
    [ordered]@{
        path = $_.Replace('\', '/')
        bytes = (Get-Item -LiteralPath $packagePath).Length
        sha256 = (Get-FileHash -LiteralPath $packagePath -Algorithm SHA256).Hash.ToLowerInvariant()
    }
})
$runtimeIdentity | Add-Member -NotePropertyName source_umap_files -NotePropertyValue @($runtimeIdentity.source_maps) -Force
$runtimeIdentity | Add-Member -NotePropertyName package_files -NotePropertyValue $runtimePackageHashes -Force
[System.IO.File]::WriteAllText(
    (Join-Path $paths.Runtime "ontotwin-runtime-manifest.json"),
    ($runtimeIdentity | ConvertTo-Json -Depth 8),
    $encoding)

$imageFiles = [ordered]@{
    backend = Join-Path $paths.Images "ontotwin-backend.tar"
    postgres = Join-Path $paths.Images "postgres.tar"
    neo4j = Join-Path $paths.Images "neo4j.tar"
}
foreach ($imagePath in $imageFiles.Values) {
    if (-not (Test-Path -LiteralPath $imagePath -PathType Leaf)) {
        throw "Fresh release image archive is missing: $imagePath"
    }
}

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
    manifest_schema_version = 3
    product = "OntoTwin ZHHZ"
    release_version = $ReleaseVersion
    data_version = $dataVersion
    project_id = $ProjectId
    generated_at = (Get-Date).ToString("o")
    runtime_project = [string]$runtimeIdentity.project_name
    runtime_target = [string]$runtimeIdentity.target_name
    runtime_source_sha256 = [string]$runtimeIdentity.source_project_sha256
    realtime_websocket_enabled = $false
    pixel_streaming_included = $false
    artstudio_enabled_by_default = $true
    reset_backend_baseline_on_upgrade = [bool]$ResetBackendBaselineOnUpgrade
    component_versions = [ordered]@{
        release_version = $ReleaseVersion
        base_release_version = "fresh-source"
        data_version = $dataVersion
        runtime = [ordered]@{
            manifest_schema_version = [int]$runtimeIdentity.schema_version
            project_name = [string]$runtimeIdentity.project_name
            target_name = [string]$runtimeIdentity.target_name
            source_project_path = [string]$runtimeIdentity.source_project_path
            source_project_sha256 = [string]$runtimeIdentity.source_project_sha256
            source_build_inputs = @($runtimeIdentity.source_build_inputs)
            source_umap_files = @($runtimeIdentity.source_umap_files)
            package_files = $runtimePackageHashes
        }
        images = [ordered]@{
            backend_image = $backendImage
            backend_sha256 = (Get-FileHash -LiteralPath $imageFiles.backend -Algorithm SHA256).Hash.ToLowerInvariant()
            postgres_image = $postgresImage
            postgres_sha256 = (Get-FileHash -LiteralPath $imageFiles.postgres -Algorithm SHA256).Hash.ToLowerInvariant()
            neo4j_image = $neo4jImage
            neo4j_sha256 = (Get-FileHash -LiteralPath $imageFiles.neo4j -Algorithm SHA256).Hash.ToLowerInvariant()
        }
        installer = [ordered]@{
            binary_version = [string]$releaseDescriptor.BinaryVersion
            bundle_version = [string]$releaseDescriptor.BundleVersion
            msi_version = [string]$releaseDescriptor.MsiVersion
        }
    }
    postgres_counts = $dataManifest.postgres
    files = $manifestFiles
}
[System.IO.File]::WriteAllText(
    (Join-Path $outputRoot "release-manifest.json"),
    ($releaseManifest | ConvertTo-Json -Depth 8),
    $encoding
)

Write-Host "Release bundle created: $outputRoot" -ForegroundColor Green
