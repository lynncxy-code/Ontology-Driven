[CmdletBinding()]
param(
    [switch]$NoBrowser
)

. (Join-Path $PSScriptRoot "Common.ps1")

& (Join-Path $PSScriptRoot "Initialize-Release.ps1")

$environment = Read-DotEnv -Path $script:EnvFile
$existingProcesses = @(Get-ZHHZRuntimeProcesses)
if ($existingProcesses.Count -gt 0) {
    $existingIds = ($existingProcesses | Select-Object -ExpandProperty ProcessId) -join ", "
    Write-Host "ZHHZ is already running (PID $existingIds)." -ForegroundColor Yellow
} else {
    $runtimePath = Get-ZHHZRuntimePath
    $startParameters = @{
        FilePath = $runtimePath
        WorkingDirectory = Split-Path -Parent $runtimePath
        ArgumentList = @(
            "-OntoTwinBackendBaseUrl=http://127.0.0.1:$($environment["ONTOTWIN_HTTP_PORT"])",
            "-OntoTwinRealtimeWebSocket=false",
            "-OntoTwinPollInterval=2.0"
        )
        PassThru = $true
    }
    $runtime = Start-Process @startParameters

    $state = [ordered]@{
        pid = $runtime.Id
        executable = $runtimePath
        started_at = (Get-Date).ToString("o")
        realtime_websocket = $false
    }
    Write-Utf8NoBom -Path $script:RuntimeStateFile -Content ($state | ConvertTo-Json)
    Write-Host "ZHHZ started (PID $($runtime.Id))." -ForegroundColor Green
}

if (-not $NoBrowser) {
    $port = [int]$environment["ONTOTWIN_HTTP_PORT"]
    Start-Process "http://127.0.0.1:$port/nexus"
}
