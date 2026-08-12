[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$OutputDirectory,

    [string]$CacheDirectory = (Join-Path $PSScriptRoot ".cache"),
    [string]$WslDistribution = "Ubuntu-22.04",
    [string]$DockerVersion = "29.1.5",
    [string]$ComposeVersion = "5.1.4",
    [string]$ApplianceVersion = "3.7.1-r1-rc7-appliance3"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$output = [System.IO.Path]::GetFullPath($OutputDirectory)
$cache = [System.IO.Path]::GetFullPath($CacheDirectory)
$guestRoot = Join-Path $PSScriptRoot "guest"
$ubuntuName = "ubuntu-24.04-server-cloudimg-amd64.img"
$ubuntuBaseUrl = "https://cloud-images.ubuntu.com/releases/24.04/release"
$ubuntuUrl = "$ubuntuBaseUrl/$ubuntuName"
$dockerUrl = "https://download.docker.com/linux/static/stable/x86_64/docker-$DockerVersion.tgz"
$composeDebName = "docker-compose-plugin_$ComposeVersion-1~ubuntu.24.04~noble`_amd64.deb"
$composeUrl = "https://download.docker.com/linux/ubuntu/dists/noble/pool/stable/amd64/$composeDebName"
$composeExpectedHash = switch ($ComposeVersion) {
    "5.1.4" { "45ef136eeb23e2cfdef0e06592d3c2d8566172a5874169b35b446cf251080ecb" }
    default { throw "No pinned Docker Compose package hash is registered for version $ComposeVersion." }
}
$systemDiskSizeGb = 20
$minimumGuestRootSizeGb = 16
$minimumGuestRootFreeGb = 8

function Invoke-Download {
    param([string]$Uri, [string]$Path)
    if (Test-Path -LiteralPath $Path -PathType Leaf) { return }
    $partial = "$Path.partial"
    Write-Host "Downloading $Uri"
    & curl.exe --fail --location --retry 5 --retry-delay 2 --retry-all-errors `
        --continue-at - --output $partial $Uri
    if ($LASTEXITCODE -ne 0) { throw "Download failed: $Uri" }
    $moved = $false
    foreach ($attempt in 1..20) {
        try {
            Move-Item -LiteralPath $partial -Destination $Path -Force
            $moved = $true
            break
        } catch [System.IO.IOException] {
            if ($attempt -eq 20) { throw }
            Start-Sleep -Milliseconds 500
        }
    }
    if (-not $moved) { throw "Downloaded file could not be finalized: $Path" }
}

function Assert-Hash {
    param([string]$Path, [string]$Expected)
    $actual = (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $Expected.ToLowerInvariant()) {
        throw "SHA-256 mismatch for $Path. Expected $Expected, got $actual"
    }
}

function Convert-ToWslPath {
    param([string]$WindowsPath)
    $fullPath = [System.IO.Path]::GetFullPath($WindowsPath)
    if ($fullPath -notmatch '^([A-Za-z]):[\\/](.*)$') {
        throw "Only local drive paths can be converted for the WSL build toolchain: $fullPath"
    }
    $drive = $Matches[1].ToLowerInvariant()
    $tail = $Matches[2].Replace('\', '/')
    return "/mnt/$drive/$tail"
}

New-Item -ItemType Directory -Path $cache -Force | Out-Null
if (Test-Path -LiteralPath $output) {
    if (@(Get-ChildItem -LiteralPath $output -Force).Count -gt 0) {
        throw "OutputDirectory must be empty: $output"
    }
} else {
    New-Item -ItemType Directory -Path $output | Out-Null
}

$ubuntuArchive = Join-Path $cache $ubuntuName
$ubuntuSums = Join-Path $cache "ubuntu-SHA256SUMS"
$dockerArchive = Join-Path $cache "docker-$DockerVersion.tgz"
$composePackage = Join-Path $cache $composeDebName
Invoke-Download -Uri $ubuntuUrl -Path $ubuntuArchive
Invoke-Download -Uri "$ubuntuBaseUrl/SHA256SUMS" -Path $ubuntuSums
Invoke-Download -Uri $dockerUrl -Path $dockerArchive
Invoke-Download -Uri $composeUrl -Path $composePackage

$sumLine = Get-Content -LiteralPath $ubuntuSums | Where-Object { $_ -match "\s\*?$([regex]::Escape($ubuntuName))$" } | Select-Object -First 1
if (-not $sumLine) { throw "Ubuntu SHA256SUMS did not contain $ubuntuName" }
$ubuntuHash = ($sumLine -split '\s+')[0]
Assert-Hash -Path $ubuntuArchive -Expected $ubuntuHash
Assert-Hash -Path $composePackage -Expected $composeExpectedHash

$toolCheck = & wsl.exe -d $WslDistribution -u root -- bash -lc "command -v qemu-img >/dev/null && command -v genisoimage >/dev/null"
if ($LASTEXITCODE -ne 0) {
    throw "WSL build tools are missing. Install qemu-utils and genisoimage in $WslDistribution before building the appliance."
}

$temporary = Join-Path $cache ("work-" + [Guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $temporary | Out-Null
try {
    $outputVhdx = Join-Path $output "ontotwin-ubuntu.vhdx"
    $sourceLinux = Convert-ToWslPath $ubuntuArchive
    $outputLinux = Convert-ToWslPath $outputVhdx
    $resizedSource = Join-Path $temporary "ubuntu-resized.qcow2"
    $resizedSourceLinux = Convert-ToWslPath $resizedSource
    Write-Host "Preparing a ${systemDiskSizeGb} GiB Ubuntu source disk..."
    & wsl.exe -d $WslDistribution -u root -- qemu-img convert -f qcow2 -O qcow2 $sourceLinux $resizedSourceLinux
    if ($LASTEXITCODE -ne 0) { throw "Ubuntu cloud image staging failed." }
    & wsl.exe -d $WslDistribution -u root -- qemu-img resize $resizedSourceLinux "${systemDiskSizeGb}G"
    if ($LASTEXITCODE -ne 0) { throw "Ubuntu cloud image expansion failed." }
    Write-Host "Converting Ubuntu disk to dynamic VHDX..."
    & wsl.exe -d $WslDistribution -u root -- qemu-img convert -p -f qcow2 -O vhdx -o subformat=dynamic,block_size=2097152 $resizedSourceLinux $outputLinux
    if ($LASTEXITCODE -ne 0) { throw "Ubuntu cloud image to VHDX conversion failed." }
    $vhdInfoText = (& wsl.exe -d $WslDistribution -u root -- qemu-img info --output=json $outputLinux) -join "`n"
    if ($LASTEXITCODE -ne 0) { throw "Ubuntu VHDX capacity verification failed." }
    $vhdInfo = $vhdInfoText | ConvertFrom-Json
    if ([int64]$vhdInfo.'virtual-size' -ne [int64]$systemDiskSizeGb * 1GB) {
        throw "Ubuntu VHDX virtual capacity is not ${systemDiskSizeGb} GiB."
    }

    $seedDirectory = Join-Path $temporary "seed"
    New-Item -ItemType Directory -Path $seedDirectory | Out-Null
    foreach ($name in @("user-data", "meta-data", "network-config")) {
        $content = (Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $guestRoot "cloud-init\$name")).Replace("`r`n", "`n")
        [System.IO.File]::WriteAllText((Join-Path $seedDirectory $name), $content, [System.Text.UTF8Encoding]::new($false))
    }
    $seedLinux = Convert-ToWslPath $seedDirectory
    $isoLinux = Convert-ToWslPath (Join-Path $output "seed.iso")
    & wsl.exe -d $WslDistribution -u root -- genisoimage -quiet -output $isoLinux -volid cidata -joliet -rock `
        "$seedLinux/user-data" "$seedLinux/meta-data" "$seedLinux/network-config"
    if ($LASTEXITCODE -ne 0) { throw "Cloud-init seed ISO creation failed." }

    $composeExtract = Join-Path $temporary "compose-package"
    New-Item -ItemType Directory -Path $composeExtract | Out-Null
    $composePackageLinux = Convert-ToWslPath $composePackage
    $composeExtractLinux = Convert-ToWslPath $composeExtract
    & wsl.exe -d $WslDistribution -u root -- dpkg-deb -x $composePackageLinux $composeExtractLinux
    if ($LASTEXITCODE -ne 0) { throw "Docker Compose package extraction failed." }
    $composeBinary = Get-ChildItem -LiteralPath $composeExtract -Recurse -File -Filter "docker-compose" | Select-Object -First 1
    if (-not $composeBinary) { throw "Docker Compose package did not contain its CLI plugin binary." }

    Copy-Item -LiteralPath $dockerArchive -Destination (Join-Path $output "docker-static.tgz")
    Copy-Item -LiteralPath $composeBinary.FullName -Destination (Join-Path $output "docker-compose")

    $manifest = [ordered]@{
        version = $ApplianceVersion
        vm_generation = 2
        system_disk_size_gb = $systemDiskSizeGb
        minimum_guest_root_size_gb = $minimumGuestRootSizeGb
        minimum_guest_root_free_gb = $minimumGuestRootFreeGb
        data_disk_size_gb = 40
        guest_os = "Ubuntu Server 24.04 LTS"
        ubuntu_source = $ubuntuUrl
        ubuntu_sha256 = $ubuntuHash.ToLowerInvariant()
        docker_engine_version = $DockerVersion
        docker_engine_sha256 = (Get-FileHash -LiteralPath $dockerArchive -Algorithm SHA256).Hash.ToLowerInvariant()
        docker_compose_version = $ComposeVersion
        docker_compose_source = $composeUrl
        docker_compose_package_sha256 = $composeExpectedHash
        docker_compose_sha256 = (Get-FileHash -LiteralPath $composeBinary.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        system_vhdx_sha256 = (Get-FileHash -LiteralPath $outputVhdx -Algorithm SHA256).Hash.ToLowerInvariant()
        seed_iso_sha256 = (Get-FileHash -LiteralPath (Join-Path $output "seed.iso") -Algorithm SHA256).Hash.ToLowerInvariant()
        generated_at = (Get-Date).ToString("o")
    }
    [System.IO.File]::WriteAllText(
        (Join-Path $output "appliance-manifest.json"),
        ($manifest | ConvertTo-Json -Depth 4),
        [System.Text.UTF8Encoding]::new($false))
} finally {
    if (Test-Path -LiteralPath $temporary) {
        Remove-Item -LiteralPath $temporary -Recurse -Force
    }
}

Write-Host "Hyper-V appliance created: $output" -ForegroundColor Green
