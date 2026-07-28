[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$BackupDirectory,

    [Parameter(Mandatory = $true)]
    [ValidateSet("RESTORE")]
    [string]$ConfirmRestore
)

. (Join-Path $PSScriptRoot "Common.ps1")

Assert-ExternalCommand -Name "docker"
if (-not (Test-Path -LiteralPath $script:EnvFile -PathType Leaf)) {
    throw "Release has not been initialized."
}

$backupRoot = [System.IO.Path]::GetFullPath($BackupDirectory)
$postgresDump = Join-Path $backupRoot "postgres.dump"
if (-not (Test-Path -LiteralPath $postgresDump -PathType Leaf)) {
    throw "PostgreSQL backup was not found: $postgresDump"
}

$manifestPath = Join-Path $backupRoot "backup-manifest.json"
if (Test-Path -LiteralPath $manifestPath -PathType Leaf) {
    $manifest = Get-Content -Raw -LiteralPath $manifestPath | ConvertFrom-Json
    $dumpEntry = @($manifest.files | Where-Object { $_.name -eq "postgres.dump" }) | Select-Object -First 1
    if ($dumpEntry) {
        $actualHash = (Get-FileHash -LiteralPath $postgresDump -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($actualHash -ne ([string]$dumpEntry.sha256).ToLowerInvariant()) {
            throw "PostgreSQL backup checksum validation failed."
        }
    }
}

$environment = Read-DotEnv -Path $script:EnvFile
$containerId = ([string](Invoke-ReleaseCompose -Arguments @("ps", "-q", "db") -CaptureOutput)).Trim()
if (-not $containerId) {
    throw "PostgreSQL container is not running. Start the system before restoring."
}

Write-Host "Creating a safety backup before restore..."
& (Join-Path $PSScriptRoot "Backup-OntoTwinZHHZ.ps1")
if ($LASTEXITCODE -ne 0) {
    throw "Safety backup failed; restore was cancelled."
}

& (Join-Path $PSScriptRoot "Stop-OntoTwinZHHZ.ps1") -KeepServices -ForceRuntime
if (Get-RecordedZHHZProcess) {
    throw "ZHHZ runtime could not be stopped; restore was cancelled."
}
Invoke-ReleaseCompose -Arguments @("stop", "backend")

$containerDump = "/tmp/ontotwin_restore.dump"
try {
    & docker cp $postgresDump "${containerId}:$containerDump"
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to copy PostgreSQL backup into the container."
    }

    $restoreArguments = @(
        "exec", $containerId, "pg_restore",
        "-U", $environment["POSTGRES_USER"],
        "-d", $environment["POSTGRES_DB"],
        "--clean", "--if-exists", "--exit-on-error",
        "--no-owner", "--no-privileges",
        $containerDump
    )
    & docker @restoreArguments
    if ($LASTEXITCODE -ne 0) {
        throw "PostgreSQL restore failed. Use the automatically created safety backup to recover."
    }

    $assetsArchive = Join-Path $backupRoot "project_assets.zip"
    if (Test-Path -LiteralPath $assetsArchive -PathType Leaf) {
        $assetsPath = Join-Path $script:DataRoot "project_assets"
        if (-not (Test-Path -LiteralPath $assetsPath -PathType Container)) {
            New-Item -ItemType Directory -Path $assetsPath | Out-Null
        }
        Get-ChildItem -LiteralPath $assetsPath -Force | Remove-Item -Recurse -Force
        Expand-Archive -LiteralPath $assetsArchive -DestinationPath $script:DataRoot -Force
    }
} finally {
    & docker exec $containerId rm -f $containerDump *> $null
    Invoke-ReleaseCompose -Arguments @("up", "-d", "backend")
}

Wait-OntoTwinBackend -Port ([int]$environment["ONTOTWIN_HTTP_PORT"])
Write-Host "Restore completed. Start ZHHZ from the launcher when ready." -ForegroundColor Green
