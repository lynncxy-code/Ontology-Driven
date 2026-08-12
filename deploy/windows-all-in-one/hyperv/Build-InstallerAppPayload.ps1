[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$ReleaseDirectory,

    [Parameter(Mandatory = $true)]
    [string]$ApplianceDirectory,

    [Parameter(Mandatory = $true)]
    [string]$OutputDirectory,

    [string]$WslDistribution = "Ubuntu-22.04"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Assert-CanonicalReleaseVersion {
    param([Parameter(Mandatory = $true)][string]$Version)

    if ($Version -cnotmatch '^\d+\.\d+\.\d+-r\d+-rc\d+(?:\.\d+)?$') {
        throw "Release manifest version is not canonical: $Version"
    }
}

function Convert-ToWslPath {
    param([Parameter(Mandatory = $true)][string]$WindowsPath)

    $fullPath = [System.IO.Path]::GetFullPath($WindowsPath)
    if ($fullPath -notmatch '^([A-Za-z]):[\\/](.*)$') {
        throw "Only local drive paths can be inspected by the WSL appliance toolchain: $fullPath"
    }
    return "/mnt/$($Matches[1].ToLowerInvariant())/$($Matches[2].Replace('\', '/'))"
}

function Assert-UnixTextFormat {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$ExpectedPrefix
    )

    $bytes = [System.IO.File]::ReadAllBytes($Path)
    $prefixBytes = [System.Text.Encoding]::ASCII.GetBytes($ExpectedPrefix)
    if ($bytes.Length -lt $prefixBytes.Length) {
        throw "Linux payload text is truncated: $Path"
    }
    if ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) {
        throw "Linux payload text must not contain a UTF-8 BOM: $Path"
    }
    if ($bytes.Length -ge 2 -and
        (($bytes[0] -eq 0xFF -and $bytes[1] -eq 0xFE) -or
         ($bytes[0] -eq 0xFE -and $bytes[1] -eq 0xFF))) {
        throw "Linux payload text must not contain a UTF-16 BOM: $Path"
    }
    if ($bytes -contains [byte]0x0D) {
        throw "Linux payload text contains CR/CRLF bytes and is unsafe for the appliance: $Path"
    }
    for ($index = 0; $index -lt $prefixBytes.Length; $index++) {
        if ($bytes[$index] -ne $prefixBytes[$index]) {
            throw "Linux payload text does not begin with the required LF-only interpreter line: $Path"
        }
    }
    if ($bytes[$bytes.Length - 1] -ne 0x0A) {
        throw "Linux payload text must end with LF: $Path"
    }
}

function Assert-RootCapacitySafety {
    param([Parameter(Mandatory = $true)][string]$BootstrapText)

    $rootCapacityFunction = [regex]::Match(
        $BootstrapText,
        '(?ms)^ensure_root_filesystem_capacity\(\) \{.*?^\}')
    if (-not $rootCapacityFunction.Success) {
        throw "Guest bootstrap is missing ensure_root_filesystem_capacity."
    }
    $rootCapacityText = $rootCapacityFunction.Value
    foreach ($requirement in @(
        'if [ "$root_size_bytes" -lt 17179869184 ]; then',
        'partition_file="/sys/class/block/$root_device_name/partition"',
        'part_number="$(awk ''NF {print $1; exit}'' "$partition_file")"',
        '[[ "$part_number" =~ ^[0-9]+$ ]]',
        '[ "$root_device_type" = "part" ]',
        '[ "$parent_type" = "disk" ]',
        'growpart "/dev/$parent_name" "$part_number"'
    )) {
        if (-not $rootCapacityText.Contains($requirement)) {
            throw "Guest bootstrap root expansion safety requirement is missing: $requirement"
        }
    }
    if ($rootCapacityText -match '(?m)lsblk\s+-no\s+PARTN' -or
        $rootCapacityText -match "awk\s+'NF\s*\{print;\s*exit\}'") {
        throw "Guest bootstrap must not pass padded lsblk PARTN output to growpart."
    }
    if ($rootCapacityText.IndexOf('if [ "$root_size_bytes" -lt 17179869184 ]; then', [System.StringComparison]::Ordinal) -ge
        $rootCapacityText.IndexOf('growpart "/dev/$parent_name" "$part_number"', [System.StringComparison]::Ordinal)) {
        throw "Guest bootstrap must check root capacity before attempting growpart."
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
    $ufsText = Get-Content -Raw -Encoding UTF8 -LiteralPath $ufsPath
    $nonUfsText = Get-Content -Raw -Encoding UTF8 -LiteralPath $nonUfsPath
    $combinedText = $ufsText + [Environment]::NewLine + $nonUfsText
    if ($combinedText -match '(?i)(^|[/\\])(test0316|tmp_ue)([/\\]|$)') {
        throw "The Shipping manifests contain a forbidden test project identity."
    }
    if ($combinedText -match '(?i)PixelStreaming') {
        throw "Pixel Streaming files are present in the Shipping manifests."
    }
    if ($ufsText -notmatch '(?im)^ZHHZ[/\\]ZHHZ\.uproject(?:\s|$)') {
        throw "The UFS manifest does not contain the ZHHZ project descriptor."
    }
    if ($ufsText -notmatch '(?im)^ZHHZ[/\\]Plugins[/\\]glTFRuntime[/\\]glTFRuntime\.uplugin(?:\s|$)') {
        throw "The UFS manifest does not contain the required glTFRuntime plugin."
    }
    if ($ufsText -notmatch '(?im)^ZHHZ[/\\]Plugins[/\\]OntoTwinSync[/\\]OntoTwinSync\.uplugin(?:\s|$)') {
        throw "The UFS manifest does not contain the required OntoTwinSync plugin."
    }
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

    # Collapse shell line continuations so the teardown command can be checked
    # as one logical command instead of relying on its current formatting.
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

function Normalize-SeedText {
    param([AllowEmptyString()][string]$Text)

    return $Text.Replace("`r`n", "`n").TrimEnd([char[]]@("`r", "`n"))
}

$release = [System.IO.Path]::GetFullPath($ReleaseDirectory)
$appliance = [System.IO.Path]::GetFullPath($ApplianceDirectory)
$output = [System.IO.Path]::GetFullPath($OutputDirectory)
$guestRoot = Join-Path $PSScriptRoot "guest"
$expectedPayloadPort = 48075

foreach ($required in @(
    (Join-Path $release "ZHHZ\ZHHZ.exe"),
    (Join-Path $release "ZHHZ\ontotwin-runtime-manifest.json"),
    (Join-Path $release "ZHHZ\Manifest_UFSFiles_Win64.txt"),
    (Join-Path $release "ZHHZ\Manifest_NonUFSFiles_Win64.txt"),
    (Join-Path $release "release-manifest.json"),
    (Join-Path $release "Deploy\docker-compose.release.yml"),
    (Join-Path $release "Deploy\customer.env.example"),
    (Join-Path $appliance "appliance-manifest.json"),
    (Join-Path $appliance "ontotwin-ubuntu.vhdx"),
    (Join-Path $appliance "seed.iso"),
    (Join-Path $appliance "docker-static.tgz"),
    (Join-Path $appliance "docker-compose")
)) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) { throw "Required payload file is missing: $required" }
}
$applianceManifestPath = Join-Path $appliance "appliance-manifest.json"
$applianceManifest = Get-Content -Raw -LiteralPath $applianceManifestPath | ConvertFrom-Json
$seedIsoPath = Join-Path $appliance "seed.iso"
$baseDiskPath = Join-Path $appliance "ontotwin-ubuntu.vhdx"
$actualSeedHash = (Get-FileHash -LiteralPath $seedIsoPath -Algorithm SHA256).Hash.ToLowerInvariant()
$actualDiskHash = (Get-FileHash -LiteralPath $baseDiskPath -Algorithm SHA256).Hash.ToLowerInvariant()
$actualDockerHash = (Get-FileHash -LiteralPath (Join-Path $appliance "docker-static.tgz") -Algorithm SHA256).Hash.ToLowerInvariant()
$actualComposeHash = (Get-FileHash -LiteralPath (Join-Path $appliance "docker-compose") -Algorithm SHA256).Hash.ToLowerInvariant()
$systemDiskSizeGb = [int]$applianceManifest.system_disk_size_gb
$minimumGuestRootSizeGb = [int]$applianceManifest.minimum_guest_root_size_gb
$minimumGuestRootFreeGb = [int]$applianceManifest.minimum_guest_root_free_gb
if ($systemDiskSizeGb -ne 20 -or $minimumGuestRootSizeGb -ne 16 -or $minimumGuestRootFreeGb -ne 8) {
    throw "Appliance capacity contract must be system disk/root/root-free = 20/16/8 GiB."
}
$baseDiskLinux = Convert-ToWslPath $baseDiskPath
$vhdInfoText = (& wsl.exe -d $WslDistribution -u root -- qemu-img info --output=json $baseDiskLinux) -join "`n"
if ($LASTEXITCODE -ne 0) { throw "Cannot inspect appliance VHDX virtual capacity with qemu-img." }
$vhdInfo = $vhdInfoText | ConvertFrom-Json
if ([int64]$vhdInfo.'virtual-size' -ne [int64]$systemDiskSizeGb * 1GB) {
    throw "Appliance VHDX virtual capacity does not match system_disk_size_gb."
}
if ($actualSeedHash -ne [string]$applianceManifest.seed_iso_sha256) {
    throw "Appliance seed hash does not match appliance-manifest.json."
}
if ($actualDiskHash -ne [string]$applianceManifest.system_vhdx_sha256) {
    throw "Appliance system disk hash does not match appliance-manifest.json."
}
if ($actualDockerHash -ne [string]$applianceManifest.docker_engine_sha256) {
    throw "Docker engine payload hash does not match appliance-manifest.json."
}
if ($actualComposeHash -ne [string]$applianceManifest.docker_compose_sha256) {
    throw "Docker Compose payload hash does not match appliance-manifest.json."
}
$seedContent = @{}
foreach ($seedName in @("user-data", "network-config", "meta-data")) {
    $seedText = (& tar.exe -xOf $seedIsoPath $seedName) -join "`n"
    if ($LASTEXITCODE -ne 0) { throw "Cannot read $seedName from appliance seed ISO." }
    $sourceText = Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $guestRoot "cloud-init\$seedName")
    if ((Normalize-SeedText $seedText) -cne (Normalize-SeedText $sourceText)) {
        throw "Appliance seed ISO contains stale $seedName; rebuild it from the current Hyper-V guest sources."
    }
    $seedContent[$seedName] = $seedText
}
$seedUserData = [string]$seedContent["user-data"]
$expectedPayloadEndpoint = "http://172.28.251.1:$expectedPayloadPort"
if (-not $seedUserData.Contains($expectedPayloadEndpoint)) {
    throw "Appliance seed does not use the host payload port $expectedPayloadPort."
}
if ($seedUserData -notmatch '(?ms)^growpart:\s*.*?^\s+devices:\s*\[''\/''\]\s*$' -or
    $seedUserData -notmatch '(?m)^resize_rootfs:\s*true\s*$') {
    throw "Appliance seed must explicitly grow the root partition and filesystem."
}
$bootstrapPath = Join-Path $guestRoot "bootstrap.sh"
Assert-UnixTextFormat -Path $bootstrapPath -ExpectedPrefix "#!/bin/bash`n"
$controlPath = Join-Path $guestRoot "control.py"
Assert-UnixTextFormat -Path $controlPath -ExpectedPrefix "#!/usr/bin/env python3`n"
$bootstrapText = Get-Content -Raw -Encoding UTF8 -LiteralPath $bootstrapPath
$controlText = Get-Content -Raw -Encoding UTF8 -LiteralPath $controlPath
if (-not $bootstrapText.Contains($expectedPayloadEndpoint)) {
    throw "Guest bootstrap does not use the host payload port $expectedPayloadPort."
}
Assert-RootCapacitySafety -BootstrapText $bootstrapText
$composeText = Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $release "Deploy\docker-compose.release.yml")
Assert-BackendUpgradeSafety -BootstrapText $bootstrapText -ComposeText $composeText -ControlText $controlText
$releaseManifest = Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $release "release-manifest.json") | ConvertFrom-Json
$releaseVersion = [string]$releaseManifest.release_version
Assert-CanonicalReleaseVersion -Version $releaseVersion
if ($releaseManifest.PSObject.Properties.Name -notcontains "component_versions") {
    throw "Release manifest does not contain component_versions."
}
if ([string]$releaseManifest.component_versions.release_version -ne $releaseVersion) {
    throw "Release manifest component version does not match release_version."
}
if ([bool]$releaseManifest.pixel_streaming_included) {
    throw "Release manifest enables Pixel Streaming, which is forbidden in this release."
}
if ($releaseManifest.PSObject.Properties.Name -notcontains "reset_backend_baseline_on_upgrade") {
    throw "Release manifest does not declare reset_backend_baseline_on_upgrade."
}
if ([bool]$releaseManifest.reset_backend_baseline_on_upgrade) {
    foreach ($requiredResetFragment in @(
        'baseline-backups/',
        'previous_bootstrap_incomplete=false',
        '[ -f "$BOOTSTRAP_IN_PROGRESS" ]',
        '[ "$previous_bootstrap_incomplete" = true ]',
        'systemctl stop docker.service',
        'mv "$DATA_ROOT/docker" "$baseline_backup_root/docker"',
        'mv "$DATA_ROOT/release-data" "$baseline_backup_root/release-data"',
        'rm -f "$PAYLOAD_MARKER" "$IMAGES_MARKER"',
        'systemctl start docker.service'
    )) {
        if (-not $bootstrapText.Contains($requiredResetFragment)) {
            throw "Guest bootstrap is missing the recoverable baseline reset contract: $requiredResetFragment"
        }
    }
}
$customerEnvironmentPath = Join-Path $release "Deploy\customer.env.example"
$customerEnvironment = Get-Content -Raw -Encoding UTF8 -LiteralPath $customerEnvironmentPath
Assert-ReleaseDeployMatchesSource `
    -SourceDeployRoot ([System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))) `
    -ReleaseCompose $composeText `
    -ReleaseEnvironment $customerEnvironment `
    -Manifest $releaseManifest
if ((Get-EnvironmentValue -Content $customerEnvironment -Key "ONTOTWIN_RELEASE_VERSION") -ne $releaseVersion) {
    throw "Customer environment release version does not match release-manifest.json."
}
foreach ($imageGate in @(
    [pscustomobject]@{ Key = "BACKEND_IMAGE"; Component = "backend_image"; Archive = "ontotwin-backend.tar" },
    [pscustomobject]@{ Key = "POSTGRES_IMAGE"; Component = "postgres_image"; Archive = "postgres.tar" },
    [pscustomobject]@{ Key = "NEO4J_IMAGE"; Component = "neo4j_image"; Archive = "neo4j.tar" }
)) {
    $configuredTag = Get-EnvironmentValue -Content $customerEnvironment -Key $imageGate.Key
    if ($configuredTag -ne [string]$releaseManifest.component_versions.images.($imageGate.Component)) {
        throw "Customer environment $($imageGate.Key) does not match component_versions."
    }
    Assert-DockerArchiveTag -Archive (Join-Path $release "Images\$($imageGate.Archive)") -ExpectedTag $configuredTag
}
$runtimeIdentity = Get-Content -Raw -LiteralPath (Join-Path $release "ZHHZ\ontotwin-runtime-manifest.json") | ConvertFrom-Json
if ($runtimeIdentity.project_name -ne "ZHHZ" -or $runtimeIdentity.target_name -ne "ZHHZ") {
    throw "Installer runtime identity mismatch: project='$($runtimeIdentity.project_name)', target='$($runtimeIdentity.target_name)'."
}
if ([string]$releaseManifest.runtime_project -ne [string]$runtimeIdentity.project_name -or
    [string]$releaseManifest.runtime_target -ne [string]$runtimeIdentity.target_name -or
    [string]$releaseManifest.runtime_source_sha256 -ne [string]$runtimeIdentity.source_project_sha256 -or
    [string]$releaseManifest.component_versions.runtime.project_name -ne [string]$runtimeIdentity.project_name -or
    [string]$releaseManifest.component_versions.runtime.target_name -ne [string]$runtimeIdentity.target_name -or
    [string]$releaseManifest.component_versions.runtime.source_project_sha256 -ne [string]$runtimeIdentity.source_project_sha256) {
    throw "Release manifest runtime identity does not match ontotwin-runtime-manifest.json."
}
Assert-RuntimeEvidence `
    -RuntimeRoot (Join-Path $release "ZHHZ") `
    -RuntimeIdentity $runtimeIdentity `
    -RuntimeComponent $releaseManifest.component_versions.runtime
Assert-RuntimePackaging -RuntimeRoot (Join-Path $release "ZHHZ")

if (Test-Path -LiteralPath $output) {
    if (@(Get-ChildItem -LiteralPath $output -Force).Count -gt 0) { throw "OutputDirectory must be empty: $output" }
} else {
    New-Item -ItemType Directory -Path $output | Out-Null
}

$backendPayload = Join-Path $output "BackendPayload"
$applianceOutput = Join-Path $output "Appliance"
New-Item -ItemType Directory -Path $backendPayload,$applianceOutput | Out-Null

Copy-Item -LiteralPath (Join-Path $release "ZHHZ") -Destination $output -Recurse
# The packaged UE runtime resolves external GLB assets from a Models folder
# next to ZHHZ.exe. Keep a second copy in the guest release archive below for
# backend/API access, but place the Windows runtime copy here as well.
Copy-Item -LiteralPath (Join-Path $release "Models") -Destination (Join-Path $output "ZHHZ") -Recurse
$releaseManifest.component_versions = [ordered]@{
    release_version = $releaseVersion
    base_release_version = [string]$releaseManifest.component_versions.base_release_version
    data_version = [string]$releaseManifest.component_versions.data_version
    runtime = $releaseManifest.component_versions.runtime
    images = $releaseManifest.component_versions.images
    installer = $releaseManifest.component_versions.installer
    appliance = [ordered]@{
        version = [string]$applianceManifest.version
        system_vhdx_sha256 = $actualDiskHash
        seed_iso_sha256 = $actualSeedHash
        payload_port = $expectedPayloadPort
        system_disk_size_gb = $systemDiskSizeGb
        minimum_guest_root_size_gb = $minimumGuestRootSizeGb
        minimum_guest_root_free_gb = $minimumGuestRootFreeGb
        docker_engine_version = [string]$applianceManifest.docker_engine_version
        docker_engine_sha256 = $actualDockerHash
        docker_compose_version = [string]$applianceManifest.docker_compose_version
        docker_compose_sha256 = $actualComposeHash
    }
}
[System.IO.File]::WriteAllText(
    (Join-Path $output "release-manifest.json"),
    ($releaseManifest | ConvertTo-Json -Depth 10),
    [System.Text.UTF8Encoding]::new($false))
foreach ($name in @("ontotwin-ubuntu.vhdx", "seed.iso", "appliance-manifest.json")) {
    Copy-Item -LiteralPath (Join-Path $appliance $name) -Destination $applianceOutput
}

Copy-Item -LiteralPath (Join-Path $guestRoot "bootstrap.sh") -Destination $backendPayload
Copy-Item -LiteralPath (Join-Path $guestRoot "control.py") -Destination $backendPayload
Assert-UnixTextFormat -Path (Join-Path $backendPayload "bootstrap.sh") -ExpectedPrefix "#!/bin/bash`n"
Assert-UnixTextFormat -Path (Join-Path $backendPayload "control.py") -ExpectedPrefix "#!/usr/bin/env python3`n"
Copy-Item -LiteralPath (Join-Path $appliance "docker-static.tgz") -Destination $backendPayload
Copy-Item -LiteralPath (Join-Path $appliance "docker-compose") -Destination $backendPayload

$imageMap = [ordered]@{
    "ontotwin-backend.tar" = "backend-image.tar"
    "postgres.tar" = "postgres-image.tar"
    "neo4j.tar" = "neo4j-image.tar"
}
foreach ($sourceName in $imageMap.Keys) {
    $source = Join-Path $release "Images\$sourceName"
    if (-not (Test-Path -LiteralPath $source -PathType Leaf)) { throw "Release image is missing: $source" }
    $componentProperty = switch ($sourceName) {
        "ontotwin-backend.tar" { "backend_sha256" }
        "postgres.tar" { "postgres_sha256" }
        "neo4j.tar" { "neo4j_sha256" }
    }
    $expectedImageHash = [string]$releaseManifest.component_versions.images.$componentProperty
    $actualImageHash = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actualImageHash -ne $expectedImageHash) {
        throw "Release image hash does not match component_versions: $sourceName"
    }
    Copy-Item -LiteralPath $source -Destination (Join-Path $backendPayload $imageMap[$sourceName])
}

$releaseStage = Join-Path ([System.IO.Path]::GetTempPath()) ("ontotwin-release-" + [Guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $releaseStage | Out-Null
try {
    $guestDeploy = Join-Path $releaseStage "Deploy"
    New-Item -ItemType Directory -Path $guestDeploy | Out-Null
    foreach ($name in @("docker-compose.release.yml", "customer.env.example")) {
        Copy-Item -LiteralPath (Join-Path $release "Deploy\$name") -Destination $guestDeploy
    }
    foreach ($name in @("Models", "Database", "Data")) {
        Copy-Item -LiteralPath (Join-Path $release $name) -Destination $releaseStage -Recurse
    }
    Copy-Item -LiteralPath (Join-Path $output "release-manifest.json") -Destination $releaseStage
    $releaseArchive = Join-Path $backendPayload "release.tar.gz"
    & tar.exe -czf $releaseArchive -C $releaseStage .
    if ($LASTEXITCODE -ne 0) { throw "Backend release archive creation failed." }
    $nestedManifest = Read-TarJsonMember -Archive $releaseArchive -RelativePath "release-manifest.json"
    if ([string]$nestedManifest.release_version -ne $releaseVersion) {
        throw "Nested backend release version '$($nestedManifest.release_version)' does not match '$releaseVersion'."
    }
    if ([string]$nestedManifest.component_versions.release_version -ne $releaseVersion -or
        [string]$nestedManifest.component_versions.appliance.version -ne [string]$applianceManifest.version) {
        throw "Nested backend component_versions do not match the installer application payload."
    }
} finally {
    if (Test-Path -LiteralPath $releaseStage) { Remove-Item -LiteralPath $releaseStage -Recurse -Force }
}

$hashLines = foreach ($file in Get-ChildItem -LiteralPath $backendPayload -File | Where-Object { $_.Name -ne "SHA256SUMS" } | Sort-Object Name) {
    "{0}  {1}" -f ((Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()), $file.Name
}
[System.IO.File]::WriteAllText(
    (Join-Path $backendPayload "SHA256SUMS"),
    (($hashLines -join "`n") + "`n"),
    [System.Text.UTF8Encoding]::new($false))

Write-Host "Installer application payload created: $output" -ForegroundColor Green
