internal static class PayloadDirectoryPolicy
{
    internal static bool IsCurrentDirectoryName(string leaf) =>
        leaf.Equals("App", StringComparison.OrdinalIgnoreCase) ||
        (leaf.StartsWith("App-", StringComparison.OrdinalIgnoreCase) && leaf.Length > 4);

    internal static bool IsLegacyCleanupDirectoryName(string leaf) =>
        leaf.Equals(".app-previous", StringComparison.OrdinalIgnoreCase) ||
        leaf.Equals(".app-new", StringComparison.OrdinalIgnoreCase);

    internal static bool IsCleanupCandidate(string leaf) =>
        IsCurrentDirectoryName(leaf) || IsLegacyCleanupDirectoryName(leaf);
}
