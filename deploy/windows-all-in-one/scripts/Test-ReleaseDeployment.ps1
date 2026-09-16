[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$ExportDirectory,

    [string]$BackendImage = "ontotwin-zhhz/backend:3.7.1-r1-test",
    [string]$PostgresImage = "postgres:16",
    [string]$Neo4jImage = "neo4j:5",
    [string]$ProjectId = "",
    [int]$ExpectedInstanceCount = -1,
    [string]$UeProjectId = "",
    [string]$UeProjectName = "",
    [string]$PackagedReleaseDirectory = "",
    [string]$RuntimeExecutable = "",
    [string]$RuntimeResultPath = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$templateRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$exportRoot = [System.IO.Path]::GetFullPath($ExportDirectory)
if (-not (Test-Path -LiteralPath (Join-Path $exportRoot "postgres\zhhz.dump") -PathType Leaf)) {
    throw "ZHHZ PostgreSQL export was not found under: $exportRoot"
}
$dataManifestPath = Join-Path $exportRoot "data-manifest.json"
if (-not (Test-Path -LiteralPath $dataManifestPath -PathType Leaf)) {
    throw "Release data manifest was not found: $dataManifestPath"
}
$dataManifest = Get-Content -Raw -Encoding UTF8 -LiteralPath $dataManifestPath | ConvertFrom-Json
if ([string]::IsNullOrWhiteSpace($ProjectId)) { $ProjectId = [string]$dataManifest.project_id }
if ($ExpectedInstanceCount -lt 0) { $ExpectedInstanceCount = [int]$dataManifest.postgres.instances }
if ([string]::IsNullOrWhiteSpace($UeProjectName)) { $UeProjectName = [string]$dataManifest.project_name }
if ([string]::IsNullOrWhiteSpace($UeProjectId)) { $UeProjectId = "ueproj_$UeProjectName" }

$suffix = [Guid]::NewGuid().ToString("N").Substring(0, 12)
$projectName = "ontotwin-zhhz-test-$suffix"
$stagingRoot = Join-Path ([System.IO.Path]::GetTempPath()) $projectName
$deployRoot = Join-Path $stagingRoot "Deploy"
$composeFile = Join-Path $deployRoot "docker-compose.release.yml"
$envFile = Join-Path $deployRoot ".env"
$httpPort = Get-Random -Minimum 15000 -Maximum 30000

function Invoke-TestCompose {
    param([Parameter(Mandatory = $true)][string[]]$Arguments)

    $allArguments = @(
        "compose", "-p", $projectName,
        "--env-file", $envFile,
        "-f", $composeFile
    ) + $Arguments
    & docker @allArguments
    if ($LASTEXITCODE -ne 0) {
        throw "Test docker compose command failed with exit code $LASTEXITCODE"
    }
}

try {
    foreach ($directory in @(
        $stagingRoot,
        $deployRoot,
        (Join-Path $stagingRoot "Models"),
        (Join-Path $stagingRoot "Database\postgres"),
        (Join-Path $stagingRoot "Database\neo4j"),
        (Join-Path $stagingRoot "Data\project_assets"),
        (Join-Path $stagingRoot "Data\exports"),
        (Join-Path $stagingRoot "Backups")
    )) {
        New-Item -ItemType Directory -Path $directory -Force | Out-Null
    }

    $composeSource = Join-Path $templateRoot "docker-compose.release.yml"
    $restoreSource = Join-Path $templateRoot "database\postgres\01-restore.sh"
    $scriptsSource = Join-Path $templateRoot "scripts"
    if ($PackagedReleaseDirectory) {
        $composeSource = Join-Path $PackagedReleaseDirectory "Deploy\docker-compose.release.yml"
        $restoreSource = Join-Path $PackagedReleaseDirectory "Database\postgres\01-restore.sh"
        $packagedScripts = Join-Path $PackagedReleaseDirectory "Deploy\scripts"
        # The slim Linux payload omits Windows support scripts. In that case
        # use the local test harness for the disposable backup/restore check.
        if (Test-Path -LiteralPath $packagedScripts -PathType Container) { $scriptsSource = $packagedScripts }
    }
    Copy-Item -LiteralPath $composeSource -Destination $composeFile
    Copy-Item -LiteralPath $restoreSource -Destination (Join-Path $stagingRoot "Database\postgres")
    Copy-Item -LiteralPath (Join-Path $exportRoot "postgres\zhhz.dump") -Destination (Join-Path $stagingRoot "Database\postgres")
    Copy-Item -Path (Join-Path $exportRoot "neo4j\*") -Destination (Join-Path $stagingRoot "Database\neo4j") -Force
    Copy-Item -LiteralPath $scriptsSource -Destination $deployRoot -Recurse

    $sourceAssets = Join-Path $exportRoot "project_assets"
    if (Test-Path -LiteralPath $sourceAssets -PathType Container) {
        Copy-Item -Path (Join-Path $sourceAssets "*") -Destination (Join-Path $stagingRoot "Data\project_assets") -Recurse -Force
    }

    # The backend only needs the mount to exist for this service validation.
    $modelMarker = Join-Path $stagingRoot "Models\deployment-test.glb"
    [System.IO.File]::WriteAllBytes($modelMarker, [byte[]]@(0x67, 0x6c, 0x54, 0x46))

    $passwordSuffix = [Guid]::NewGuid().ToString("N")
    $environment = @"
BACKEND_IMAGE=$BackendImage
POSTGRES_IMAGE=$PostgresImage
NEO4J_IMAGE=$Neo4jImage
ONTOTWIN_DATA_VERSION=zhhz-test-$suffix
ONTOTWIN_HTTP_PORT=$httpPort
POSTGRES_USER=ontotwin
POSTGRES_PASSWORD=Pg$passwordSuffix
POSTGRES_DB=ontotwin
NEO4J_USER=neo4j
NEO4J_PASSWORD=Neo$passwordSuffix
ARTSTUDIO_ENABLED=false
ARTSTUDIO_BASE_URL=
ARTSTUDIO_TOKEN=
ONTOTWIN_MIDDLEWARE_ENABLED=false
ONTOTWIN_MIDDLEWARE_URL=
ONTOTWIN_MEDIA_ALLOWED_HOSTS=
ONTOTWIN_MEDIA_HTTP_EXCEPTIONS=
"@
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($envFile, $environment, $utf8NoBom)

    Invoke-TestCompose -Arguments @("config", "--quiet")
    Invoke-TestCompose -Arguments @("up", "-d", "backend")

    $deadline = (Get-Date).AddMinutes(4)
    $baseUri = "http://127.0.0.1:$httpPort"
    $root = $null
    do {
        try {
            $root = Invoke-WebRequest -UseBasicParsing -Uri "$baseUri/" -TimeoutSec 5
            if ($root.StatusCode -eq 200) { break }
        } catch {
            Start-Sleep -Seconds 2
        }
    } while ((Get-Date) -lt $deadline)
    if (-not $root -or $root.StatusCode -ne 200) {
        throw "Release backend did not become ready."
    }

    $memoryLimits = @{}
    foreach ($serviceName in @("backend", "db", "neo4j")) {
        $serviceIdArguments = @(
            "compose", "-p", $projectName, "--env-file", $envFile, "-f", $composeFile,
            "ps", "-q", $serviceName
        )
        $serviceId = ([string](& docker @serviceIdArguments)).Trim()
        if ($LASTEXITCODE -ne 0 -or -not $serviceId) {
            throw "Could not resolve the $serviceName container for memory-limit validation."
        }
        $memoryLimit = [long](& docker inspect --format "{{.HostConfig.Memory}}" $serviceId)
        if ($LASTEXITCODE -ne 0) {
            throw "Could not inspect the $serviceName container memory limit."
        }
        $memoryLimits[$serviceName] = $memoryLimit
    }
    if ($memoryLimits["backend"] -ne 2GB -or $memoryLimits["db"] -ne 1GB -or $memoryLimits["neo4j"] -ne 2GB) {
        throw "Release container memory limits do not match the 2 GB / 1 GB / 2 GB policy."
    }

    $datasets = Invoke-RestMethod -Uri "$baseUri/api/v2/ontology/datasets" -TimeoutSec 20
    $snapshots = Invoke-WebRequest -UseBasicParsing -Uri "$baseUri/api/v2/state/snapshots" -TimeoutSec 30
    $registry = Invoke-RestMethod -Uri "$baseUri/api/v2/ontology/registry" -TimeoutSec 20
    $ueHeaders = @{
        "X-OntoTwin-UE-Project-Id" = $UeProjectId
        "X-OntoTwin-UE-Project-Name" = $UeProjectName
    }
    $deltaReset = Invoke-WebRequest -UseBasicParsing -Uri "$baseUri/api/v2/state/snapshot_changes" -Headers $ueHeaders -TimeoutSec 30
    $deltaResetBody = $deltaReset.Content | ConvertFrom-Json
    $deltaNoopParameters = @{
        UseBasicParsing = $true
        Uri = "$baseUri/api/v2/state/snapshot_changes?cursor=$([Uri]::EscapeDataString($deltaResetBody.cursor))"
        Headers = $ueHeaders
        TimeoutSec = 30
    }
    $deltaNoop = Invoke-WebRequest @deltaNoopParameters
    $deltaNoopBody = $deltaNoop.Content | ConvertFrom-Json
    if ($deltaResetBody.mode -ne "reset" -or $deltaNoopBody.mode -ne "delta" -or @($deltaNoopBody.upserts).Count -ne 0) {
        throw "Incremental snapshot reset/delta contract validation failed."
    }

    $postgresArguments = @(
        "compose", "-p", $projectName, "--env-file", $envFile, "-f", $composeFile,
        "exec", "-T", "db", "psql", "-U", "ontotwin", "-d", "ontotwin",
        "-At", "-F", ",", "-c",
        "SELECT (SELECT count(*) FROM project),(SELECT count(*) FROM object_type WHERE deleted_at IS NULL),(SELECT count(*) FROM instance WHERE deleted_at IS NULL),(SELECT v FROM app_singleton WHERE k='active_project_id');"
    )
    $postgresCounts = & docker @postgresArguments
    if ($LASTEXITCODE -ne 0) { throw "PostgreSQL release query failed." }

    # Regression gate for the semantic-graph database switch bug. Switching to
    # Demo and back to ZHHZ must not rewrite type capability configuration or
    # instance-level overrides in PostgreSQL.
    $configHashSql = @"
SELECT
  md5(string_agg(rid || ':' || data::text, '|' ORDER BY rid)),
  (SELECT md5(string_agg(id || ':' || render_config::text, '|' ORDER BY id))
     FROM instance
    WHERE project_id='$ProjectId' AND deleted_at IS NULL)
FROM object_type
WHERE project_id='$ProjectId' AND deleted_at IS NULL;
"@
    $configHashArguments = @(
        "compose", "-p", $projectName, "--env-file", $envFile, "-f", $composeFile,
        "exec", "-T", "db", "psql", "-U", "ontotwin", "-d", "ontotwin",
        "-At", "-F", ",", "-c", $configHashSql
    )
    $configHashesBefore = ([string](& docker @configHashArguments)).Trim()
    if ($LASTEXITCODE -ne 0 -or -not $configHashesBefore) {
        throw "Could not capture the pre-switch ZHHZ configuration hashes."
    }
    Invoke-RestMethod -Method Post -Uri "$baseUri/api/v2/ontology/datasets/activate" `
        -ContentType "application/json" -Body '{"dataset_id":"demo"}' -TimeoutSec 20 | Out-Null
    $switchBack = Invoke-RestMethod -Method Post -Uri "$baseUri/api/v2/ontology/datasets/activate" `
        -ContentType "application/json" -Body (@{dataset_id=$ProjectId} | ConvertTo-Json -Compress) -TimeoutSec 20
    $configHashesAfter = ([string](& docker @configHashArguments)).Trim()
    if ($LASTEXITCODE -ne 0 -or $configHashesAfter -ne $configHashesBefore -or
        $switchBack.active -ne $ProjectId) {
        throw "Dataset switch regression: ZHHZ type or instance configuration was rewritten."
    }

    if ($RuntimeExecutable) {
        if (-not $RuntimeResultPath) { throw "RuntimeResultPath is required for a runtime acceptance run." }
        $RuntimeResultPath = [IO.Path]::GetFullPath($RuntimeResultPath)
        if (Test-Path -LiteralPath $RuntimeResultPath) { throw "A fresh runtime result path is required; refusing to reuse prior evidence." }
        New-Item -ItemType Directory -Path (Split-Path -Parent $RuntimeResultPath) -Force | Out-Null
        $runtimeProcess = Start-Process -FilePath $RuntimeExecutable -PassThru -WindowStyle Hidden -ArgumentList @(
            '-NullRHI', '-nosound', '-Unattended', '-OntoTwinDisplaySchemesSelfTest',
            "-OntoTwinBackendBaseUrl=$baseUri", "-OntoTwinSelfTestOutput=`"$RuntimeResultPath`""
        )
        if (-not $runtimeProcess.WaitForExit(660000)) {
            Stop-Process -Id $runtimeProcess.Id -Force -ErrorAction SilentlyContinue
            throw "Packaged UE scheme acceptance timed out."
        }
        if (-not (Test-Path -LiteralPath $RuntimeResultPath -PathType Leaf)) {
            throw "UE exited without a selftest result; process exit alone is not acceptance."
        }
        $runtimeResult = Get-Content -LiteralPath $RuntimeResultPath -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($runtimeProcess.ExitCode -ne 0 -or $runtimeResult.passed -ne $true -or
            @($runtimeResult.checks | Where-Object { $_.passed -ne $true }).Count -ne 0 -or
            @($runtimeResult.checks).Count -lt 50 -or $runtimeResult.backend_url -ne $baseUri -or
            $runtimeResult.ue_project_id -ne $UeProjectId) {
            throw "Packaged UE scheme acceptance failed. Read $RuntimeResultPath"
        }
        [ordered]@{
            executable = [IO.Path]::GetFullPath($RuntimeExecutable)
            executable_sha256 = (Get-FileHash -LiteralPath $RuntimeExecutable -Algorithm SHA256).Hash
            seed_sha256 = (Get-FileHash -LiteralPath (Join-Path $exportRoot 'postgres\zhhz.dump') -Algorithm SHA256).Hash
            backend_image = $BackendImage
            project_id = $ProjectId
            result = $RuntimeResultPath
            passed = $true
        } | ConvertTo-Json | Set-Content -LiteralPath "$RuntimeResultPath.provenance.json" -Encoding UTF8
        Write-Host "Packaged UE scheme acceptance: PASS ($(@($runtimeResult.checks).Count) checks)."
    }

    $neo4jArguments = @(
        "compose", "-p", $projectName, "--env-file", $envFile, "-f", $composeFile,
        "exec", "-T", "neo4j", "cypher-shell", "-u", "neo4j", "-p", "Neo$passwordSuffix",
        "MATCH (n) WITH count(n) AS nodes MATCH ()-[r]->() RETURN nodes, count(r) AS relationships;"
    )
    $neo4jCounts = & docker @neo4jArguments
    if ($LASTEXITCODE -ne 0) { throw "Neo4j release query failed." }

    $previousComposeProjectName = $env:COMPOSE_PROJECT_NAME
    $env:COMPOSE_PROJECT_NAME = $projectName
    try {
        & (Join-Path $deployRoot "scripts\Backup-OntoTwinZHHZ.ps1")
        $testBackup = Get-ChildItem -LiteralPath (Join-Path $stagingRoot "Backups") -Directory |
            Sort-Object LastWriteTime -Descending |
            Select-Object -First 1
        if (-not $testBackup) {
            throw "Customer backup script did not create a backup."
        }

        $deleteArguments = @(
            "compose", "-p", $projectName, "--env-file", $envFile, "-f", $composeFile,
            "exec", "-T", "db", "psql", "-U", "ontotwin", "-d", "ontotwin",
            "-v", "ON_ERROR_STOP=1", "-c", "DELETE FROM instance;"
        )
        & docker @deleteArguments
        if ($LASTEXITCODE -ne 0) { throw "Restore test could not mutate the disposable database." }

        & (Join-Path $deployRoot "scripts\Restore-OntoTwinZHHZ.ps1") `
            -BackupDirectory $testBackup.FullName `
            -ConfirmRestore RESTORE

        $restoredCountArguments = @(
            "compose", "-p", $projectName, "--env-file", $envFile, "-f", $composeFile,
            "exec", "-T", "db", "psql", "-U", "ontotwin", "-d", "ontotwin",
            "-At", "-c", "SELECT count(*) FROM instance WHERE deleted_at IS NULL;"
        )
        $restoredInstanceCount = ([string](& docker @restoredCountArguments)).Trim()
        if ($LASTEXITCODE -ne 0 -or $restoredInstanceCount -ne [string]$ExpectedInstanceCount) {
            throw "Customer restore script did not restore the expected $ExpectedInstanceCount active instances."
        }
    } finally {
        $env:COMPOSE_PROJECT_NAME = $previousComposeProjectName
    }

    $datasetRows = @($datasets)
    $activeDataset = @($datasetRows | Where-Object { $_.is_active }) | Select-Object -First 1
    if (-not $activeDataset -or $activeDataset.id -ne $ProjectId) {
        throw "ZHHZ is not the active release dataset."
    }

    [pscustomobject]@{
        Project = $activeDataset.id
        DatasetCount = $datasetRows.Count
        SnapshotBytes = $snapshots.RawContentLength
        IncrementalResetBytes = $deltaReset.RawContentLength
        IncrementalNoChangeBytes = $deltaNoop.RawContentLength
        RestoredInstances = $restoredInstanceCount
        DatasetSwitch = "Demo -> ZHHZ preserved type and instance configuration"
        MemoryLimitsGB = "backend=$($memoryLimits['backend'] / 1GB), db=$($memoryLimits['db'] / 1GB), neo4j=$($memoryLimits['neo4j'] / 1GB)"
        PostgreSQL = ([string]$postgresCounts).Trim()
        Neo4j = (([string[]]$neo4jCounts) -join " | ")
        BackendImage = $BackendImage
        HttpPort = $httpPort
    } | Format-List
} finally {
    if (Test-Path -LiteralPath $envFile -PathType Leaf) {
        $previousErrorActionPreference = $ErrorActionPreference
        $ErrorActionPreference = "Continue"
        try {
            & docker compose -p $projectName --env-file $envFile -f $composeFile down -v --remove-orphans *> $null
        } catch {
            # Test resources are uniquely prefixed; a failed cleanup is reported by the next orphan audit.
        } finally {
            $ErrorActionPreference = $previousErrorActionPreference
        }
    }
    if ($stagingRoot.StartsWith([System.IO.Path]::GetTempPath(), [System.StringComparison]::OrdinalIgnoreCase) -and
        (Split-Path -Leaf $stagingRoot).StartsWith("ontotwin-zhhz-test-")) {
        Remove-Item -LiteralPath $stagingRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}
