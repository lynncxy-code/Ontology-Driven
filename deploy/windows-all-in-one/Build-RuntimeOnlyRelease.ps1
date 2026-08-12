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
    [string]$ReleaseVersion
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
    param([Parameter(Mandatory = $true)][string]$RuntimeRoot)

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
    if ($ufsText -notmatch '(?im)^ZHHZ[/\\]ZHHZ\.uproject(?:\s|$)') {
        throw "The UFS manifest does not contain the ZHHZ project descriptor."
    }
    if ($ufsText -notmatch '(?im)^ZHHZ[/\\]Plugins[/\\]glTFRuntime[/\\]glTFRuntime\.uplugin(?:\s|$)') {
        throw "The UFS manifest does not contain the required glTFRuntime plugin."
    }
    if ($ufsText -notmatch '(?im)^ZHHZ[/\\]Plugins[/\\]OntoTwinSync[/\\]OntoTwinSync\.uplugin(?:\s|$)') {
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

foreach ($required in @(
    (Join-Path $runtime "ZHHZ.exe"),
    $runtimeManifestPath,
    (Join-Path $runtime "ZHHZ"),
    (Join-Path $runtime "Manifest_UFSFiles_Win64.txt"),
    (Join-Path $runtime "Manifest_NonUFSFiles_Win64.txt"),
    $sourceProject,
    $baseManifestPath,
    (Join-Path $baseRelease "Models"),
    (Join-Path $baseRelease "Database"),
    (Join-Path $baseRelease "Images"),
    $currentComposePath,
    $currentEnvironmentTemplatePath
)) {
    if (-not (Test-Path -LiteralPath $required)) { throw "Required release input is missing: $required" }
}

$runtimeIdentity = Get-Content -Raw -LiteralPath $runtimeManifestPath | ConvertFrom-Json
if ($runtimeIdentity.project_name -ne "ZHHZ" -or $runtimeIdentity.target_name -ne "ZHHZ") {
    throw "Runtime identity mismatch: project='$($runtimeIdentity.project_name)', target='$($runtimeIdentity.target_name)'."
}
if ([int]$runtimeIdentity.schema_version -lt 3 -or @($runtimeIdentity.source_build_inputs).Count -eq 0) {
    throw "Runtime identity is missing schema-3 source/config/plugin evidence. Run a fresh Cook instead of reusing an old runtime."
}
if ([System.IO.Path]::GetFileNameWithoutExtension($sourceProject) -ne "ZHHZ") {
    throw "SourceProjectPath must point to ZHHZ.uproject: $sourceProject"
}
$sourceProjectHash = (Get-FileHash -LiteralPath $sourceProject -Algorithm SHA256).Hash.ToLowerInvariant()
if ($sourceProjectHash -ne [string]$runtimeIdentity.source_project_sha256) {
    throw "SourceProjectPath hash does not match the packaged runtime manifest."
}
$sourceProjectRoot = Split-Path -Parent $sourceProject
$sourceProjectPrefix = [System.IO.Path]::GetFullPath($sourceProjectRoot).TrimEnd('\') + '\'
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
Assert-RuntimePackaging -RuntimeRoot $runtime

if (Test-Path -LiteralPath $output) {
    if (@(Get-ChildItem -LiteralPath $output -Force).Count -gt 0) {
        throw "OutputDirectory must be empty: $output"
    }
} else {
    New-Item -ItemType Directory -Path $output | Out-Null
}

foreach ($item in Get-ChildItem -LiteralPath $baseRelease -Force | Where-Object {
    $_.Name -notin @("ZHHZ", "release-manifest.json", "Deployment-Guide.md")
}) {
    Copy-Item -LiteralPath $item.FullName -Destination $output -Recurse -Force
}
Copy-Item -LiteralPath $runtime -Destination (Join-Path $output "ZHHZ") -Recurse -Force
$outputRuntime = Join-Path $output "ZHHZ"
$runtimePackagePaths = @(
    "ZHHZ.exe",
    "ZHHZ\Binaries\Win64\ZHHZ-Win64-Shipping.exe",
    "ZHHZ\Content\Paks\ZHHZ-Windows.pak",
    "ZHHZ\Content\Paks\ZHHZ-Windows.ucas",
    "ZHHZ\Content\Paks\ZHHZ-Windows.utoc"
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
if ($baseManifest.PSObject.Properties.Name -notcontains "reset_backend_baseline_on_upgrade") {
    throw "Base release manifest does not declare reset_backend_baseline_on_upgrade."
}
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
$customerEnvironment = Set-EnvironmentValue -Content $customerEnvironment -Key "BACKEND_IMAGE" -Value ([string]$baseManifest.component_versions.images.backend_image)
$customerEnvironment = Set-EnvironmentValue -Content $customerEnvironment -Key "POSTGRES_IMAGE" -Value ([string]$baseManifest.component_versions.images.postgres_image)
$customerEnvironment = Set-EnvironmentValue -Content $customerEnvironment -Key "NEO4J_IMAGE" -Value ([string]$baseManifest.component_versions.images.neo4j_image)
$customerEnvironment = Set-EnvironmentValue -Content $customerEnvironment -Key "ONTOTWIN_RELEASE_VERSION" -Value $ReleaseVersion
$customerEnvironment = Set-EnvironmentValue -Content $customerEnvironment -Key "ONTOTWIN_DATA_VERSION" -Value ([string]$baseManifest.data_version)
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

$componentVersions = [ordered]@{
    release_version = $ReleaseVersion
    base_release_version = [string]$baseManifest.release_version
    data_version = [string]$baseManifest.data_version
    runtime = [ordered]@{
        manifest_schema_version = [int]$runtimeIdentity.schema_version
        project_name = [string]$runtimeIdentity.project_name
        target_name = [string]$runtimeIdentity.target_name
        source_project_path = $sourceProject
        source_project_sha256 = [string]$runtimeIdentity.source_project_sha256
        source_build_inputs = @($runtimeIdentity.source_build_inputs)
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
    manifest_schema_version = 3
    product = "OntoTwin ZHHZ"
    release_version = $ReleaseVersion
    data_version = $baseManifest.data_version
    project_id = $baseManifest.project_id
    generated_at = (Get-Date).ToString("o")
    runtime_project = $runtimeIdentity.project_name
    runtime_target = $runtimeIdentity.target_name
    runtime_source_sha256 = $runtimeIdentity.source_project_sha256
    realtime_websocket_enabled = $false
    pixel_streaming_included = $false
    artstudio_enabled_by_default = $true
    reset_backend_baseline_on_upgrade = [bool]$baseManifest.reset_backend_baseline_on_upgrade
    component_versions = $componentVersions
    postgres_counts = $baseManifest.postgres_counts
    files = $manifestFiles
}
[System.IO.File]::WriteAllText(
    (Join-Path $output "release-manifest.json"),
    ($releaseManifest | ConvertTo-Json -Depth 8),
    [System.Text.UTF8Encoding]::new($false))

Write-Host "Runtime-only release created: $output" -ForegroundColor Green
