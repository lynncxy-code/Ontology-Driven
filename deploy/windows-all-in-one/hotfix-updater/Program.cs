using System.Diagnostics;
using System.Formats.Tar;
using System.IO.Compression;
using System.Net.Sockets;
using System.Reflection;
using System.Security.Cryptography;
using System.ServiceProcess;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.Win32;

const string ProductKey = @"SOFTWARE\OntoTwin\ZHHZ";
const string ServiceName = "OntoTwinZHHZHost";
const string PayloadResource = "OntoTwin.ZHHZ.HotfixPayload.zip";
const string ExpectedBaseVersion = "3.7.1-r1-rc10.10";
const string PreviousHotfixVersion = "3.7.1-r1-rc10.10-hf1";
const string TargetHotfixVersion = "3.7.1-r1-rc10.10-hf2";
const int ServiceControlPort = 48073;

var logRoot = Path.Combine(
    Environment.GetFolderPath(Environment.SpecialFolder.CommonApplicationData),
    "OntoTwin-ZHHZ",
    "Logs");
Directory.CreateDirectory(logRoot);
var logPath = Path.Combine(logRoot, "rc10.10-hf2-update.log");

void Log(string message)
{
    var line = $"[{DateTime.Now:yyyy-MM-dd HH:mm:ss}] {message}";
    Console.WriteLine(line);
    try { File.AppendAllText(logPath, line + Environment.NewLine, new UTF8Encoding(false)); }
    catch { }
}

int Finish(int code, string message)
{
    Log(message);
    Console.WriteLine();
    Console.WriteLine(code == 0 ? "按任意键关闭。" : $"日志：{logPath}\n按任意键关闭。");
    if (!Console.IsInputRedirected) Console.ReadKey(intercept: true);
    return code;
}

if (args.Contains("--verify-package", StringComparer.OrdinalIgnoreCase))
{
    var verifyRoot = Path.Combine(Path.GetTempPath(), "ontotwin-hf2-verify-" + Guid.NewGuid().ToString("N"));
    Directory.CreateDirectory(verifyRoot);
    try
    {
        ExtractEmbeddedPayload(verifyRoot);
        var hotfix = JsonSerializer.Deserialize<HotfixManifest>(
            File.ReadAllText(Path.Combine(verifyRoot, "hotfix-manifest.json"), Encoding.UTF8),
            JsonOptions()) ?? throw new InvalidDataException("HF2 清单无效。");
        if (hotfix.BaseVersion != ExpectedBaseVersion || hotfix.TargetVersion != TargetHotfixVersion)
            throw new InvalidDataException("HF2 版本身份不匹配。");
        VerifyPayloadFiles(verifyRoot, hotfix.TargetFiles);
        if (hotfix.TargetFiles.Keys.Any(path =>
                path.StartsWith("ZHHZ/", StringComparison.OrdinalIgnoreCase) ||
                path.StartsWith("Database/", StringComparison.OrdinalIgnoreCase) ||
                path.Contains("data.vhdx", StringComparison.OrdinalIgnoreCase)))
            throw new InvalidDataException("HF2 越界包含了 UE 或数据库文件。");

        var rootManifest = ReadReleaseManifest(Path.Combine(verifyRoot, "release-manifest.json"));
        var releaseArchive = Path.Combine(verifyRoot, "BackendPayload", "release.tar.gz");
        var nestedManifest = JsonDocument.Parse(ReadTarEntryText(
            releaseArchive, "release-manifest.json"));
        foreach (var manifest in new[] { rootManifest, nestedManifest })
        {
            if (manifest.RootElement.GetProperty("release_version").GetString() != TargetHotfixVersion)
                throw new InvalidDataException("HF2 release-manifest 版本不正确。");
            if (manifest.RootElement.GetProperty("reset_backend_baseline_on_upgrade").GetBoolean())
                throw new InvalidDataException("HF2 禁止重置后台数据库基线。");
        }
        if (rootManifest.RootElement.GetProperty("data_version").GetString() !=
                nestedManifest.RootElement.GetProperty("data_version").GetString() ||
            rootManifest.RootElement.GetProperty("project_id").GetString() !=
                nestedManifest.RootElement.GetProperty("project_id").GetString())
            throw new InvalidDataException("HF2 根清单和虚拟机清单的数据身份不一致。");
        var counts = nestedManifest.RootElement.GetProperty("postgres_counts");
        if (counts.GetProperty("object_types").GetInt32() != 38 ||
            counts.GetProperty("instances").GetInt32() != 669)
            throw new InvalidDataException("HF2 清单不再对应 38 Types / 669 Instances 基线。");

        var compose = ReadTarEntryText(releaseArchive, "Deploy/docker-compose.release.yml");
        if (!compose.Contains("ONTOTWIN_MOCK_SIMULATOR_ENABLED: \"true\"", StringComparison.Ordinal) ||
            compose.Contains("restart: unless-stopped", StringComparison.Ordinal) ||
            compose.Split("restart: on-failure:5", StringSplitOptions.None).Length - 1 != 3)
            throw new InvalidDataException("HF2 Compose 性能或启动顺序策略不正确。");
        var environment = ReadTarEntryText(releaseArchive, "Deploy/customer.env.example");
        if (!environment.Contains(
                $"BACKEND_IMAGE=ontotwin-zhhz/backend:{TargetHotfixVersion}", StringComparison.Ordinal) ||
            !environment.Contains($"ONTOTWIN_RELEASE_VERSION={TargetHotfixVersion}", StringComparison.Ordinal))
            throw new InvalidDataException("HF2 环境模板未指向热修复后台镜像。");
        var sums = File.ReadAllLines(
            Path.Combine(verifyRoot, "BackendPayload", "SHA256SUMS"), Encoding.UTF8);
        var imageEntries = sums.Count(line =>
            line.EndsWith("backend-image.tar", StringComparison.Ordinal) ||
            line.EndsWith("postgres-image.tar", StringComparison.Ordinal) ||
            line.EndsWith("neo4j-image.tar", StringComparison.Ordinal));
        if (imageEntries != 3)
            throw new InvalidDataException($"HF2 SHA256SUMS 容器镜像数量异常：{imageEntries}");
        Console.WriteLine("HF2 embedded payload verification: PASS");
        Console.WriteLine($"Base={hotfix.BaseVersion}; Target={hotfix.TargetVersion}; Files={hotfix.TargetFiles.Count}; DatabaseReset=false");
        return 0;
    }
    finally
    {
        try { Directory.Delete(verifyRoot, recursive: true); } catch { }
    }
}

try
{
    Console.OutputEncoding = Encoding.UTF8;
    Console.WriteLine("OntoTwin ZHHZ RC10.10-HF2 后端热修复");
    Console.WriteLine("只更新后台，不修改 ZHHZ.exe、数据库数据卷或客户配置。\n");

    using var productKey = Registry.LocalMachine.OpenSubKey(ProductKey, writable: true)
        ?? throw new InvalidOperationException("未检测到 OntoTwin ZHHZ 安装信息。请先安装 RC10.10。");
    var appRoot = Path.GetFullPath((productKey.GetValue("AppRoot") as string)?.Trim()
        ?? throw new InvalidOperationException("安装信息缺少 AppRoot。"));
    var dataRoot = Path.GetFullPath((productKey.GetValue("DataRoot") as string)?.Trim()
        ?? Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.CommonApplicationData), "OntoTwin-ZHHZ"));
    var payloadVersion = (productKey.GetValue("PayloadVersion") as string)?.Trim() ?? "";
    var installedHotfix = (productKey.GetValue("BackendHotfixVersion") as string)?.Trim() ?? "";
    ValidateAppRoot(appRoot);

    var manifestPath = Path.Combine(appRoot, "release-manifest.json");
    var backendPayloadRoot = Path.Combine(appRoot, "BackendPayload");
    if (!File.Exists(manifestPath) || !Directory.Exists(backendPayloadRoot))
        throw new InvalidDataException("当前 AppRoot 不是完整的一体化安装目录。");
    var installedVersion = ReadReleaseVersion(manifestPath);
    if (installedVersion == TargetHotfixVersion && installedHotfix == TargetHotfixVersion)
        return Finish(0, "HF2 已安装，无需重复更新。");
    if (payloadVersion != ExpectedBaseVersion ||
        (installedVersion != ExpectedBaseVersion &&
         installedVersion != PreviousHotfixVersion &&
         installedVersion != TargetHotfixVersion))
        throw new InvalidOperationException(
            $"此维护包只适用于 RC10.10。PayloadVersion={payloadVersion}; ReleaseVersion={installedVersion}");
    var targetFilesAlreadyInstalled = installedVersion == TargetHotfixVersion;

    var workRoot = Path.Combine(dataRoot, "HotfixWork", Guid.NewGuid().ToString("N"));
    Directory.CreateDirectory(workRoot);
    try
    {
        Log("解包并校验 HF2 载荷……");
        ExtractEmbeddedPayload(workRoot);
        var hotfixManifestPath = Path.Combine(workRoot, "hotfix-manifest.json");
        var hotfix = JsonSerializer.Deserialize<HotfixManifest>(
            File.ReadAllText(hotfixManifestPath, Encoding.UTF8), JsonOptions())
            ?? throw new InvalidDataException("HF2 清单无效。");
        if (hotfix.BaseVersion != ExpectedBaseVersion || hotfix.TargetVersion != TargetHotfixVersion)
            throw new InvalidDataException("HF2 版本身份不匹配。");
        VerifyPayloadFiles(workRoot, hotfix.TargetFiles);
        if (targetFilesAlreadyInstalled)
        {
            VerifyPayloadFiles(appRoot, hotfix.TargetFiles);
            Log("检测到上次已完成文件替换，将从后台启动验证阶段继续。 ");
        }
        else if (installedVersion == PreviousHotfixVersion)
        {
            VerifyExistingFilesPresent(appRoot, hotfix.RequiredBaseFiles.Keys);
            Log("检测到 HF1，将在保留客户数据的前提下升级到 HF2。");
        }
        else
        {
            VerifyExistingBaseFiles(appRoot, hotfix.RequiredBaseFiles);
        }

        Log("请求后台备份（后台当前不可用时将跳过，不触碰数据盘）……");
        try
        {
            var response = await SendServiceRequestAsync("backup", TimeSpan.FromMinutes(15));
            Log(response.Ok ? "数据库备份完成。" : $"备份未完成，将继续仅替换应用载荷：{response.Message}");
        }
        catch (Exception backupError)
        {
            Log($"备份接口当前不可用，将继续仅替换应用载荷：{backupError.Message}");
        }

        if (!targetFilesAlreadyInstalled)
        {
            Log("安全停止后台虚拟机和主机服务……");
            StopHostService();

            var backupRoot = Path.Combine(
                dataRoot,
                "HotfixBackups",
                $"rc10.10-before-hf2-{DateTime.Now:yyyyMMdd-HHmmss}");
            Directory.CreateDirectory(backupRoot);
            BackupTargets(appRoot, backupRoot, hotfix.TargetFiles.Keys);
            Log($"旧后台载荷已备份：{backupRoot}");

            try
            {
                ReplaceTargets(appRoot, workRoot, hotfix.TargetFiles);
                VerifyPayloadFiles(appRoot, hotfix.TargetFiles);
            }
            catch
            {
                Log("文件替换失败，正在恢复旧后台载荷……");
                RestoreTargets(appRoot, backupRoot, hotfix.TargetFiles.Keys);
                throw;
            }
        }

        Log("启动 OntoTwin 后台管理服务……");
        StartHostService();
        Log("启动后台虚拟机并应用 HF2；首次应用通常需要 3–10 分钟……");
        var start = await SendServiceRequestAsync("start", TimeSpan.FromMinutes(25));
        if (!start.Ok || !start.BackendReady)
            throw new InvalidOperationException(
                $"HF2 文件已安装，但后台未就绪：{start.Message}{Environment.NewLine}{start.Output}");

        var validation = await ValidateBackendAsync();
        Log($"后台验证通过：{validation}");
        productKey.SetValue("BackendHotfixVersion", TargetHotfixVersion, RegistryValueKind.String);
        return Finish(0, "RC10.10-HF2 后端热修复完成。现在可从桌面“灵云智”启动系统。");
    }
    finally
    {
        try { if (Directory.Exists(workRoot)) Directory.Delete(workRoot, recursive: true); }
        catch (Exception cleanupError) { Log($"临时目录稍后清理：{cleanupError.Message}"); }
    }
}
catch (Exception exception)
{
    return Finish(1, "热修复失败：" + exception);
}

static void ValidateAppRoot(string appRoot)
{
    if (!Path.IsPathFullyQualified(appRoot))
        throw new InvalidDataException("AppRoot 必须是绝对路径。");
    if ((File.GetAttributes(appRoot) & FileAttributes.ReparsePoint) != 0)
        throw new InvalidDataException("AppRoot 不能是符号链接或联接目录。");
    var leaf = new DirectoryInfo(appRoot).Name;
    if (!leaf.Equals("App", StringComparison.OrdinalIgnoreCase) &&
        !leaf.StartsWith("App-", StringComparison.OrdinalIgnoreCase))
        throw new InvalidDataException($"拒绝更新非 OntoTwin App 目录：{appRoot}");
}

static string ReadReleaseVersion(string manifestPath)
{
    using var document = JsonDocument.Parse(File.ReadAllText(manifestPath, Encoding.UTF8));
    return document.RootElement.GetProperty("release_version").GetString() ?? "";
}

static JsonDocument ReadReleaseManifest(string manifestPath) =>
    JsonDocument.Parse(File.ReadAllText(manifestPath, Encoding.UTF8));

static string ReadTarEntryText(string archivePath, string expectedName)
{
    using var source = File.OpenRead(archivePath);
    using var gzip = new GZipStream(source, CompressionMode.Decompress);
    using var reader = new TarReader(gzip);
    TarEntry? entry;
    while ((entry = reader.GetNextEntry()) is not null)
    {
        var name = entry.Name.Replace('\\', '/').TrimStart('.', '/');
        if (!name.Equals(expectedName, StringComparison.OrdinalIgnoreCase)) continue;
        if (entry.DataStream is null) throw new InvalidDataException($"归档成员为空：{expectedName}");
        using var text = new StreamReader(entry.DataStream, Encoding.UTF8, true, 4096, leaveOpen: true);
        return text.ReadToEnd();
    }
    throw new InvalidDataException($"release.tar.gz 缺少 {expectedName}。");
}

static void ExtractEmbeddedPayload(string destination)
{
    using var resource = Assembly.GetExecutingAssembly().GetManifestResourceStream(PayloadResource)
        ?? throw new InvalidDataException("维护程序未包含 HF2 载荷。");
    using var archive = new ZipArchive(resource, ZipArchiveMode.Read, leaveOpen: false);
    foreach (var entry in archive.Entries)
    {
        var relative = entry.FullName.Replace('/', Path.DirectorySeparatorChar);
        var target = Path.GetFullPath(Path.Combine(destination, relative));
        var prefix = Path.GetFullPath(destination).TrimEnd(Path.DirectorySeparatorChar) + Path.DirectorySeparatorChar;
        if (!target.StartsWith(prefix, StringComparison.OrdinalIgnoreCase))
            throw new InvalidDataException($"维护载荷包含非法路径：{entry.FullName}");
        if (string.IsNullOrEmpty(entry.Name))
        {
            Directory.CreateDirectory(target);
            continue;
        }
        Directory.CreateDirectory(Path.GetDirectoryName(target)!);
        entry.ExtractToFile(target, overwrite: true);
    }
}

static JsonSerializerOptions JsonOptions() => new()
{
    PropertyNameCaseInsensitive = true,
    PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower,
};

static void VerifyPayloadFiles(string root, IReadOnlyDictionary<string, string> expected)
{
    foreach (var (relative, hash) in expected)
    {
        var path = SafeTarget(root, relative);
        if (!File.Exists(path)) throw new FileNotFoundException($"缺少维护文件：{relative}", path);
        var actual = Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(path))).ToLowerInvariant();
        if (!actual.Equals(hash, StringComparison.OrdinalIgnoreCase))
            throw new InvalidDataException($"维护文件校验失败：{relative}");
    }
}

static void VerifyExistingBaseFiles(string appRoot, IReadOnlyDictionary<string, string> expected)
{
    foreach (var (relative, hash) in expected)
    {
        var path = SafeTarget(appRoot, relative);
        if (!File.Exists(path)) throw new FileNotFoundException($"RC10.10 基础文件缺失：{relative}", path);
        using var stream = File.OpenRead(path);
        var actual = Convert.ToHexString(SHA256.HashData(stream)).ToLowerInvariant();
        if (!actual.Equals(hash, StringComparison.OrdinalIgnoreCase))
            throw new InvalidDataException($"RC10.10 基础文件已被修改，拒绝盲目覆盖：{relative}");
    }
}

static void VerifyExistingFilesPresent(string appRoot, IEnumerable<string> expected)
{
    foreach (var relative in expected)
    {
        var path = SafeTarget(appRoot, relative);
        if (!File.Exists(path))
            throw new FileNotFoundException($"升级 HF2 所需文件缺失：{relative}", path);
    }
}

static void BackupTargets(string appRoot, string backupRoot, IEnumerable<string> relativePaths)
{
    foreach (var relative in relativePaths)
    {
        var source = SafeTarget(appRoot, relative);
        if (!File.Exists(source)) continue;
        var destination = SafeTarget(backupRoot, relative);
        Directory.CreateDirectory(Path.GetDirectoryName(destination)!);
        File.Copy(source, destination, overwrite: false);
    }
}

static void ReplaceTargets(
    string appRoot,
    string payloadRoot,
    IReadOnlyDictionary<string, string> targetFiles)
{
    foreach (var relative in targetFiles.Keys.OrderBy(path => path.Equals(
                 "release-manifest.json", StringComparison.OrdinalIgnoreCase) ? 1 : 0))
    {
        var source = SafeTarget(payloadRoot, relative);
        var destination = SafeTarget(appRoot, relative);
        Directory.CreateDirectory(Path.GetDirectoryName(destination)!);
        var pending = destination + ".hf2-new";
        File.Copy(source, pending, overwrite: true);
        File.Move(pending, destination, overwrite: true);
    }
}

static void RestoreTargets(string appRoot, string backupRoot, IEnumerable<string> relativePaths)
{
    foreach (var relative in relativePaths)
    {
        var source = SafeTarget(backupRoot, relative);
        if (!File.Exists(source)) continue;
        var destination = SafeTarget(appRoot, relative);
        File.Copy(source, destination, overwrite: true);
    }
}

static string SafeTarget(string root, string relative)
{
    if (Path.IsPathFullyQualified(relative))
        throw new InvalidDataException($"清单路径不能是绝对路径：{relative}");
    var fullRoot = Path.GetFullPath(root).TrimEnd(Path.DirectorySeparatorChar);
    var fullPath = Path.GetFullPath(Path.Combine(fullRoot, relative.Replace('/', Path.DirectorySeparatorChar)));
    var prefix = fullRoot + Path.DirectorySeparatorChar;
    if (!fullPath.StartsWith(prefix, StringComparison.OrdinalIgnoreCase))
        throw new InvalidDataException($"清单路径越界：{relative}");
    return fullPath;
}

static ServiceController FindHostService()
{
    var services = ServiceController.GetServices();
    var match = services.FirstOrDefault(service =>
        service.ServiceName.Equals(ServiceName, StringComparison.OrdinalIgnoreCase));
    foreach (var service in services)
        if (!ReferenceEquals(service, match)) service.Dispose();
    return match ?? throw new InvalidOperationException($"未安装后台管理服务 {ServiceName}。");
}

static void StopHostService()
{
    using var service = FindHostService();
    service.Refresh();
    if (service.Status == ServiceControllerStatus.Stopped) return;
    if (service.Status == ServiceControllerStatus.StartPending)
        service.WaitForStatus(ServiceControllerStatus.Running, TimeSpan.FromSeconds(90));
    service.Refresh();
    if (service.Status != ServiceControllerStatus.StopPending) service.Stop();
    service.WaitForStatus(ServiceControllerStatus.Stopped, TimeSpan.FromMinutes(4));
}

static void StartHostService()
{
    using var service = FindHostService();
    service.Refresh();
    if (service.Status == ServiceControllerStatus.Running) return;
    if (service.Status == ServiceControllerStatus.StopPending)
        service.WaitForStatus(ServiceControllerStatus.Stopped, TimeSpan.FromMinutes(4));
    service.Refresh();
    if (service.Status == ServiceControllerStatus.Stopped) service.Start();
    service.WaitForStatus(ServiceControllerStatus.Running, TimeSpan.FromSeconds(90));
}

static async Task<ControlResponse> SendServiceRequestAsync(string action, TimeSpan timeout)
{
    using var cancellation = new CancellationTokenSource(timeout);
    using var client = new TcpClient();
    await client.ConnectAsync("127.0.0.1", ServiceControlPort, cancellation.Token);
    await using var stream = client.GetStream();
    await using var writer = new StreamWriter(
        stream, new UTF8Encoding(false), 4096, leaveOpen: true) { AutoFlush = true };
    using var reader = new StreamReader(stream, new UTF8Encoding(false), false, 4096, leaveOpen: true);
    await writer.WriteLineAsync(JsonSerializer.Serialize(new { action }));
    var line = await reader.ReadLineAsync(cancellation.Token);
    return JsonSerializer.Deserialize<ControlResponse>(line ?? "", JsonOptions())
        ?? throw new InvalidDataException("后台管理服务返回了无效响应。");
}

static async Task<string> ValidateBackendAsync()
{
    using var client = new HttpClient { Timeout = TimeSpan.FromMinutes(5) };
    using var datasetsResponse = await client.GetAsync("http://127.0.0.1:5000/api/v2/ontology/datasets");
    datasetsResponse.EnsureSuccessStatusCode();
    using var datasets = JsonDocument.Parse(await datasetsResponse.Content.ReadAsStringAsync());
    var active = datasets.RootElement.EnumerateArray().FirstOrDefault(item =>
        item.TryGetProperty("is_active", out var activeValue) && activeValue.GetBoolean());
    if (active.ValueKind == JsonValueKind.Undefined)
        throw new InvalidDataException("后台没有激活的 ZHHZ 数据集。");
    var typeCount = active.GetProperty("type_count").GetInt32();
    var instanceCount = active.GetProperty("instance_count").GetInt32();
    if (typeCount != 38 || instanceCount != 669)
        throw new InvalidDataException($"数据数量不符合 RC10.10 基线：types={typeCount}, instances={instanceCount}");

    var stopwatch = Stopwatch.StartNew();
    using var typesResponse = await client.GetAsync("http://127.0.0.1:5000/api/v2/ontology/types");
    typesResponse.EnsureSuccessStatusCode();
    stopwatch.Stop();
    using var types = JsonDocument.Parse(await typesResponse.Content.ReadAsStringAsync());
    var returnedTypes = types.RootElement.GetArrayLength();
    if (returnedTypes != 38)
        throw new InvalidDataException($"Type 接口返回数量异常：{returnedTypes}");

    using var snapshotRequest = new HttpRequestMessage(
        HttpMethod.Get, "http://127.0.0.1:5000/api/v2/state/snapshot_changes");
    snapshotRequest.Headers.TryAddWithoutValidation("X-OntoTwin-UE-Project-Id", "ueproj_ZHHZ");
    snapshotRequest.Headers.TryAddWithoutValidation("X-OntoTwin-UE-Project-Name", "ZHHZ");
    using var snapshotResponse = await client.SendAsync(snapshotRequest);
    snapshotResponse.EnsureSuccessStatusCode();
    using var snapshot = JsonDocument.Parse(await snapshotResponse.Content.ReadAsStringAsync());
    var upserts = snapshot.RootElement.GetProperty("upserts");
    var snapshotCount = upserts.GetArrayLength();
    var representableCount = 0;
    var renderPartCount = 0;
    foreach (var item in upserts.EnumerateArray())
    {
        if (!item.TryGetProperty("interfaces", out var interfaces) ||
            !interfaces.TryGetProperty("I3D_Representable", out var representable))
            continue;
        representableCount++;
        if (representable.TryGetProperty("render_parts", out var renderParts) &&
            renderParts.ValueKind == JsonValueKind.Array)
            renderPartCount += renderParts.GetArrayLength();
    }
    if (snapshotCount != 669 || representableCount != 669 || renderPartCount != 15693)
        throw new InvalidDataException(
            $"模型快照异常：snapshots={snapshotCount}, representable={representableCount}, render_parts={renderPartCount}");

    await Task.Delay(TimeSpan.FromSeconds(2));
    using var instancesRequest = new HttpRequestMessage(
        HttpMethod.Get, "http://127.0.0.1:5000/api/v2/instances");
    instancesRequest.Headers.TryAddWithoutValidation("X-OntoTwin-UE-Project-Id", "ueproj_ZHHZ");
    instancesRequest.Headers.TryAddWithoutValidation("X-OntoTwin-UE-Project-Name", "ZHHZ");
    using var instancesResponse = await client.SendAsync(instancesRequest);
    instancesResponse.EnsureSuccessStatusCode();
    using var instances = JsonDocument.Parse(await instancesResponse.Content.ReadAsStringAsync());
    var onlineCount = instances.RootElement.EnumerateArray().Count(item =>
        item.TryGetProperty("status", out var status) && status.GetString() == "online");
    if (onlineCount != 669)
        throw new InvalidDataException($"实例心跳异常：online={onlineCount}, expected=669");

    return $"38 Types / 669 Instances / 669 Snapshots / 15,693 Render Parts / {onlineCount} Online；Type 接口 {stopwatch.Elapsed.TotalSeconds:N1}s";
}

sealed record HotfixManifest(
    [property: JsonPropertyName("base_version")] string BaseVersion,
    [property: JsonPropertyName("target_version")] string TargetVersion,
    [property: JsonPropertyName("required_base_files")] Dictionary<string, string> RequiredBaseFiles,
    [property: JsonPropertyName("target_files")] Dictionary<string, string> TargetFiles);

sealed record ControlResponse(
    [property: JsonPropertyName("ok")] bool Ok,
    [property: JsonPropertyName("message")] string Message,
    [property: JsonPropertyName("output")] string Output,
    [property: JsonPropertyName("backendReady")] bool BackendReady,
    [property: JsonPropertyName("vmState")] string VmState,
    [property: JsonPropertyName("backupPath")] string? BackupPath);
