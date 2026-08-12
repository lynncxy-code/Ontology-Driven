[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$BaseApplianceDirectory,

    [Parameter(Mandatory = $true)]
    [string]$OutputDirectory,

    [string]$WslDistribution = "Ubuntu-22.04",

    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$ApplianceVersion
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$base = [System.IO.Path]::GetFullPath($BaseApplianceDirectory)
$output = [System.IO.Path]::GetFullPath($OutputDirectory)
$guestRoot = Join-Path $PSScriptRoot "guest"
$systemDiskSizeGb = 20
$minimumGuestRootSizeGb = 16
$minimumGuestRootFreeGb = 8

function Convert-ToWslPath {
    param([string]$WindowsPath)
    $fullPath = [System.IO.Path]::GetFullPath($WindowsPath)
    if ($fullPath -notmatch '^([A-Za-z]):[\\/](.*)$') {
        throw "Only local drive paths can be converted for the WSL build toolchain: $fullPath"
    }
    return "/mnt/$($Matches[1].ToLowerInvariant())/$($Matches[2].Replace('\', '/'))"
}

foreach ($required in @(
    "ontotwin-ubuntu.vhdx",
    "docker-static.tgz",
    "docker-compose",
    "appliance-manifest.json"
)) {
    $path = Join-Path $base $required
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Base appliance file is missing: $path"
    }
}
if (Test-Path -LiteralPath $output) {
    if (@(Get-ChildItem -LiteralPath $output -Force).Count -gt 0) {
        throw "OutputDirectory must be empty: $output"
    }
} else {
    New-Item -ItemType Directory -Path $output | Out-Null
}

foreach ($name in @("docker-static.tgz", "docker-compose")) {
    Copy-Item -LiteralPath (Join-Path $base $name) -Destination (Join-Path $output $name)
}
$outputVhdx = Join-Path $output "ontotwin-ubuntu.vhdx"
$baseVhdxLinux = Convert-ToWslPath (Join-Path $base "ontotwin-ubuntu.vhdx")
$outputVhdxLinux = Convert-ToWslPath $outputVhdx
$resizedSource = Join-Path $output "system-resize.qcow2"
$resizedSourceLinux = Convert-ToWslPath $resizedSource
& wsl.exe -d $WslDistribution -u root -- qemu-img convert -f vhdx -O qcow2 $baseVhdxLinux $resizedSourceLinux
if ($LASTEXITCODE -ne 0) { throw "Appliance VHDX staging conversion failed." }
& wsl.exe -d $WslDistribution -u root -- qemu-img resize $resizedSourceLinux "${systemDiskSizeGb}G"
if ($LASTEXITCODE -ne 0) { throw "Appliance system disk expansion failed." }
& wsl.exe -d $WslDistribution -u root -- qemu-img convert -f qcow2 -O vhdx `
    -o subformat=dynamic,block_size=2097152 $resizedSourceLinux $outputVhdxLinux
if ($LASTEXITCODE -ne 0) { throw "Expanded appliance VHDX conversion failed." }
Remove-Item -LiteralPath $resizedSource -Force
$vhdInfoText = (& wsl.exe -d $WslDistribution -u root -- qemu-img info --output=json $outputVhdxLinux) -join "`n"
if ($LASTEXITCODE -ne 0) { throw "Appliance VHDX capacity verification failed." }
$vhdInfo = $vhdInfoText | ConvertFrom-Json
if ([int64]$vhdInfo.'virtual-size' -ne [int64]$systemDiskSizeGb * 1GB) {
    throw "Appliance VHDX virtual capacity is not ${systemDiskSizeGb} GiB."
}

$temporary = Join-Path ([System.IO.Path]::GetTempPath()) ("ontotwin-seed-" + [Guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $temporary | Out-Null
try {
    foreach ($name in @("user-data", "meta-data", "network-config")) {
        $content = (Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $guestRoot "cloud-init\$name")).Replace("`r`n", "`n")
        [System.IO.File]::WriteAllText((Join-Path $temporary $name), $content, [System.Text.UTF8Encoding]::new($false))
    }
    $seedLinux = Convert-ToWslPath $temporary
    $isoPath = Join-Path $output "seed.iso"
    $isoLinux = Convert-ToWslPath $isoPath
    & wsl.exe -d $WslDistribution -u root -- genisoimage -quiet -output $isoLinux -volid cidata -joliet -rock `
        "$seedLinux/user-data" "$seedLinux/meta-data" "$seedLinux/network-config"
    if ($LASTEXITCODE -ne 0) { throw "Cloud-init seed ISO creation failed." }

    $manifest = Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $base "appliance-manifest.json") | ConvertFrom-Json
    if ([string]$manifest.version -eq $ApplianceVersion) {
        throw "The rebuilt seed must use a new appliance version so installed VMs refresh: $ApplianceVersion"
    }
    $manifest.version = $ApplianceVersion
    $manifest | Add-Member -NotePropertyName system_disk_size_gb -NotePropertyValue $systemDiskSizeGb -Force
    $manifest | Add-Member -NotePropertyName minimum_guest_root_size_gb -NotePropertyValue $minimumGuestRootSizeGb -Force
    $manifest | Add-Member -NotePropertyName minimum_guest_root_free_gb -NotePropertyValue $minimumGuestRootFreeGb -Force
    $manifest.system_vhdx_sha256 = (Get-FileHash -LiteralPath (Join-Path $output "ontotwin-ubuntu.vhdx") -Algorithm SHA256).Hash.ToLowerInvariant()
    $manifest.seed_iso_sha256 = (Get-FileHash -LiteralPath $isoPath -Algorithm SHA256).Hash.ToLowerInvariant()
    $manifest.generated_at = (Get-Date).ToString("o")
    [System.IO.File]::WriteAllText(
        (Join-Path $output "appliance-manifest.json"),
        ($manifest | ConvertTo-Json -Depth 4),
        [System.Text.UTF8Encoding]::new($false))
} finally {
    if (Test-Path -LiteralPath $temporary) {
        Remove-Item -LiteralPath $temporary -Recurse -Force
    }
}

Write-Host "Updated Hyper-V appliance seed created: $output" -ForegroundColor Green
