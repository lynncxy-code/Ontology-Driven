[CmdletBinding()]
param()

. (Join-Path $PSScriptRoot "Common.ps1")

$checks = New-Object System.Collections.Generic.List[object]
function Add-Check {
    param(
        [Parameter(Mandatory = $true)][string]$Item,
        [Parameter(Mandatory = $true)][ValidateSet("PASS", "WARN", "FAIL")][string]$Status,
        [Parameter(Mandatory = $true)][string]$Detail
    )
    $checks.Add([pscustomobject]@{ Item = $Item; Status = $Status; Detail = $Detail })
}

$os = Get-CimInstance Win32_OperatingSystem
$is64Bit = [Environment]::Is64BitOperatingSystem
Add-Check -Item "Windows" -Status $(if ($is64Bit) { "PASS" } else { "FAIL" }) `
    -Detail "$($os.Caption) $($os.Version), x64=$is64Bit"

$computer = Get-CimInstance Win32_ComputerSystem
$ramGB = [math]::Round([double]$computer.TotalPhysicalMemory / 1GB, 1)
Add-Check -Item "Memory" -Status $(if ($ramGB -ge 32) { "PASS" } elseif ($ramGB -ge 24) { "WARN" } else { "FAIL" }) `
    -Detail "$ramGB GB installed; 32 GB minimum for the all-in-one runtime"

$cpu = Get-CimInstance Win32_Processor | Select-Object -First 1
Add-Check -Item "CPU" -Status $(if ([int]$cpu.NumberOfLogicalProcessors -ge 8) { "PASS" } else { "WARN" }) `
    -Detail "$($cpu.Name.Trim()), $($cpu.NumberOfCores) cores / $($cpu.NumberOfLogicalProcessors) logical processors"

$virtualizationReady = [bool]$cpu.VirtualizationFirmwareEnabled -or [bool]$computer.HypervisorPresent
Add-Check -Item "Virtualization" -Status $(if ($virtualizationReady) { "PASS" } else { "FAIL" }) `
    -Detail $(if ($virtualizationReady) { "Firmware virtualization or a Windows hypervisor is active" } else { "Enable Intel VT-x/AMD-V in BIOS/UEFI for Docker Desktop" })

$releaseDrive = [System.IO.Path]::GetPathRoot($script:ReleaseRoot).TrimEnd('\')
$drive = Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='$releaseDrive'"
$freeGB = if ($drive) { [math]::Round([double]$drive.FreeSpace / 1GB, 1) } else { 0 }
Add-Check -Item "Free disk" -Status $(if ($freeGB -ge 30) { "PASS" } elseif ($freeGB -ge 20) { "WARN" } else { "FAIL" }) `
    -Detail "$freeGB GB free on $releaseDrive; keep at least 30 GB for images, volumes and backups"

$nvidiaGpu = Get-CimInstance Win32_VideoController | Where-Object { $_.Name -match "NVIDIA" } | Select-Object -First 1
if (-not $nvidiaGpu) {
    Add-Check -Item "NVIDIA GPU" -Status "FAIL" -Detail "No NVIDIA display adapter detected"
} else {
    $gpuDetail = "$($nvidiaGpu.Name), driver $($nvidiaGpu.DriverVersion)"
    $nvidiaSmi = Get-Command "nvidia-smi" -ErrorAction SilentlyContinue
    if ($nvidiaSmi) {
        $vramText = (& $nvidiaSmi.Source --query-gpu=memory.total --format=csv,noheader,nounits 2>$null | Select-Object -First 1)
        $vramMB = 0
        [void][int]::TryParse(([string]$vramText).Trim(), [ref]$vramMB)
        $gpuStatus = if ($vramMB -ge 8192) { "PASS" } else { "WARN" }
        Add-Check -Item "NVIDIA GPU" -Status $gpuStatus -Detail "$gpuDetail, $vramMB MB VRAM; 8 GB is the v1 minimum"
    } else {
        Add-Check -Item "NVIDIA GPU" -Status "WARN" -Detail "$gpuDetail; VRAM could not be verified because nvidia-smi was unavailable"
    }
}

$docker = Get-Command "docker" -ErrorAction SilentlyContinue
if (-not $docker) {
    Add-Check -Item "Docker Desktop" -Status "FAIL" -Detail "docker.exe not found; install Docker Desktop with the WSL 2 backend"
} else {
    $dockerVersion = (& docker version --format '{{.Server.Version}}' 2>$null)
    if ($LASTEXITCODE -eq 0 -and $dockerVersion) {
        Add-Check -Item "Docker Desktop" -Status "PASS" -Detail "Engine $dockerVersion is running"
    } else {
        Add-Check -Item "Docker Desktop" -Status "FAIL" -Detail "Docker is installed but the engine is not running"
    }

    $composeVersion = (& docker compose version --short 2>$null)
    Add-Check -Item "Docker Compose" -Status $(if ($LASTEXITCODE -eq 0 -and $composeVersion) { "PASS" } else { "FAIL" }) `
        -Detail $(if ($composeVersion) { "Compose $composeVersion" } else { "Docker Compose v2 is unavailable" })
}

$port = 5000
if (Test-Path -LiteralPath $script:EnvFile -PathType Leaf) {
    $environment = Read-DotEnv -Path $script:EnvFile
    if ($environment.ContainsKey("ONTOTWIN_HTTP_PORT")) {
        $port = [int]$environment["ONTOTWIN_HTTP_PORT"]
    }
}
$listeners = @(Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue)
if ($listeners.Count -eq 0) {
    Add-Check -Item "Local port" -Status "PASS" -Detail "127.0.0.1:$port is available"
} else {
    Add-Check -Item "Local port" -Status "WARN" -Detail "Port $port is already listening; this is expected only when OntoTwin is already running"
}

$checks | Format-Table -AutoSize -Wrap
$failures = @($checks | Where-Object { $_.Status -eq "FAIL" })
$warnings = @($checks | Where-Object { $_.Status -eq "WARN" })
Write-Host "Environment check: $($failures.Count) failure(s), $($warnings.Count) warning(s)."
if ($failures.Count -gt 0) {
    exit 2
}
