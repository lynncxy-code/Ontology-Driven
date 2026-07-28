[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = [Security.Principal.WindowsPrincipal]::new($identity)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw "The installer must run as administrator."
}

$os = Get-CimInstance Win32_OperatingSystem
if ([int]$os.ProductType -ne 1) {
    throw "This release supports Windows 10/11 Pro, Enterprise, or Education workstations only; Windows Server is not supported."
}
$caption = [string]$os.Caption
if ($caption -notmatch "Windows 10|Windows 11" -or $caption -match "Home") {
    throw "This Windows edition does not provide the required Hyper-V feature. Use Windows 10/11 Pro, Enterprise, or Education."
}

$cpu = Get-CimInstance Win32_Processor | Select-Object -First 1
$computer = Get-CimInstance Win32_ComputerSystem
if (-not [bool]$cpu.VirtualizationFirmwareEnabled -and -not [bool]$computer.HypervisorPresent) {
    throw "CPU virtualization (Intel VT-x or AMD-V) is disabled in BIOS/UEFI. Enable it and run setup again."
}

$features = @(
    "Microsoft-Hyper-V-All",
    "Microsoft-Hyper-V-Management-PowerShell"
)
$restartRequired = $false
foreach ($feature in $features) {
    $state = Get-WindowsOptionalFeature -Online -FeatureName $feature
    if ($state.State -ne "Enabled") {
        $result = Enable-WindowsOptionalFeature -Online -FeatureName $feature -All -NoRestart
        if ($result.RestartNeeded) { $restartRequired = $true }
    }
}

if ($restartRequired) { exit 3010 }
exit 0
