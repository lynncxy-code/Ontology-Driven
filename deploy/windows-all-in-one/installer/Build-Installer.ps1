[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$AppPayloadDirectory,

    [Parameter(Mandatory = $true)]
    [string]$OutputDirectory,

    [string]$ExistingPayloadArchive = "",
    [string]$CodeSigningCertificateThumbprint = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-ReleaseDescriptor {
    param([Parameter(Mandatory = $true)][string]$Version)

    if ($Version -cnotmatch '^(?<product>\d+\.\d+\.\d+)-r(?<release>\d+)-rc(?<candidateMajor>\d+)(?:\.(?<candidateMinor>\d+))?$') {
        throw "Release version is not canonical: $Version"
    }
    $productVersion = $Matches.product
    $releaseNumber = $Matches.release
    $candidateMajor = [int]$Matches.candidateMajor
    $hasCandidateMinor = $Matches.ContainsKey('candidateMinor') -and -not [string]::IsNullOrWhiteSpace([string]$Matches['candidateMinor'])
    $candidateMinor = if ($hasCandidateMinor) { [int]$Matches['candidateMinor'] } else { 0 }
    if ($candidateMinor -gt 99) { throw "The RC minor revision must be between 0 and 99: $Version" }
    $candidateNumber = if ($hasCandidateMinor) { "$candidateMajor.$candidateMinor" } else { "$candidateMajor" }
    $numericRevision = ($candidateMajor * 100) + $candidateMinor
    if ($numericRevision -gt 65535) { throw "The RC revision is too large for a Windows binary version: $Version" }
    $msiParts = $productVersion.Split('.')
    $label = "OntoTwin-ZHHZ-$productVersion-R$releaseNumber-RC$candidateNumber"
    return [pscustomobject]@{
        Version = $Version
        DisplayVersion = "$productVersion R$releaseNumber RC$candidateNumber"
        Candidate = "RC$candidateNumber"
        Label = $label
        SetupFile = "$label-Setup.exe"
        BinaryVersion = "$productVersion.$numericRevision"
        BundleVersion = "$productVersion.$numericRevision"
        MsiVersion = "$($msiParts[0]).$($msiParts[1]).$numericRevision"
    }
}

function Assert-UnixTextBytes {
    param(
        [Parameter(Mandatory = $true)][byte[]]$Bytes,
        [Parameter(Mandatory = $true)][string]$ExpectedPrefix,
        [Parameter(Mandatory = $true)][string]$DisplayName
    )

    $prefixBytes = [System.Text.Encoding]::ASCII.GetBytes($ExpectedPrefix)
    if ($Bytes.Length -lt $prefixBytes.Length) {
        throw "Linux payload text is truncated: $DisplayName"
    }
    if ($Bytes.Length -ge 3 -and $Bytes[0] -eq 0xEF -and $Bytes[1] -eq 0xBB -and $Bytes[2] -eq 0xBF) {
        throw "Linux payload text must not contain a UTF-8 BOM: $DisplayName"
    }
    if ($Bytes.Length -ge 2 -and
        (($Bytes[0] -eq 0xFF -and $Bytes[1] -eq 0xFE) -or
         ($Bytes[0] -eq 0xFE -and $Bytes[1] -eq 0xFF))) {
        throw "Linux payload text must not contain a UTF-16 BOM: $DisplayName"
    }
    if ($Bytes -contains [byte]0x0D) {
        throw "Linux payload text contains CR/CRLF bytes and is unsafe for the appliance: $DisplayName"
    }
    for ($index = 0; $index -lt $prefixBytes.Length; $index++) {
        if ($Bytes[$index] -ne $prefixBytes[$index]) {
            throw "Linux payload text does not begin with the required LF-only interpreter line: $DisplayName"
        }
    }
    if ($Bytes[$Bytes.Length - 1] -ne 0x0A) {
        throw "Linux payload text must end with LF: $DisplayName"
    }
}

function Assert-UnixTextFormat {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$ExpectedPrefix
    )
    Assert-UnixTextBytes `
        -Bytes ([System.IO.File]::ReadAllBytes($Path)) `
        -ExpectedPrefix $ExpectedPrefix `
        -DisplayName $Path
}

function Write-ReleaseDocument {
    param(
        [Parameter(Mandatory = $true)][string]$Source,
        [Parameter(Mandatory = $true)][string]$Destination,
        [Parameter(Mandatory = $true)]$Descriptor
    )

    $content = Get-Content -Raw -Encoding UTF8 -LiteralPath $Source
    $content = $content.Replace('__RELEASE_VERSION__', [string]$Descriptor.Version)
    $content = $content.Replace('__RELEASE_DISPLAY_VERSION__', [string]$Descriptor.DisplayVersion)
    $content = $content.Replace('__RELEASE_RC__', [string]$Descriptor.Candidate)
    $content = $content.Replace('__RELEASE_LABEL__', [string]$Descriptor.Label)
    $content = $content.Replace('__SETUP_FILE__', [string]$Descriptor.SetupFile)
    if ($content -match '__RELEASE_[A-Z_]+__|__SETUP_FILE__') {
        throw "An unresolved release token remains in $Source."
    }
    [System.IO.File]::WriteAllText($Destination, $content, [System.Text.UTF8Encoding]::new($false))
}

function Assert-RuntimeManifestText {
    param(
        [Parameter(Mandatory = $true)][string]$UfsText,
        [Parameter(Mandatory = $true)][string]$NonUfsText
    )

    $combinedText = $UfsText + [Environment]::NewLine + $NonUfsText
    if ($combinedText -match '(?i)(^|[/\\])(test0316|tmp_ue)([/\\]|$)') {
        throw "The Shipping manifests contain a forbidden test project identity."
    }
    if ($combinedText -match '(?i)PixelStreaming') {
        throw "Pixel Streaming files are present in the Shipping manifests."
    }
    if ($UfsText -notmatch '(?im)^ZHHZ[/\\]ZHHZ\.uproject(?:\s|$)') {
        throw "The UFS manifest does not contain the ZHHZ project descriptor."
    }
    if ($UfsText -notmatch '(?im)^ZHHZ[/\\]Plugins[/\\]glTFRuntime[/\\]glTFRuntime\.uplugin(?:\s|$)') {
        throw "The UFS manifest does not contain the required glTFRuntime plugin."
    }
    if ($UfsText -notmatch '(?im)^ZHHZ[/\\]Plugins[/\\]OntoTwinSync[/\\]OntoTwinSync\.uplugin(?:\s|$)') {
        throw "The UFS manifest does not contain the required OntoTwinSync plugin."
    }
}

function Assert-RuntimePackaging {
    param([Parameter(Mandatory = $true)][string]$RuntimeRoot)

    $ufsPath = Join-Path $RuntimeRoot "Manifest_UFSFiles_Win64.txt"
    $nonUfsPath = Join-Path $RuntimeRoot "Manifest_NonUFSFiles_Win64.txt"
    foreach ($manifestPath in @($ufsPath, $nonUfsPath)) {
        if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
            throw "Required Shipping manifest is missing: $manifestPath"
        }
    }
    Assert-RuntimeManifestText `
        -UfsText (Get-Content -Raw -Encoding UTF8 -LiteralPath $ufsPath) `
        -NonUfsText (Get-Content -Raw -Encoding UTF8 -LiteralPath $nonUfsPath)
    $forbiddenPath = Get-ChildItem -LiteralPath $RuntimeRoot -Recurse -Force | Where-Object {
        $_.FullName.Substring($RuntimeRoot.Length).TrimStart([char[]]@('\', '/')) -match '(?i)(^|[/\\])(test0316|tmp_ue|PixelStreaming)([/\\]|$)'
    } | Select-Object -First 1
    if ($null -ne $forbiddenPath) { throw "The packaged runtime contains a forbidden path: $($forbiddenPath.FullName)" }
}

function Assert-RuntimeEvidence {
    param(
        [Parameter(Mandatory = $true)][string]$RuntimeRoot,
        [Parameter(Mandatory = $true)]$RuntimeIdentity,
        [Parameter(Mandatory = $true)]$RuntimeComponent
    )

    if ([string]$RuntimeIdentity.source_project_path -notmatch '(?i)(^|[/\\])ZHHZ\.uproject$' -or
        [string]$RuntimeIdentity.source_project_sha256 -cnotmatch '^[0-9a-f]{64}$' -or
        [int]$RuntimeIdentity.schema_version -lt 3 -or
        @($RuntimeIdentity.source_build_inputs).Count -eq 0 -or
        @($RuntimeIdentity.source_umap_files).Count -eq 0) {
        throw "Runtime manifest does not contain valid source/config/plugin and .umap evidence."
    }
    if ((@($RuntimeIdentity.source_build_inputs) | ConvertTo-Json -Depth 5 -Compress) -cne
        (@($RuntimeComponent.source_build_inputs) | ConvertTo-Json -Depth 5 -Compress) -or
        (@($RuntimeIdentity.source_umap_files) | ConvertTo-Json -Depth 5 -Compress) -cne
        (@($RuntimeComponent.source_umap_files) | ConvertTo-Json -Depth 5 -Compress) -or
        (@($RuntimeIdentity.package_files) | ConvertTo-Json -Depth 5 -Compress) -cne
        (@($RuntimeComponent.package_files) | ConvertTo-Json -Depth 5 -Compress)) {
        throw "Runtime evidence differs between runtime manifest and component_versions."
    }

    $runtimePrefix = [System.IO.Path]::GetFullPath($RuntimeRoot).TrimEnd('\') + '\'
    $requiredPackages = @(
        "ZHHZ.exe",
        "ZHHZ/Binaries/Win64/ZHHZ-Win64-Shipping.exe",
        "ZHHZ/Content/Paks/ZHHZ-Windows.pak",
        "ZHHZ/Content/Paks/ZHHZ-Windows.ucas",
        "ZHHZ/Content/Paks/ZHHZ-Windows.utoc"
    )
    $evidenceByPath = @{}
    foreach ($entry in @($RuntimeIdentity.package_files)) { $evidenceByPath[[string]$entry.path] = $entry }
    foreach ($relativePath in $requiredPackages) {
        if (-not $evidenceByPath.ContainsKey($relativePath)) { throw "Runtime evidence is missing: $relativePath" }
        $fullPath = [System.IO.Path]::GetFullPath((Join-Path $RuntimeRoot $relativePath.Replace('/', '\')))
        if (-not $fullPath.StartsWith($runtimePrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
            throw "Unsafe runtime evidence path: $relativePath"
        }
        $entry = $evidenceByPath[$relativePath]
        if (-not (Test-Path -LiteralPath $fullPath -PathType Leaf) -or
            (Get-Item -LiteralPath $fullPath).Length -ne [long]$entry.bytes -or
            (Get-FileHash -LiteralPath $fullPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne [string]$entry.sha256) {
            throw "Runtime package evidence mismatch: $relativePath"
        }
    }
}

function Read-TarJsonMember {
    param(
        [Parameter(Mandatory = $true)][string]$Archive,
        [Parameter(Mandatory = $true)][string]$RelativePath
    )

    $members = @(& tar.exe -tf $Archive)
    if ($LASTEXITCODE -ne 0) { throw "Cannot list archive: $Archive" }
    $member = $members | Where-Object {
        ([string]$_).Replace('\', '/').TrimStart([char[]]@('.', '/')) -eq $RelativePath
    } | Select-Object -First 1
    if (-not $member) { throw "Archive member is missing from ${Archive}: $RelativePath" }
    $jsonText = (& tar.exe -xOf $Archive $member) -join "`n"
    if ($LASTEXITCODE -ne 0) { throw "Cannot read $RelativePath from $Archive" }
    return $jsonText | ConvertFrom-Json
}

function Read-TarTextMember {
    param(
        [Parameter(Mandatory = $true)][string]$Archive,
        [Parameter(Mandatory = $true)][string]$RelativePath
    )

    $members = @(& tar.exe -tf $Archive)
    if ($LASTEXITCODE -ne 0) { throw "Cannot list archive: $Archive" }
    $member = $members | Where-Object {
        ([string]$_).Replace('\', '/').TrimStart([char[]]@('.', '/')) -eq $RelativePath
    } | Select-Object -First 1
    if (-not $member) { throw "Archive member is missing from ${Archive}: $RelativePath" }
    $text = (& tar.exe -xOf $Archive $member) -join "`n"
    if ($LASTEXITCODE -ne 0) { throw "Cannot read $RelativePath from $Archive" }
    return $text
}

function Get-EnvironmentValue {
    param(
        [Parameter(Mandatory = $true)][string]$Content,
        [Parameter(Mandatory = $true)][string]$Key
    )

    $pattern = '(?m)^' + [regex]::Escape($Key) + '=(.*)$'
    $matches = [regex]::Matches($Content, $pattern)
    if ($matches.Count -ne 1) { throw "Expected exactly one $Key entry in customer.env.example; found $($matches.Count)." }
    return $matches[0].Groups[1].Value.TrimEnd("`r")
}

function Normalize-DeployText {
    param([AllowEmptyString()][string]$Text)

    return $Text.Replace("`r`n", "`n").TrimEnd([char[]]@("`r", "`n"))
}

function Assert-ReleaseDeployMatchesSource {
    param(
        [Parameter(Mandatory = $true)][string]$SourceDeployRoot,
        [Parameter(Mandatory = $true)][string]$ReleaseCompose,
        [Parameter(Mandatory = $true)][string]$ReleaseEnvironment,
        [Parameter(Mandatory = $true)]$Manifest
    )

    $sourceCompose = Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $SourceDeployRoot "docker-compose.release.yml")
    if ((Normalize-DeployText $ReleaseCompose) -cne (Normalize-DeployText $sourceCompose)) {
        throw "Release docker-compose.release.yml is stale relative to the current deployment source."
    }

    $dataVersion = [string]$Manifest.data_version
    if ([string]::IsNullOrWhiteSpace($dataVersion) -or
        $dataVersion -ne [string]$Manifest.component_versions.data_version) {
        throw "Release manifest has missing or inconsistent data_version values."
    }
    $renderedValues = @{
        BACKEND_IMAGE = [string]$Manifest.component_versions.images.backend_image
        POSTGRES_IMAGE = [string]$Manifest.component_versions.images.postgres_image
        NEO4J_IMAGE = [string]$Manifest.component_versions.images.neo4j_image
        ONTOTWIN_RELEASE_VERSION = [string]$Manifest.release_version
        ONTOTWIN_DATA_VERSION = $dataVersion
    }
    foreach ($value in $renderedValues.Values) {
        if ([string]::IsNullOrWhiteSpace([string]$value)) {
            throw "Release manifest cannot render the current customer environment template."
        }
    }

    $sourceEnvironment = Normalize-DeployText (
        Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $SourceDeployRoot "customer.env.example"))
    $renderCounts = @{}
    $expectedLines = foreach ($line in ($sourceEnvironment -split "`n")) {
        if ($line -match '^([^#=\s]+)=(.*)$' -and $renderedValues.ContainsKey($Matches[1])) {
            $key = $Matches[1]
            $renderCounts[$key] = 1 + [int]$renderCounts[$key]
            "$key=$($renderedValues[$key])"
        } else {
            $line
        }
    }
    foreach ($key in $renderedValues.Keys) {
        if ([int]$renderCounts[$key] -ne 1) {
            throw "Current customer environment template must declare exactly one $key entry."
        }
    }
    $expectedEnvironment = $expectedLines -join "`n"
    if ($expectedEnvironment -match '__RELEASE_VERSION__|__DATA_VERSION__') {
        throw "Rendered customer environment still contains a release/data placeholder."
    }
    if ((Normalize-DeployText $ReleaseEnvironment) -cne $expectedEnvironment) {
        throw "Release customer.env.example is stale relative to the current deployment source."
    }
}

function Assert-DataRootContract {
    param(
        [Parameter(Mandatory = $true)][string]$DeployRoot,
        [Parameter(Mandatory = $true)]$ApplianceManifest
    )

    $sourcePaths = [ordered]@{
        PayloadInstaller = Join-Path $DeployRoot "installer\PayloadInstaller\Program.cs"
        HostService = Join-Path $DeployRoot "host-service\OntoTwin.ZHHZ.HostService\Program.cs"
        Launcher = Join-Path $DeployRoot "launcher\OntoTwin.ZHHZ.Launcher\MainWindow.xaml.cs"
        HostControl = Join-Path $DeployRoot "hyperv\host\HostControl.ps1"
    }
    $sourceText = @{}
    foreach ($name in $sourcePaths.Keys) {
        $path = $sourcePaths[$name]
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
            throw "DataRoot contract source is missing: $path"
        }
        $text = Get-Content -Raw -Encoding UTF8 -LiteralPath $path
        if (-not $text.Contains('SOFTWARE\OntoTwin\ZHHZ') -or -not $text.Contains('DataRoot')) {
            throw "$name does not use the shared HKLM SOFTWARE\OntoTwin\ZHHZ DataRoot contract."
        }
        $sourceText[$name] = $text
    }
    foreach ($name in @('PayloadInstaller', 'HostService', 'Launcher')) {
        if (-not $sourceText[$name].Contains('GetValue("DataRoot")')) {
            throw "$name must read the shared HKLM DataRoot registry value."
        }
    }
    $launcherXamlPath = Join-Path $DeployRoot "launcher\OntoTwin.ZHHZ.Launcher\MainWindow.xaml"
    if (-not (Test-Path -LiteralPath $launcherXamlPath -PathType Leaf)) {
        throw "Launcher XAML is missing: $launcherXamlPath"
    }
    $launcherXaml = Get-Content -Raw -Encoding UTF8 -LiteralPath $launcherXamlPath
    if ($launcherXaml -match '(?i)\bRC\d+(?:\.\d+)*\b') {
        throw "Launcher UI must not contain a hard-coded RC version."
    }
    if (-not $launcherXaml.Contains('x:Name="ReleaseCaptionText"') -or
        -not $sourceText.Launcher.Contains('ResolveReleaseCaption') -or
        -not $sourceText.Launcher.Contains('"release-manifest.json"')) {
        throw "Launcher must render its release caption from the installed release manifest."
    }
    if (-not $sourceText.PayloadInstaller.Contains('key.SetValue("DataRoot", dataRoot')) {
        throw "PayloadInstaller must persist the selected DataRoot in HKLM."
    }
    if (-not $sourceText.HostService.Contains('"-DataRoot", _dataRoot')) {
        throw "HostService must pass its resolved DataRoot to HostControl."
    }
    $placementPolicyPath = Join-Path $DeployRoot "installer\PayloadInstaller\DiskPlacementPolicy.cs"
    $placementPolicy = Get-Content -Raw -Encoding UTF8 -LiteralPath $placementPolicyPath
    foreach ($requiredPolicyFragment in @(
        'if (!probeSucceeded) return isSystemVolume;',
        'normalized.Equals("NVMe"',
        'normalized.Equals("SATA"'
    )) {
        if (-not $placementPolicy.Contains($requiredPolicyFragment)) {
            throw "Automatic disk placement policy is incomplete: $requiredPolicyFragment"
        }
    }
    foreach ($excludedBus in @('USB', 'SD', 'MMC', 'Unknown', 'iSCSI', 'File Backed Virtual')) {
        if ($placementPolicy -match ('normalized\.Equals\("' + [regex]::Escape($excludedBus) + '"')) {
            throw "Automatic disk placement must not allow bus type $excludedBus."
        }
    }
    foreach ($requiredProbeFragment in @(
        'ProbeWindowsStorageDisk',
        'Get-Partition -DriveLetter',
        'Get-Disk -ErrorAction Stop',
        'DiskPlacementPolicy.IsEligible'
    )) {
        if (-not $sourceText.PayloadInstaller.Contains($requiredProbeFragment)) {
            throw "PayloadInstaller is missing safe local-disk probing: $requiredProbeFragment"
        }
    }
    if ($sourceText.PayloadInstaller.Contains('archiveRoot')) {
        throw "Automatic placement must not prefer the installer media volume."
    }
    $payloadDirectoryPolicyPath = Join-Path $DeployRoot "installer\PayloadInstaller\PayloadDirectoryPolicy.cs"
    $payloadDirectoryPolicy = Get-Content -Raw -Encoding UTF8 -LiteralPath $payloadDirectoryPolicyPath
    foreach ($requiredCleanupFragment in @(
        '.app-previous',
        '.app-new',
        'PayloadDirectoryPolicy.IsCleanupCandidate',
        'EnsureOrdinaryDirectory(fullPath, "legacy application directory")',
        'DeletePayloadDirectoryWithRetries(stale, installRoot, log)',
        'RetryFileSystemAction(() => Directory.Delete(validated, recursive: true)'
    )) {
        if (-not ($payloadDirectoryPolicy.Contains($requiredCleanupFragment) -or
                  $sourceText.PayloadInstaller.Contains($requiredCleanupFragment))) {
            throw "Payload cleanup safety contract is incomplete: $requiredCleanupFragment"
        }
    }
    $localControlPorts = @(
        [regex]::Match($sourceText.PayloadInstaller, '(?m)^const int ServiceControlPort = (\d+);\s*$'),
        [regex]::Match($sourceText.HostService, '(?m)^\s*private const int ControlPort = (\d+);\s*$'),
        [regex]::Match($sourceText.Launcher, '(?m)^\s*private const int ControlPort = (\d+);\s*$')
    )
    if ($localControlPorts.Where({ -not $_.Success }).Count -gt 0 -or
        $localControlPorts.Where({ [int]$_.Groups[1].Value -ne 48073 }).Count -gt 0) {
        throw "PayloadInstaller, HostService, and Launcher must use local control port 48073."
    }
    if (-not $sourceText.PayloadInstaller.Contains('Skipping application cleanup because payload ownership changed') -or
        -not $sourceText.HostService.Contains('Skipping backend removal because payload ownership changed')) {
        throw "MSI uninstall helpers must preserve the registered payload during bundle rollback."
    }
    if (-not $sourceText.PayloadInstaller.Contains('drive.DriveType == DriveType.Fixed') -or
        -not $sourceText.PayloadInstaller.Contains('drive.DriveFormat.Equals("NTFS"') -or
        -not $sourceText.HostControl.Contains('$drive.DriveType -ne [System.IO.DriveType]::Fixed') -or
        -not $sourceText.HostControl.Contains('$drive.DriveFormat.Equals("NTFS"')) {
        throw "PayloadInstaller and HostControl must restrict DataRoot to a fixed NTFS volume."
    }

    $payloadNew = [regex]::Matches(
        $sourceText.PayloadInstaller,
        '(?m)^\s*const long NewDataRootFreeBytes = (\d+)L \* 1024 \* 1024 \* 1024;\s*$')
    $payloadExisting = [regex]::Matches(
        $sourceText.PayloadInstaller,
        '(?m)^\s*const long ExistingDataRootFreeBytes = (\d+)L \* 1024 \* 1024 \* 1024;\s*$')
    $hostNew = [regex]::Matches(
        $sourceText.HostControl,
        '(?m)^\s*\$newDataRootFreeBytes\s*=\s*(\d+)GB\s*$')
    $hostExisting = [regex]::Matches(
        $sourceText.HostControl,
        '(?m)^\s*\$existingDataRootFreeBytes\s*=\s*(\d+)GB\s*$')
    foreach ($matchSet in @($payloadNew, $payloadExisting, $hostNew, $hostExisting)) {
        if ($matchSet.Count -ne 1) {
            throw "DataRoot capacity thresholds must each be declared exactly once."
        }
    }
    $payloadNewGiB = [int]$payloadNew[0].Groups[1].Value
    $payloadExistingGiB = [int]$payloadExisting[0].Groups[1].Value
    $hostNewGiB = [int]$hostNew[0].Groups[1].Value
    $hostExistingGiB = [int]$hostExisting[0].Groups[1].Value
    if ($payloadNewGiB -ne 60 -or $payloadExistingGiB -ne 20 -or
        $hostNewGiB -ne 50 -or $hostExistingGiB -ne 20) {
        throw "DataRoot thresholds must be installer 60/20 GiB and HostControl 50/20 GiB (new/existing)."
    }
    if ([regex]::Matches(
            $sourceText.HostControl,
            '(?m)^\s*Assert-DataRootCapacity -AdditionalRequiredBytes \$refreshReserveBytes\s*`?\s*$').Count -ne 1 -or
        [regex]::Matches($sourceText.HostControl, '(?m)^\s*DataVolumeFreeGB\s*=').Count -ne 1) {
        throw "HostControl must enforce refresh-aware DataRoot capacity and expose DataVolumeFreeGB in Status."
    }

    foreach ($requiredRefreshSafety in @(
        '$systemDiskRefreshSafetyBytes = 1GB',
        '$minimumSystemDiskBytes = 20GB',
        'if ($needsSystemRefresh -and (Test-Path -LiteralPath $dataDisk -PathType Leaf))',
        '$baseDiskLength = [int64](Get-Item -LiteralPath $baseDisk -ErrorAction Stop).Length',
        '$refreshReserveBytes = $baseDiskLength + [int64]$systemDiskRefreshSafetyBytes',
        '-AdditionalReason $refreshReserveReason'
    )) {
        if (-not $sourceText.HostControl.Contains($requiredRefreshSafety)) {
            throw "HostControl is missing the existing-volume system-refresh reserve: $requiredRefreshSafety"
        }
    }

    foreach ($requiredNetworkSafety in @(
        'elseif ([string]$switch.SwitchType -ne "Internal")',
        'function Ensure-BackendPortProxy',
        'Get-NetTCPConnection -State Listen -LocalPort $backendPort',
        'TCP port $backendPort is owned by a different Windows portproxy mapping',
        'function Remove-ProductBackendPortProxy',
        'BackendPortProxyOwned = $backendPortProxyOwned',
        'if ($backendPortProxyOwned)',
        'Ensure-VmNetworkAdapter -Vm $vm',
        'Connect-VMNetworkAdapter -VMNetworkAdapter $adapters[0] -SwitchName $switchName'
    )) {
        if (-not $sourceText.HostControl.Contains($requiredNetworkSafety)) {
            throw "HostControl is missing a required host-network ownership guard: $requiredNetworkSafety"
        }
    }
    if ([regex]::Matches(
            $sourceText.HostControl,
            '(?im)netsh\.exe\s+interface\s+portproxy\s+delete\s+v4tov4').Count -ne 1 -or
        $sourceText.HostControl.Contains('Remove-NetIPAddress')) {
        throw "HostControl must only remove its verified portproxy and must preserve existing host IP addresses."
    }
    $removeProxyFunctionIndex = $sourceText.HostControl.IndexOf(
        'function Remove-ProductBackendPortProxy', [System.StringComparison]::Ordinal)
    $deleteProxyIndex = $sourceText.HostControl.IndexOf(
        'netsh.exe interface portproxy delete v4tov4', [System.StringComparison]::Ordinal)
    if ($removeProxyFunctionIndex -lt 0 -or $deleteProxyIndex -le $removeProxyFunctionIndex) {
        throw "The only portproxy deletion must be inside the ownership-checked removal function."
    }

    $removeStaleDvdIndex = $sourceText.HostControl.IndexOf(
        'Remove-VMDvdDrive -VMDvdDrive $dvdDrive', [System.StringComparison]::Ordinal)
    $addMissingHardDiskIndex = $sourceText.HostControl.IndexOf(
        'Add-VMHardDiskDrive -VMName $Vm.Name', [System.StringComparison]::Ordinal)
    if ($removeStaleDvdIndex -lt 0 -or $addMissingHardDiskIndex -le $removeStaleDvdIndex) {
        throw "HostControl must free stale DVD SCSI locations before attaching missing hard disks."
    }

    foreach ($requiredAtomicRefresh in @(
        '$stagedSystemDisk = Join-Path $vmRoot "system.installing.vhdx"',
        'Copy-Item -LiteralPath $baseDisk -Destination $stagedSystemDisk',
        '$stagedSystemDiskLength -ne $expectedSystemDiskLength',
        'Resize-VHD -Path $stagedSystemDisk -SizeBytes ([int64]$minimumSystemDiskBytes)',
        '[int64]$stagedVhd.Size -lt [int64]$minimumSystemDiskBytes',
        'Move-Item -LiteralPath $stagedSystemDisk -Destination $systemDisk',
        'Move-Item -LiteralPath $oldSystemDisk -Destination $systemDisk -ErrorAction SilentlyContinue'
    )) {
        if (-not $sourceText.HostControl.Contains($requiredAtomicRefresh)) {
            throw "HostControl is missing atomic system-disk refresh protection: $requiredAtomicRefresh"
        }
    }
    if ($sourceText.HostControl.Contains('Copy-Item -LiteralPath $baseDisk -Destination $systemDisk')) {
        throw "HostControl must stage a complete system-disk copy before replacing the bootable disk."
    }
    $stageCopyIndex = $sourceText.HostControl.IndexOf(
        'Copy-Item -LiteralPath $baseDisk -Destination $stagedSystemDisk', [System.StringComparison]::Ordinal)
    $discardStaleStageIndex = $sourceText.HostControl.IndexOf(
        'if ($needsSystemRefresh -and (Test-Path -LiteralPath $stagedSystemDisk))',
        [System.StringComparison]::Ordinal)
    $refreshCapacityCheckIndex = $sourceText.HostControl.IndexOf(
        'Assert-DataRootCapacity -AdditionalRequiredBytes $refreshReserveBytes',
        [System.StringComparison]::Ordinal)
    $removeVmForRefreshIndex = $sourceText.HostControl.IndexOf(
        'Remove-RegisteredVm', $stageCopyIndex, [System.StringComparison]::Ordinal)
    $activateStagedDiskIndex = $sourceText.HostControl.IndexOf(
        'Move-Item -LiteralPath $stagedSystemDisk -Destination $systemDisk', [System.StringComparison]::Ordinal)
    if ($discardStaleStageIndex -lt 0 -or
        $refreshCapacityCheckIndex -le $discardStaleStageIndex -or
        $stageCopyIndex -le $refreshCapacityCheckIndex -or
        $removeVmForRefreshIndex -le $stageCopyIndex -or
        $activateStagedDiskIndex -le $removeVmForRefreshIndex) {
        throw "System-disk refresh must clear stale staging, check reserve, finish staging, then replace the VM disk."
    }

    $dataDiskGiB = [int]$ApplianceManifest.data_disk_size_gb
    if ($dataDiskGiB -le 0 -or $dataDiskGiB -gt 40) {
        throw "Appliance data_disk_size_gb must be between 1 and 40 GiB for this release: $dataDiskGiB"
    }
    if ($payloadNewGiB -lt ($dataDiskGiB + 20)) {
        throw "Installer new-DataRoot threshold must reserve the appliance data disk plus at least 20 GiB."
    }
    if ($hostNewGiB -lt ($dataDiskGiB + 10)) {
        throw "HostControl new-DataRoot threshold must reserve the appliance data disk plus at least 10 GiB."
    }
}

function Assert-DockerArchiveTag {
    param(
        [Parameter(Mandatory = $true)][string]$Archive,
        [Parameter(Mandatory = $true)][string]$ExpectedTag
    )

    $manifestText = (& tar.exe -xOf $Archive manifest.json) -join "`n"
    if ($LASTEXITCODE -ne 0) { throw "Cannot read Docker manifest.json from $Archive" }
    $dockerManifest = $manifestText | ConvertFrom-Json
    $repoTags = @($dockerManifest | ForEach-Object { @($_.RepoTags) })
    if ($repoTags -notcontains $ExpectedTag) {
        throw "Docker archive '$Archive' does not contain the configured tag '$ExpectedTag'."
    }
}

function Assert-BackendUpgradeSafety {
    param(
        [Parameter(Mandatory = $true)][string]$BootstrapText,
        [Parameter(Mandatory = $true)][string]$ComposeText,
        [Parameter(Mandatory = $true)][string]$ControlText
    )

    $normalizedBootstrap = [regex]::Replace($BootstrapText, '\\\r?\n\s*', ' ')
    $teardownCommands = [regex]::Matches(
        $normalizedBootstrap,
        '(?im)^.*\bdocker\s+compose\b.*\bdown\b.*$')
    if ($teardownCommands.Count -ne 1) {
        throw "Guest bootstrap must contain exactly one Docker Compose teardown command."
    }
    $teardown = $teardownCommands[0].Value
    if ($teardown -notmatch '(?:^|\s)down\s+--remove-orphans(?:\s|$)') {
        throw "Guest bootstrap upgrades must remove old Compose containers and orphans."
    }
    if ($teardown -match '(?:^|\s)(?:-v|--volumes)(?:\s|$)') {
        throw "Guest bootstrap teardown must preserve customer database volumes."
    }
    if (-not $BootstrapText.Contains('Compose teardown did not complete; continuing with project-label cleanup:')) {
        throw "Guest bootstrap must fall back to label cleanup when old Compose metadata is damaged."
    }
    $teardownBlockStart = $BootstrapText.IndexOf('if ! teardown_output=', [System.StringComparison]::Ordinal)
    $labelFallbackStart = $BootstrapText.IndexOf('# An appliance upgrade', [System.StringComparison]::Ordinal)
    if ($teardownBlockStart -lt 0 -or $labelFallbackStart -le $teardownBlockStart -or
        $BootstrapText.Substring($teardownBlockStart, $labelFallbackStart - $teardownBlockStart) -match '(?m)^\s*exit\s+[1-9]\d*\s*$') {
        throw "A failed Compose down must reach the safe project-label fallback instead of aborting early."
    }
    foreach ($requiredCleanup in @(
        'label=com.docker.compose.project=ontotwin-zhhz',
        'docker stop --time 120',
        'docker rm "${residual_containers[@]}"',
        'docker network rm "${residual_networks[@]}"'
    )) {
        if (-not $BootstrapText.Contains($requiredCleanup)) {
            throw "Guest bootstrap is missing persistent-data-disk cleanup: $requiredCleanup"
        }
    }
    if ($normalizedBootstrap -match '(?im)\bdocker\s+volume\s+(?:rm|prune)\b') {
        throw "Guest bootstrap must never remove customer Docker volumes during an upgrade."
    }
    if (-not $BootstrapText.Contains('printf ''%s\n'' "$image_fingerprint" > "$IMAGES_MARKER.new"')) {
        throw "Guest bootstrap must cache container archives independently from the release payload."
    }

    $earlyControl = $BootstrapText.IndexOf('log "Early diagnostic control service started"', [System.StringComparison]::Ordinal)
    $largePayloadLoop = $BootstrapText.IndexOf('while read -r checksum filename; do', [System.StringComparison]::Ordinal)
    $progressMarker = $BootstrapText.IndexOf('> "$BOOTSTRAP_IN_PROGRESS"', [System.StringComparison]::Ordinal)
    if ($progressMarker -lt 0 -or $earlyControl -le $progressMarker -or
        $largePayloadLoop -le $earlyControl) {
        throw "Diagnostic control must start after the in-progress marker and before the large payload loop."
    }
    if ([regex]::Matches($BootstrapText, '(?m)^\s*install_control_service\s*$').Count -ne 2) {
        throw "Guest bootstrap must start control early and reinstall/restart it after release setup."
    }
    $controlUnitFunction = [regex]::Match(
        $BootstrapText,
        '(?ms)^install_control_service\(\) \{.*?^\}')
    if (-not $controlUnitFunction.Success -or
        $controlUnitFunction.Value -match '(?m)^(?:After=.*\bdocker\.service\b|Requires=.*\bdocker\.service\b)') {
        throw "Early diagnostic control service must not depend on Docker."
    }
    foreach ($controlRequirement in @(
        'def compose_status():',
        'Bootstrap is still preparing: missing',
        '"bootstrap_in_progress": bootstrap_active',
        '"ready": not bootstrap_active and backend_ready()',
        '"root_total_bytes": root_total',
        '"root_free_bytes": root_free'
    )) {
        if (-not $ControlText.Contains($controlRequirement)) {
            throw "Guest control is not safe during early bootstrap: $controlRequirement"
        }
    }

    $subnets = [regex]::Matches($ComposeText, '(?im)^\s*-\s*subnet:\s*([^\s#]+)\s*(?:#.*)?$')
    if ($subnets.Count -ne 1 -or $subnets[0].Groups[1].Value -ne '10.251.0.0/24') {
        throw "Release Compose must reserve exactly the backend subnet 10.251.0.0/24."
    }
    if ($ComposeText -notmatch '(?im)^networks:\s*$' -or
        $ComposeText -notmatch '(?im)^\s{2}default:\s*$') {
        throw "Release Compose must apply the reserved subnet to its default network."
    }
    if ($ComposeText -match '(?im)^\s*-\s*subnet:\s*172\.28\.251\.0/24\s*$') {
        throw "Release Compose network overlaps the Hyper-V host/guest transport subnet."
    }
}

function Assert-StartupReadinessContract {
    param(
        [Parameter(Mandatory = $true)][string]$BootstrapText,
        [Parameter(Mandatory = $true)][string]$HostControlText,
        [Parameter(Mandatory = $true)][string]$LauncherText
    )

    foreach ($quietProbeRequirement in @(
        "with urllib.request.urlopen('http://127.0.0.1:5000/', timeout=5) as response:",
        'except Exception:',
        'raise SystemExit(1)'
    )) {
        if (-not $BootstrapText.Contains($quietProbeRequirement)) {
            throw "Guest bootstrap health checks must retry transient disconnects without a Python traceback: $quietProbeRequirement"
        }
    }
    $rootCapacityFunction = [regex]::Match(
        $BootstrapText,
        '(?ms)^ensure_root_filesystem_capacity\(\) \{.*?^\}')
    if (-not $rootCapacityFunction.Success) {
        throw "Guest bootstrap is missing ensure_root_filesystem_capacity."
    }
    $rootCapacityText = $rootCapacityFunction.Value
    foreach ($capacityRequirement in @(
        'root_size_bytes="$(df -B1 --output=size / | tail -n 1 | tr -d ''[:space:]'')"',
        'if [ "$root_size_bytes" -lt 17179869184 ]; then',
        'root_device="$(readlink -f -- "$root_source"',
        'partition_file="/sys/class/block/$root_device_name/partition"',
        'root_device_type="$(lsblk -dnro TYPE -- "$root_device"',
        'parent_type="$(lsblk -dnro TYPE -- "/dev/$parent_name"',
        'part_number="$(awk ''NF {print $1; exit}'' "$partition_file")"',
        '[[ "$part_number" =~ ^[0-9]+$ ]]',
        '[ "$root_device_type" = "part" ]',
        '[ "$parent_type" = "disk" ]',
        'growpart "/dev/$parent_name" "$part_number"',
        'Root partition expansion warning:',
        'resize2fs "$root_source"',
        'the appliance root filesystem is smaller than 16 GiB',
        'less than 8 GiB is available on the appliance root filesystem'
    )) {
        if (-not $rootCapacityText.Contains($capacityRequirement)) {
            throw "Guest bootstrap must safely expand and validate root filesystem capacity: $capacityRequirement"
        }
    }
    if ($rootCapacityText -match '(?m)lsblk\s+-no\s+PARTN' -or
        $rootCapacityText -match "awk\s+'NF\s*\{print;\s*exit\}'") {
        throw "Guest bootstrap must not pass padded lsblk PARTN output to growpart."
    }
    $initialCapacityProbe = $rootCapacityText.IndexOf(
        'root_size_bytes="$(df -B1 --output=size /', [System.StringComparison]::Ordinal)
    $growthGate = $rootCapacityText.IndexOf(
        'if [ "$root_size_bytes" -lt 17179869184 ]; then', [System.StringComparison]::Ordinal)
    $growpartCall = $rootCapacityText.IndexOf(
        'growpart "/dev/$parent_name" "$part_number"', [System.StringComparison]::Ordinal)
    if ($initialCapacityProbe -lt 0 -or $growthGate -le $initialCapacityProbe -or
        $growpartCall -le $growthGate) {
        throw "Guest bootstrap must check root capacity before attempting growpart."
    }
    $earlyControlIndex = $BootstrapText.IndexOf(
        'log "Early diagnostic control service started"', [System.StringComparison]::Ordinal)
    $rootCapacityIndex = $BootstrapText.IndexOf(
        'ensure_root_filesystem_capacity', $earlyControlIndex + 1, [System.StringComparison]::Ordinal)
    $largePayloadIndex = $BootstrapText.IndexOf(
        'while read -r checksum filename; do', [System.StringComparison]::Ordinal)
    if ($earlyControlIndex -lt 0 -or $rootCapacityIndex -le $earlyControlIndex -or
        $largePayloadIndex -le $rootCapacityIndex) {
        throw "Guest root capacity must be checked after early diagnostics and before large payload downloads."
    }
    if ($HostControlText -notmatch '(?s)function Wait-GuestReady\s*\{\s*param\(\[int\]\$TimeoutSeconds = 1200\)' -or
        -not $HostControlText.Contains('$diagnosticDeadline = (Get-Date).AddSeconds(180)') -or
        -not $HostControlText.Contains('guest diagnostic service did not start within 180 seconds') -or
        -not $HostControlText.Contains('A slow first installation can finish exactly on the timeout boundary.') -or
        -not $HostControlText.Contains('if ($status.ready) { return $status }')) {
        throw "HostControl must allow a 20-minute guest bootstrap and perform a final boundary probe."
    }
    if (-not $LauncherText.Contains('SendRequestAsync("start", TimeSpan.FromMinutes(30))')) {
        throw "The launcher start request must outlive the guest and host readiness windows."
    }
    foreach ($runtimeLaunchRequirement in @(
        '"ZHHZ-Win64-Shipping.exe"',
        'using var runtimeProcess = Process.Start(startInfo)',
        'runtimeProcess.HasExited',
        'runtimeProcess.ExitCode'
    )) {
        if (-not $LauncherText.Contains($runtimeLaunchRequirement)) {
            throw "The launcher must start and verify the real UE Shipping process: $runtimeLaunchRequirement"
        }
    }
}

function Assert-BackendPayloadHashes {
    param([Parameter(Mandatory = $true)][string]$BackendPayloadRoot)

    $checksumPath = Join-Path $BackendPayloadRoot "SHA256SUMS"
    $expectedNames = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::Ordinal)
    foreach ($line in Get-Content -Encoding UTF8 -LiteralPath $checksumPath) {
        if ($line -notmatch '^([0-9a-fA-F]{64})  ([^/\\]+)$') { throw "Invalid BackendPayload SHA256SUMS line: $line" }
        $expectedHash = $Matches[1].ToLowerInvariant()
        $name = $Matches[2]
        if (-not $expectedNames.Add($name)) { throw "Duplicate BackendPayload checksum entry: $name" }
        $path = Join-Path $BackendPayloadRoot $name
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "BackendPayload checksum target is missing: $name" }
        $actualHash = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($actualHash -ne $expectedHash) { throw "BackendPayload checksum mismatch: $name" }
    }
    $actualNames = @(Get-ChildItem -LiteralPath $BackendPayloadRoot -File | Where-Object { $_.Name -ne "SHA256SUMS" } | ForEach-Object Name)
    foreach ($name in $actualNames) {
        if (-not $expectedNames.Contains($name)) { throw "BackendPayload file is not covered by SHA256SUMS: $name" }
    }
    if ($expectedNames.Count -ne $actualNames.Count) { throw "BackendPayload SHA256SUMS file set is incomplete." }
}

function Get-ZipEntryByPath {
    param(
        [Parameter(Mandatory = $true)]$Zip,
        [Parameter(Mandatory = $true)][string]$RelativePath
    )

    $normalized = $RelativePath.Replace('\', '/')
    $matches = @($Zip.Entries | Where-Object { $_.FullName.Replace('\', '/') -eq $normalized })
    if ($matches.Count -ne 1) { throw "Payload archive must contain exactly one '$normalized' entry; found $($matches.Count)." }
    return $matches[0]
}

function Get-ZipEntryText {
    param([Parameter(Mandatory = $true)]$Entry)

    $stream = $Entry.Open()
    $reader = [System.IO.StreamReader]::new($stream, [System.Text.Encoding]::UTF8, $true)
    try { return $reader.ReadToEnd() } finally { $reader.Dispose() }
}

function Get-ZipEntrySha256 {
    param([Parameter(Mandatory = $true)]$Entry)

    $stream = $Entry.Open()
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        return ([System.BitConverter]::ToString($sha.ComputeHash($stream))).Replace('-', '').ToLowerInvariant()
    } finally {
        $sha.Dispose()
        $stream.Dispose()
    }
}

function Get-ZipEntryBytes {
    param([Parameter(Mandatory = $true)]$Entry)

    $stream = $Entry.Open()
    $memory = [System.IO.MemoryStream]::new()
    try {
        $stream.CopyTo($memory)
        return ,$memory.ToArray()
    } finally {
        $memory.Dispose()
        $stream.Dispose()
    }
}

function Assert-PayloadArchiveMatches {
    param(
        [Parameter(Mandatory = $true)][string]$Archive,
        [Parameter(Mandatory = $true)][string]$PayloadRoot,
        [Parameter(Mandatory = $true)][string]$ExpectedVersion
    )

    $zip = [System.IO.Compression.ZipFile]::OpenRead($Archive)
    try {
        $zipFiles = @($zip.Entries | Where-Object { -not [string]::IsNullOrEmpty($_.Name) })
        $forbiddenEntry = $zipFiles | Where-Object {
            $_.FullName.Replace('\', '/') -match '(?i)(^|/)(test0316|tmp_ue|PixelStreaming)(/|$)'
        } | Select-Object -First 1
        if ($null -ne $forbiddenEntry) { throw "Payload archive contains a forbidden entry: $($forbiddenEntry.FullName)" }

        $localFiles = @(Get-ChildItem -LiteralPath $PayloadRoot -Recurse -File)
        $localNames = @($localFiles | ForEach-Object { $_.FullName.Substring($PayloadRoot.Length + 1).Replace('\', '/') } | Sort-Object)
        $zipNames = @($zipFiles | ForEach-Object { $_.FullName.Replace('\', '/') } | Sort-Object)
        if (($localNames -join "`n") -cne ($zipNames -join "`n")) {
            throw "Payload archive file set does not match AppPayloadDirectory."
        }

        $localByPath = @{}
        foreach ($file in $localFiles) {
            $relativePath = $file.FullName.Substring($PayloadRoot.Length + 1).Replace('\', '/')
            $localByPath[$relativePath] = $file
            $entry = Get-ZipEntryByPath -Zip $zip -RelativePath $relativePath
            if ([long]$entry.Length -ne [long]$file.Length) {
                throw "Payload archive size mismatch: $relativePath"
            }
        }

        $exactPaths = @(
            "release-manifest.json",
            "ZHHZ/ontotwin-runtime-manifest.json",
            "ZHHZ/Manifest_UFSFiles_Win64.txt",
            "ZHHZ/Manifest_NonUFSFiles_Win64.txt",
            "ZHHZ/ZHHZ.exe",
            "ZHHZ/ZHHZ/Binaries/Win64/ZHHZ-Win64-Shipping.exe",
            "ZHHZ/ZHHZ/Content/Paks/ZHHZ-Windows.pak",
            "ZHHZ/ZHHZ/Content/Paks/ZHHZ-Windows.ucas",
            "ZHHZ/ZHHZ/Content/Paks/ZHHZ-Windows.utoc",
            "Appliance/appliance-manifest.json",
            "Appliance/ontotwin-ubuntu.vhdx",
            "Appliance/seed.iso",
            "BackendPayload/bootstrap.sh",
            "BackendPayload/control.py",
            "BackendPayload/release.tar.gz",
            "BackendPayload/SHA256SUMS"
        )
        foreach ($relativePath in $exactPaths) {
            if (-not $localByPath.ContainsKey($relativePath)) { throw "Required AppPayload file is missing: $relativePath" }
            $localHash = (Get-FileHash -LiteralPath $localByPath[$relativePath].FullName -Algorithm SHA256).Hash.ToLowerInvariant()
            $archiveHash = Get-ZipEntrySha256 -Entry (Get-ZipEntryByPath -Zip $zip -RelativePath $relativePath)
            if ($archiveHash -ne $localHash) { throw "Payload archive content mismatch: $relativePath" }
        }

        $archiveRelease = (Get-ZipEntryText -Entry (Get-ZipEntryByPath -Zip $zip -RelativePath "release-manifest.json")) | ConvertFrom-Json
        $archiveRuntime = (Get-ZipEntryText -Entry (Get-ZipEntryByPath -Zip $zip -RelativePath "ZHHZ/ontotwin-runtime-manifest.json")) | ConvertFrom-Json
        $archiveAppliance = (Get-ZipEntryText -Entry (Get-ZipEntryByPath -Zip $zip -RelativePath "Appliance/appliance-manifest.json")) | ConvertFrom-Json
        if ([string]$archiveRelease.release_version -ne $ExpectedVersion -or
            [string]$archiveRelease.component_versions.release_version -ne $ExpectedVersion) {
            throw "Payload archive release version does not match $ExpectedVersion."
        }
        if ([string]$archiveRuntime.project_name -ne "ZHHZ" -or [string]$archiveRuntime.target_name -ne "ZHHZ") {
            throw "Payload archive runtime identity is not ZHHZ/ZHHZ."
        }
        if ([string]$archiveRelease.component_versions.appliance.version -ne [string]$archiveAppliance.version) {
            throw "Payload archive appliance version is inconsistent."
        }
        Assert-UnixTextBytes `
            -Bytes (Get-ZipEntryBytes -Entry (Get-ZipEntryByPath -Zip $zip -RelativePath "BackendPayload/bootstrap.sh")) `
            -ExpectedPrefix "#!/bin/bash`n" `
            -DisplayName "$Archive::BackendPayload/bootstrap.sh"
        Assert-UnixTextBytes `
            -Bytes (Get-ZipEntryBytes -Entry (Get-ZipEntryByPath -Zip $zip -RelativePath "BackendPayload/control.py")) `
            -ExpectedPrefix "#!/usr/bin/env python3`n" `
            -DisplayName "$Archive::BackendPayload/control.py"
        Assert-RuntimeManifestText `
            -UfsText (Get-ZipEntryText -Entry (Get-ZipEntryByPath -Zip $zip -RelativePath "ZHHZ/Manifest_UFSFiles_Win64.txt")) `
            -NonUfsText (Get-ZipEntryText -Entry (Get-ZipEntryByPath -Zip $zip -RelativePath "ZHHZ/Manifest_NonUFSFiles_Win64.txt"))
    } finally {
        $zip.Dispose()
    }
}

function Invoke-CodeSigning {
    param(
        [Parameter(Mandatory = $true)][string]$File,
        [Parameter(Mandatory = $true)][string]$SignTool,
        [Parameter(Mandatory = $true)][string]$CertificateThumbprint
    )

    & $SignTool sign /sha1 $CertificateThumbprint /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 $File
    if ($LASTEXITCODE -ne 0) { throw "Code signing failed: $File" }
}

function Clear-ProjectBuildArtifacts {
    param([Parameter(Mandatory = $true)][string]$ProjectDirectory)

    $fullProjectDirectory = [System.IO.Path]::GetFullPath($ProjectDirectory)
    foreach ($name in @("bin", "obj")) {
        $artifactPath = Join-Path $fullProjectDirectory $name
        if (Test-Path -LiteralPath $artifactPath) { Remove-Item -LiteralPath $artifactPath -Recurse -Force }
    }
}

$installerRoot = [System.IO.Path]::GetFullPath($PSScriptRoot)
$deployRoot = [System.IO.Path]::GetFullPath((Join-Path $installerRoot ".."))
$appPayload = [System.IO.Path]::GetFullPath($AppPayloadDirectory)
$output = [System.IO.Path]::GetFullPath($OutputDirectory)
Add-Type -AssemblyName System.IO.Compression.FileSystem
$signToolPath = ""
if ($CodeSigningCertificateThumbprint) {
    $signToolPath = (Get-Command signtool.exe -ErrorAction Stop).Source
}

foreach ($required in @(
    (Join-Path $appPayload "ZHHZ\ZHHZ.exe"),
    (Join-Path $appPayload "ZHHZ\ontotwin-runtime-manifest.json"),
    (Join-Path $appPayload "ZHHZ\Manifest_UFSFiles_Win64.txt"),
    (Join-Path $appPayload "ZHHZ\Manifest_NonUFSFiles_Win64.txt"),
    (Join-Path $appPayload "release-manifest.json"),
    (Join-Path $appPayload "Appliance\appliance-manifest.json"),
    (Join-Path $appPayload "Appliance\ontotwin-ubuntu.vhdx"),
    (Join-Path $appPayload "Appliance\seed.iso"),
    (Join-Path $appPayload "BackendPayload\release.tar.gz"),
    (Join-Path $appPayload "BackendPayload\SHA256SUMS")
)) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) { throw "Installer app payload is incomplete: $required" }
}
$releaseManifest = Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $appPayload "release-manifest.json") | ConvertFrom-Json
$releaseVersion = [string]$releaseManifest.release_version
$releaseDescriptor = Get-ReleaseDescriptor -Version $releaseVersion
$releaseLabel = [string]$releaseDescriptor.Label
if ($releaseManifest.PSObject.Properties.Name -notcontains "component_versions" -or
    [string]$releaseManifest.component_versions.release_version -ne $releaseVersion) {
    throw "Installer release manifest has missing or inconsistent component_versions."
}
if ([string]$releaseManifest.component_versions.installer.binary_version -ne [string]$releaseDescriptor.BinaryVersion -or
    [string]$releaseManifest.component_versions.installer.bundle_version -ne [string]$releaseDescriptor.BundleVersion -or
    [string]$releaseManifest.component_versions.installer.msi_version -ne [string]$releaseDescriptor.MsiVersion) {
    throw "Installer component versions were not derived from release version $releaseVersion."
}
if ([bool]$releaseManifest.pixel_streaming_included) {
    throw "Installer release manifest enables Pixel Streaming."
}
$runtimeIdentity = Get-Content -Raw -LiteralPath (Join-Path $appPayload "ZHHZ\ontotwin-runtime-manifest.json") | ConvertFrom-Json
if ($runtimeIdentity.project_name -ne "ZHHZ" -or $runtimeIdentity.target_name -ne "ZHHZ") {
    throw "Installer runtime identity mismatch: project='$($runtimeIdentity.project_name)', target='$($runtimeIdentity.target_name)'."
}
if ([string]$releaseManifest.runtime_project -ne [string]$runtimeIdentity.project_name -or
    [string]$releaseManifest.runtime_target -ne [string]$runtimeIdentity.target_name -or
    [string]$releaseManifest.runtime_source_sha256 -ne [string]$runtimeIdentity.source_project_sha256 -or
    [string]$releaseManifest.component_versions.runtime.project_name -ne [string]$runtimeIdentity.project_name -or
    [string]$releaseManifest.component_versions.runtime.target_name -ne [string]$runtimeIdentity.target_name -or
    [string]$releaseManifest.component_versions.runtime.source_project_sha256 -ne [string]$runtimeIdentity.source_project_sha256) {
    throw "Installer release manifest runtime identity is inconsistent."
}
Assert-RuntimeEvidence `
    -RuntimeRoot (Join-Path $appPayload "ZHHZ") `
    -RuntimeIdentity $runtimeIdentity `
    -RuntimeComponent $releaseManifest.component_versions.runtime
Assert-RuntimePackaging -RuntimeRoot (Join-Path $appPayload "ZHHZ")
$applianceManifest = Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $appPayload "Appliance\appliance-manifest.json") | ConvertFrom-Json
if ([string]$releaseManifest.component_versions.appliance.version -ne [string]$applianceManifest.version) {
    throw "Installer release manifest and appliance manifest versions do not match."
}
if ([int]$applianceManifest.system_disk_size_gb -ne 20 -or
    [int]$applianceManifest.minimum_guest_root_size_gb -ne 16 -or
    [int]$applianceManifest.minimum_guest_root_free_gb -ne 8) {
    throw "Appliance capacity contract must be system disk/root/root-free = 20/16/8 GiB."
}
foreach ($capacityField in @(
    "system_disk_size_gb",
    "minimum_guest_root_size_gb",
    "minimum_guest_root_free_gb"
)) {
    if ([int]$releaseManifest.component_versions.appliance.$capacityField -ne [int]$applianceManifest.$capacityField) {
        throw "Installer release manifest appliance capacity differs for $capacityField."
    }
}
if ([int]$releaseManifest.component_versions.appliance.payload_port -ne 48075) {
    throw "Installer release manifest does not declare the required payload port 48075."
}
$seedUserData = (& tar.exe -xOf (Join-Path $appPayload "Appliance\seed.iso") user-data) -join "`n"
if ($LASTEXITCODE -ne 0) { throw "Installer cannot read user-data from the appliance seed ISO." }
$beforeLines = [regex]::Matches($seedUserData, '(?im)^\s*Before=(.*)$')
if ($beforeLines.Count -ne 1) {
    throw "Appliance bootstrap service must declare exactly one systemd Before= line."
}
$beforeUnits = @($beforeLines[0].Groups[1].Value.Trim() -split '\s+')
if ($beforeUnits -notcontains 'ontotwin-stack.service' -or
    $beforeUnits -contains 'ontotwin-control.service') {
    throw "Appliance bootstrap ordering must precede the stack without blocking the diagnostic control service."
}
foreach ($requiredDirective in @('Type=oneshot', 'Restart=on-failure', 'TimeoutStartSec=0')) {
    if (-not $seedUserData.Contains($requiredDirective)) {
        throw "Appliance bootstrap service is missing $requiredDirective."
    }
}
if ($seedUserData -notmatch '(?ms)^growpart:\s*.*?^\s+devices:\s*\[''\/''\]\s*$' -or
    $seedUserData -notmatch '(?m)^resize_rootfs:\s*true\s*$') {
    throw "Appliance seed must explicitly grow the root partition and filesystem."
}
Assert-DataRootContract -DeployRoot $deployRoot -ApplianceManifest $applianceManifest
$placementPolicyTests = Join-Path $installerRoot "tests\PayloadInstaller.PolicyTests\PayloadInstaller.PolicyTests.csproj"
& dotnet run --project $placementPolicyTests -c Release --nologo
if ($LASTEXITCODE -ne 0) { throw "Payload placement policy tests failed." }
$nestedManifest = Read-TarJsonMember -Archive (Join-Path $appPayload "BackendPayload\release.tar.gz") -RelativePath "release-manifest.json"
if ([string]$nestedManifest.release_version -ne $releaseVersion -or
    [string]$nestedManifest.component_versions.release_version -ne $releaseVersion -or
    [string]$nestedManifest.component_versions.appliance.version -ne [string]$applianceManifest.version) {
    throw "Nested backend release manifest is inconsistent with the AppPayload manifest."
}
$nestedEnvironment = Read-TarTextMember `
    -Archive (Join-Path $appPayload "BackendPayload\release.tar.gz") `
    -RelativePath "Deploy/customer.env.example"
$nestedCompose = Read-TarTextMember `
    -Archive (Join-Path $appPayload "BackendPayload\release.tar.gz") `
    -RelativePath "Deploy/docker-compose.release.yml"
$packagedBootstrapPath = Join-Path $appPayload "BackendPayload\bootstrap.sh"
$packagedControlPath = Join-Path $appPayload "BackendPayload\control.py"
Assert-UnixTextFormat -Path $packagedBootstrapPath -ExpectedPrefix "#!/bin/bash`n"
Assert-UnixTextFormat -Path $packagedControlPath -ExpectedPrefix "#!/usr/bin/env python3`n"
$packagedBootstrap = Get-Content -Raw -Encoding UTF8 -LiteralPath $packagedBootstrapPath
$packagedControl = Get-Content -Raw -Encoding UTF8 -LiteralPath $packagedControlPath
Assert-BackendUpgradeSafety `
    -BootstrapText $packagedBootstrap `
    -ComposeText $nestedCompose `
    -ControlText $packagedControl
Assert-StartupReadinessContract `
    -BootstrapText $packagedBootstrap `
    -HostControlText (Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $deployRoot "hyperv\host\HostControl.ps1")) `
    -LauncherText (Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $deployRoot "launcher\OntoTwin.ZHHZ.Launcher\MainWindow.xaml.cs"))
Assert-ReleaseDeployMatchesSource `
    -SourceDeployRoot $deployRoot `
    -ReleaseCompose $nestedCompose `
    -ReleaseEnvironment $nestedEnvironment `
    -Manifest $releaseManifest
if ((Get-EnvironmentValue -Content $nestedEnvironment -Key "ONTOTWIN_RELEASE_VERSION") -ne $releaseVersion) {
    throw "Nested customer environment release version is inconsistent."
}
foreach ($imageGate in @(
    [pscustomobject]@{ Key = "BACKEND_IMAGE"; Component = "backend_image"; Archive = "backend-image.tar" },
    [pscustomobject]@{ Key = "POSTGRES_IMAGE"; Component = "postgres_image"; Archive = "postgres-image.tar" },
    [pscustomobject]@{ Key = "NEO4J_IMAGE"; Component = "neo4j_image"; Archive = "neo4j-image.tar" }
)) {
    $configuredTag = Get-EnvironmentValue -Content $nestedEnvironment -Key $imageGate.Key
    if ($configuredTag -ne [string]$releaseManifest.component_versions.images.($imageGate.Component)) {
        throw "Nested customer environment $($imageGate.Key) does not match component_versions."
    }
    Assert-DockerArchiveTag `
        -Archive (Join-Path $appPayload "BackendPayload\$($imageGate.Archive)") `
        -ExpectedTag $configuredTag
}
Assert-BackendPayloadHashes -BackendPayloadRoot (Join-Path $appPayload "BackendPayload")
if (@(Get-ChildItem -LiteralPath (Join-Path $appPayload "ZHHZ\Models") -Filter "*.glb" -File -ErrorAction SilentlyContinue).Count -eq 0) {
    throw "Installer app payload does not contain any runtime GLB models."
}

$bundleSource = Join-Path $installerRoot "Bundle\Bundle.wxs"
$bundleText = Get-Content -Raw -Encoding UTF8 -LiteralPath $bundleSource
$msiSource = Join-Path $installerRoot "Msi\Package.wxs"
$msiText = Get-Content -Raw -Encoding UTF8 -LiteralPath $msiSource
if (-not $bundleText.Contains('$(var.PayloadVersion)') -or -not $bundleText.Contains('$(var.BundleVersion)')) {
    throw "Bundle.wxs must consume the PayloadVersion and BundleVersion build variables."
}
if (-not $msiText.Contains('$(var.MsiVersion)')) {
    throw "Package.wxs must consume the MsiVersion build variable."
}
if (-not $msiText.Contains('Include="$(var.LauncherDirectory)\**"') -or
    -not $msiText.Contains('Exclude Files="$(var.LauncherPath)"')) {
    throw "Package.wxs must install every launcher publish output while keeping LauncherExe explicitly authored."
}
foreach ($shortcutId in @('DesktopShortcut', 'StartMenuShortcut')) {
    if ($msiText -notmatch ('(?s)<Shortcut\s+Id="' + [regex]::Escape($shortcutId) + '"[^>]*Advertise="no"[^>]*/>')) {
        throw "Package.wxs must create $shortcutId as a direct, non-advertised executable shortcut."
    }
}
if ($msiText -match '(?s)<Shortcut\s+[^>]*Advertise="yes"') {
    throw "Package.wxs must not create advertised shortcuts; they can appear as blank, non-launching desktop files."
}
if ($msiText -notmatch '(?s)<Shortcut\s+Id="DesktopShortcut"[^>]*WorkingDirectory="LauncherFolder"' -or
    $msiText -notmatch '(?s)<Shortcut\s+Id="StartMenuShortcut"[^>]*WorkingDirectory="LauncherFolder"') {
    throw "OntoTwin shortcuts must use LauncherFolder as their working directory."
}
if ($msiText -notmatch '(?s)<Shortcut\s+Id="DesktopShortcut"[^>]*Target="\[LauncherFolder\]OntoTwin-ZHHZ-Launcher\.exe"' -or
    $msiText -notmatch '(?s)<Shortcut\s+Id="StartMenuShortcut"[^>]*Target="\[LauncherFolder\]OntoTwin-ZHHZ-Launcher\.exe"') {
    throw "OntoTwin shortcuts must target the installed launcher executable directly."
}
foreach ($requiredMsiLifecycleFragment in @(
    'FileRef="PayloadInstallerExe"',
    'ExeCommand="uninstall &quot;$(var.PayloadVersion)&quot;"',
    '--remove-backend-if-version &quot;$(var.PayloadVersion)&quot;',
    'Before="RemoveApplicationPayload"',
    'Before="RemoveFiles"',
    'REMOVE~=&quot;ALL&quot; AND NOT UPGRADINGPRODUCTCODE'
)) {
    if (-not $msiText.Contains($requiredMsiLifecycleFragment)) {
        throw "Package.wxs is missing rollback-safe uninstall lifecycle wiring: $requiredMsiLifecycleFragment"
    }
}
if ($msiText.Contains('NOT BURNMSIUNINSTALL')) {
    throw "Bundle uninstall must not skip Hyper-V or application payload cleanup."
}
if (Test-Path -LiteralPath $output) {
    if (@(Get-ChildItem -LiteralPath $output -Force).Count -gt 0) { throw "OutputDirectory must be empty: $output" }
} else {
    New-Item -ItemType Directory -Path $output | Out-Null
}

$work = Join-Path ([System.IO.Path]::GetTempPath()) ("ontotwin-installer-" + [Guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $work | Out-Null
try {
    $publish = Join-Path $work "publish"
    $launcherOutput = Join-Path $publish "Launcher"
    $serviceOutput = Join-Path $publish "Service"
    $environmentOutput = Join-Path $publish "Environment"
    $payloadInstallerOutput = Join-Path $publish "PayloadInstaller"
    $msiCustomerReadme = Join-Path $work "Deployment-Guide.md"
    Write-ReleaseDocument `
        -Source (Join-Path $deployRoot "CUSTOMER-README.md") `
        -Destination $msiCustomerReadme `
        -Descriptor $releaseDescriptor

    if ($ExistingPayloadArchive) {
        $payloadArchive = [System.IO.Path]::GetFullPath($ExistingPayloadArchive)
        $payloadChecksum = "$payloadArchive.sha256"
        if (-not (Test-Path -LiteralPath $payloadArchive -PathType Leaf) -or
            -not (Test-Path -LiteralPath $payloadChecksum -PathType Leaf)) {
            throw "Existing payload archive or checksum is missing: $payloadArchive"
        }
        $expectedPayloadHash = ((Get-Content -Raw -Encoding UTF8 -LiteralPath $payloadChecksum) -split '\s+')[0]
        $actualPayloadHash = (Get-FileHash -LiteralPath $payloadArchive -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($actualPayloadHash -ne $expectedPayloadHash.ToLowerInvariant()) {
            throw "Existing payload archive failed SHA-256 validation: $payloadArchive"
        }
        $payloadHash = $actualPayloadHash
        Assert-PayloadArchiveMatches -Archive $payloadArchive -PayloadRoot $appPayload -ExpectedVersion $releaseVersion
        Write-Host "Reusing application payload archive after identity and component validation."
    } else {
        $payloadArchive = Join-Path $work "OntoTwin-ZHHZ.payload.zip"
        Write-Host "Creating the application payload archive..."
        [System.IO.Compression.ZipFile]::CreateFromDirectory(
            $appPayload,
            $payloadArchive,
            [System.IO.Compression.CompressionLevel]::Fastest,
            $false)
        $payloadHash = (Get-FileHash -LiteralPath $payloadArchive -Algorithm SHA256).Hash.ToLowerInvariant()
        $payloadChecksum = "$payloadArchive.sha256"
        [System.IO.File]::WriteAllText(
            $payloadChecksum,
            "$payloadHash  OntoTwin-ZHHZ.payload.zip`n",
            [System.Text.UTF8Encoding]::new($false))
        Assert-PayloadArchiveMatches -Archive $payloadArchive -PayloadRoot $appPayload -ExpectedVersion $releaseVersion
    }
    if ($payloadHash -cnotmatch '^[0-9a-f]{64}$') { throw "Payload SHA-256 is not canonical: $payloadHash" }

    $projects = @(
        [pscustomobject]@{ Output = $launcherOutput; Project = Join-Path $deployRoot "launcher\OntoTwin.ZHHZ.Launcher\OntoTwin.ZHHZ.Launcher.csproj"; BindPayloadHash = $false },
        [pscustomobject]@{ Output = $serviceOutput; Project = Join-Path $deployRoot "host-service\OntoTwin.ZHHZ.HostService\OntoTwin.ZHHZ.HostService.csproj"; BindPayloadHash = $false },
        [pscustomobject]@{ Output = $environmentOutput; Project = Join-Path $installerRoot "EnvironmentBootstrapper\EnvironmentBootstrapper.csproj"; BindPayloadHash = $false },
        [pscustomobject]@{ Output = $payloadInstallerOutput; Project = Join-Path $installerRoot "PayloadInstaller\PayloadInstaller.csproj"; BindPayloadHash = $true }
    )
    foreach ($item in $projects) {
        $publishProperties = @("-p:Version=$($releaseDescriptor.BinaryVersion)")
        if ($item.BindPayloadHash) { $publishProperties += "-p:PayloadExpectedSha256=$payloadHash" }
        & dotnet publish $item.Project -c Release -r win-x64 --self-contained true `
            -p:PublishSingleFile=true @publishProperties -o $item.Output --nologo
        if ($LASTEXITCODE -ne 0) { throw "dotnet publish failed: $($item.Project)" }
    }
    foreach ($requiredLauncherFile in @(
        'OntoTwin-ZHHZ-Launcher.exe',
        'D3DCompiler_47_cor3.dll',
        'PenImc_cor3.dll',
        'PresentationNative_cor3.dll',
        'vcruntime140_cor3.dll',
        'wpfgfx_cor3.dll'
    )) {
        $requiredLauncherPath = Join-Path $launcherOutput $requiredLauncherFile
        if (-not (Test-Path -LiteralPath $requiredLauncherPath -PathType Leaf)) {
            throw "Self-contained WPF launcher dependency is missing from publish output: $requiredLauncherPath"
        }
    }
    if ($CodeSigningCertificateThumbprint) {
        foreach ($item in $projects) {
            foreach ($publishedExecutable in Get-ChildItem -LiteralPath $item.Output -Filter "*.exe" -File) {
                Invoke-CodeSigning `
                    -File $publishedExecutable.FullName `
                    -SignTool $signToolPath `
                    -CertificateThumbprint $CodeSigningCertificateThumbprint
            }
        }
    }

    $msiProject = Join-Path $installerRoot "Msi\OntoTwin.ZHHZ.Msi.wixproj"
    Clear-ProjectBuildArtifacts -ProjectDirectory (Split-Path -Parent $msiProject)
    & dotnet build $msiProject -c Release -t:Rebuild --nologo `
        "-p:MsiVersion=$($releaseDescriptor.MsiVersion)" `
        "-p:PayloadVersion=$releaseVersion" `
        "-p:LauncherPath=$(Join-Path $launcherOutput 'OntoTwin-ZHHZ-Launcher.exe')" `
        "-p:LauncherDirectory=$launcherOutput" `
        "-p:LauncherIconPath=$(Join-Path $deployRoot 'launcher\OntoTwin.ZHHZ.Launcher\LingYunZhi.ico')" `
        "-p:ServicePath=$(Join-Path $serviceOutput 'OntoTwin-ZHHZ-HostService.exe')" `
        "-p:HostScriptPath=$(Join-Path $deployRoot 'hyperv\host\HostControl.ps1')" `
        "-p:PayloadInstallerPath=$(Join-Path $payloadInstallerOutput 'OntoTwin-ZHHZ-PayloadInstaller.exe')" `
        "-p:CustomerReadmePath=$msiCustomerReadme"
    if ($LASTEXITCODE -ne 0) { throw "MSI build failed." }
    $msi = Join-Path $installerRoot "Msi\bin\x64\Release\OntoTwin.ZHHZ.Msi.msi"
    if ($CodeSigningCertificateThumbprint) {
        Invoke-CodeSigning -File $msi -SignTool $signToolPath -CertificateThumbprint $CodeSigningCertificateThumbprint
    }

    $bundleProject = Join-Path $installerRoot "Bundle\OntoTwin.ZHHZ.Bundle.wixproj"
    Clear-ProjectBuildArtifacts -ProjectDirectory (Split-Path -Parent $bundleProject)
    & dotnet build $bundleProject -c Release -t:Rebuild --nologo `
        "-p:BundleVersion=$($releaseDescriptor.BundleVersion)" `
        "-p:PayloadVersion=$releaseVersion" `
        "-p:LauncherIconPath=$(Join-Path $deployRoot 'launcher\OntoTwin.ZHHZ.Launcher\LingYunZhi.ico')" `
        "-p:EnvironmentBootstrapperPath=$(Join-Path $environmentOutput 'OntoTwin-ZHHZ-Environment.exe')" `
        "-p:EnableHyperVScriptPath=$(Join-Path $deployRoot 'hyperv\host\Enable-HyperV.ps1')" `
        "-p:PayloadInstallerPath=$(Join-Path $payloadInstallerOutput 'OntoTwin-ZHHZ-PayloadInstaller.exe')" `
        "-p:PayloadArchivePath=$payloadArchive" `
        "-p:PayloadChecksumPath=$payloadChecksum" `
        "-p:MsiPath=$msi"
    if ($LASTEXITCODE -ne 0) { throw "Installer bundle build failed." }

    $bundleOutput = Join-Path $installerRoot "Bundle\bin\x64\Release"
    Copy-Item -Path (Join-Path $bundleOutput "*") -Destination $output -Recurse -Force
    Copy-Item -LiteralPath $payloadArchive -Destination (Join-Path $output "OntoTwin-ZHHZ.payload.zip") -Force
    Copy-Item -LiteralPath $payloadChecksum -Destination (Join-Path $output "OntoTwin-ZHHZ.payload.zip.sha256") -Force
    $bundleExe = Join-Path $output "OntoTwin.ZHHZ.Bundle.exe"
    $setupExe = Join-Path $output $releaseDescriptor.SetupFile
    Move-Item -LiteralPath $bundleExe -Destination $setupExe -Force
    if ($CodeSigningCertificateThumbprint) {
        Invoke-CodeSigning -File $setupExe -SignTool $signToolPath -CertificateThumbprint $CodeSigningCertificateThumbprint
    }
    # Burn resolves the external MSI by its build-time filename, so keep that
    # support filename unchanged rather than renaming or duplicating it.
    Write-ReleaseDocument `
        -Source (Join-Path $deployRoot "CUSTOMER-README.md") `
        -Destination (Join-Path $output "Deployment-Guide.md") `
        -Descriptor $releaseDescriptor
    # Build the Chinese delivery filename from code points so Windows PowerShell
    # 5.1 cannot corrupt it when this UTF-8 script is read without a BOM.
    $basicOperationsFileName = (-join @(
        [char]0x57FA, [char]0x7840, [char]0x64CD,
        [char]0x4F5C, [char]0x8BF4, [char]0x660E
    )) + ".md"
    Write-ReleaseDocument `
        -Source (Join-Path $deployRoot "BASIC-OPERATIONS.md") `
        -Destination (Join-Path $output $basicOperationsFileName) `
        -Descriptor $releaseDescriptor
    Copy-Item -LiteralPath (Join-Path $appPayload "release-manifest.json") `
        -Destination (Join-Path $output "release-manifest.json")
    Copy-Item -LiteralPath (Join-Path $appPayload "Appliance\appliance-manifest.json") `
        -Destination (Join-Path $output "appliance-manifest.json")
    Get-ChildItem -LiteralPath $output -Filter "*.wixpdb" -File | Remove-Item -Force

    $deliveredPayload = Join-Path $output "OntoTwin-ZHHZ.payload.zip"
    if ((Get-Item -LiteralPath $deliveredPayload).Length -ne (Get-Item -LiteralPath $payloadArchive).Length) {
        throw "Delivered payload archive size differs from the validated source archive."
    }
    $deliveredPayloadHash = (Get-FileHash -LiteralPath $deliveredPayload -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($deliveredPayloadHash -ne $payloadHash) {
        throw "Delivered payload archive hash differs from the hash embedded in PayloadInstaller."
    }
    $deliveredChecksumHash = ((Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $output "OntoTwin-ZHHZ.payload.zip.sha256")) -split '\s+')[0].ToLowerInvariant()
    if ($deliveredChecksumHash -ne $payloadHash) {
        throw "Delivered payload sidecar hash differs from the hash embedded in PayloadInstaller."
    }

    $deliveryHashes = foreach ($file in Get-ChildItem -LiteralPath $output -File | Sort-Object Name) {
        "{0}  {1}" -f ((Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()), $file.Name
    }
    [System.IO.File]::WriteAllLines((Join-Path $output "SHA256SUMS"), $deliveryHashes, [System.Text.UTF8Encoding]::new($false))
} finally {
    if (Test-Path -LiteralPath $work) { Remove-Item -LiteralPath $work -Recurse -Force }
}

Write-Host "Installer media created: $output" -ForegroundColor Green
