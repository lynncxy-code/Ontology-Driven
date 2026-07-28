[CmdletBinding()]
param()

. (Join-Path $PSScriptRoot "Common.ps1")

$runtimeProcesses = @(Get-ZHHZRuntimeProcesses)
$backendReady = $false
$consoleUrl = $null

if (Test-Path -LiteralPath $script:EnvFile -PathType Leaf) {
    $environment = Read-DotEnv -Path $script:EnvFile
    $port = [int]$environment["ONTOTWIN_HTTP_PORT"]
    $consoleUrl = "http://127.0.0.1:$port/nexus"
    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:$port/" -TimeoutSec 3
        $backendReady = $response.StatusCode -eq 200
    } catch {}

    Invoke-ReleaseCompose -Arguments @("ps")
} else {
    Write-Warning "Release has not been initialized yet."
}

[pscustomobject]@{
    ZHHZRunning = $runtimeProcesses.Count -gt 0
    ZHHZProcessId = if ($runtimeProcesses.Count -gt 0) { ($runtimeProcesses.ProcessId -join ", ") } else { $null }
    BackendReady = $backendReady
    ConsoleUrl = $consoleUrl
    RealtimeWebSocket = "disabled"
} | Format-List
