Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$script:DeployRoot = Split-Path -Parent $PSScriptRoot
$script:ReleaseRoot = Split-Path -Parent $script:DeployRoot
$script:ComposeFile = Join-Path $script:DeployRoot "docker-compose.release.yml"
$script:EnvFile = Join-Path $script:DeployRoot ".env"
$script:EnvTemplate = Join-Path $script:DeployRoot "customer.env.example"
$script:DataRoot = Join-Path $script:ReleaseRoot "Data"
$script:RuntimeStateFile = Join-Path $script:DataRoot "zhhz-process.json"

function Assert-ExternalCommand {
    param([Parameter(Mandatory = $true)][string]$Name)

    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command was not found: $Name"
    }
}

function Assert-ReleaseLayout {
    foreach ($path in @($script:ComposeFile, $script:EnvTemplate)) {
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
            throw "Release file is missing: $path"
        }
    }

    $runtimeExe = Join-Path $script:ReleaseRoot "ZHHZ\ZHHZ.exe"
    if (-not (Test-Path -LiteralPath $runtimeExe -PathType Leaf)) {
        throw "ZHHZ runtime was not found: $runtimeExe"
    }

    $modelFiles = @(Get-ChildItem -LiteralPath (Join-Path $script:ReleaseRoot "Models") -Filter "*.glb" -File -ErrorAction SilentlyContinue)
    if ($modelFiles.Count -eq 0) {
        throw "No GLB models were found in the release Models directory."
    }

    $pgSeed = Join-Path $script:ReleaseRoot "Database\postgres\zhhz.dump"
    if (-not (Test-Path -LiteralPath $pgSeed -PathType Leaf)) {
        throw "PostgreSQL release seed was not found: $pgSeed"
    }

    foreach ($seedName in @("ontotwin.zhhz.cypher", "ontotwin.zhhz.extensions.cypher")) {
        $seedPath = Join-Path $script:ReleaseRoot "Database\neo4j\$seedName"
        if (-not (Test-Path -LiteralPath $seedPath -PathType Leaf)) {
            throw "Neo4j release seed was not found: $seedPath"
        }
    }
}

function Invoke-ReleaseCompose {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments,
        [switch]$CaptureOutput
    )

    if (-not (Test-Path -LiteralPath $script:EnvFile -PathType Leaf)) {
        throw "Release environment has not been initialized: $script:EnvFile"
    }

    $commandArguments = @("compose", "--env-file", $script:EnvFile, "-f", $script:ComposeFile) + $Arguments
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
}

function Read-DotEnv {
    param([Parameter(Mandatory = $true)][string]$Path)

    $values = @{}
    foreach ($line in Get-Content -LiteralPath $Path) {
        $trimmed = $line.Trim()
        if (-not $trimmed -or $trimmed.StartsWith("#")) {
            continue
        }
        $separator = $trimmed.IndexOf("=")
        if ($separator -le 0) {
            continue
        }
        $key = $trimmed.Substring(0, $separator).Trim()
        $value = $trimmed.Substring($separator + 1).Trim()
        $values[$key] = $value
    }
    return $values
}

function New-RandomAlphaNumericSecret {
    param([int]$Length = 32)

    $alphabet = "abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    $bytes = New-Object byte[] $Length
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try {
        $rng.GetBytes($bytes)
    } finally {
        $rng.Dispose()
    }

    $builder = New-Object System.Text.StringBuilder
    foreach ($value in $bytes) {
        [void]$builder.Append($alphabet[$value % $alphabet.Length])
    }
    return $builder.ToString()
}

function Write-Utf8NoBom {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Content
    )

    $encoding = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $Content, $encoding)
}

function Wait-OntoTwinBackend {
    param(
        [int]$Port = 5000,
        [int]$TimeoutSeconds = 180
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    $uri = "http://127.0.0.1:$Port/"
    do {
        try {
            $response = Invoke-WebRequest -UseBasicParsing -Uri $uri -TimeoutSec 5
            if ($response.StatusCode -eq 200) {
                return
            }
        } catch {
            Start-Sleep -Seconds 2
        }
    } while ((Get-Date) -lt $deadline)

    throw "OntoTwin backend did not become ready within $TimeoutSeconds seconds. Check docker compose logs."
}

function Get-ZHHZRuntimePath {
    return Join-Path $script:ReleaseRoot "ZHHZ\ZHHZ.exe"
}

function Get-ZHHZRuntimeProcesses {
    $runtimeDirectory = [System.IO.Path]::GetFullPath((Join-Path $script:ReleaseRoot "ZHHZ"))
    $runtimePrefix = $runtimeDirectory.TrimEnd([System.IO.Path]::DirectorySeparatorChar) + [System.IO.Path]::DirectorySeparatorChar
    return @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
        $_.ExecutablePath -and
        [System.IO.Path]::GetFullPath([string]$_.ExecutablePath).StartsWith(
            $runtimePrefix,
            [System.StringComparison]::OrdinalIgnoreCase)
    })
}

function Get-RecordedZHHZProcess {
    if (-not (Test-Path -LiteralPath $script:RuntimeStateFile -PathType Leaf)) {
        return $null
    }

    try {
        $state = Get-Content -Raw -LiteralPath $script:RuntimeStateFile | ConvertFrom-Json
        $process = Get-CimInstance Win32_Process -Filter "ProcessId=$($state.pid)" -ErrorAction SilentlyContinue
        if (-not $process) {
            return $null
        }

        $expected = [System.IO.Path]::GetFullPath((Get-ZHHZRuntimePath))
        $actual = [System.IO.Path]::GetFullPath([string]$process.ExecutablePath)
        if (-not $actual.Equals($expected, [System.StringComparison]::OrdinalIgnoreCase)) {
            return $null
        }

        return $process
    } catch {
        return $null
    }
}
