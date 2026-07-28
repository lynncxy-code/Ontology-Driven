[CmdletBinding()]
param(
    [switch]$SkipServiceStart
)

. (Join-Path $PSScriptRoot "Common.ps1")

Assert-ExternalCommand -Name "docker"
Assert-ReleaseLayout

try {
    & docker info *> $null
    if ($LASTEXITCODE -ne 0) {
        throw "Docker Desktop is not running."
    }
} catch {
    throw "Docker Desktop is unavailable. Start Docker Desktop and run the launcher again."
}

foreach ($directory in @(
    $script:DataRoot,
    (Join-Path $script:DataRoot "project_assets"),
    (Join-Path $script:DataRoot "exports"),
    (Join-Path $script:ReleaseRoot "Backups")
)) {
    if (-not (Test-Path -LiteralPath $directory)) {
        New-Item -ItemType Directory -Path $directory | Out-Null
    }
}

if (-not (Test-Path -LiteralPath $script:EnvFile -PathType Leaf)) {
    $manifestPath = Join-Path $script:ReleaseRoot "release-manifest.json"
    if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
        throw "Release manifest is missing: $manifestPath"
    }

    $manifest = Get-Content -Raw -Encoding UTF8 -LiteralPath $manifestPath | ConvertFrom-Json
    $content = Get-Content -Raw -LiteralPath $script:EnvTemplate
    $content = $content.Replace("__RELEASE_VERSION__", [string]$manifest.release_version)
    $content = $content.Replace("__DATA_VERSION__", [string]$manifest.data_version)
    $content = $content.Replace("__POSTGRES_PASSWORD__", (New-RandomAlphaNumericSecret))
    $content = $content.Replace("__NEO4J_PASSWORD__", (New-RandomAlphaNumericSecret))
    Write-Utf8NoBom -Path $script:EnvFile -Content $content
    Write-Host "Created customer-specific secrets in Deploy\.env" -ForegroundColor Green
}

$environment = Read-DotEnv -Path $script:EnvFile
$imageMarker = Join-Path $script:DataRoot ".images-loaded"
if (-not (Test-Path -LiteralPath $imageMarker -PathType Leaf)) {
    $imageArchives = @(Get-ChildItem -LiteralPath (Join-Path $script:ReleaseRoot "Images") -Filter "*.tar" -File -ErrorAction SilentlyContinue)
    if ($imageArchives.Count -eq 0) {
        throw "No offline Docker image archives were found in the Images directory."
    }

    foreach ($archive in $imageArchives) {
        Write-Host "Loading Docker image: $($archive.Name)"
        & docker load --input $archive.FullName
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to load Docker image archive: $($archive.FullName)"
        }
    }
    Write-Utf8NoBom -Path $imageMarker -Content ((Get-Date).ToString("o"))
}

foreach ($imageKey in @("BACKEND_IMAGE", "POSTGRES_IMAGE", "NEO4J_IMAGE")) {
    $imageName = [string]$environment[$imageKey]
    & docker image inspect $imageName *> $null
    if ($LASTEXITCODE -ne 0) {
        throw "Required release image was not loaded: $imageName"
    }
}

if (-not $SkipServiceStart) {
    Invoke-ReleaseCompose -Arguments @("up", "-d", "backend")
    Wait-OntoTwinBackend -Port ([int]$environment["ONTOTWIN_HTTP_PORT"])
    Write-Host "OntoTwin backend and databases are ready." -ForegroundColor Green
}
