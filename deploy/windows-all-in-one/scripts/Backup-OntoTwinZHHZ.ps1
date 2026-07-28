[CmdletBinding()]
param()

. (Join-Path $PSScriptRoot "Common.ps1")

Assert-ExternalCommand -Name "docker"
if (-not (Test-Path -LiteralPath $script:EnvFile -PathType Leaf)) {
    throw "Release has not been initialized."
}

$environment = Read-DotEnv -Path $script:EnvFile
$stamp = Get-Date -Format "yyyyMMdd_HHmmss_fff"
$backupRoot = Join-Path $script:ReleaseRoot "Backups\$stamp"
New-Item -ItemType Directory -Path $backupRoot | Out-Null

$containerId = ([string](Invoke-ReleaseCompose -Arguments @("ps", "-q", "db") -CaptureOutput)).Trim()
if (-not $containerId) {
    throw "PostgreSQL container is not running."
}

$containerDump = "/tmp/ontotwin_customer_$stamp.dump"
$dumpArguments = @(
    "exec", $containerId, "pg_dump",
    "-U", $environment["POSTGRES_USER"],
    "-d", $environment["POSTGRES_DB"],
    "-Fc", "--no-owner", "--no-privileges",
    "-f", $containerDump
)
& docker @dumpArguments
if ($LASTEXITCODE -ne 0) {
    throw "PostgreSQL backup failed."
}

$hostDump = Join-Path $backupRoot "postgres.dump"
try {
    & docker cp "${containerId}:$containerDump" $hostDump
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to copy PostgreSQL backup from the container."
    }
} finally {
    & docker exec $containerId rm -f $containerDump *> $null
}

$assetsPath = Join-Path $script:DataRoot "project_assets"
if (Test-Path -LiteralPath $assetsPath) {
    Compress-Archive -Path $assetsPath -DestinationPath (Join-Path $backupRoot "project_assets.zip") -CompressionLevel Optimal
}

$files = @(Get-ChildItem -LiteralPath $backupRoot -File | ForEach-Object {
    [ordered]@{
        name = $_.Name
        bytes = $_.Length
        sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    }
})
$manifest = [ordered]@{
    created_at = (Get-Date).ToString("o")
    release_data_version = $environment["ONTOTWIN_DATA_VERSION"]
    includes = @("PostgreSQL", "project_assets")
    neo4j_restore_source = "Database/neo4j release seed"
    files = $files
}
Write-Utf8NoBom -Path (Join-Path $backupRoot "backup-manifest.json") -Content ($manifest | ConvertTo-Json -Depth 5)

Write-Host "Backup created: $backupRoot" -ForegroundColor Green
