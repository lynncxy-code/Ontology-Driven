using System.IO.Compression;
using System.Diagnostics;
using System.Net.Sockets;
using System.Reflection;
using System.Security.Cryptography;
using System.ServiceProcess;
using System.Text;
using System.Text.Json;
using Microsoft.Win32;

const string ProductKey = @"SOFTWARE\OntoTwin\ZHHZ";
const string ServiceName = "OntoTwinZHHZHost";
const int ServiceControlPort = 48073;
const long NewDataRootFreeBytes = 60L * 1024 * 1024 * 1024;
const long ExistingDataRootFreeBytes = 20L * 1024 * 1024 * 1024;

var logDirectory = Path.Combine(
    Environment.GetFolderPath(Environment.SpecialFolder.CommonApplicationData),
    "OntoTwin-ZHHZ-Installer",
    "Logs");
Directory.CreateDirectory(logDirectory);
var logPath = Path.Combine(logDirectory, "payload-installer.log");

void Log(string message)
{
    var line = $"[{DateTime.Now:yyyy-MM-dd HH:mm:ss}] {message}";
    Console.WriteLine(line);
    try { File.AppendAllText(logPath, line + Environment.NewLine, new UTF8Encoding(false)); }
    catch { /* Console output remains available if logging is unavailable. */ }
}

if (args.Length == 0)
{
    Console.Error.WriteLine("Usage: install [archive] | uninstall <expected-payload-version>");
    return 2;
}

var programFiles = Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles);
var installRoot = Path.GetFullPath(Path.Combine(programFiles, "OntoTwin", "ZHHZ"));
var legacyDestination = Path.Combine(installRoot, "App");
var legacyDataRoot = Path.Combine(
    Environment.GetFolderPath(Environment.SpecialFolder.CommonApplicationData),
    "OntoTwin-ZHHZ");
var configuredDestination = ReadConfiguredAppRoot();
var configuredDataRoot = ReadConfiguredDataRoot();
var action = args[0].ToLowerInvariant();

if (action == "uninstall")
{
    if (args.Length != 2 || string.IsNullOrWhiteSpace(args[1]))
    {
        Console.Error.WriteLine("A non-empty expected payload version is required for safe uninstall.");
        return 2;
    }
    var expectedPayloadVersion = args[1].Trim();
    var registeredPayloadVersion = ReadConfiguredPayloadVersion();
    if (!string.Equals(registeredPayloadVersion, expectedPayloadVersion, StringComparison.OrdinalIgnoreCase))
    {
        Log($"Skipping application cleanup because payload ownership changed. " +
            $"Expected={expectedPayloadVersion}; Registered={registeredPayloadVersion ?? "<missing>"}. " +
            "This normally means an installer upgrade is rolling back; the registered application was preserved.");
        return 0;
    }

    var destinations = GetTrustedPayloadDirectories(
        configuredDestination,
        legacyDestination,
        installRoot);
    foreach (var destinationToRemove in destinations) StopProcessesUnder(destinationToRemove, Log);
    _ = StopServiceForReplacement(ServiceName, Log);
    foreach (var destinationToRemove in destinations)
        DeletePayloadDirectoryWithRetries(destinationToRemove, installRoot, Log);
    using var key = Registry.LocalMachine.OpenSubKey(ProductKey, writable: true);
    key?.DeleteValue("PayloadVersion", throwOnMissingValue: false);
    key?.DeleteValue("AppRoot", throwOnMissingValue: false);
    return 0;
}
if (action != "install")
{
    Console.Error.WriteLine($"Unsupported action: {action}");
    return 2;
}

var archive = args.Length >= 2 ? Path.GetFullPath(args[1]) : Path.Combine(AppContext.BaseDirectory, "OntoTwin-ZHHZ.payload.zip");
var checksumFile = archive + ".sha256";
if (!File.Exists(archive))
{
    Console.Error.WriteLine($"Payload archive is missing: {archive}");
    return 3;
}
if (!File.Exists(checksumFile))
{
    Console.Error.WriteLine($"Payload checksum is missing: {checksumFile}");
    return 3;
}

var sidecarTokens = File.ReadAllText(checksumFile, Encoding.UTF8)
    .Split((char[]?)null, StringSplitOptions.RemoveEmptyEntries);
if (sidecarTokens.Length == 0)
{
    Console.Error.WriteLine($"Payload checksum file is empty: {checksumFile}");
    return 4;
}
var sidecarExpected = sidecarTokens[0];
var embeddedExpected = Assembly.GetExecutingAssembly()
    .GetCustomAttributes<AssemblyMetadataAttribute>()
    .FirstOrDefault(attribute => attribute.Key.Equals("PayloadSha256", StringComparison.Ordinal))?
    .Value?.Trim();
if (embeddedExpected is null || embeddedExpected.Length != 64 || !embeddedExpected.All(Uri.IsHexDigit))
{
    Console.Error.WriteLine("The payload installer does not contain a valid build-time SHA-256 identity.");
    return 4;
}
if (!sidecarExpected.Equals(embeddedExpected, StringComparison.OrdinalIgnoreCase))
{
    Console.Error.WriteLine(
        $"Payload checksum identity mismatch. The signed installer expects {embeddedExpected}, " +
        $"but the delivery sidecar contains {sidecarExpected}.");
    return 4;
}
Console.WriteLine("Verifying OntoTwin ZHHZ payload...");
await using (var stream = new FileStream(archive, FileMode.Open, FileAccess.Read, FileShare.Read, 4 * 1024 * 1024, true))
{
    var actual = Convert.ToHexString(await SHA256.HashDataAsync(stream)).ToLowerInvariant();
    if (!actual.Equals(embeddedExpected, StringComparison.OrdinalIgnoreCase))
    {
        Console.Error.WriteLine($"Payload SHA-256 mismatch. Expected {embeddedExpected}, got {actual}");
        return 4;
    }
}

long payloadSize;
using (var payload = ZipFile.OpenRead(archive))
    payloadSize = payload.Entries.Sum(entry => entry.Length);

var registrySnapshot = CaptureProductRegistry();
string? destination = null;
string? destinationParent = null;
string? stagingRoot = null;
string? staging = null;
var installedNewDestination = false;
var serviceWasStopped = false;
var serviceSnapshot = ServiceStateSnapshot.NotInstalled;
var payloadVersion = "unknown";
try
{
    Log($"Installing payload from {archive}");
    Directory.CreateDirectory(installRoot);

    if (!string.IsNullOrWhiteSpace(configuredDestination))
        configuredDestination = ValidatePayloadPath(configuredDestination, installRoot);
    var destinationBase = SelectPayloadDestination(
        legacyDestination,
        configuredDestination,
        payloadSize,
        Log);
    destinationBase = ValidatePayloadPath(destinationBase, installRoot);
    destinationParent = Directory.GetParent(destinationBase)?.FullName
        ?? throw new InvalidOperationException($"The payload destination has no parent directory: {destinationBase}");
    Directory.CreateDirectory(destinationParent);
    ValidatePayloadParent(destinationParent, installRoot);

    var dataRootSelection = SelectDataRoot(
        configuredDataRoot,
        legacyDataRoot,
        destinationParent,
        NewDataRootFreeBytes,
        ExistingDataRootFreeBytes,
        Log);
    var dataRoot = dataRootSelection.Path;
    Log($"Backend DataRoot: {dataRoot}");

    // Stage on the destination volume. This avoids requiring write access or
    // another full payload worth of free space beside the installation media,
    // and makes the final directory promotion an atomic same-volume move.
    stagingRoot = Path.Combine(destinationParent, ".ontotwin-installer-staging");
    Directory.CreateDirectory(stagingRoot);
    EnsureOrdinaryDirectory(stagingRoot, "payload staging directory");
    staging = Path.Combine(stagingRoot, "app-" + Guid.NewGuid().ToString("N"));
    Log($"Selected payload parent directory: {destinationParent}");

    var stagingDrive = new DriveInfo(Path.GetPathRoot(stagingRoot)!);
    var stagingRequired = payloadSize + 1024L * 1024 * 1024;
    Log($"Staging drive {stagingDrive.Name} has {stagingDrive.AvailableFreeSpace / 1024d / 1024 / 1024:N2} GB free; " +
        $"the extracted payload is {payloadSize / 1024d / 1024 / 1024:N2} GB.");
    if (stagingDrive.AvailableFreeSpace < stagingRequired)
        throw new IOException($"Not enough free space on staging drive {stagingDrive.Name}. " +
                              $"At least {stagingRequired / 1024d / 1024 / 1024:N2} GB is required.");

    Log("Extracting OntoTwin ZHHZ application files...");
    ZipFile.ExtractToDirectory(archive, staging, overwriteFiles: true);
    foreach (var required in new[]
    {
        Path.Combine(staging, "ZHHZ", "ZHHZ.exe"),
        Path.Combine(staging, "Appliance", "appliance-manifest.json"),
        Path.Combine(staging, "Appliance", "ontotwin-ubuntu.vhdx"),
        Path.Combine(staging, "Appliance", "seed.iso"),
        Path.Combine(staging, "BackendPayload", "SHA256SUMS"),
        Path.Combine(staging, "release-manifest.json")
    })
    {
        if (!File.Exists(required)) throw new InvalidDataException($"Extracted payload is incomplete: {required}");
    }
    using (var manifestDocument = JsonDocument.Parse(
               File.ReadAllText(Path.Combine(staging, "release-manifest.json"), Encoding.UTF8)))
    {
        payloadVersion = manifestDocument.RootElement.GetProperty("release_version").GetString()
            ?? throw new InvalidDataException("The payload release version is empty.");
    }
    if (payloadVersion.Any(character =>
            !(char.IsAsciiLetterOrDigit(character) || character is '.' or '-' or '_')))
        throw new InvalidDataException($"The payload release version is invalid: {payloadVersion}");
    if (payloadVersion.Length is 0 or > 80)
        throw new InvalidDataException($"The payload release version length is invalid: {payloadVersion.Length}");
    Log($"Validated payload version {payloadVersion}.");

    destination = BuildUniqueSideBySideDestination(destinationParent, payloadVersion);
    destination = ValidatePayloadPath(destination, installRoot);
    Log($"Installing into a new side-by-side application directory: {destination}");

    // Keep the current AppRoot intact until the replacement is fully staged
    // and validated. Closing its processes reduces mixed-version execution,
    // but the current files are never moved or deleted by an upgrade.
    if (!string.IsNullOrWhiteSpace(configuredDestination))
        StopProcessesUnder(configuredDestination, Log);
    if (string.IsNullOrWhiteSpace(configuredDestination) ||
        !configuredDestination.Equals(legacyDestination, StringComparison.OrdinalIgnoreCase))
        StopProcessesUnder(legacyDestination, Log);

    var priorBackendExists = !string.IsNullOrWhiteSpace(configuredDestination) ||
                             Directory.Exists(legacyDestination) ||
                             Directory.Exists(Path.Combine(dataRoot, "VM"));
    if (priorBackendExists)
    {
        await QuiesceBackendAsync(
            ServiceName,
            ServiceControlPort,
            installRoot,
            configuredDestination ?? legacyDestination,
            dataRoot,
            Log);
    }
    else
    {
        Log("No previous backend appliance was detected; backend quiescence is not required for this first installation.");
    }
    serviceSnapshot = StopServiceForReplacement(ServiceName, Log);
    serviceWasStopped = serviceSnapshot.Exists;

    InstallStagedDirectory(staging, destination, Log);
    installedNewDestination = true;

    using var key = Registry.LocalMachine.CreateSubKey(ProductKey, writable: true);
    key.SetValue("InstallRoot", installRoot, RegistryValueKind.String);
    key.SetValue("AppRoot", destination, RegistryValueKind.String);
    key.SetValue("DataRoot", dataRoot, RegistryValueKind.String);
    key.SetValue("PayloadVersion", payloadVersion, RegistryValueKind.String);

    RestoreServiceState(ServiceName, serviceSnapshot, Log);

    // The previously registered AppRoot is retained as the one rollback copy.
    // Everything older is now stale and can otherwise consume another 6-7 GiB
    // on every upgrade. Cleanup is best-effort and happens only after the new
    // registry state has committed and the service has been restored.
    try
    {
        CleanupStalePayloadDirectories(
            destination,
            configuredDestination,
            legacyDestination,
            installRoot,
            Log);
    }
    catch (Exception cleanupError)
    {
        Log($"Warning: stale application cleanup was deferred: {cleanupError.Message}");
    }

    Log($"OntoTwin ZHHZ payload {payloadVersion} installed successfully.");
    return 0;
}
catch (Exception exception)
{
    Log("Payload installation failed: " + exception);
    if (serviceWasStopped)
    {
        try { EnsureServiceStopped(ServiceName, Log); }
        catch (Exception stopError) { Log($"Failed to stop the replacement service during rollback: {stopError}"); }
    }

    try { RestoreProductRegistry(registrySnapshot); }
    catch (Exception registryError) { Log($"Failed to restore the previous registry values: {registryError}"); }

    if (installedNewDestination && destination is not null && Directory.Exists(destination))
    {
        try { DeletePayloadDirectoryWithRetries(destination, installRoot, Log); }
        catch (Exception cleanupError) { Log($"Failed to remove the uncommitted payload: {cleanupError}"); }
    }

    if (serviceWasStopped)
    {
        try { RestoreServiceState(ServiceName, serviceSnapshot, Log); }
        catch (Exception serviceError) { Log($"Failed to restart the previous service: {serviceError}"); }
    }
    return 5;
}

finally
{
    if (staging is not null && stagingRoot is not null)
    {
        try { DeleteDirectoryUnderRootWithRetries(staging, stagingRoot, Log); }
        catch (Exception cleanupError) { Log($"Warning: deferred cleanup of the staging directory: {cleanupError.Message}"); }
        TryDeleteEmptyDirectory(stagingRoot, Log);
    }
}

static string? ReadConfiguredAppRoot()
{
    using var key = Registry.LocalMachine.OpenSubKey(ProductKey);
    var value = key?.GetValue("AppRoot") as string;
    return string.IsNullOrWhiteSpace(value) ? null : value.Trim();
}

static string? ReadConfiguredDataRoot()
{
    using var key = Registry.LocalMachine.OpenSubKey(ProductKey);
    var value = key?.GetValue("DataRoot") as string;
    return string.IsNullOrWhiteSpace(value) ? null : value.Trim();
}

static string? ReadConfiguredPayloadVersion()
{
    using var key = Registry.LocalMachine.OpenSubKey(ProductKey);
    var value = key?.GetValue("PayloadVersion") as string;
    return string.IsNullOrWhiteSpace(value) ? null : value.Trim();
}

static ProductRegistrySnapshot CaptureProductRegistry()
{
    using var key = Registry.LocalMachine.OpenSubKey(ProductKey);
    var values = new Dictionary<string, RegistryValueSnapshot>(StringComparer.OrdinalIgnoreCase);
    var existingNames = key?.GetValueNames().ToHashSet(StringComparer.OrdinalIgnoreCase)
        ?? new HashSet<string>(StringComparer.OrdinalIgnoreCase);
    foreach (var name in new[] { "InstallRoot", "AppRoot", "DataRoot", "PayloadVersion" })
    {
        if (key is null || !existingNames.Contains(name))
        {
            values[name] = RegistryValueSnapshot.Missing;
            continue;
        }

        values[name] = new RegistryValueSnapshot(
            true,
            key.GetValue(name, null, RegistryValueOptions.DoNotExpandEnvironmentNames),
            key.GetValueKind(name));
    }
    return new ProductRegistrySnapshot(key is not null, values);
}

static void RestoreProductRegistry(ProductRegistrySnapshot snapshot)
{
    using (var key = Registry.LocalMachine.CreateSubKey(ProductKey, writable: true))
    {
        foreach (var (name, state) in snapshot.Values)
        {
            if (state.Exists)
                key.SetValue(name, state.Value ?? string.Empty, state.Kind);
            else
                key.DeleteValue(name, throwOnMissingValue: false);
        }
    }

    if (!snapshot.KeyExisted)
    {
        using var restored = Registry.LocalMachine.OpenSubKey(ProductKey);
        if (restored is not null && restored.ValueCount == 0 && restored.SubKeyCount == 0)
        {
            restored.Close();
            Registry.LocalMachine.DeleteSubKey(ProductKey, throwOnMissingSubKey: false);
        }
    }
}

static string SelectPayloadDestination(
    string legacyDestination,
    string? configuredDestination,
    long payloadSize,
    Action<string> log)
{
    if (!string.IsNullOrWhiteSpace(configuredDestination))
    {
        log($"Reusing configured application directory: {configuredDestination}");
        return Path.GetFullPath(configuredDestination);
    }

    var systemRoot = Path.GetPathRoot(legacyDestination)!;
    var required = payloadSize + 2L * 1024 * 1024 * 1024;
    var candidates = DriveInfo.GetDrives()
        .Where(drive => IsEligibleAutomaticDrive(drive, systemRoot, log))
        .Where(drive => !drive.RootDirectory.FullName.Equals(systemRoot, StringComparison.OrdinalIgnoreCase))
        .Where(drive => drive.AvailableFreeSpace >= required)
        .OrderByDescending(drive => drive.AvailableFreeSpace)
        .ToArray();
    var candidate = candidates.FirstOrDefault();

    if (candidate is null) return legacyDestination;
    var selected = Path.Combine(candidate.RootDirectory.FullName, "OntoTwin-ZHHZ", "App");
    log($"Using {candidate.Name} for the large application payload " +
        $"({candidate.AvailableFreeSpace / 1024d / 1024 / 1024:N2} GB free).");
    return selected;
}

static DataRootSelection SelectDataRoot(
    string? configuredDataRoot,
    string legacyDataRoot,
    string destinationParent,
    long newDataRootFreeBytes,
    long existingDataRootFreeBytes,
    Action<string> log)
{
    if (!string.IsNullOrWhiteSpace(configuredDataRoot))
    {
        var configured = ValidateDataRootPath(configuredDataRoot, legacyDataRoot);
        var hasDataDisk = File.Exists(Path.Combine(configured, "VM", "data.vhdx"));
        AssertDataRootCapacity(
            configured,
            hasDataDisk ? existingDataRootFreeBytes : newDataRootFreeBytes,
            hasDataDisk ? "existing backend data" : "backend data disk creation",
            log);
        log($"Reusing the configured DataRoot without moving customer data: {configured}");
        return new DataRootSelection(configured, hasDataDisk, true);
    }

    // Releases before DataRoot was registered always stored their VM and
    // backups below ProgramData. Adopt that location in place whenever it has
    // substantive content; never guess at a migration destination.
    if (HasSubstantiveDataRoot(legacyDataRoot))
    {
        var legacy = ValidateDataRootPath(legacyDataRoot, legacyDataRoot);
        var hasDataDisk = File.Exists(Path.Combine(legacy, "VM", "data.vhdx"));
        AssertDataRootCapacity(
            legacy,
            hasDataDisk ? existingDataRootFreeBytes : newDataRootFreeBytes,
            hasDataDisk ? "existing legacy backend data" : "legacy backend data disk creation",
            log);
        log($"Existing legacy DataRoot detected and retained in place: {legacy}");
        return new DataRootSelection(legacy, hasDataDisk, true);
    }

    var systemRoot = NormalizeDriveRoot(Path.GetPathRoot(legacyDataRoot)!);
    var applicationRoot = NormalizeDriveRoot(Path.GetPathRoot(destinationParent)!);
    var fixedNtfsDrives = DriveInfo.GetDrives()
        .Where(IsEligibleDataDrive)
        .ToArray();

    // Detection is deliberately broader than automatic selection. If an old,
    // unregistered DataRoot exists even on a USB-reported fixed disk, stop and
    // ask for recovery instead of silently creating a second database.
    var unregisteredDataRoots = fixedNtfsDrives
        .Select(drive => BuildCanonicalDataRoot(drive, systemRoot, legacyDataRoot))
        .Where(path => !path.Equals(legacyDataRoot, StringComparison.OrdinalIgnoreCase))
        .Where(HasSubstantiveDataRoot)
        .ToArray();
    if (unregisteredDataRoots.Length > 0)
    {
        throw new InvalidOperationException(
            "Unregistered OntoTwin backend data already exists. To prevent accidental data loss, " +
            "the installer will not choose another volume automatically. Existing path(s): " +
            string.Join(", ", unregisteredDataRoots));
    }

    var drives = fixedNtfsDrives
        .Where(drive => IsEligibleAutomaticDrive(drive, systemRoot, log))
        .OrderBy(drive => NormalizeDriveRoot(drive.RootDirectory.FullName)
            .Equals(systemRoot, StringComparison.OrdinalIgnoreCase) ? 1 : 0)
        .ThenBy(drive =>
        {
            var root = NormalizeDriveRoot(drive.RootDirectory.FullName);
            if (root.Equals(applicationRoot, StringComparison.OrdinalIgnoreCase)) return 0;
            return 1;
        })
        .ThenByDescending(drive => drive.AvailableFreeSpace)
        .ToArray();

    foreach (var drive in drives)
    {
        var requiredNow = newDataRootFreeBytes;
        if (drive.AvailableFreeSpace < requiredNow) continue;

        var selected = ValidateDataRootPath(
            BuildCanonicalDataRoot(drive, systemRoot, legacyDataRoot),
            legacyDataRoot);
        log($"Selected fixed NTFS volume {drive.Name} for backend data " +
            $"({FormatGiB(drive.AvailableFreeSpace)} GiB free; {FormatGiB(requiredNow)} GiB required now). " +
            $"DataRoot={selected}");
        return new DataRootSelection(selected, false, false);
    }

    var driveSummary = drives.Length == 0
        ? "No ready fixed NTFS volume was found."
        : string.Join("; ", drives.Select(drive =>
            $"{drive.Name} {FormatGiB(drive.AvailableFreeSpace)} GiB free"));
    throw new IOException(
        $"No fixed NTFS volume has enough free space for a new OntoTwin backend DataRoot. " +
        $"At least {FormatGiB(newDataRootFreeBytes)} GiB must be available at installation start for the VM, " +
        $"databases and backups. {driveSummary}");
}

static string BuildCanonicalDataRoot(DriveInfo drive, string systemRoot, string legacyDataRoot)
{
    var root = NormalizeDriveRoot(drive.RootDirectory.FullName);
    return root.Equals(systemRoot, StringComparison.OrdinalIgnoreCase)
        ? Path.GetFullPath(legacyDataRoot)
        : Path.Combine(drive.RootDirectory.FullName, "OntoTwin-ZHHZ", "Data");
}

static void AssertDataRootCapacity(
    string dataRoot,
    long baseRequiredBytes,
    string reason,
    Action<string> log)
{
    var dataDrive = GetEligibleDataDrive(dataRoot);
    var requiredNow = baseRequiredBytes;
    log($"Data volume {dataDrive.Name} has {FormatGiB(dataDrive.AvailableFreeSpace)} GiB free; " +
        $"{FormatGiB(requiredNow)} GiB is required now for {reason}.");
    if (dataDrive.AvailableFreeSpace < requiredNow)
    {
        throw new IOException(
            $"Insufficient free space on backend data volume {dataDrive.Name}. " +
            $"DataRoot={dataRoot}; available={FormatGiB(dataDrive.AvailableFreeSpace)} GiB; " +
            $"required now={FormatGiB(requiredNow)} GiB ({reason}). " +
            "Existing customer data was not moved or modified.");
    }
}

static string ValidateDataRootPath(string path, string legacyDataRoot)
{
    if (string.IsNullOrWhiteSpace(path) || !Path.IsPathFullyQualified(path))
        throw new InvalidDataException($"The configured DataRoot is not an absolute path: {path}");

    var fullPath = Path.GetFullPath(path)
        .TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar);
    var normalizedLegacy = Path.GetFullPath(legacyDataRoot)
        .TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar);
    var drive = GetEligibleDataDrive(fullPath);
    var systemRoot = NormalizeDriveRoot(Path.GetPathRoot(normalizedLegacy)!);
    var driveRoot = NormalizeDriveRoot(drive.RootDirectory.FullName);
    var isLegacy = fullPath.Equals(normalizedLegacy, StringComparison.OrdinalIgnoreCase);

    var directory = new DirectoryInfo(fullPath);
    var productDirectory = directory.Parent;
    var productParent = productDirectory?.Parent;
    var isExternalCanonical = !driveRoot.Equals(systemRoot, StringComparison.OrdinalIgnoreCase) &&
                              directory.Name.Equals("Data", StringComparison.OrdinalIgnoreCase) &&
                              productDirectory is not null &&
                              productDirectory.Name.Equals("OntoTwin-ZHHZ", StringComparison.OrdinalIgnoreCase) &&
                              productParent is not null &&
                              NormalizeDriveRoot(productParent.FullName)
                                  .Equals(driveRoot, StringComparison.OrdinalIgnoreCase);
    if (!isLegacy && !isExternalCanonical)
        throw new InvalidDataException(
            $"The configured DataRoot is outside an approved OntoTwin data directory: {fullPath}");

    if (productDirectory is not null) EnsureOrdinaryDirectory(productDirectory.FullName, "DataRoot product directory");
    EnsureOrdinaryDirectory(fullPath, "DataRoot directory");
    return fullPath;
}

static DriveInfo GetEligibleDataDrive(string path)
{
    var root = Path.GetPathRoot(Path.GetFullPath(path))
        ?? throw new InvalidDataException($"The DataRoot path has no volume root: {path}");
    var drive = new DriveInfo(root);
    if (!IsEligibleDataDrive(drive))
        throw new InvalidDataException(
            $"The DataRoot volume must be a ready fixed NTFS volume: {root}");
    return drive;
}

static bool IsEligibleDataDrive(DriveInfo drive)
{
    try
    {
        return drive.IsReady &&
               drive.DriveType == DriveType.Fixed &&
               drive.DriveFormat.Equals("NTFS", StringComparison.OrdinalIgnoreCase);
    }
    catch
    {
        return false;
    }
}

static bool IsEligibleAutomaticDrive(DriveInfo drive, string systemRoot, Action<string> log)
{
    if (!IsEligibleDataDrive(drive)) return false;

    var root = NormalizeDriveRoot(drive.RootDirectory.FullName);
    var isSystemVolume = root.Equals(NormalizeDriveRoot(systemRoot), StringComparison.OrdinalIgnoreCase);
    var assessment = ProbeWindowsStorageDisk(drive);
    if (!assessment.Succeeded)
    {
        if (DiskPlacementPolicy.IsEligible(
                false,
                assessment.BusType,
                assessment.IsBoot,
                assessment.IsSystem,
                isSystemVolume))
        {
            log($"Windows Storage could not classify system volume {drive.Name}; " +
                $"the system-volume fallback remains eligible. Detail: {assessment.Detail}");
            return true;
        }
        log($"Excluded {drive.Name} from automatic placement because Windows Storage classification failed. " +
            $"Only the system volume or an already registered path is allowed on probe failure. Detail: {assessment.Detail}");
        return false;
    }

    var allowed = DiskPlacementPolicy.IsEligible(
        true,
        assessment.BusType,
        assessment.IsBoot,
        assessment.IsSystem,
        isSystemVolume);
    if (!allowed)
    {
        log($"Excluded {drive.Name} from automatic placement: BusType={assessment.BusType}, " +
            $"IsBoot={assessment.IsBoot}, IsSystem={assessment.IsSystem}. " +
            "USB, SD/MMC, external, virtual, network, and unknown disks are not eligible.");
        return false;
    }

    log($"Eligible local volume {drive.Name}: BusType={assessment.BusType}, " +
        $"IsBoot={assessment.IsBoot}, IsSystem={assessment.IsSystem}.");
    return true;
}

static WindowsStorageDiskAssessment ProbeWindowsStorageDisk(DriveInfo drive)
{
    var root = NormalizeDriveRoot(drive.RootDirectory.FullName);
    if (root.Length < 1 || !char.IsAsciiLetter(root[0]))
        return new WindowsStorageDiskAssessment(false, "Unknown", false, false, $"Invalid drive root: {root}");

    var driveLetter = char.ToUpperInvariant(root[0]);
    var command =
        "$ErrorActionPreference='Stop';" +
        "$OutputEncoding=[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false);" +
        $"$p=@(Get-Partition -DriveLetter '{driveLetter}' -ErrorAction Stop);" +
        "if($p.Count -ne 1){throw ('Expected one partition, found '+$p.Count)};" +
        "$d=@($p[0] | Get-Disk -ErrorAction Stop);" +
        "if($d.Count -ne 1){throw ('Expected one disk, found '+$d.Count)};" +
        "[pscustomobject]@{BusType=$d[0].BusType.ToString();" +
        "IsBoot=[bool]$d[0].IsBoot;IsSystem=[bool]$d[0].IsSystem;" +
        "FriendlyName=[string]$d[0].FriendlyName;Location=[string]$d[0].Location}" +
        "| ConvertTo-Json -Compress";

    var powerShell = Path.Combine(
        Environment.SystemDirectory,
        "WindowsPowerShell",
        "v1.0",
        "powershell.exe");
    var startInfo = new ProcessStartInfo
    {
        FileName = powerShell,
        UseShellExecute = false,
        RedirectStandardOutput = true,
        RedirectStandardError = true,
        CreateNoWindow = true,
        StandardOutputEncoding = Encoding.UTF8,
        StandardErrorEncoding = Encoding.UTF8
    };
    foreach (var argument in new[] { "-NoProfile", "-NonInteractive", "-Command", command })
        startInfo.ArgumentList.Add(argument);

    try
    {
        using var process = new Process { StartInfo = startInfo };
        process.Start();
        var stdout = process.StandardOutput.ReadToEndAsync();
        var stderr = process.StandardError.ReadToEndAsync();
        if (!process.WaitForExit(15000))
        {
            try { process.Kill(entireProcessTree: true); } catch { }
            return new WindowsStorageDiskAssessment(false, "Unknown", false, false, "Get-Disk timed out.");
        }
        var output = stdout.GetAwaiter().GetResult().Trim();
        var error = stderr.GetAwaiter().GetResult().Trim();
        if (process.ExitCode != 0 || string.IsNullOrWhiteSpace(output))
            return new WindowsStorageDiskAssessment(
                false,
                "Unknown",
                false,
                false,
                string.IsNullOrWhiteSpace(error) ? $"Get-Disk exited {process.ExitCode}." : error);

        using var document = JsonDocument.Parse(output);
        var rootElement = document.RootElement;
        var busType = rootElement.GetProperty("BusType").GetString() ?? "Unknown";
        var isBoot = rootElement.GetProperty("IsBoot").GetBoolean();
        var isSystem = rootElement.GetProperty("IsSystem").GetBoolean();
        var friendlyName = rootElement.TryGetProperty("FriendlyName", out var friendly)
            ? friendly.GetString() ?? ""
            : "";
        var location = rootElement.TryGetProperty("Location", out var locationElement)
            ? locationElement.GetString() ?? ""
            : "";
        return new WindowsStorageDiskAssessment(
            true,
            busType,
            isBoot,
            isSystem,
            $"FriendlyName={friendlyName}; Location={location}");
    }
    catch (Exception exception)
    {
        return new WindowsStorageDiskAssessment(false, "Unknown", false, false, exception.Message);
    }
}

static bool HasSubstantiveDataRoot(string path)
{
    if (!Directory.Exists(path)) return false;
    EnsureOrdinaryDirectory(path, "existing DataRoot directory");
    foreach (var entry in Directory.EnumerateFileSystemEntries(path))
    {
        if (Path.GetFileName(entry).Equals("Logs", StringComparison.OrdinalIgnoreCase)) continue;
        return true;
    }
    return false;
}

static string NormalizeDriveRoot(string path) =>
    Path.GetFullPath(path).TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar);

static string FormatGiB(long bytes) =>
    (bytes / 1024d / 1024 / 1024).ToString("N1", System.Globalization.CultureInfo.InvariantCulture);

static string BuildUniqueSideBySideDestination(string destinationParent, string payloadVersion)
{
    var safeVersion = new string(payloadVersion
        .Select(character => char.IsAsciiLetterOrDigit(character) || character is '.' or '-' or '_'
            ? character
            : '_')
        .ToArray());
    for (var attempt = 0; attempt < 20; attempt++)
    {
        var suffix = Guid.NewGuid().ToString("N")[..12];
        var candidate = Path.Combine(destinationParent, $"App-{safeVersion}-{suffix}");
        if (!Directory.Exists(candidate) && !File.Exists(candidate)) return candidate;
    }
    throw new IOException("Unable to allocate a unique side-by-side application directory.");
}

static string[] GetTrustedPayloadDirectories(
    string? configuredDestination,
    string legacyDestination,
    string installRoot)
{
    var parents = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
    foreach (var candidate in new[] { configuredDestination, legacyDestination })
    {
        if (string.IsNullOrWhiteSpace(candidate)) continue;
        var validated = ValidatePayloadPath(candidate, installRoot);
        var parent = Directory.GetParent(validated)?.FullName
            ?? throw new InvalidDataException($"The application path has no product directory: {validated}");
        ValidatePayloadParent(parent, installRoot);
        parents.Add(parent);
    }

    var destinations = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
    foreach (var parent in parents)
    {
        if (!Directory.Exists(parent)) continue;
        EnsureOrdinaryDirectory(parent, "payload parent directory");
        foreach (var directory in Directory.EnumerateDirectories(parent))
        {
            var leaf = Path.GetFileName(directory);
            if (!PayloadDirectoryPolicy.IsCleanupCandidate(leaf))
                continue;
            destinations.Add(ValidatePayloadCleanupPath(directory, installRoot));
        }
    }
    return destinations.OrderBy(path => path, StringComparer.OrdinalIgnoreCase).ToArray();
}

static string ValidatePayloadCleanupPath(string path, string installRoot)
{
    var fullPath = Path.GetFullPath(path)
        .TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar);
    var leaf = Path.GetFileName(fullPath);
    if (PayloadDirectoryPolicy.IsCurrentDirectoryName(leaf)) return ValidatePayloadPath(fullPath, installRoot);
    if (!PayloadDirectoryPolicy.IsLegacyCleanupDirectoryName(leaf))
        throw new InvalidDataException($"The directory is not an approved OntoTwin payload directory: {fullPath}");

    var parent = Directory.GetParent(fullPath)?.FullName
        ?? throw new InvalidDataException($"The legacy payload path has no product directory: {fullPath}");
    ValidatePayloadParent(parent, installRoot);
    EnsureOrdinaryDirectory(fullPath, "legacy application directory");
    return fullPath;
}

static void CleanupStalePayloadDirectories(
    string currentDestination,
    string? previousDestination,
    string legacyDestination,
    string installRoot,
    Action<string> log)
{
    var current = ValidatePayloadPath(currentDestination, installRoot);
    var all = GetTrustedPayloadDirectories(current, legacyDestination, installRoot);
    var keep = new HashSet<string>(StringComparer.OrdinalIgnoreCase) { current };

    if (!string.IsNullOrWhiteSpace(previousDestination))
    {
        var previous = ValidatePayloadPath(previousDestination, installRoot);
        if (Directory.Exists(previous) && !previous.Equals(current, StringComparison.OrdinalIgnoreCase))
            keep.Add(previous);
    }
    if (keep.Count == 1)
    {
        var mostRecentPrevious = all
            .Where(path => !path.Equals(current, StringComparison.OrdinalIgnoreCase))
            .OrderByDescending(path => Directory.GetLastWriteTimeUtc(path))
            .FirstOrDefault();
        if (mostRecentPrevious is not null) keep.Add(mostRecentPrevious);
    }

    foreach (var stale in all.Where(path => !keep.Contains(path)))
    {
        try
        {
            StopProcessesUnder(stale, log);
            DeletePayloadDirectoryWithRetries(stale, installRoot, log);
            log($"Removed stale side-by-side application directory: {stale}");
        }
        catch (Exception exception)
        {
            log($"Warning: could not remove stale application directory {stale}: {exception.Message}");
        }
    }
}

static string ValidatePayloadPath(string path, string installRoot)
{
    if (string.IsNullOrWhiteSpace(path) || !Path.IsPathFullyQualified(path))
        throw new InvalidDataException($"The configured application path is not an absolute path: {path}");

    var fullPath = Path.GetFullPath(path).TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar);
    var pathRoot = Path.GetPathRoot(fullPath)
        ?? throw new InvalidDataException($"The configured application path has no drive root: {fullPath}");
    if (fullPath.Equals(pathRoot.TrimEnd(Path.DirectorySeparatorChar), StringComparison.OrdinalIgnoreCase))
        throw new InvalidDataException($"Refusing to use a drive root as the application path: {fullPath}");

    var directory = new DirectoryInfo(fullPath);
    var leaf = directory.Name;
    if (!leaf.Equals("App", StringComparison.OrdinalIgnoreCase) &&
        !(leaf.StartsWith("App-", StringComparison.OrdinalIgnoreCase) && leaf.Length > 4))
        throw new InvalidDataException($"The configured application directory is not an OntoTwin App directory: {fullPath}");

    var parent = directory.Parent
        ?? throw new InvalidDataException($"The configured application path has no product directory: {fullPath}");
    var normalizedInstallRoot = Path.GetFullPath(installRoot)
        .TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar);
    var inProgramFilesProduct = parent.FullName
        .TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar)
        .Equals(normalizedInstallRoot, StringComparison.OrdinalIgnoreCase);

    var externalParent = parent.Parent;
    var externalRoot = externalParent?.FullName
        .TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar);
    var expectedExternalRoot = Path.GetPathRoot(parent.FullName)?
        .TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar);
    var inExternalProductRoot = parent.Name.Equals("OntoTwin-ZHHZ", StringComparison.OrdinalIgnoreCase) &&
                                externalRoot is not null && expectedExternalRoot is not null &&
                                externalRoot.Equals(expectedExternalRoot, StringComparison.OrdinalIgnoreCase);
    if (!inProgramFilesProduct && !inExternalProductRoot)
        throw new InvalidDataException($"The configured application path is outside an approved OntoTwin product directory: {fullPath}");

    if (inExternalProductRoot)
    {
        var drive = new DriveInfo(pathRoot);
        if (!drive.IsReady || drive.DriveType != DriveType.Fixed ||
            !drive.DriveFormat.Equals("NTFS", StringComparison.OrdinalIgnoreCase))
            throw new InvalidDataException(
                $"The configured application path must be on a ready fixed NTFS drive: {fullPath}");
    }

    EnsureOrdinaryDirectory(parent.FullName, "payload parent directory");
    EnsureOrdinaryDirectory(fullPath, "application directory");
    return fullPath;
}

static void ValidatePayloadParent(string parent, string installRoot)
{
    _ = ValidatePayloadPath(Path.Combine(parent, "App"), installRoot);
}

static void EnsureOrdinaryDirectory(string path, string description)
{
    if (!Directory.Exists(path)) return;
    var attributes = File.GetAttributes(path);
    if ((attributes & FileAttributes.ReparsePoint) != 0)
        throw new InvalidDataException($"The {description} cannot be a reparse point: {path}");
}

static void StopProcessesUnder(string directory, Action<string> log)
{
    var prefix = Path.GetFullPath(directory).TrimEnd(Path.DirectorySeparatorChar) + Path.DirectorySeparatorChar;
    foreach (var process in System.Diagnostics.Process.GetProcesses())
    {
        try
        {
            string? executable;
            try
            {
                if (process.Id == Environment.ProcessId) continue;
                executable = process.MainModule?.FileName;
            }
            catch (UnauthorizedAccessException)
            {
                continue;
            }
            catch (System.ComponentModel.Win32Exception)
            {
                continue;
            }
            catch (InvalidOperationException)
            {
                continue;
            }

            if (string.IsNullOrWhiteSpace(executable) ||
                !Path.GetFullPath(executable).StartsWith(prefix, StringComparison.OrdinalIgnoreCase)) continue;

            try
            {
                log($"Closing running application {process.ProcessName} ({process.Id}) before payload replacement.");
                if (process.CloseMainWindow() && process.WaitForExit(5000)) continue;
                process.Kill(entireProcessTree: true);
                process.WaitForExit(10000);
            }
            catch (Exception exception)
            {
                log($"Could not close application {executable}: {exception.Message}");
            }
        }
        finally
        {
            process.Dispose();
        }
    }
}

static async Task QuiesceBackendAsync(
    string serviceName,
    int controlPort,
    string installRoot,
    string appRoot,
    string dataRoot,
    Action<string> log)
{
    using var service = FindService(serviceName);
    if (service is not null)
    {
        service.Refresh();
        if (service.Status == ServiceControllerStatus.StartPending)
        {
            log($"Waiting for service {serviceName} to accept the backend stop request.");
            service.WaitForStatus(ServiceControllerStatus.Running, TimeSpan.FromSeconds(90));
            service.Refresh();
        }
        else if (service.Status == ServiceControllerStatus.StopPending)
        {
            log($"Waiting for service {serviceName} to finish its in-progress shutdown.");
            service.WaitForStatus(ServiceControllerStatus.Stopped, TimeSpan.FromSeconds(180));
            service.Refresh();
        }
        if (service.Status is not ServiceControllerStatus.Stopped and not ServiceControllerStatus.StopPending)
        {
            log("Requesting a safe backend shutdown through the host service operation lock.");
            await RequestBackendStopAsync(controlPort, log);
            return;
        }
    }

    log("The host service is unavailable or stopped; using HostControl.ps1 to stop the backend directly.");
    await RunDirectBackendStopAsync(installRoot, appRoot, dataRoot, log);
}

static async Task RequestBackendStopAsync(int controlPort, Action<string> log)
{
    using var cancellation = new CancellationTokenSource(TimeSpan.FromSeconds(180));
    using var client = new TcpClient();
    try
    {
        await client.ConnectAsync("127.0.0.1", controlPort, cancellation.Token);
        await using var stream = client.GetStream();
        await using var writer = new StreamWriter(
            stream,
            new UTF8Encoding(false),
            4096,
            leaveOpen: true) { AutoFlush = true };
        using var reader = new StreamReader(stream, new UTF8Encoding(false), false, 4096, leaveOpen: true);
        await writer.WriteLineAsync("{\"action\":\"stop\"}");
        var responseLine = await reader.ReadLineAsync(cancellation.Token);
        if (string.IsNullOrWhiteSpace(responseLine))
            throw new InvalidDataException("The host service returned an empty backend stop response.");

        using var response = JsonDocument.Parse(responseLine);
        var root = response.RootElement;
        var ok = root.TryGetProperty("ok", out var okElement) && okElement.GetBoolean();
        var message = root.TryGetProperty("message", out var messageElement)
            ? messageElement.GetString() ?? ""
            : "";
        var output = root.TryGetProperty("output", out var outputElement)
            ? outputElement.GetString() ?? ""
            : "";
        var vmState = root.TryGetProperty("vmState", out var stateElement)
            ? stateElement.GetString() ?? ""
            : "";
        if (!ok)
            throw new InvalidOperationException($"The host service rejected the backend stop request: {message}{Environment.NewLine}{output}");
        if (!IsBackendOff(vmState, output))
            throw new InvalidOperationException(
                $"The host service did not confirm that the backend VM is off. Reported state: {vmState}.{Environment.NewLine}{output}");
        log($"Backend shutdown confirmed by the host service ({vmState}).");
    }
    catch (OperationCanceledException exception)
    {
        throw new System.TimeoutException("Timed out waiting for the host service to stop the backend VM.", exception);
    }
}

static async Task RunDirectBackendStopAsync(
    string installRoot,
    string appRoot,
    string dataRoot,
    Action<string> log)
{
    var hostScript = Path.Combine(installRoot, "Host", "HostControl.ps1");
    if (!File.Exists(hostScript))
        throw new FileNotFoundException("The installed HostControl.ps1 required for backend shutdown is missing.", hostScript);

    var startInfo = new ProcessStartInfo
    {
        FileName = "powershell.exe",
        UseShellExecute = false,
        CreateNoWindow = true,
        RedirectStandardOutput = true,
        RedirectStandardError = true,
        WorkingDirectory = Path.GetDirectoryName(hostScript) ?? installRoot
    };
    foreach (var argument in new[]
    {
        "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", hostScript,
        "-Action", "Stop", "-AppRoot", appRoot, "-DataRoot", dataRoot
    }) startInfo.ArgumentList.Add(argument);

    using var process = new Process { StartInfo = startInfo };
    process.Start();
    var stdout = process.StandardOutput.ReadToEndAsync();
    var stderr = process.StandardError.ReadToEndAsync();
    using var cancellation = new CancellationTokenSource(TimeSpan.FromSeconds(180));
    try
    {
        await process.WaitForExitAsync(cancellation.Token);
    }
    catch (OperationCanceledException exception)
    {
        try { process.Kill(entireProcessTree: true); } catch { }
        throw new System.TimeoutException("Timed out while HostControl.ps1 was stopping the backend VM.", exception);
    }

    var output = (await stdout) + (await stderr);
    if (process.ExitCode != 0)
        throw new InvalidOperationException(
            $"HostControl.ps1 could not safely stop the backend VM (exit {process.ExitCode}).{Environment.NewLine}{output}");
    if (!IsBackendOff("", output))
        throw new InvalidOperationException(
            $"HostControl.ps1 completed without confirming that the backend VM is off.{Environment.NewLine}{output}");
    log("Backend shutdown confirmed by HostControl.ps1.");
}

static bool IsBackendOff(string vmState, string output)
{
    return vmState.Equals("Off", StringComparison.OrdinalIgnoreCase) ||
           vmState.Equals("NotInstalled", StringComparison.OrdinalIgnoreCase) ||
           output.Contains("NotInstalled", StringComparison.OrdinalIgnoreCase) ||
           output.Contains("VMState", StringComparison.OrdinalIgnoreCase) &&
           output.Contains("Off", StringComparison.OrdinalIgnoreCase);
}

static ServiceStateSnapshot StopServiceForReplacement(string serviceName, Action<string> log)
{
    using var service = FindService(serviceName);
    if (service is null)
    {
        log($"Service {serviceName} is not installed yet.");
        return ServiceStateSnapshot.NotInstalled;
    }

    service.Refresh();
    var originalStatus = service.Status;
    var desiredState = originalStatus is ServiceControllerStatus.Stopped or ServiceControllerStatus.StopPending
        ? DesiredServiceState.Stopped
        : originalStatus is ServiceControllerStatus.Paused or ServiceControllerStatus.PausePending
            ? DesiredServiceState.Paused
            : DesiredServiceState.Running;
    EnsureControllerStopped(service, serviceName, log);
    return new ServiceStateSnapshot(true, desiredState);
}

static void EnsureServiceStopped(string serviceName, Action<string> log)
{
    using var service = FindService(serviceName);
    if (service is null) return;
    EnsureControllerStopped(service, serviceName, log);
}

static void EnsureControllerStopped(ServiceController service, string serviceName, Action<string> log)
{
    service.Refresh();
    if (service.Status == ServiceControllerStatus.Stopped) return;
    if (service.Status == ServiceControllerStatus.StopPending)
    {
        log($"Waiting for service {serviceName} to finish stopping.");
        service.WaitForStatus(ServiceControllerStatus.Stopped, TimeSpan.FromSeconds(180));
        return;
    }

    if (service.Status == ServiceControllerStatus.StartPending)
        service.WaitForStatus(ServiceControllerStatus.Running, TimeSpan.FromSeconds(90));
    else if (service.Status == ServiceControllerStatus.ContinuePending)
        service.WaitForStatus(ServiceControllerStatus.Running, TimeSpan.FromSeconds(90));
    else if (service.Status == ServiceControllerStatus.PausePending)
        service.WaitForStatus(ServiceControllerStatus.Paused, TimeSpan.FromSeconds(90));

    service.Refresh();
    if (service.Status == ServiceControllerStatus.Stopped) return;
    log($"Stopping service {serviceName} before payload replacement and waiting for backend quiescence.");
    service.Stop();
    service.WaitForStatus(ServiceControllerStatus.Stopped, TimeSpan.FromSeconds(180));
}

static void RestoreServiceState(string serviceName, ServiceStateSnapshot snapshot, Action<string> log)
{
    if (!snapshot.Exists) return;
    using var service = FindService(serviceName)
        ?? throw new InvalidOperationException($"Service {serviceName} disappeared during payload installation.");
    service.Refresh();
    if (snapshot.DesiredState == DesiredServiceState.Stopped)
    {
        EnsureControllerStopped(service, serviceName, log);
        return;
    }

    if (service.Status == ServiceControllerStatus.StopPending)
        service.WaitForStatus(ServiceControllerStatus.Stopped, TimeSpan.FromSeconds(180));
    service.Refresh();
    if (service.Status == ServiceControllerStatus.Stopped)
    {
        log($"Starting service {serviceName} after committing the new AppRoot.");
        service.Start();
        service.WaitForStatus(ServiceControllerStatus.Running, TimeSpan.FromSeconds(90));
    }
    else if (service.Status == ServiceControllerStatus.StartPending)
    {
        service.WaitForStatus(ServiceControllerStatus.Running, TimeSpan.FromSeconds(90));
    }
    else if (service.Status == ServiceControllerStatus.Paused)
    {
        service.Continue();
        service.WaitForStatus(ServiceControllerStatus.Running, TimeSpan.FromSeconds(90));
    }
    else if (service.Status == ServiceControllerStatus.ContinuePending)
    {
        service.WaitForStatus(ServiceControllerStatus.Running, TimeSpan.FromSeconds(90));
    }

    if (snapshot.DesiredState == DesiredServiceState.Paused)
    {
        service.Refresh();
        if (service.Status != ServiceControllerStatus.Paused)
        {
            log($"Restoring service {serviceName} to its previous paused state.");
            service.Pause();
            service.WaitForStatus(ServiceControllerStatus.Paused, TimeSpan.FromSeconds(90));
        }
    }
}

static ServiceController? FindService(string serviceName)
{
    var services = ServiceController.GetServices();
    var match = services.FirstOrDefault(candidate =>
        candidate.ServiceName.Equals(serviceName, StringComparison.OrdinalIgnoreCase));
    foreach (var service in services)
    {
        if (!ReferenceEquals(service, match)) service.Dispose();
    }
    return match;
}

static void MoveDirectoryWithRetries(string source, string destination, Action<string> log)
{
    RetryFileSystemAction(
        () => Directory.Move(source, destination),
        $"move {source} to {destination}",
        log);
}

static void InstallStagedDirectory(string staging, string destination, Action<string> log)
{
    if (!Path.GetPathRoot(staging)!.Equals(Path.GetPathRoot(destination), StringComparison.OrdinalIgnoreCase))
        throw new InvalidOperationException("The staged payload must be on the same volume as its final AppRoot.");
    MoveDirectoryWithRetries(staging, destination, log);
}

static void DeletePayloadDirectoryWithRetries(string path, string installRoot, Action<string> log)
{
    var validated = ValidatePayloadCleanupPath(path, installRoot);
    if (Directory.Exists(validated))
        RetryFileSystemAction(() => Directory.Delete(validated, recursive: true), $"delete {validated}", log);
}

static void DeleteDirectoryUnderRootWithRetries(string path, string allowedRoot, Action<string> log)
{
    var fullPath = Path.GetFullPath(path);
    var rootPrefix = Path.GetFullPath(allowedRoot).TrimEnd(Path.DirectorySeparatorChar) + Path.DirectorySeparatorChar;
    if (!fullPath.StartsWith(rootPrefix, StringComparison.OrdinalIgnoreCase))
        throw new InvalidOperationException($"Refusing to delete outside the product directory: {fullPath}");
    EnsureOrdinaryDirectory(fullPath, "temporary installer directory");
    if (Directory.Exists(fullPath))
        RetryFileSystemAction(() => Directory.Delete(fullPath, recursive: true), $"delete {fullPath}", log);
}

static void TryDeleteEmptyDirectory(string path, Action<string> log)
{
    try
    {
        EnsureOrdinaryDirectory(path, "payload staging directory");
        if (Directory.Exists(path) && !Directory.EnumerateFileSystemEntries(path).Any())
            Directory.Delete(path);
    }
    catch (Exception exception)
    {
        log($"Warning: could not remove the empty staging root {path}: {exception.Message}");
    }
}

static void RetryFileSystemAction(Action action, string description, Action<string> log)
{
    const int attempts = 12;
    for (var attempt = 1; ; attempt++)
    {
        try
        {
            action();
            return;
        }
        catch (Exception exception) when (
            attempt < attempts &&
            (exception is IOException || exception is UnauthorizedAccessException))
        {
            log($"Waiting for file access to {description} (attempt {attempt}/{attempts}): {exception.Message}");
            Thread.Sleep(500 * attempt);
        }
    }
}

enum DesiredServiceState
{
    Stopped,
    Running,
    Paused
}

sealed record ServiceStateSnapshot(bool Exists, DesiredServiceState DesiredState)
{
    public static readonly ServiceStateSnapshot NotInstalled = new(false, DesiredServiceState.Stopped);
}

sealed record RegistryValueSnapshot(bool Exists, object? Value, RegistryValueKind Kind)
{
    public static readonly RegistryValueSnapshot Missing = new(false, null, RegistryValueKind.None);
}

sealed record ProductRegistrySnapshot(
    bool KeyExisted,
    IReadOnlyDictionary<string, RegistryValueSnapshot> Values);

sealed record DataRootSelection(string Path, bool HasDataDisk, bool PreservedExistingLocation);

sealed record WindowsStorageDiskAssessment(
    bool Succeeded,
    string BusType,
    bool IsBoot,
    bool IsSystem,
    string Detail);
