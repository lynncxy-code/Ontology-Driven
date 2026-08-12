[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("Provision", "Start", "Stop", "Status", "Remove")]
    [string]$Action,

    [string]$AppRoot = (Join-Path $PSScriptRoot "..\..\App"),
    [string]$DataRoot = "",
    [switch]$PurgeData
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$vmName = "OntoTwin-ZHHZ-Backend"
$switchName = "OntoTwin-ZHHZ"
$natName = "OntoTwin-ZHHZ-NAT"
$hostAddress = "172.28.251.1"
$guestAddress = "172.28.251.2"
$networkPrefix = "172.28.251.0/24"
$backendPort = 5000
$guestControlPort = 49274
$payloadPort = 48075
$payloadFirewallRuleName = "OntoTwin-ZHHZ-Payload"
$legacyDataRoot = [System.IO.Path]::GetFullPath((Join-Path $env:ProgramData "OntoTwin-ZHHZ"))
$newDataRootFreeBytes = 50GB
$existingDataRootFreeBytes = 20GB
$systemDiskRefreshSafetyBytes = 1GB
$minimumSystemDiskBytes = 20GB

if ([string]::IsNullOrWhiteSpace($DataRoot)) {
    $configuredDataRoot = $null
    try {
        $configuredDataRoot = [string](Get-ItemPropertyValue `
            -LiteralPath "HKLM:\SOFTWARE\OntoTwin\ZHHZ" `
            -Name "DataRoot" `
            -ErrorAction Stop)
    } catch {}
    $DataRoot = if ([string]::IsNullOrWhiteSpace($configuredDataRoot)) {
        $legacyDataRoot
    } else {
        $configuredDataRoot
    }
}

$app = [System.IO.Path]::GetFullPath($AppRoot)
if ($DataRoot -notmatch '^[A-Za-z]:[\\/]') {
    throw "The configured backend DataRoot is not an absolute drive path: $DataRoot"
}
$data = [System.IO.Path]::GetFullPath($DataRoot)
$vmRoot = Join-Path $data "VM"
$systemDisk = Join-Path $vmRoot "system.vhdx"
$stagedSystemDisk = Join-Path $vmRoot "system.installing.vhdx"
$dataDisk = Join-Path $vmRoot "data.vhdx"
$versionMarker = Join-Path $vmRoot "appliance.version"
$pendingVersionMarker = Join-Path $vmRoot "appliance.pending"
$applianceRoot = Join-Path $app "Appliance"
$manifestPath = Join-Path $applianceRoot "appliance-manifest.json"
$baseDisk = Join-Path $applianceRoot "ontotwin-ubuntu.vhdx"
$seedIso = Join-Path $applianceRoot "seed.iso"
$tokenPath = Join-Path $data "control.token"

function Assert-Administrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]::new($identity)
    if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw "OntoTwin backend management requires administrator or LocalSystem privileges."
    }
}

function Assert-HyperV {
    if (-not (Get-Command Get-VM -ErrorAction SilentlyContinue)) {
        throw "Hyper-V management is not enabled. Run OntoTwin ZHHZ Setup again and complete the required Windows restart."
    }
}

function Get-DataRootDrive {
    $root = [System.IO.Path]::GetPathRoot($data)
    if ([string]::IsNullOrWhiteSpace($root)) {
        throw "The configured backend DataRoot has no volume root: $data"
    }
    $drive = [System.IO.DriveInfo]::new($root)
    if (-not $drive.IsReady -or
        $drive.DriveType -ne [System.IO.DriveType]::Fixed -or
        -not $drive.DriveFormat.Equals("NTFS", [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "The backend DataRoot volume must be a ready fixed NTFS volume. DataRoot=$data; Volume=$root"
    }
    return $drive
}

function Assert-OrdinaryDataDirectory {
    param([Parameter(Mandatory = $true)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) { return }
    $item = Get-Item -LiteralPath $Path -Force
    if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw "The backend DataRoot cannot use a reparse point: $Path"
    }
}

function Assert-DataRootConfiguration {
    $drive = Get-DataRootDrive
    $driveRoot = [System.IO.Path]::GetFullPath($drive.RootDirectory.FullName).TrimEnd("\")
    $systemRoot = [System.IO.Path]::GetFullPath(
        [System.IO.Path]::GetPathRoot($legacyDataRoot)).TrimEnd("\")
    $normalizedData = $data.TrimEnd("\")
    $normalizedLegacy = $legacyDataRoot.TrimEnd("\")
    $dataDirectory = [System.IO.DirectoryInfo]::new($normalizedData)
    $productDirectory = $dataDirectory.Parent
    $productParent = if ($productDirectory) { $productDirectory.Parent } else { $null }
    $isLegacy = $normalizedData.Equals(
        $normalizedLegacy,
        [System.StringComparison]::OrdinalIgnoreCase)
    $isExternalCanonical = -not $driveRoot.Equals(
            $systemRoot,
            [System.StringComparison]::OrdinalIgnoreCase) -and
        $dataDirectory.Name.Equals("Data", [System.StringComparison]::OrdinalIgnoreCase) -and
        $productDirectory -and
        $productDirectory.Name.Equals("OntoTwin-ZHHZ", [System.StringComparison]::OrdinalIgnoreCase) -and
        $productParent -and
        ([System.IO.Path]::GetFullPath($productParent.FullName).TrimEnd("\")).Equals(
            $driveRoot,
            [System.StringComparison]::OrdinalIgnoreCase)
    if (-not $isLegacy -and -not $isExternalCanonical) {
        throw "The backend DataRoot is outside an approved OntoTwin data directory: $data"
    }
    if ($productDirectory) { Assert-OrdinaryDataDirectory -Path $productDirectory.FullName }
    Assert-OrdinaryDataDirectory -Path $data
}

function Assert-DataRootCapacity {
    param(
        [int64]$AdditionalRequiredBytes = 0,
        [string]$AdditionalReason = ""
    )

    if ($AdditionalRequiredBytes -lt 0) {
        throw "AdditionalRequiredBytes cannot be negative."
    }
    $drive = Get-DataRootDrive
    $hasDataDisk = Test-Path -LiteralPath $dataDisk -PathType Leaf
    $baseRequired = if ($hasDataDisk) { [int64]$existingDataRootFreeBytes } else { [int64]$newDataRootFreeBytes }
    $required = $baseRequired + $AdditionalRequiredBytes
    $reason = if ($hasDataDisk) {
        "existing VM/database operation at startup"
    } else {
        "new 40 GB data-disk provisioning at startup (the application payload is already installed)"
    }
    if ($AdditionalRequiredBytes -gt 0) {
        $additionalGiB = [math]::Round($AdditionalRequiredBytes / 1GB, 1)
        $reason += "; ${additionalGiB} GiB additional reserve for $AdditionalReason"
    }
    if ([int64]$drive.AvailableFreeSpace -lt $required) {
        $availableGiB = [math]::Round([int64]$drive.AvailableFreeSpace / 1GB, 1)
        $requiredGiB = [math]::Round($required / 1GB, 1)
        throw "Insufficient free space on the backend data volume. " +
            "DataRoot=$data; Volume=$($drive.Name); Available=${availableGiB} GiB; " +
            "Required=${requiredGiB} GiB for $reason. Existing customer data was not moved or modified."
    }
}

function Read-ApplianceManifest {
    if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
        throw "The backend appliance manifest is missing: $manifestPath"
    }
    if (-not (Test-Path -LiteralPath $baseDisk -PathType Leaf)) {
        throw "The backend appliance system disk is missing: $baseDisk"
    }
    if (-not (Test-Path -LiteralPath $seedIso -PathType Leaf)) {
        throw "The backend appliance seed media is missing: $seedIso"
    }
    $manifest = Get-Content -Raw -Encoding UTF8 -LiteralPath $manifestPath | ConvertFrom-Json
    if ([int]$manifest.system_disk_size_gb -ne 20 -or
        [int]$manifest.minimum_guest_root_size_gb -ne 16 -or
        [int]$manifest.minimum_guest_root_free_gb -ne 8) {
        throw "The appliance capacity contract must be system disk/root/root-free = 20/16/8 GiB."
    }
    return $manifest
}

function Get-ApplianceFingerprint {
    param([Parameter(Mandatory = $true)][object]$Manifest)

    $version = ([string]$Manifest.version).Trim()
    $systemHash = ([string]$Manifest.system_vhdx_sha256).Trim().ToLowerInvariant()
    $seedHash = ([string]$Manifest.seed_iso_sha256).Trim().ToLowerInvariant()
    $systemDiskSizeGb = [int]$Manifest.system_disk_size_gb
    if ([string]::IsNullOrWhiteSpace($version) -or
        [string]::IsNullOrWhiteSpace($systemHash) -or
        [string]::IsNullOrWhiteSpace($seedHash)) {
        throw "The backend appliance manifest does not contain a complete version/disk/seed fingerprint."
    }
    return "$version|$systemHash|$seedHash|system-disk-${systemDiskSizeGb}gb"
}

function Ensure-ControlToken {
    if (Test-Path -LiteralPath $tokenPath -PathType Leaf) {
        return ([string](Get-Content -Raw -LiteralPath $tokenPath)).Trim()
    }
    New-Item -ItemType Directory -Path $data -Force | Out-Null
    $bytes = New-Object byte[] 32
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try { $rng.GetBytes($bytes) } finally { $rng.Dispose() }
    # Windows PowerShell 5.1 runs on .NET Framework, where
    # Convert.ToHexString is unavailable. BitConverter works on both the
    # customer baseline and newer PowerShell/.NET runtimes.
    $token = [BitConverter]::ToString($bytes).Replace("-", "").ToLowerInvariant()
    [System.IO.File]::WriteAllText($tokenPath, $token, [System.Text.UTF8Encoding]::new($false))
    & icacls.exe $tokenPath /inheritance:r /grant:r "SYSTEM:(F)" "Administrators:(F)" *> $null
    return $token
}

function Get-BackendPortProxyEntries {
    $output = @(& netsh.exe interface portproxy show v4tov4 2>&1)
    if ($LASTEXITCODE -ne 0) {
        throw "Unable to inspect Windows portproxy configuration (netsh exit code $LASTEXITCODE)."
    }

    $entries = @()
    foreach ($line in $output) {
        if ([string]$line -match '^\s*(\S+)\s+(\d+)\s+(\S+)\s+(\d+)\s*$') {
            $entries += [pscustomobject]@{
                ListenAddress = [string]$matches[1]
                ListenPort = [int]$matches[2]
                ConnectAddress = [string]$matches[3]
                ConnectPort = [int]$matches[4]
            }
        }
    }
    return @($entries)
}

function Get-BackendListenPortProxyEntries {
    param([Parameter(Mandatory = $true)][AllowEmptyCollection()][object[]]$Entries)

    return @($Entries | Where-Object {
        $_.ListenAddress -eq "127.0.0.1" -and [int]$_.ListenPort -eq $backendPort
    })
}

function Test-ProductBackendPortProxy {
    param([Parameter(Mandatory = $true)][AllowEmptyCollection()][object[]]$Entries)

    $listenEntries = @(Get-BackendListenPortProxyEntries -Entries $Entries)
    return $listenEntries.Count -eq 1 -and
        $listenEntries[0].ConnectAddress -eq $guestAddress -and
        [int]$listenEntries[0].ConnectPort -eq $backendPort
}

function Get-BackendPortListenerDescription {
    $listeners = @(Get-NetTCPConnection -State Listen -LocalPort $backendPort -ErrorAction SilentlyContinue |
        Where-Object { $_.LocalAddress -in @("127.0.0.1", "0.0.0.0", "::", "::1") })
    if ($listeners.Count -eq 0) { return "" }

    $owners = @($listeners | ForEach-Object {
        $listener = $_
        $processName = "unknown"
        try { $processName = (Get-Process -Id $listener.OwningProcess -ErrorAction Stop).ProcessName } catch {}
        "PID=$($listener.OwningProcess), Process=$processName, Address=$($listener.LocalAddress)"
    } | Sort-Object -Unique)
    return $owners -join "; "
}

function Ensure-BackendPortProxy {
    $entries = @(Get-BackendPortProxyEntries)
    if (Test-ProductBackendPortProxy -Entries $entries) { return }

    $listenEntries = @(Get-BackendListenPortProxyEntries -Entries $entries)
    if ($listenEntries.Count -gt 0) {
        $mapping = @($listenEntries | ForEach-Object {
            "$($_.ListenAddress):$($_.ListenPort) -> $($_.ConnectAddress):$($_.ConnectPort)"
        }) -join "; "
        throw "TCP port $backendPort is owned by a different Windows portproxy mapping: $mapping. " +
            "OntoTwin did not modify the existing mapping."
    }

    $listenerDescription = Get-BackendPortListenerDescription
    if (-not [string]::IsNullOrWhiteSpace($listenerDescription)) {
        throw "TCP port $backendPort is already listening ($listenerDescription). " +
            "Stop or reconfigure that program, then retry. OntoTwin did not modify the existing listener."
    }

    & netsh.exe interface portproxy add v4tov4 listenaddress=127.0.0.1 listenport=$backendPort `
        connectaddress=$guestAddress connectport=$backendPort | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Unable to reserve TCP port $backendPort for the OntoTwin backend (netsh exit code $LASTEXITCODE)."
    }
    $verifiedEntries = @(Get-BackendPortProxyEntries)
    if (-not (Test-ProductBackendPortProxy -Entries $verifiedEntries)) {
        throw "Windows did not retain the expected OntoTwin portproxy mapping for TCP port $backendPort."
    }
}

function Remove-ProductBackendPortProxy {
    $entries = @(Get-BackendPortProxyEntries)
    if (-not (Test-ProductBackendPortProxy -Entries $entries)) {
        $listenEntries = @(Get-BackendListenPortProxyEntries -Entries $entries)
        if ($listenEntries.Count -gt 0) {
            Write-Warning "TCP port $backendPort has a non-OntoTwin portproxy mapping; it was preserved."
        }
        return
    }

    & netsh.exe interface portproxy delete v4tov4 listenaddress=127.0.0.1 `
        listenport=$backendPort | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Unable to remove the OntoTwin portproxy mapping for TCP port $backendPort."
    }
}

function Ensure-Network {
    $switch = Get-VMSwitch -Name $switchName -ErrorAction SilentlyContinue
    if (-not $switch) {
        $switch = New-VMSwitch -Name $switchName -SwitchType Internal
    } elseif ([string]$switch.SwitchType -ne "Internal") {
        throw "A Hyper-V switch named '$switchName' already exists but is not an Internal switch. " +
            "OntoTwin did not modify the existing switch."
    }

    $adapter = Get-NetAdapter -Name "vEthernet ($switchName)" -ErrorAction SilentlyContinue
    if (-not $adapter) {
        throw "The OntoTwin Hyper-V internal network adapter was not found."
    }

    $address = Get-NetIPAddress -InterfaceIndex $adapter.ifIndex -AddressFamily IPv4 -ErrorAction SilentlyContinue |
        Where-Object { $_.IPAddress -eq $hostAddress }
    if (-not $address) {
        New-NetIPAddress -InterfaceIndex $adapter.ifIndex -IPAddress $hostAddress -PrefixLength 24 | Out-Null
    }

    $nat = Get-NetNat -Name $natName -ErrorAction SilentlyContinue
    if (-not $nat) {
        New-NetNat -Name $natName -InternalIPInterfaceAddressPrefix $networkPrefix | Out-Null
    } elseif ($nat.InternalIPInterfaceAddressPrefix -ne $networkPrefix) {
        throw "A NAT with the same name but a different network prefix already exists: $natName"
    }

    $payloadRule = Get-NetFirewallRule -Name $payloadFirewallRuleName -ErrorAction SilentlyContinue
    if (-not $payloadRule) {
        $payloadRule = New-NetFirewallRule -Name $payloadFirewallRuleName `
            -DisplayName "OntoTwin ZHHZ backend payload" -Direction Inbound -Action Allow `
            -Enabled True -Profile Any -Protocol TCP -LocalPort $payloadPort `
            -LocalAddress $hostAddress -RemoteAddress $guestAddress
    } else {
        Set-NetFirewallRule -Name $payloadFirewallRuleName -Direction Inbound -Action Allow `
            -Enabled True -Profile Any | Out-Null
        $payloadRule | Get-NetFirewallPortFilter | Set-NetFirewallPortFilter `
            -Protocol TCP -LocalPort $payloadPort -RemotePort Any | Out-Null
        $payloadRule | Get-NetFirewallAddressFilter | Set-NetFirewallAddressFilter `
            -LocalAddress $hostAddress -RemoteAddress $guestAddress | Out-Null
    }

    & sc.exe config iphlpsvc start= auto *> $null
    & sc.exe start iphlpsvc *> $null
    Ensure-BackendPortProxy
}

function Stop-RegisteredVmGracefully {
    param(
        [Parameter(Mandatory = $true)]
        [object]$Vm,
        [int]$TimeoutSeconds = 90,
        [switch]$AllowTurnOff
    )

    if ($Vm.State -eq "Off") { return $Vm }

    $shutdownRequested = $false
    if (Test-Path -LiteralPath $tokenPath -PathType Leaf) {
        try {
            $token = ([string](Get-Content -Raw -LiteralPath $tokenPath)).Trim()
            if (-not [string]::IsNullOrWhiteSpace($token)) {
                Invoke-RestMethod -Method Post -Uri "http://${guestAddress}:$guestControlPort/shutdown" `
                    -Headers @{ "X-OntoTwin-Token" = $token } -TimeoutSec 10 | Out-Null
                $shutdownRequested = $true
            }
        } catch {
            Write-Verbose "Guest shutdown endpoint was unavailable: $($_.Exception.Message)"
        }
    }

    if (-not $shutdownRequested) {
        try {
            # Stop-VM without -TurnOff uses the Hyper-V shutdown integration
            # service. -Force suppresses confirmation; it is not a power cut.
            Stop-VM -Name $Vm.Name -Force -Confirm:$false -ErrorAction Stop
            $shutdownRequested = $true
        } catch {
            Write-Verbose "Hyper-V graceful shutdown request failed: $($_.Exception.Message)"
        }
    }

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        Start-Sleep -Milliseconds 500
        $Vm = Get-VM -Name $Vm.Name -ErrorAction Stop
    } while ($Vm.State -ne "Off" -and (Get-Date) -lt $deadline)

    if ($Vm.State -ne "Off") {
        if (-not $AllowTurnOff) {
            throw "The OntoTwin backend VM did not shut down gracefully within $TimeoutSeconds seconds. " +
                "The appliance refresh was cancelled to protect the database disk. Stop the system and retry."
        }
        Write-Warning "The OntoTwin backend VM did not shut down gracefully; turning it off for explicit removal."
        Stop-VM -Name $Vm.Name -TurnOff -Force -Confirm:$false -ErrorAction Stop
        $Vm = Get-VM -Name $Vm.Name -ErrorAction Stop
    }
    return $Vm
}

function Remove-RegisteredVm {
    param([switch]$AllowTurnOff)

    $vm = Get-VM -Name $vmName -ErrorAction SilentlyContinue
    if (-not $vm) { return }
    if ($vm.State -ne "Off") {
        $vm = Stop-RegisteredVmGracefully -Vm $vm -AllowTurnOff:$AllowTurnOff
    }
    Remove-VM -Name $vmName -Force
}

function Test-SamePath {
    param(
        [string]$Left,
        [string]$Right
    )
    if ([string]::IsNullOrWhiteSpace($Left) -or [string]::IsNullOrWhiteSpace($Right)) {
        return $false
    }
    return [System.IO.Path]::GetFullPath($Left).TrimEnd("\") -ieq
        [System.IO.Path]::GetFullPath($Right).TrimEnd("\")
}

function Get-FreeScsiLocation {
    param(
        [string]$TargetVmName,
        [int]$ControllerNumber = 0
    )
    $usedLocations = @{}
    $drives = @(
        @(Get-VMHardDiskDrive -VMName $TargetVmName -ErrorAction SilentlyContinue)
        @(Get-VMDvdDrive -VMName $TargetVmName -ErrorAction SilentlyContinue)
    )
    foreach ($drive in $drives) {
        if ([string]$drive.ControllerType -eq "SCSI" -and
            [int]$drive.ControllerNumber -eq $ControllerNumber) {
            $usedLocations[[int]$drive.ControllerLocation] = $true
        }
    }
    foreach ($location in 0..63) {
        if (-not $usedLocations.ContainsKey($location)) { return $location }
    }
    throw "No free SCSI location is available for the OntoTwin backend VM."
}

function Ensure-VmStorage {
    param([object]$Vm)

    $hardDisks = @(Get-VMHardDiskDrive -VMName $Vm.Name -ErrorAction Stop)
    $systemAttached = @($hardDisks | Where-Object { Test-SamePath $_.Path $systemDisk }).Count -gt 0
    $dataAttached = @($hardDisks | Where-Object { Test-SamePath $_.Path $dataDisk }).Count -gt 0
    $dvdDrives = @(Get-VMDvdDrive -VMName $Vm.Name -ErrorAction Stop)
    $seedAttached = @($dvdDrives | Where-Object { Test-SamePath $_.Path $seedIso }).Count -gt 0
    $storageRepairRequired = -not $systemAttached -or -not $dataAttached -or -not $seedAttached -or
        $dvdDrives.Count -ne 1

    if ($storageRepairRequired -and $Vm.State -ne "Off") {
        $Vm = Stop-RegisteredVmGracefully -Vm $Vm
    }

    # A side-by-side application upgrade changes the absolute seed ISO path.
    # Reuse one DVD and remove every stale/duplicate DVD before adding missing
    # disks. Old releases could fill all 64 SCSI locations with seed DVDs; in
    # that state attempting to attach a hard disk first can never succeed.
    $dvdDrives = @(Get-VMDvdDrive -VMName $Vm.Name -ErrorAction Stop)
    $seedDrive = $dvdDrives | Where-Object { Test-SamePath $_.Path $seedIso } | Select-Object -First 1
    if (-not $seedDrive -and $dvdDrives.Count -gt 0) {
        $seedDrive = $dvdDrives | Select-Object -First 1
        Set-VMDvdDrive -VMDvdDrive $seedDrive -Path $seedIso | Out-Null
    }
    $dvdDrives = @(Get-VMDvdDrive -VMName $Vm.Name -ErrorAction Stop)
    $seedDrive = $dvdDrives | Where-Object { Test-SamePath $_.Path $seedIso } | Select-Object -First 1
    foreach ($dvdDrive in $dvdDrives) {
        $isKeptDrive = $seedDrive -and
            [int]$dvdDrive.ControllerNumber -eq [int]$seedDrive.ControllerNumber -and
            [int]$dvdDrive.ControllerLocation -eq [int]$seedDrive.ControllerLocation
        if (-not $isKeptDrive) {
            Remove-VMDvdDrive -VMDvdDrive $dvdDrive | Out-Null
        }
    }

    if (-not $systemAttached) {
        $location = Get-FreeScsiLocation -TargetVmName $Vm.Name
        Add-VMHardDiskDrive -VMName $Vm.Name -ControllerType SCSI -ControllerNumber 0 `
            -ControllerLocation $location -Path $systemDisk | Out-Null
    }
    if (-not $dataAttached) {
        $location = Get-FreeScsiLocation -TargetVmName $Vm.Name
        Add-VMHardDiskDrive -VMName $Vm.Name -ControllerType SCSI -ControllerNumber 0 `
            -ControllerLocation $location -Path $dataDisk | Out-Null
    }
    if (-not $seedDrive) {
        $location = Get-FreeScsiLocation -TargetVmName $Vm.Name
        Add-VMDvdDrive -VMName $Vm.Name -ControllerNumber 0 -ControllerLocation $location `
            -Path $seedIso | Out-Null
    }
}

function Ensure-VmNetworkAdapter {
    param([Parameter(Mandatory = $true)][object]$Vm)

    $adapters = @(Get-VMNetworkAdapter -VMName $Vm.Name -ErrorAction Stop)
    if ($adapters.Count -eq 0) {
        Add-VMNetworkAdapter -VMName $Vm.Name -SwitchName $switchName | Out-Null
        return
    }
    if (@($adapters | Where-Object { $_.SwitchName -eq $switchName }).Count -eq 0) {
        # This VM is product-owned. Repair its first adapter, but do not touch
        # similarly named host switches or adapters belonging to other VMs.
        Connect-VMNetworkAdapter -VMNetworkAdapter $adapters[0] -SwitchName $switchName | Out-Null
    }
}

function Ensure-Vm {
    $manifest = Read-ApplianceManifest
    $applianceFingerprint = Get-ApplianceFingerprint -Manifest $manifest
    $installedFingerprint = if (Test-Path -LiteralPath $versionMarker -PathType Leaf) {
        ([string](Get-Content -Raw -LiteralPath $versionMarker)).Trim()
    } else { "" }
    $pendingFingerprint = if (Test-Path -LiteralPath $pendingVersionMarker -PathType Leaf) {
        ([string](Get-Content -Raw -LiteralPath $pendingVersionMarker)).Trim()
    } else { "" }
    $installedSystemDiskBytes = [int64]0
    if (Test-Path -LiteralPath $systemDisk -PathType Leaf) {
        try {
            $installedSystemDiskBytes = [int64](Get-VHD -Path $systemDisk -ErrorAction Stop).Size
        } catch {
            throw "Unable to inspect the installed appliance system disk: $systemDisk. $($_.Exception.Message)"
        }
    }
    $needsSystemRefresh = ($installedFingerprint -ne $applianceFingerprint -and
        $pendingFingerprint -ne $applianceFingerprint) -or
        -not (Test-Path -LiteralPath $systemDisk -PathType Leaf) -or
        $installedSystemDiskBytes -lt [int64]$minimumSystemDiskBytes

    # A process interruption may leave a full staged copy behind. It is never
    # attached to the VM and has no committed marker, so discard it before the
    # free-space check and create a newly validated copy below.
    if ($needsSystemRefresh -and (Test-Path -LiteralPath $stagedSystemDisk)) {
        Remove-Item -LiteralPath $stagedSystemDisk -Force
    }
    $refreshReserveBytes = [int64]0
    $refreshReserveReason = ""
    if ($needsSystemRefresh -and (Test-Path -LiteralPath $dataDisk -PathType Leaf)) {
        $baseDiskLength = [int64](Get-Item -LiteralPath $baseDisk -ErrorAction Stop).Length
        $refreshReserveBytes = $baseDiskLength + [int64]$systemDiskRefreshSafetyBytes
        $baseDiskGiB = [math]::Round($baseDiskLength / 1GB, 1)
        $safetyGiB = [math]::Round([int64]$systemDiskRefreshSafetyBytes / 1GB, 1)
        $refreshReserveReason = "appliance system-disk refresh (${baseDiskGiB} GiB source copy plus ${safetyGiB} GiB copy safety margin)"
    }
    Assert-DataRootCapacity -AdditionalRequiredBytes $refreshReserveBytes `
        -AdditionalReason $refreshReserveReason

    [void](Ensure-ControlToken)
    Ensure-Network
    New-Item -ItemType Directory -Path $vmRoot -Force | Out-Null

    if ($needsSystemRefresh) {
        # Copy and validate the replacement while the currently bootable disk
        # is still untouched. A failed copy can then be retried safely.
        if (Test-Path -LiteralPath $stagedSystemDisk) {
            Remove-Item -LiteralPath $stagedSystemDisk -Force
        }
        try {
            $expectedSystemDiskLength = [int64](Get-Item -LiteralPath $baseDisk -ErrorAction Stop).Length
            Copy-Item -LiteralPath $baseDisk -Destination $stagedSystemDisk
            $stagedSystemDiskLength = [int64](Get-Item -LiteralPath $stagedSystemDisk -ErrorAction Stop).Length
            if ($stagedSystemDiskLength -ne $expectedSystemDiskLength) {
                throw "The staged appliance system disk length does not match its source."
            }
            $stagedVhd = Get-VHD -Path $stagedSystemDisk -ErrorAction Stop
            if ([int64]$stagedVhd.Size -lt [int64]$minimumSystemDiskBytes) {
                Resize-VHD -Path $stagedSystemDisk -SizeBytes ([int64]$minimumSystemDiskBytes) -ErrorAction Stop
                $stagedVhd = Get-VHD -Path $stagedSystemDisk -ErrorAction Stop
            }
            if ([int64]$stagedVhd.Size -lt [int64]$minimumSystemDiskBytes) {
                throw "The staged appliance system disk could not be expanded to the required 20 GiB capacity."
            }
        } catch {
            Remove-Item -LiteralPath $stagedSystemDisk -Force -ErrorAction SilentlyContinue
            throw
        }

        Remove-RegisteredVm
        $oldSystemDisk = ""
        try {
            if (Test-Path -LiteralPath $systemDisk -PathType Leaf) {
                $oldSystemDisk = Join-Path $vmRoot ("system.previous-{0}.vhdx" -f [guid]::NewGuid().ToString("N"))
                Move-Item -LiteralPath $systemDisk -Destination $oldSystemDisk
            }
            Move-Item -LiteralPath $stagedSystemDisk -Destination $systemDisk
        } catch {
            # If the final rename fails, put the previously bootable disk back
            # whenever possible. Never delete the backup on this error path.
            if (-not (Test-Path -LiteralPath $systemDisk) -and
                -not [string]::IsNullOrWhiteSpace($oldSystemDisk) -and
                (Test-Path -LiteralPath $oldSystemDisk -PathType Leaf)) {
                Move-Item -LiteralPath $oldSystemDisk -Destination $systemDisk -ErrorAction SilentlyContinue
            }
            throw
        }
        [System.IO.File]::WriteAllText(
            $pendingVersionMarker,
            $applianceFingerprint,
            [System.Text.UTF8Encoding]::new($false))
    } elseif ($installedFingerprint -eq $applianceFingerprint -and
        (Test-Path -LiteralPath $pendingVersionMarker -PathType Leaf)) {
        Remove-Item -LiteralPath $pendingVersionMarker -Force
    }

    $previousSystemDisks = @(Get-ChildItem -LiteralPath $vmRoot -Filter "system.previous-*.vhdx" `
        -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending)
    if ($previousSystemDisks.Count -gt 1) {
        $previousSystemDisks | Select-Object -Skip 1 | Remove-Item -Force
    }

    if (-not (Test-Path -LiteralPath $dataDisk -PathType Leaf)) {
        New-VHD -Path $dataDisk -Dynamic -SizeBytes ([int64]$manifest.data_disk_size_gb * 1GB) | Out-Null
    }

    $vm = Get-VM -Name $vmName -ErrorAction SilentlyContinue
    if (-not $vm) {
        $generation = [int]$manifest.vm_generation
        $vm = New-VM -Name $vmName -Generation $generation -MemoryStartupBytes 6GB -VHDPath $systemDisk -SwitchName $switchName
        if ($generation -eq 2) {
            Set-VMFirmware -VMName $vmName -EnableSecureBoot On -SecureBootTemplate MicrosoftUEFICertificateAuthority
        }
        Set-VM -Name $vmName -AutomaticStartAction Nothing -AutomaticStopAction ShutDown -CheckpointType Disabled
        Set-VMMemory -VMName $vmName -DynamicMemoryEnabled $true -MinimumBytes 4GB -StartupBytes 6GB -MaximumBytes 8GB
        Set-VMProcessor -VMName $vmName -Count 4
    }
    Ensure-VmNetworkAdapter -Vm $vm
    Ensure-VmStorage -Vm $vm
}

function Get-GuestHeaders {
    $token = Ensure-ControlToken
    return @{ "X-OntoTwin-Token" = $token }
}

function Wait-GuestReady {
    param([int]$TimeoutSeconds = 1200)
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    $diagnosticDeadline = (Get-Date).AddSeconds(180)
    $diagnosticServiceResponded = $false
    $lastFailure = "No response received from the guest control service."
    $lastStatus = ""
    $lastComposeError = ""
    $lastBootstrapLog = ""
    do {
        try {
            $status = Invoke-RestMethod -Uri "http://${guestAddress}:$guestControlPort/status" -Headers (Get-GuestHeaders) -TimeoutSec 5
            $diagnosticServiceResponded = $true
            if ($status.ready) { return $status }
            $lastStatus = ($status | ConvertTo-Json -Compress -Depth 5)
            if ($status.PSObject.Properties["compose_error"]) {
                $lastComposeError = [string]$status.compose_error
            }
            if ($status.PSObject.Properties["bootstrap_log_tail"]) {
                $lastBootstrapLog = [string]$status.bootstrap_log_tail
            }
            $lastFailure = "The guest control service responded, but the backend is not ready."
        } catch {
            $lastFailure = $_.Exception.Message
        }
        if (-not $diagnosticServiceResponded -and (Get-Date) -ge $diagnosticDeadline) {
            if (Test-Path -LiteralPath $pendingVersionMarker -PathType Leaf) {
                Remove-Item -LiteralPath $pendingVersionMarker -Force
            }
            $diagnosticVm = Get-VM -Name $vmName -ErrorAction SilentlyContinue
            $diagnosticVmState = if ($diagnosticVm) { [string]$diagnosticVm.State } else { "NotInstalled" }
            throw "The OntoTwin guest diagnostic service did not start within 180 seconds. " +
                "VMState=$diagnosticVmState; GuestControl=http://${guestAddress}:$guestControlPort; " +
                "LastError=$lastFailure. The next Start will refresh only the appliance system disk; customer data is preserved."
        }
        Start-Sleep -Seconds 3
    } while ((Get-Date) -lt $deadline)

    # A slow first installation can finish exactly on the timeout boundary.
    # Probe once more before reporting failure so a completed bootstrap is not
    # misclassified merely because the previous sleep crossed the deadline.
    try {
        $status = Invoke-RestMethod -Uri "http://${guestAddress}:$guestControlPort/status" -Headers (Get-GuestHeaders) -TimeoutSec 10
        if ($status.ready) { return $status }
        $lastStatus = ($status | ConvertTo-Json -Compress -Depth 5)
        if ($status.PSObject.Properties["compose_error"]) {
            $lastComposeError = [string]$status.compose_error
        }
        if ($status.PSObject.Properties["bootstrap_log_tail"]) {
            $lastBootstrapLog = [string]$status.bootstrap_log_tail
        }
        $lastFailure = "The guest control service responded on the final probe, but the backend is not ready."
    } catch {
        $lastFailure = $_.Exception.Message
    }

    $vm = Get-VM -Name $vmName -ErrorAction SilentlyContinue
    $vmState = if ($vm) { [string]$vm.State } else { "NotInstalled" }
    $guestIps = if ($vm) {
        @((Get-VMNetworkAdapter -VMName $vmName -ErrorAction SilentlyContinue).IPAddresses) -join ","
    } else { "" }
    if ($lastStatus.Length -gt 1200) { $lastStatus = $lastStatus.Substring(0, 1200) + "..." }
    if ($lastComposeError.Length -gt 2000) {
        $lastComposeError = $lastComposeError.Substring($lastComposeError.Length - 2000)
    }
    if ($lastBootstrapLog.Length -gt 6000) {
        $lastBootstrapLog = $lastBootstrapLog.Substring($lastBootstrapLog.Length - 6000)
    }
    # If the guest never exposed even its early diagnostic service, regard the
    # just-staged system disk as an incomplete attempt. Customer data remains on
    # the separate data VHDX, while the next Start recreates only the system disk.
    if ([string]::IsNullOrWhiteSpace($lastStatus) -and
        [string]::IsNullOrWhiteSpace($lastBootstrapLog) -and
        (Test-Path -LiteralPath $pendingVersionMarker -PathType Leaf)) {
        Remove-Item -LiteralPath $pendingVersionMarker -Force
    }
    throw "The OntoTwin backend appliance did not become ready within $TimeoutSeconds seconds. " +
        "VMState=$vmState; GuestIPs=$guestIps; GuestControl=http://${guestAddress}:$guestControlPort; " +
        "LastError=$lastFailure; LastStatus=$lastStatus; ComposeError=$lastComposeError; " +
        "BootstrapLogTail=$lastBootstrapLog. " +
        "Review $(Join-Path $data 'Logs\host-service.log') and the VM console before retrying."
}

function Get-Status {
    $vm = Get-VM -Name $vmName -ErrorAction SilentlyContinue
    $dataDrive = Get-DataRootDrive
    $backendReady = $false
    $backendPortProxyOwned = $false
    try {
        $backendPortProxyOwned = Test-ProductBackendPortProxy -Entries @(Get-BackendPortProxyEntries)
        if ($backendPortProxyOwned) {
            $response = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:$backendPort/" -TimeoutSec 3
            $backendReady = $response.StatusCode -eq 200
        }
    } catch {}
    return [pscustomobject]@{
        VMInstalled = $null -ne $vm
        VMState = if ($vm) { [string]$vm.State } else { "NotInstalled" }
        BackendPortProxyOwned = $backendPortProxyOwned
        BackendReady = $backendReady
        ConsoleUrl = "http://127.0.0.1:$backendPort/nexus"
        DataRoot = $data
        DataVolume = $dataDrive.Name
        DataVolumeFreeGB = [math]::Round([int64]$dataDrive.AvailableFreeSpace / 1GB, 1)
    }
}

Assert-Administrator
Assert-HyperV
Assert-DataRootConfiguration

switch ($Action) {
    "Provision" {
        Ensure-Vm
        Get-Status
    }
    "Start" {
        Ensure-Vm
        $vm = Get-VM -Name $vmName
        if ($vm.State -ne "Running") {
            Start-VM -Name $vmName | Out-Null
        }
        [void](Wait-GuestReady)
        $deadline = (Get-Date).AddMinutes(3)
        do {
            $status = Get-Status
            if ($status.BackendReady) { break }
            Start-Sleep -Seconds 2
        } while ((Get-Date) -lt $deadline)
        if (-not $status.BackendReady) {
            throw "The OntoTwin backend did not pass its health check."
        }
        $manifest = Read-ApplianceManifest
        [System.IO.File]::WriteAllText(
            $versionMarker,
            (Get-ApplianceFingerprint -Manifest $manifest),
            [System.Text.UTF8Encoding]::new($false))
        if (Test-Path -LiteralPath $pendingVersionMarker -PathType Leaf) {
            Remove-Item -LiteralPath $pendingVersionMarker -Force
        }
        $status
    }
    "Stop" {
        $vm = Get-VM -Name $vmName -ErrorAction SilentlyContinue
        if ($vm -and $vm.State -ne "Off") {
            [void](Stop-RegisteredVmGracefully -Vm $vm)
        }
        $vm = Get-VM -Name $vmName -ErrorAction SilentlyContinue
        if ($vm -and $vm.State -ne "Off") {
            throw "The OntoTwin backend VM did not reach the Off state."
        }
        Get-Status
    }
    "Status" {
        Get-Status
    }
    "Remove" {
        Remove-RegisteredVm -AllowTurnOff
        Remove-ProductBackendPortProxy
        Remove-NetFirewallRule -Name $payloadFirewallRuleName -ErrorAction SilentlyContinue
        $nat = Get-NetNat -Name $natName -ErrorAction SilentlyContinue
        if ($nat -and $nat.InternalIPInterfaceAddressPrefix -eq $networkPrefix) {
            Remove-NetNat -Name $natName -Confirm:$false
        } elseif ($nat) {
            Write-Warning "A non-OntoTwin NAT named '$natName' was preserved."
        }
        $switch = Get-VMSwitch -Name $switchName -ErrorAction SilentlyContinue
        if ($switch -and [string]$switch.SwitchType -eq "Internal") {
            Remove-VMSwitch -Name $switchName -Force
        } elseif ($switch) {
            Write-Warning "A non-Internal Hyper-V switch named '$switchName' was preserved."
        }
        if ($PurgeData) {
            # Assert-DataRootConfiguration above restricts deletion to the
            # legacy ProgramData root or X:\OntoTwin-ZHHZ\Data on a fixed NTFS volume.
            if (Test-Path -LiteralPath $data) {
                Assert-OrdinaryDataDirectory -Path $data
                Remove-Item -LiteralPath $data -Recurse -Force
            }
        }
        [pscustomobject]@{ Removed = $true; DataPreserved = -not $PurgeData }
    }
}
