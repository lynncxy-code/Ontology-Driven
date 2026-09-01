[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$BaseReleaseDirectory,

    [Parameter(Mandatory = $true)]
    [string]$RuntimeDirectory,

    [Parameter(Mandatory = $true)]
    [string]$SourceProjectPath,

    [Parameter(Mandatory = $true)]
    [string]$OutputDirectory,

    [Parameter(Mandatory = $true)]
    [string]$ReleaseVersion,

    [string]$DataDirectory = "",
    [string]$ProjectId = "",
    [string]$ProjectName = "",
    [string]$BackendImageArchive = "",
    [string]$BackendImageTag = "",

    [switch]$ResetBackendBaselineOnUpgrade
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-ReleaseDescriptor {
    param([Parameter(Mandatory = $true)][string]$Version)

    if ($Version -cnotmatch '^(?<product>\d+\.\d+\.\d+)-r(?<release>\d+)-rc(?<candidateMajor>\d+)(?:\.(?<candidateMinor>\d+))?$') {
        throw "ReleaseVersion must use the canonical lower-case form '<version>-r<number>-rc<number>', for example '3.7.1-r1-rc9.3'. Got: $Version"
    }
    $productVersion = $Matches.product
    $releaseNumber = $Matches.release
    $candidateMajor = [int]$Matches.candidateMajor
    $hasCandidateMinor = $Matches.ContainsKey('candidateMinor') -and -not [string]::IsNullOrWhiteSpace([string]$Matches['candidateMinor'])
    $candidateMinor = if ($hasCandidateMinor) { [int]$Matches['candidateMinor'] } else { 0 }
    if ($candidateMinor -gt 99) { throw "The RC minor revision must be between 0 and 99: $Version" }
    $candidateNumber = if ($hasCandidateMinor) { "$candidateMajor.$candidateMinor" } else { "$candidateMajor" }
    $numericRevision = ($candidateMajor * 100) + $candidateMinor
    if ($numericRevision -gt 65535) { throw "The RC revision is too large for a Windows binary version: $Version" }
    $msiParts = $productVersion.Split('.')
    $releaseLabel = "OntoTwin-ZHHZ-$productVersion-R$releaseNumber-RC$candidateNumber"
    return [pscustomobject]@{
        Version = $Version
        DisplayVersion = "$productVersion R$releaseNumber RC$candidateNumber"
        Candidate = "RC$candidateNumber"
        Label = $releaseLabel
        SetupFile = "$releaseLabel-Setup.exe"
        BinaryVersion = "$productVersion.$numericRevision"
        BundleVersion = "$productVersion.$numericRevision"
        MsiVersion = "$($msiParts[0]).$($msiParts[1]).$numericRevision"
    }
}

function Write-ReleaseDocument {
    param(
        [Parameter(Mandatory = $true)][string]$Source,
        [Parameter(Mandatory = $true)][string]$Destination,
        [Parameter(Mandatory = $true)]$Descriptor
    )

    $content = Get-Content -Raw -Encoding UTF8 -LiteralPath $Source
    $content = $content.Replace('__RELEASE_VERSION__', [string]$Descriptor.Version)
    $content = $content.Replace('__RELEASE_DISPLAY_VERSION__', [string]$Descriptor.DisplayVersion)
    $content = $content.Replace('__RELEASE_RC__', [string]$Descriptor.Candidate)
    $content = $content.Replace('__RELEASE_LABEL__', [string]$Descriptor.Label)
    $content = $content.Replace('__SETUP_FILE__', [string]$Descriptor.SetupFile)
    if ($content -match '__RELEASE_[A-Z_]+__|__SETUP_FILE__') {
        throw "An unresolved release token remains in $Source."
    }
    [System.IO.File]::WriteAllText($Destination, $content, [System.Text.UTF8Encoding]::new($false))
}

function Assert-RuntimePackaging {
    param(
        [Parameter(Mandatory = $true)][string]$RuntimeRoot,
        [Parameter(Mandatory = $true)][string]$ExpectedProjectName
    )

    $ufsPath = Join-Path $RuntimeRoot "Manifest_UFSFiles_Win64.txt"
    $nonUfsPath = Join-Path $RuntimeRoot "Manifest_NonUFSFiles_Win64.txt"
    foreach ($manifestPath in @($ufsPath, $nonUfsPath)) {
        if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
            throw "Required Shipping manifest is missing: $manifestPath"
        }
    }

    $ufsText = Get-Content -Raw -Encoding UTF8 -LiteralPath $ufsPath
    $nonUfsText = Get-Content -Raw -Encoding UTF8 -LiteralPath $nonUfsPath
    $combinedText = $ufsText + [Environment]::NewLine + $nonUfsText
    if ($combinedText -match '(?i)(^|[/\\])(test0316|tmp_ue)([/\\]|$)') {
        throw "The Shipping manifests contain a forbidden test project identity."
    }
    if ($combinedText -match '(?i)PixelStreaming') {
        throw "Pixel Streaming files are present even though this release must not include Pixel Streaming."
    }
    $projectPattern = [regex]::Escape($ExpectedProjectName)
    if ($ufsText -notmatch "(?im)^$projectPattern[/\\]$projectPattern\.uproject(?:\s|`$)") {
        throw "The UFS manifest does not contain the $ExpectedProjectName project descriptor."
    }
    if ($ufsText -notmatch "(?im)^$projectPattern[/\\]Plugins[/\\]glTFRuntime[/\\]glTFRuntime\.uplugin(?:\s|`$)") {
        throw "The UFS manifest does not contain the required glTFRuntime plugin."
    }
    if ($ufsText -notmatch "(?im)^$projectPattern[/\\]Plugins[/\\]OntoTwinSync[/\\]OntoTwinSync\.uplugin(?:\s|`$)") {
        throw "The UFS manifest does not contain the required OntoTwinSync plugin."
    }

    $forbiddenPath = Get-ChildItem -LiteralPath $RuntimeRoot -Recurse -Force | Where-Object {
        $_.FullName.Substring($RuntimeRoot.Length).TrimStart([char[]]@('\', '/')) -match '(?i)(^|[/\\])(test0316|tmp_ue|PixelStreaming)([/\\]|$)'
    } | Select-Object -First 1
    if ($null -ne $forbiddenPath) {
        throw "The packaged runtime contains a forbidden path: $($forbiddenPath.FullName)"
    }
}

function Get-EnvironmentValue {
    param(
        [Parameter(Mandatory = $true)][string]$Content,
        [Parameter(Mandatory = $true)][string]$Key
    )

    $pattern = '(?m)^' + [regex]::Escape($Key) + '=(.*)$'
    $matches = [regex]::Matches($Content, $pattern)
    if ($matches.Count -ne 1) { throw "Expected exactly one $Key entry in customer.env.example; found $($matches.Count)." }
    return $matches[0].Groups[1].Value.TrimEnd("`r")
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
    return [regex]::Replace($Content, $pattern, "$Key=$Value")
}

function Get-NormalizedText {
    param([Parameter(Mandatory = $true)][string]$Content)

    # Release inputs are shared by Windows and Linux. Compare their semantic
    # text with canonical LF endings so a checkout's CRLF policy cannot hide a
    # stale Deploy file or create a false mismatch.
    return ([regex]::Replace($Content, "`r`n?|`n", "`n")).TrimEnd("`n") + "`n"
}

function Assert-NormalizedFileContent {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$ExpectedContent,
        [Parameter(Mandatory = $true)][string]$Description
    )

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "$Description is missing: $Path"
    }
    $actual = Get-NormalizedText -Content (Get-Content -Raw -Encoding UTF8 -LiteralPath $Path)
    $expected = Get-NormalizedText -Content $ExpectedContent
    if ($actual -cne $expected) {
        throw "$Description does not match the current deployment source: $Path"
    }
}

function Assert-DockerArchiveTag {
    param(
        [Parameter(Mandatory = $true)][string]$Archive,
        [Parameter(Mandatory = $true)][string]$ExpectedTag
    )

    $manifestText = (& tar.exe -xOf $Archive manifest.json) -join "`n"
    if ($LASTEXITCODE -ne 0) { throw "Cannot read Docker manifest.json from $Archive" }
    $dockerManifest = $manifestText | ConvertFrom-Json
    $repoTags = @($dockerManifest | ForEach-Object { @($_.RepoTags) })
    if ($repoTags -notcontains $ExpectedTag) {
        throw "Docker archive '$Archive' does not contain the configured tag '$ExpectedTag'. Found: $($repoTags -join ', ')"
    }

    # Docker Desktop may export OCI image archives.  In that format Docker
    # uses index.json annotations for the imported name; checking only the
    # legacy manifest.json RepoTags can let a stale tag through.
    $indexText = (& tar.exe -xOf $Archive index.json 2>$null) -join "`n"
    $indexExitCode = $LASTEXITCODE
    if ($indexExitCode -eq 0 -and -not [string]::IsNullOrWhiteSpace($indexText)) {
        try { $ociIndex = $indexText | ConvertFrom-Json }
        catch { throw "OCI index.json in '$Archive' is not valid JSON: $($_.Exception.Message)" }
        $expectedNames = @($ExpectedTag, "docker.io/$ExpectedTag")
        $ociNames = @($ociIndex.manifests | ForEach-Object {
            @($_.annotations.'io.containerd.image.name', $_.annotations.'org.opencontainers.image.ref.name')
        }) | Where-Object { -not [string]::IsNullOrWhiteSpace([string]$_) }
        $ociMatches = @($ociNames | Where-Object { $_ -in $expectedNames -or $_ -eq ($ExpectedTag -replace '^docker.io/', '') })
        if ($ociMatches.Count -eq 0) {
            throw "OCI archive '$Archive' does not expose the configured tag '$ExpectedTag' in index.json. Found: $($ociNames -join ', ')"
        }
    }
}

$baseRelease = [System.IO.Path]::GetFullPath($BaseReleaseDirectory)
$runtime = [System.IO.Path]::GetFullPath($RuntimeDirectory)
$sourceProject = [System.IO.Path]::GetFullPath($SourceProjectPath)
$output = [System.IO.Path]::GetFullPath($OutputDirectory)
$releaseDescriptor = Get-ReleaseDescriptor -Version $ReleaseVersion
$runtimeManifestPath = Join-Path $runtime "ontotwin-runtime-manifest.json"
$baseManifestPath = Join-Path $baseRelease "release-manifest.json"
$currentComposePath = Join-Path $PSScriptRoot "docker-compose.release.yml"
$currentEnvironmentTemplatePath = Join-Path $PSScriptRoot "customer.env.example"
$currentPostgresRestoreScriptPath = Join-Path $PSScriptRoot "database\postgres\01-restore.sh"

if (-not (Test-Path -LiteralPath $runtimeManifestPath -PathType Leaf)) {
    throw "Required release input is missing: $runtimeManifestPath"
}
$runtimeIdentity = Get-Content -Raw -LiteralPath $runtimeManifestPath | ConvertFrom-Json
$runtimeProjectName = [string]$runtimeIdentity.project_name
$runtimeTargetName = [string]$runtimeIdentity.target_name
if ($runtimeProjectName -notmatch '^[A-Za-z0-9_]+$' -or $runtimeTargetName -notmatch '^[A-Za-z0-9_]+$') {
    throw "Runtime identity contains an invalid project or target name."
}
if ($runtimeProjectName -ne $runtimeTargetName) {
    throw "Runtime project and target must match: project='$runtimeProjectName', target='$runtimeTargetName'."
}
$resolvedDataDirectory = if ([string]::IsNullOrWhiteSpace($DataDirectory)) {
    Join-Path $baseRelease "Database"
} else {
    [System.IO.Path]::GetFullPath($DataDirectory)
}

foreach ($required in @(
    (Join-Path $runtime "$runtimeTargetName.exe"),
    (Join-Path $runtime $runtimeProjectName),
    (Join-Path $runtime "Manifest_UFSFiles_Win64.txt"),
    (Join-Path $runtime "Manifest_NonUFSFiles_Win64.txt"),
    $sourceProject,
    $baseManifestPath,
    (Join-Path $baseRelease "Models"),
    $resolvedDataDirectory,
    (Join-Path $baseRelease "Images"),
    $currentComposePath,
    $currentEnvironmentTemplatePath,
    $currentPostgresRestoreScriptPath
)) {
    if (-not (Test-Path -LiteralPath $required)) { throw "Required release input is missing: $required" }
}

if ([System.IO.Path]::GetFileNameWithoutExtension($sourceProject) -ne $runtimeProjectName) {
    throw "SourceProjectPath must point to $runtimeProjectName.uproject: $sourceProject"
}
$sourceProjectHash = (Get-FileHash -LiteralPath $sourceProject -Algorithm SHA256).Hash.ToLowerInvariant()
if ($sourceProjectHash -ne [string]$runtimeIdentity.source_project_sha256) {
    throw "SourceProjectPath hash does not match the packaged runtime manifest."
}
$sourceProjectRoot = Split-Path -Parent $sourceProject
$sourceContentRoot = Join-Path $sourceProjectRoot "Content"
$sourceMaps = @(Get-ChildItem -LiteralPath $sourceContentRoot -Filter "*.umap" -Recurse -File | Sort-Object FullName)
if ($sourceMaps.Count -eq 0) { throw "Source project does not contain any .umap files: $sourceContentRoot" }
$runtimeGeneratedAt = [DateTimeOffset]::Parse(
    [string]$runtimeIdentity.generated_at,
    [System.Globalization.CultureInfo]::InvariantCulture)
$newerSourceMap = $sourceMaps | Where-Object {
    $_.LastWriteTimeUtc -gt $runtimeGeneratedAt.UtcDateTime
} | Select-Object -First 1
if ($null -ne $newerSourceMap) {
    throw "A source map is newer than the packaged runtime and must be recooked: $($newerSourceMap.FullName)"
}
$sourceMapHashes = @($sourceMaps | ForEach-Object {
    [ordered]@{
        path = $_.FullName.Substring($sourceProjectRoot.Length + 1).Replace('\', '/')
        bytes = $_.Length
        last_write_utc = $_.LastWriteTimeUtc.ToString("o")
        sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    }
})
Assert-RuntimePackaging -RuntimeRoot $runtime -ExpectedProjectName $runtimeProjectName

if (Test-Path -LiteralPath $output) {
    if (@(Get-ChildItem -LiteralPath $output -Force).Count -gt 0) {
        throw "OutputDirectory must be empty: $output"
    }
} else {
    New-Item -ItemType Directory -Path $output | Out-Null
}

$excludedBaseItems = @("ZHHZ", "release-manifest.json", "Deployment-Guide.md")
if (-not [string]::IsNullOrWhiteSpace($DataDirectory)) { $excludedBaseItems += @("Database", "Data") }
foreach ($item in Get-ChildItem -LiteralPath $baseRelease -Force | Where-Object {
    $_.Name -notin $excludedBaseItems
}) {
    Copy-Item -LiteralPath $item.FullName -Destination $output -Recurse -Force
}
if (-not [string]::IsNullOrWhiteSpace($BackendImageArchive)) {
    if ([string]::IsNullOrWhiteSpace($BackendImageTag)) {
        throw "BackendImageTag is required when BackendImageArchive is provided."
    }
    $resolvedBackendImageArchive = [System.IO.Path]::GetFullPath($BackendImageArchive)
    if (-not (Test-Path -LiteralPath $resolvedBackendImageArchive -PathType Leaf)) {
        throw "Backend image archive was not found: $resolvedBackendImageArchive"
    }
    Copy-Item -LiteralPath $resolvedBackendImageArchive -Destination (Join-Path $output "Images\ontotwin-backend.tar") -Force
}
Copy-Item -LiteralPath $runtime -Destination (Join-Path $output "ZHHZ") -Recurse -Force
$outputRuntime = Join-Path $output "ZHHZ"
$runtimePackagePaths = @(
    "$runtimeTargetName.exe",
    "$runtimeProjectName\Binaries\Win64\$runtimeTargetName-Win64-Shipping.exe",
    "$runtimeProjectName\Content\Paks\$runtimeProjectName-Windows.pak",
    "$runtimeProjectName\Content\Paks\$runtimeProjectName-Windows.ucas",
    "$runtimeProjectName\Content\Paks\$runtimeProjectName-Windows.utoc"
)
$runtimePackageHashes = @($runtimePackagePaths | ForEach-Object {
    $packagePath = Join-Path $outputRuntime $_
    if (-not (Test-Path -LiteralPath $packagePath -PathType Leaf)) { throw "Required runtime package file is missing: $packagePath" }
    [ordered]@{
        path = $_.Replace('\', '/')
        bytes = (Get-Item -LiteralPath $packagePath).Length
        sha256 = (Get-FileHash -LiteralPath $packagePath -Algorithm SHA256).Hash.ToLowerInvariant()
    }
})
$runtimeIdentity | Add-Member -NotePropertyName source_project_path -NotePropertyValue $sourceProject -Force
$runtimeIdentity | Add-Member -NotePropertyName source_project_sha256 -NotePropertyValue $sourceProjectHash -Force
$runtimeIdentity | Add-Member -NotePropertyName source_umap_files -NotePropertyValue $sourceMapHashes -Force
$runtimeIdentity | Add-Member -NotePropertyName package_files -NotePropertyValue $runtimePackageHashes -Force
[System.IO.File]::WriteAllText(
    (Join-Path $outputRuntime "ontotwin-runtime-manifest.json"),
    ($runtimeIdentity | ConvertTo-Json -Depth 8),
    [System.Text.UTF8Encoding]::new($false))
Write-ReleaseDocument `
    -Source (Join-Path $PSScriptRoot "CUSTOMER-README.md") `
    -Destination (Join-Path $output "Deployment-Guide.md") `
    -Descriptor $releaseDescriptor

$baseManifest = Get-Content -Raw -LiteralPath $baseManifestPath | ConvertFrom-Json
$dataManifest = $null
if (-not [string]::IsNullOrWhiteSpace($DataDirectory)) {
    $dataManifestPath = Join-Path $resolvedDataDirectory "data-manifest.json"
    if (-not (Test-Path -LiteralPath $dataManifestPath -PathType Leaf)) {
        throw "DataDirectory does not contain data-manifest.json: $resolvedDataDirectory"
    }
    $dataManifest = Get-Content -Raw -Encoding UTF8 -LiteralPath $dataManifestPath | ConvertFrom-Json
    if ([string]::IsNullOrWhiteSpace($ProjectId)) { $ProjectId = [string]$dataManifest.project_id }
    if ([string]::IsNullOrWhiteSpace($ProjectName)) { $ProjectName = [string]$dataManifest.project_name }
    if ([string]$dataManifest.project_id -ne $ProjectId -or [string]$dataManifest.project_name -ne $ProjectName) {
        throw "Data identity does not match ProjectId/ProjectName."
    }
    Copy-Item -LiteralPath $resolvedDataDirectory -Destination (Join-Path $output "Database") -Recurse -Force
    $outputData = Join-Path $output "Data"
    New-Item -ItemType Directory -Path (Join-Path $outputData "project_assets"),(Join-Path $outputData "exports") -Force | Out-Null
    $exportedAssets = Join-Path $resolvedDataDirectory "project_assets\$ProjectId"
    if (Test-Path -LiteralPath $exportedAssets -PathType Container) {
        Copy-Item -LiteralPath $exportedAssets -Destination (Join-Path $outputData "project_assets") -Recurse -Force
    }
} else {
    if ([string]::IsNullOrWhiteSpace($ProjectId)) { $ProjectId = [string]$baseManifest.project_id }
    if ([string]::IsNullOrWhiteSpace($ProjectName)) { $ProjectName = $runtimeProjectName }
}

# DataDirectory is an exported data snapshot and intentionally contains only
# data artifacts. The PostgreSQL restore hook is deployment policy, so always
# inject the current checkout's script after copying either a fresh snapshot or
# a base release. Writing normalized UTF-8/LF prevents a Windows checkout from
# producing a script that PostgreSQL cannot execute in the Linux container.
$outputPostgresDirectory = Join-Path $output "Database\postgres"
$outputPostgresRestoreScriptPath = Join-Path $outputPostgresDirectory "01-restore.sh"
New-Item -ItemType Directory -Path $outputPostgresDirectory -Force | Out-Null
$currentPostgresRestoreScript = Get-Content -Raw -Encoding UTF8 -LiteralPath $currentPostgresRestoreScriptPath
[System.IO.File]::WriteAllText(
    $outputPostgresRestoreScriptPath,
    (Get-NormalizedText -Content $currentPostgresRestoreScript),
    [System.Text.UTF8Encoding]::new($false))
Assert-NormalizedFileContent `
    -Path $outputPostgresRestoreScriptPath `
    -ExpectedContent $currentPostgresRestoreScript `
    -Description "PostgreSQL release restore script"
$restoreScriptBytes = [System.IO.File]::ReadAllBytes($outputPostgresRestoreScriptPath)
if ($restoreScriptBytes.Length -eq 0 -or $restoreScriptBytes -contains [byte]0x0D -or
    $restoreScriptBytes[$restoreScriptBytes.Length - 1] -ne 0x0A) {
    throw "PostgreSQL release restore script must be non-empty LF-only text ending in LF: $outputPostgresRestoreScriptPath"
}
$restoreScriptPrefix = [System.Text.Encoding]::ASCII.GetBytes("#!/usr/bin/env bash`n")
if ($restoreScriptBytes.Length -lt $restoreScriptPrefix.Length) {
    throw "PostgreSQL release restore script is truncated: $outputPostgresRestoreScriptPath"
}
for ($index = 0; $index -lt $restoreScriptPrefix.Length; $index++) {
    if ($restoreScriptBytes[$index] -ne $restoreScriptPrefix[$index]) {
        throw "PostgreSQL release restore script has an invalid interpreter line: $outputPostgresRestoreScriptPath"
    }
}
$dataVersion = if ($null -ne $dataManifest) { "zhhz-new-" + (Get-Date -Format "yyyyMMdd-HHmmss") } else { [string]$baseManifest.data_version }
$postgresCounts = if ($null -ne $dataManifest) { $dataManifest.postgres } else { $baseManifest.postgres_counts }
$outputDeploy = Join-Path $output "Deploy"
New-Item -ItemType Directory -Path $outputDeploy -Force | Out-Null

# Runtime-only releases intentionally reuse the immutable image archives and
# database seed from BaseReleaseDirectory, but deployment policy must always
# come from this checkout. Otherwise an RC built from an older base silently
# inherits an obsolete Compose network or environment template.
$currentCompose = Get-Content -Raw -Encoding UTF8 -LiteralPath $currentComposePath
$outputComposePath = Join-Path $outputDeploy "docker-compose.release.yml"
[System.IO.File]::WriteAllText(
    $outputComposePath,
    (Get-NormalizedText -Content $currentCompose),
    [System.Text.UTF8Encoding]::new($false))
Assert-NormalizedFileContent `
    -Path $outputComposePath `
    -ExpectedContent $currentCompose `
    -Description "Runtime-only release Docker Compose file"

$customerEnvironmentPath = Join-Path $output "Deploy\customer.env.example"
if ($baseManifest.PSObject.Properties.Name -notcontains "component_versions" -or
    $baseManifest.component_versions.PSObject.Properties.Name -notcontains "images") {
    throw "Base release manifest does not contain reusable image component versions."
}
$customerEnvironment = Get-Content -Raw -Encoding UTF8 -LiteralPath $currentEnvironmentTemplatePath
$resolvedBackendImageTag = if ([string]::IsNullOrWhiteSpace($BackendImageTag)) {
    [string]$baseManifest.component_versions.images.backend_image
} else {
    $BackendImageTag
}
$customerEnvironment = Set-EnvironmentValue -Content $customerEnvironment -Key "BACKEND_IMAGE" -Value $resolvedBackendImageTag
$customerEnvironment = Set-EnvironmentValue -Content $customerEnvironment -Key "POSTGRES_IMAGE" -Value ([string]$baseManifest.component_versions.images.postgres_image)
$customerEnvironment = Set-EnvironmentValue -Content $customerEnvironment -Key "NEO4J_IMAGE" -Value ([string]$baseManifest.component_versions.images.neo4j_image)
$customerEnvironment = Set-EnvironmentValue -Content $customerEnvironment -Key "ONTOTWIN_RELEASE_VERSION" -Value $ReleaseVersion
$customerEnvironment = Set-EnvironmentValue -Content $customerEnvironment -Key "ONTOTWIN_DATA_VERSION" -Value $dataVersion
if ($customerEnvironment.Contains("__RELEASE_VERSION__") -or $customerEnvironment.Contains("__DATA_VERSION__")) {
    throw "Rendered customer environment still contains a release/data version placeholder."
}
[System.IO.File]::WriteAllText(
    $customerEnvironmentPath,
    (Get-NormalizedText -Content $customerEnvironment),
    [System.Text.UTF8Encoding]::new($false))
Assert-NormalizedFileContent `
    -Path $customerEnvironmentPath `
    -ExpectedContent $customerEnvironment `
    -Description "Runtime-only release customer environment"

$backendImageTag = Get-EnvironmentValue -Content $customerEnvironment -Key "BACKEND_IMAGE"
$postgresImageTag = Get-EnvironmentValue -Content $customerEnvironment -Key "POSTGRES_IMAGE"
$neo4jImageTag = Get-EnvironmentValue -Content $customerEnvironment -Key "NEO4J_IMAGE"
if ((Get-EnvironmentValue -Content $customerEnvironment -Key "ONTOTWIN_RELEASE_VERSION") -ne $ReleaseVersion) {
    throw "Customer environment release version was not updated to $ReleaseVersion."
}
Assert-DockerArchiveTag -Archive (Join-Path $output "Images\ontotwin-backend.tar") -ExpectedTag $backendImageTag
Assert-DockerArchiveTag -Archive (Join-Path $output "Images\postgres.tar") -ExpectedTag $postgresImageTag
Assert-DockerArchiveTag -Archive (Join-Path $output "Images\neo4j.tar") -ExpectedTag $neo4jImageTag

$immutableFiles = @(Get-ChildItem -Recurse -File -LiteralPath $output) | Sort-Object FullName -Unique
$manifestFiles = @($immutableFiles | ForEach-Object {
    [ordered]@{
        path = $_.FullName.Substring($output.Length + 1).Replace('\', '/')
        bytes = $_.Length
        sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    }
})
$manifestByPath = @{}
foreach ($entry in $manifestFiles) { $manifestByPath[[string]$entry.path] = $entry }
foreach ($imagePath in @("Images/ontotwin-backend.tar", "Images/postgres.tar", "Images/neo4j.tar")) {
    if (-not $manifestByPath.ContainsKey($imagePath)) { throw "Required image is missing from the release manifest: $imagePath" }
}
if (-not $manifestByPath.ContainsKey("Database/postgres/01-restore.sh")) {
    throw "PostgreSQL restore script is missing from the release manifest."
}

$baseReleaseVersion = [string]$baseManifest.release_version
if ($baseReleaseVersion -eq $ReleaseVersion -and
    $baseManifest.PSObject.Properties.Name -contains "component_versions" -and
    $baseManifest.component_versions.PSObject.Properties.Name -contains "base_release_version") {
    # A rejected draft of the same RC is a valid immutable-artifact source for
    # a rebuild. Preserve the actual ancestry instead of reporting the RC as
    # its own base release.
    $baseReleaseVersion = [string]$baseManifest.component_versions.base_release_version
}

$componentVersions = [ordered]@{
    release_version = $ReleaseVersion
    base_release_version = $baseReleaseVersion
    data_version = $dataVersion
    runtime = [ordered]@{
        manifest_schema_version = [int]$runtimeIdentity.schema_version
        project_name = [string]$runtimeIdentity.project_name
        target_name = [string]$runtimeIdentity.target_name
        source_project_path = $sourceProject
        source_project_sha256 = [string]$runtimeIdentity.source_project_sha256
        source_umap_files = $sourceMapHashes
        package_files = $runtimePackageHashes
    }
    images = [ordered]@{
        backend_image = $backendImageTag
        backend_sha256 = [string]$manifestByPath["Images/ontotwin-backend.tar"].sha256
        postgres_image = $postgresImageTag
        postgres_sha256 = [string]$manifestByPath["Images/postgres.tar"].sha256
        neo4j_image = $neo4jImageTag
        neo4j_sha256 = [string]$manifestByPath["Images/neo4j.tar"].sha256
    }
    installer = [ordered]@{
        binary_version = [string]$releaseDescriptor.BinaryVersion
        bundle_version = [string]$releaseDescriptor.BundleVersion
        msi_version = [string]$releaseDescriptor.MsiVersion
    }
}

$releaseManifest = [ordered]@{
    manifest_schema_version = 2
    product = "OntoTwin ZHHZ"
    release_version = $ReleaseVersion
    data_version = $dataVersion
    project_id = $ProjectId
    project_name = $ProjectName
    ue_project_id = "ueproj_$runtimeProjectName"
    generated_at = (Get-Date).ToString("o")
    runtime_project = $runtimeIdentity.project_name
    runtime_target = $runtimeIdentity.target_name
    runtime_source_sha256 = $runtimeIdentity.source_project_sha256
    realtime_websocket_enabled = $false
    pixel_streaming_included = $false
    artstudio_enabled_by_default = $true
    reset_backend_baseline_on_upgrade = [bool]$ResetBackendBaselineOnUpgrade
    component_versions = $componentVersions
    postgres_counts = $postgresCounts
    files = $manifestFiles
}
[System.IO.File]::WriteAllText(
    (Join-Path $output "release-manifest.json"),
    ($releaseManifest | ConvertTo-Json -Depth 8),
    [System.Text.UTF8Encoding]::new($false))

Write-Host "Runtime-only release created: $output" -ForegroundColor Green
