internal static class DiskPlacementPolicy
{
    internal static bool IsEligible(
        bool probeSucceeded,
        string? busType,
        bool isBoot,
        bool isSystem,
        bool isSystemVolume)
    {
        // If Storage/CIM is unavailable, never guess that an arbitrary fixed
        // disk is local. The Windows system volume is the only new-placement
        // fallback; already registered paths are handled before this policy.
        if (!probeSucceeded) return isSystemVolume;

        var normalized = (busType ?? "").Replace(" ", "", StringComparison.Ordinal).Trim();
        return normalized.Equals("SCSI", StringComparison.OrdinalIgnoreCase) ||
               normalized.Equals("ATA", StringComparison.OrdinalIgnoreCase) ||
               normalized.Equals("RAID", StringComparison.OrdinalIgnoreCase) ||
               normalized.Equals("SAS", StringComparison.OrdinalIgnoreCase) ||
               normalized.Equals("SATA", StringComparison.OrdinalIgnoreCase) ||
               normalized.Equals("StorageSpaces", StringComparison.OrdinalIgnoreCase) ||
               normalized.Equals("NVMe", StringComparison.OrdinalIgnoreCase) ||
               normalized.Equals("SCM", StringComparison.OrdinalIgnoreCase) ||
               normalized.Equals("UFS", StringComparison.OrdinalIgnoreCase);
    }
}
