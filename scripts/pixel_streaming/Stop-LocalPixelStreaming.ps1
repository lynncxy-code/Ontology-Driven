[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$stateRoot = Join-Path $env:LOCALAPPDATA "OntoTwin\PixelStreaming"
$stateFile = Join-Path $stateRoot "local-session.json"

function Stop-ProcessTree {
    param([int]$ProcessId)

    $children = Get-CimInstance Win32_Process -Filter "ParentProcessId=$ProcessId" -ErrorAction SilentlyContinue
    foreach ($child in $children) {
        Stop-ProcessTree -ProcessId $child.ProcessId
    }
    Stop-Process -Id $ProcessId -Force -ErrorAction SilentlyContinue
}

if (-not (Test-Path -LiteralPath $stateFile -PathType Leaf)) {
    Write-Host "No local Pixel Streaming session has been recorded."
    return
}

$state = Get-Content -Raw -LiteralPath $stateFile | ConvertFrom-Json

if ($state.runtime_pid) {
    Stop-ProcessTree -ProcessId ([int]$state.runtime_pid)
}

$runtimeRoot = Split-Path -Parent ([string]$state.runtime_exe)
$runtimeProcesses = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
    $_.ExecutablePath -and
    $_.ExecutablePath.StartsWith($runtimeRoot, [System.StringComparison]::OrdinalIgnoreCase) -and
    $_.CommandLine -match 'PixelStreamingURL='
}
foreach ($process in $runtimeProcesses) {
    Stop-ProcessTree -ProcessId $process.ProcessId
}

$serverProcess = Get-CimInstance Win32_Process -Filter "ProcessId=$($state.server_pid)" -ErrorAction SilentlyContinue
if ($serverProcess -and $serverProcess.CommandLine -match 'SignallingWebServer|dist[/\\]index\.js') {
    Stop-ProcessTree -ProcessId ([int]$state.server_pid)
}

Remove-Item -LiteralPath $stateFile -Force
Write-Host "Local Pixel Streaming session stopped." -ForegroundColor Green
