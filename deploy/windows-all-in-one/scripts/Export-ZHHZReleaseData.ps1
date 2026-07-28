[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$OutputDirectory,

    [string]$ProjectId = "ds_1784694647848",
    [string]$SourceDatabase = "ontotwin",
    [string]$SourceDatabaseUser = "ontotwin"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ($ProjectId -notmatch '^[A-Za-z0-9_.:-]+$') {
    throw "ProjectId contains unsupported characters: $ProjectId"
}

$repositoryRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot "..\..\.."))
$sourceCompose = Join-Path $repositoryRoot "docker-compose.yml"
if (-not (Test-Path -LiteralPath $sourceCompose -PathType Leaf)) {
    throw "Source docker-compose.yml was not found: $sourceCompose"
}

$outputRoot = [System.IO.Path]::GetFullPath($OutputDirectory)
$postgresOutput = Join-Path $outputRoot "postgres"
$neo4jOutput = Join-Path $outputRoot "neo4j"
$assetsOutput = Join-Path $outputRoot "project_assets"
foreach ($directory in @($outputRoot, $postgresOutput, $neo4jOutput, $assetsOutput)) {
    if (-not (Test-Path -LiteralPath $directory)) {
        New-Item -ItemType Directory -Path $directory | Out-Null
    }
}

function Invoke-SourceCompose {
    param(
        [Parameter(Mandatory = $true)][string[]]$Arguments,
        [switch]$CaptureOutput
    )

    Push-Location $repositoryRoot
    try {
        $commandArguments = @("compose", "-f", $sourceCompose) + $Arguments
        if ($CaptureOutput) {
            $output = & docker @commandArguments
            if ($LASTEXITCODE -ne 0) {
                throw "docker compose failed with exit code $LASTEXITCODE"
            }
            return $output
        }
        & docker @commandArguments
        if ($LASTEXITCODE -ne 0) {
            throw "docker compose failed with exit code $LASTEXITCODE"
        }
    } finally {
        Pop-Location
    }
}

& docker info *> $null
if ($LASTEXITCODE -ne 0) {
    throw "Docker Desktop is not running."
}

$dbContainer = ([string](Invoke-SourceCompose -Arguments @("ps", "-q", "db") -CaptureOutput)).Trim()
if (-not $dbContainer) {
    throw "Source PostgreSQL container is not running."
}

$projectExists = ([string](Invoke-SourceCompose -Arguments @(
    "exec", "-T", "db", "psql", "-U", $SourceDatabaseUser, "-d", $SourceDatabase,
    "-At", "-c", "SELECT count(*) FROM project WHERE id='$ProjectId' AND deleted_at IS NULL;"
) -CaptureOutput)).Trim()
if ($projectExists -ne "1") {
    throw "Expected exactly one active project '$ProjectId', found: $projectExists"
}

$temporaryDatabase = "ontotwin_release_" + ([Guid]::NewGuid().ToString("N").Substring(0, 12))
$containerDump = "/tmp/$temporaryDatabase.dump"

try {
    Invoke-SourceCompose -Arguments @(
        "exec", "-T", "db", "createdb", "-U", $SourceDatabaseUser, $temporaryDatabase
    )

    $cloneCommand = "set -eu; pg_dump -U '$SourceDatabaseUser' -d '$SourceDatabase' --no-owner --no-privileges | psql -v ON_ERROR_STOP=1 -U '$SourceDatabaseUser' -d '$temporaryDatabase'"
    Invoke-SourceCompose -Arguments @("exec", "-T", "db", "sh", "-lc", $cloneCommand)

    $cleanupSql = "BEGIN; DELETE FROM project WHERE id <> '$ProjectId'; INSERT INTO app_singleton(k,v) VALUES ('active_project_id','$ProjectId') ON CONFLICT(k) DO UPDATE SET v=EXCLUDED.v; COMMIT;"
    Invoke-SourceCompose -Arguments @(
        "exec", "-T", "db", "psql", "-v", "ON_ERROR_STOP=1", "-U", $SourceDatabaseUser,
        "-d", $temporaryDatabase, "-c", $cleanupSql
    )

    $countsCsv = ([string](Invoke-SourceCompose -Arguments @(
        "exec", "-T", "db", "psql", "-U", $SourceDatabaseUser, "-d", $temporaryDatabase,
        "-At", "-F", ",", "-c",
        "SELECT (SELECT count(*) FROM project),(SELECT count(*) FROM object_type WHERE deleted_at IS NULL),(SELECT count(*) FROM instance WHERE deleted_at IS NULL),(SELECT count(*) FROM zone WHERE deleted_at IS NULL),(SELECT v FROM app_singleton WHERE k='active_project_id');"
    ) -CaptureOutput)).Trim()
    $countParts = $countsCsv.Split(',')
    if ($countParts.Count -ne 5 -or $countParts[0] -ne "1" -or $countParts[4] -ne $ProjectId) {
        throw "Unexpected ZHHZ release database counts: $countsCsv"
    }

    Invoke-SourceCompose -Arguments @(
        "exec", "-T", "db", "pg_dump", "-U", $SourceDatabaseUser, "-d", $temporaryDatabase,
        "-Fc", "--no-owner", "--no-privileges", "-f", $containerDump
    )

    $hostDump = Join-Path $postgresOutput "zhhz.dump"
    & docker cp "${dbContainer}:$containerDump" $hostDump
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to copy the filtered PostgreSQL dump from the container."
    }
} finally {
    & docker exec $dbContainer rm -f $containerDump *> $null
    Invoke-SourceCompose -Arguments @(
        "exec", "-T", "db", "dropdb", "--if-exists", "-U", $SourceDatabaseUser, $temporaryDatabase
    )
}

$registryRoot = Join-Path $repositoryRoot "backend\ontology_registry"
$neo4jSources = @{
    "ontotwin.zhhz.cypher" = Join-Path $registryRoot "ontotwin.$ProjectId.cypher"
    "ontotwin.zhhz.extensions.cypher" = Join-Path $registryRoot "ontotwin.$ProjectId.extensions.cypher"
    "ontotwin.zhhz.ontology.json" = Join-Path $registryRoot "ontotwin.$ProjectId.ontology.json"
}
foreach ($entry in $neo4jSources.GetEnumerator()) {
    if (-not (Test-Path -LiteralPath $entry.Value -PathType Leaf)) {
        throw "ZHHZ Neo4j registry artifact is missing: $($entry.Value)"
    }
    Copy-Item -LiteralPath $entry.Value -Destination (Join-Path $neo4jOutput $entry.Key) -Force
}

$sourceAssets = Join-Path $repositoryRoot "backend\data\project_assets\$ProjectId"
if (Test-Path -LiteralPath $sourceAssets -PathType Container) {
    $destinationAssets = Join-Path $assetsOutput $ProjectId
    if (-not (Test-Path -LiteralPath $destinationAssets)) {
        New-Item -ItemType Directory -Path $destinationAssets | Out-Null
    }
    Copy-Item -Path (Join-Path $sourceAssets "*") -Destination $destinationAssets -Recurse -Force
}

$releaseFiles = @(Get-ChildItem -LiteralPath $outputRoot -Recurse -File | ForEach-Object {
    [ordered]@{
        path = $_.FullName.Substring($outputRoot.Length + 1).Replace('\', '/')
        bytes = $_.Length
        sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    }
})
$manifest = [ordered]@{
    generated_at = (Get-Date).ToString("o")
    project_id = $ProjectId
    project_name = "ZHHZ"
    postgres = [ordered]@{
        projects = [int]$countParts[0]
        object_types = [int]$countParts[1]
        instances = [int]$countParts[2]
        zones = [int]$countParts[3]
        active_project_id = $countParts[4]
    }
    neo4j_source = "clean initialization from ZHHZ ontology registry"
    files = $releaseFiles
}
$encoding = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText(
    (Join-Path $outputRoot "data-manifest.json"),
    ($manifest | ConvertTo-Json -Depth 6),
    $encoding
)

Write-Host "ZHHZ release data exported: $outputRoot" -ForegroundColor Green
Write-Host "PostgreSQL counts: $countsCsv"
