[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$BaseAppDirectory,

    [Parameter(Mandatory = $true)]
    [string]$OutputDirectory,

    [string]$BaseVersion = "3.7.1-r1-rc10.10",
    [string]$TargetVersion = "3.7.1-r1-rc10.10-hf2"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$allInOneRoot = Split-Path -Parent $scriptRoot
$repositoryRoot = [System.IO.Path]::GetFullPath((Join-Path $allInOneRoot "..\.."))
$baseApp = [System.IO.Path]::GetFullPath($BaseAppDirectory)
$output = [System.IO.Path]::GetFullPath($OutputDirectory)
$basePayload = Join-Path $baseApp "BackendPayload"
$baseReleaseManifestPath = Join-Path $baseApp "release-manifest.json"
$backendTag = "ontotwin-zhhz/backend:$TargetVersion"
$encoding = [System.Text.UTF8Encoding]::new($false)

function Get-LowerHash {
    param([Parameter(Mandatory = $true)][string]$Path)
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Set-EnvironmentValue {
    param(
        [Parameter(Mandatory = $true)][string]$Text,
        [Parameter(Mandatory = $true)][string]$Key,
        [Parameter(Mandatory = $true)][string]$Value
    )
    $pattern = '(?m)^' + [regex]::Escape($Key) + '=.*$'
    if ([regex]::Matches($Text, $pattern).Count -ne 1) {
        throw "Expected one $Key entry in the release environment."
    }
    return [regex]::Replace($Text, $pattern, "$Key=$Value", 1)
}

function Update-ManifestFileEntry {
    param(
        [Parameter(Mandatory = $true)]$Manifest,
        [Parameter(Mandatory = $true)][string]$RelativePath,
        [Parameter(Mandatory = $true)][string]$PhysicalPath
    )
    $entry = @($Manifest.files | Where-Object { [string]$_.path -eq $RelativePath })
    if ($entry.Count -ne 1) { throw "Release manifest entry is missing or duplicated: $RelativePath" }
    $entry[0].bytes = (Get-Item -LiteralPath $PhysicalPath).Length
    $entry[0].sha256 = Get-LowerHash $PhysicalPath
}

foreach ($required in @(
    $baseReleaseManifestPath,
    (Join-Path $basePayload "SHA256SUMS"),
    (Join-Path $basePayload "backend-image.tar"),
    (Join-Path $basePayload "postgres-image.tar"),
    (Join-Path $basePayload "neo4j-image.tar"),
    (Join-Path $basePayload "docker-static.tgz"),
    (Join-Path $basePayload "docker-compose"),
    (Join-Path $basePayload "release.tar.gz")
)) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
        throw "RC10.10 base payload is incomplete: $required"
    }
}

$baseManifest = Get-Content -Raw -Encoding UTF8 -LiteralPath $baseReleaseManifestPath | ConvertFrom-Json
if ([string]$baseManifest.release_version -ne $BaseVersion) {
    throw "Base App version mismatch: $($baseManifest.release_version)"
}

if (Test-Path -LiteralPath $output) {
    if (@(Get-ChildItem -LiteralPath $output -Force).Count -gt 0) {
        throw "OutputDirectory must be empty: $output"
    }
} else {
    New-Item -ItemType Directory -Path $output | Out-Null
}

$workRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("ontotwin-hf2-" + [Guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $workRoot | Out-Null
try {
    $payloadStage = Join-Path $workRoot "payload"
    $backendPayloadStage = Join-Path $payloadStage "BackendPayload"
    $releaseStage = Join-Path $workRoot "release"
    $publishStage = Join-Path $workRoot "publish"
    New-Item -ItemType Directory -Path $backendPayloadStage,$releaseStage,$publishStage | Out-Null

    Write-Host "Building $backendTag ..." -ForegroundColor Cyan
    Push-Location $repositoryRoot
    try {
        & docker build -f (Join-Path $allInOneRoot "Dockerfile.backend") -t $backendTag .
        if ($LASTEXITCODE -ne 0) { throw "Backend image build failed." }
    } finally {
        Pop-Location
    }
    $backendArchive = Join-Path $backendPayloadStage "backend-image.tar"
    & docker save --output $backendArchive $backendTag
    if ($LASTEXITCODE -ne 0) { throw "Backend image export failed." }
    $backendHash = Get-LowerHash $backendArchive

    Write-Host "Preparing the preserved RC10.10 release payload ..." -ForegroundColor Cyan
    & tar.exe -xzf (Join-Path $basePayload "release.tar.gz") -C $releaseStage
    if ($LASTEXITCODE -ne 0) { throw "Cannot extract the RC10.10 backend release archive." }

    $composePath = Join-Path $releaseStage "Deploy\docker-compose.release.yml"
    $environmentPath = Join-Path $releaseStage "Deploy\customer.env.example"
    Copy-Item -LiteralPath (Join-Path $allInOneRoot "docker-compose.release.yml") -Destination $composePath -Force
    $environment = Get-Content -Raw -Encoding UTF8 -LiteralPath $environmentPath
    $environment = Set-EnvironmentValue $environment "BACKEND_IMAGE" $backendTag
    $environment = Set-EnvironmentValue $environment "ONTOTWIN_RELEASE_VERSION" $TargetVersion
    [System.IO.File]::WriteAllText($environmentPath, $environment, $encoding)

    $nestedManifestPath = Join-Path $releaseStage "release-manifest.json"
    $targetManifest = Get-Content -Raw -Encoding UTF8 -LiteralPath $nestedManifestPath | ConvertFrom-Json
    if ([string]$targetManifest.release_version -ne $BaseVersion) {
        throw "Nested base release version mismatch: $($targetManifest.release_version)"
    }
    $targetManifest.release_version = $TargetVersion
    $targetManifest.generated_at = (Get-Date).ToString("o")
    $targetManifest.reset_backend_baseline_on_upgrade = $false
    $targetManifest.component_versions.release_version = $TargetVersion
    $targetManifest.component_versions.base_release_version = $BaseVersion
    $targetManifest.component_versions.images.backend_image = $backendTag
    $targetManifest.component_versions.images.backend_sha256 = $backendHash
    Update-ManifestFileEntry $targetManifest "Deploy/docker-compose.release.yml" $composePath
    Update-ManifestFileEntry $targetManifest "Deploy/customer.env.example" $environmentPath
    $backendFileEntry = @($targetManifest.files | Where-Object { [string]$_.path -eq "Images/ontotwin-backend.tar" })
    if ($backendFileEntry.Count -ne 1) { throw "Backend archive entry is missing from release-manifest.json." }
    $backendFileEntry[0].bytes = (Get-Item -LiteralPath $backendArchive).Length
    $backendFileEntry[0].sha256 = $backendHash
    [System.IO.File]::WriteAllText(
        $nestedManifestPath,
        ($targetManifest | ConvertTo-Json -Depth 20),
        $encoding)
    Copy-Item -LiteralPath $nestedManifestPath -Destination (Join-Path $payloadStage "release-manifest.json")

    $releaseArchive = Join-Path $backendPayloadStage "release.tar.gz"
    & tar.exe -czf $releaseArchive -C $releaseStage .
    if ($LASTEXITCODE -ne 0) { throw "Cannot create the HF2 backend release archive." }
    foreach ($name in @("bootstrap.sh", "control.py")) {
        Copy-Item -LiteralPath (Join-Path $allInOneRoot "hyperv\guest\$name") -Destination $backendPayloadStage
    }

    $payloadHashes = @{}
    foreach ($line in Get-Content -Encoding UTF8 -LiteralPath (Join-Path $basePayload "SHA256SUMS")) {
        if ($line -notmatch '^([0-9a-fA-F]{64})\s+(.+)$') { throw "Invalid base SHA256SUMS line: $line" }
        $payloadHashes[$Matches[2].Trim()] = $Matches[1].ToLowerInvariant()
    }
    foreach ($name in @("backend-image.tar", "release.tar.gz", "bootstrap.sh", "control.py")) {
        $payloadHashes[$name] = Get-LowerHash (Join-Path $backendPayloadStage $name)
    }
    $sumLines = foreach ($name in @($payloadHashes.Keys | Sort-Object)) {
        "$($payloadHashes[$name])  $name"
    }
    [System.IO.File]::WriteAllText(
        (Join-Path $backendPayloadStage "SHA256SUMS"),
        (($sumLines -join "`n") + "`n"),
        $encoding)

    $requiredBaseFiles = [ordered]@{
        "release-manifest.json" = Get-LowerHash $baseReleaseManifestPath
    }
    foreach ($name in @($payloadHashes.Keys | Sort-Object)) {
        $baseFile = Join-Path $basePayload $name
        if (-not (Test-Path -LiteralPath $baseFile -PathType Leaf)) {
            throw "Base BackendPayload file is missing: $baseFile"
        }
        $requiredBaseFiles["BackendPayload/$name"] = Get-LowerHash $baseFile
    }

    $targetFiles = [ordered]@{}
    foreach ($relative in @(
        "release-manifest.json",
        "BackendPayload/backend-image.tar",
        "BackendPayload/release.tar.gz",
        "BackendPayload/bootstrap.sh",
        "BackendPayload/control.py",
        "BackendPayload/SHA256SUMS"
    )) {
        $targetFiles[$relative] = Get-LowerHash (Join-Path $payloadStage $relative)
    }
    $hotfixManifest = [ordered]@{
        schema_version = 1
        product = "OntoTwin ZHHZ"
        base_version = $BaseVersion
        target_version = $TargetVersion
        generated_at = (Get-Date).ToString("o")
        data_policy = "preserve-existing-volumes"
        required_base_files = $requiredBaseFiles
        target_files = $targetFiles
    }
    [System.IO.File]::WriteAllText(
        (Join-Path $payloadStage "hotfix-manifest.json"),
        ($hotfixManifest | ConvertTo-Json -Depth 8),
        $encoding)

    $payloadZip = Join-Path $workRoot "OntoTwin-ZHHZ-RC10.10-HF2.payload.zip"
    Compress-Archive -Path (Join-Path $payloadStage "*") -DestinationPath $payloadZip -CompressionLevel Optimal

    Write-Host "Publishing the one-click maintenance executable ..." -ForegroundColor Cyan
    & dotnet publish (Join-Path $scriptRoot "OntoTwin.ZHHZ.HotfixUpdater.csproj") `
        -c Release -r win-x64 --self-contained true `
        -p:PublishSingleFile=true -p:HotfixPayloadPath="$payloadZip" `
        -o $publishStage
    if ($LASTEXITCODE -ne 0) { throw "HF2 updater publish failed." }
    $publishedExe = Join-Path $publishStage "OntoTwin-ZHHZ-RC10.10-HF2.exe"
    if (-not (Test-Path -LiteralPath $publishedExe -PathType Leaf)) {
        throw "Published HF2 executable is missing: $publishedExe"
    }
    $finalExe = Join-Path $output "OntoTwin-ZHHZ-RC10.10-HF2.exe"
    Copy-Item -LiteralPath $publishedExe -Destination $finalExe
    $finalHash = Get-LowerHash $finalExe
    [System.IO.File]::WriteAllText(
        (Join-Path $output "OntoTwin-ZHHZ-RC10.10-HF2.exe.sha256"),
        "$finalHash  OntoTwin-ZHHZ-RC10.10-HF2.exe`n",
        $encoding)
    Copy-Item -LiteralPath (Join-Path $scriptRoot "HF2-README.txt") -Destination $output

    Write-Host "HF2 package created: $output" -ForegroundColor Green
    Get-Item -LiteralPath $finalExe | Format-List FullName,Length,LastWriteTime
    Write-Host "SHA256: $finalHash"
} finally {
    if (Test-Path -LiteralPath $workRoot) {
        Remove-Item -LiteralPath $workRoot -Recurse -Force
    }
}
