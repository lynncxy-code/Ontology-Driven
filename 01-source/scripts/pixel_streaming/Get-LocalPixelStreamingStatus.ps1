[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$stateRoot = Join-Path $env:LOCALAPPDATA "OntoTwin\PixelStreaming"
$stateFile = Join-Path $stateRoot "local-session.json"

if (-not (Test-Path -LiteralPath $stateFile -PathType Leaf)) {
    Write-Host "No local Pixel Streaming session has been recorded."
    return
}

$state = Get-Content -Raw -LiteralPath $stateFile | ConvertFrom-Json
$serverRunning = [bool](Get-Process -Id $state.server_pid -ErrorAction SilentlyContinue)
$runtimeRoot = Split-Path -Parent ([string]$state.runtime_exe)
$runtimeProcesses = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
    $_.ExecutablePath -and
    $_.ExecutablePath.StartsWith($runtimeRoot, [System.StringComparison]::OrdinalIgnoreCase) -and
    $_.CommandLine -like "*-PixelStreamingURL=$($state.streamer_url)*"
})
$runtimeRunning = $runtimeProcesses.Count -gt 0
$runtimeProcessIds = @($runtimeProcesses | Select-Object -ExpandProperty ProcessId -ErrorAction SilentlyContinue)
$playerListening = [bool](Get-NetTCPConnection -LocalPort $state.player_port -State Listen -ErrorAction SilentlyContinue)
$streamerListening = [bool](Get-NetTCPConnection -LocalPort $state.streamer_port -State Listen -ErrorAction SilentlyContinue)
$streamerRegistered = $false
$subscriberCount = 0
try {
    $streamers = @(Invoke-RestMethod -Uri "$($state.player_url)api/streamers" -TimeoutSec 2)
    $streamer = $streamers | Where-Object { $_.streamerId -eq "DefaultStreamer" } | Select-Object -First 1
    if ($streamer) {
        $streamerRegistered = $true
        $subscriberCount = @($streamer.subscribers).Count
    }
} catch {}

[pscustomobject]@{
    StartedAt = $state.started_at
    ServerRunning = $serverRunning
    RuntimeRunning = $runtimeRunning
    RuntimeProcessIds = ($runtimeProcessIds -join ", ")
    PlayerListening = $playerListening
    StreamerListening = $streamerListening
    StreamerRegistered = $streamerRegistered
    SubscriberCount = $subscriberCount
    PlayerUrl = $state.player_url
    StreamerUrl = $state.streamer_url
    SignallingStdout = $state.stdout_log
    SignallingStderr = $state.stderr_log
} | Format-List
