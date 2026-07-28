[CmdletBinding()]
param(
    [switch]$KeepServices,
    [switch]$ForceRuntime
)

. (Join-Path $PSScriptRoot "Common.ps1")

$runtimeProcesses = @(Get-ZHHZRuntimeProcesses)
foreach ($runtimeProcess in $runtimeProcesses) {
    $process = Get-Process -Id $runtimeProcess.ProcessId -ErrorAction SilentlyContinue
    if ($process -and $process.MainWindowHandle -ne 0) {
        [void]$process.CloseMainWindow()
    }
}

$deadline = (Get-Date).AddSeconds(10)
do {
    $remainingProcesses = @(Get-ZHHZRuntimeProcesses)
    if ($remainingProcesses.Count -eq 0) {
        break
    }
    Start-Sleep -Milliseconds 500
} while ((Get-Date) -lt $deadline)

if ($remainingProcesses.Count -gt 0 -and $ForceRuntime) {
    foreach ($remainingProcess in $remainingProcesses) {
        Stop-Process -Id $remainingProcess.ProcessId -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Milliseconds 500
    $remainingProcesses = @(Get-ZHHZRuntimeProcesses)
}

$runtimeStopped = $remainingProcesses.Count -eq 0
if (-not $runtimeStopped) {
    $remainingIds = ($remainingProcesses | Select-Object -ExpandProperty ProcessId) -join ", "
    Write-Warning "ZHHZ processes are still running (PID $remainingIds). Re-run with -ForceRuntime if required."
}

if ($runtimeStopped -and (Test-Path -LiteralPath $script:RuntimeStateFile)) {
    Remove-Item -LiteralPath $script:RuntimeStateFile -Force
}

if (-not $KeepServices -and (Test-Path -LiteralPath $script:EnvFile -PathType Leaf)) {
    Invoke-ReleaseCompose -Arguments @("stop")
}

Write-Host "OntoTwin ZHHZ stop request completed." -ForegroundColor Green
