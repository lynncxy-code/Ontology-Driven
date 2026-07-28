var failures = new List<string>();

void Expect(
    string name,
    bool expected,
    bool probeSucceeded,
    string? busType,
    bool isBoot = false,
    bool isSystem = false,
    bool isSystemVolume = false)
{
    var actual = DiskPlacementPolicy.IsEligible(
        probeSucceeded,
        busType,
        isBoot,
        isSystem,
        isSystemVolume);
    if (actual != expected) failures.Add($"{name}: expected {expected}, got {actual}");
}

foreach (var bus in new[] { "NVMe", "SATA", "SAS", "RAID", "SCSI", "ATA", "Storage Spaces", "SCM", "UFS" })
    Expect($"local {bus}", true, true, bus);

foreach (var bus in new[] { "USB", "SD", "MMC", "Unknown", "iSCSI", "Fibre Channel", "File Backed Virtual", "1394", "" })
    Expect($"excluded {bus}", false, true, bus);

Expect("probe failure on external volume", false, false, null);
Expect("probe failure on system volume", true, false, null, isSystemVolume: true);
Expect("unknown boot disk remains excluded", false, true, "Unknown", isBoot: true);
Expect("USB system disk remains excluded", false, true, "USB", isSystem: true, isSystemVolume: true);
Expect("NVMe system disk is eligible", true, true, "NVMe", isSystem: true, isSystemVolume: true);

foreach (var allowedName in new[] { "App", "app", "App-3.7.1-R1-RC9.4-a1b2", ".app-previous", ".APP-NEW" })
{
    if (!PayloadDirectoryPolicy.IsCleanupCandidate(allowedName))
        failures.Add($"cleanup allowlist rejected {allowedName}");
}
foreach (var rejectedName in new[] { "App-", "Application", "Data", ".app-staging-123", ".app-previous-2", ".git", "" })
{
    if (PayloadDirectoryPolicy.IsCleanupCandidate(rejectedName))
        failures.Add($"cleanup allowlist accepted {rejectedName}");
}

if (failures.Count == 0)
{
    Console.WriteLine("Payload placement policy tests: PASS");
    return 0;
}

foreach (var failure in failures) Console.Error.WriteLine(failure);
return 1;
