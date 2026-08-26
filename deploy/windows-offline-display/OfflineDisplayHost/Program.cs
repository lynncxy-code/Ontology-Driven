using System.Diagnostics;
using System.Net;
using System.Net.Sockets;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using Microsoft.AspNetCore.Http.Features;

namespace LingYunZhi.Offline;

internal static class Program
{
    [DllImport("user32.dll", CharSet = CharSet.Unicode)]
    private static extern int MessageBoxW(IntPtr hWnd, string text, string caption, uint type);

    public static async Task<int> Main(string[] args)
    {
        try
        {
            return await RunAsync(args);
        }
        catch (Exception ex)
        {
            WriteEmergencyLog(ex);
            MessageBoxW(IntPtr.Zero, ex.Message, "灵云智离线展示版", 0x10);
            return 1;
        }
    }

    private static async Task<int> RunAsync(string[] args)
    {
        var requestedPort = ReadIntArgument(args, "--listen-port=", 5000);
        if (requestedPort is < 1024 or > 65535)
        {
            throw new ArgumentOutOfRangeException(nameof(requestedPort), "本地服务端口必须在 1024–65535 之间。 ");
        }
        var listenPort = SelectAvailableLoopbackPort(requestedPort);
        var listenUrl = $"http://127.0.0.1:{listenPort}";
        var selfTest = args.Any(arg => arg.Equals("--self-test", StringComparison.OrdinalIgnoreCase));
        var root = AppContext.BaseDirectory;
        var runtimePack = Path.Combine(root, "RuntimePack");
        var manifestPath = Path.Combine(runtimePack, "runtime-pack.json");
        var ueExecutable = Path.Combine(root, "ZHHZ_NEW", "ZHHZ_NEW.exe");
        RequireFile(manifestPath, "离线数据清单缺失");
        RequireFile(ueExecutable, "ZHHZ_NEW 运行程序缺失");

        var manifest = JsonDocument.Parse(await File.ReadAllBytesAsync(manifestPath));
        var projectId = manifest.RootElement.GetProperty("project_id").GetString() ?? "";
        var ueProjectId = manifest.RootElement.GetProperty("ue_project_id").GetString() ?? "";
        if (projectId.Length == 0 || ueProjectId != "ueproj_ZHHZ_NEW")
        {
            throw new InvalidDataException("离线包身份校验失败，拒绝启动。 ");
        }

        var logDir = Path.Combine(root, "Logs");
        Directory.CreateDirectory(logDir);
        var logPath = Path.Combine(logDir, "offline-host.log");
        await File.AppendAllTextAsync(
            logPath,
            $"[{DateTimeOffset.Now:O}] starting project={projectId} ue={ueProjectId} requested_port={requestedPort} selected_port={listenPort}{Environment.NewLine}",
            Encoding.UTF8);

        var binding = await LoadVerifiedAsync(runtimePack, "binding.json", manifest.RootElement);
        var snapshots = await LoadVerifiedAsync(runtimePack, "snapshots.json", manifest.RootElement);
        var reset = await LoadVerifiedAsync(runtimePack, "snapshot-reset.json", manifest.RootElement);
        var delta = await LoadVerifiedAsync(runtimePack, "snapshot-delta.json", manifest.RootElement);
        var scene = await LoadVerifiedAsync(runtimePack, "scene-runtime.json", manifest.RootElement);
        var web = await LoadVerifiedAsync(runtimePack, "web-runtime.json", manifest.RootElement);
        var webRevision = JsonDocument.Parse(web).RootElement.GetProperty("revision").GetInt32();

        var builder = WebApplication.CreateSlimBuilder(Array.Empty<string>());
        builder.Logging.ClearProviders();
        builder.WebHost.UseUrls(listenUrl);
        builder.WebHost.ConfigureKestrel(options =>
        {
            options.Limits.MaxRequestBodySize = 2 * 1024 * 1024;
            options.Limits.KeepAliveTimeout = TimeSpan.FromSeconds(30);
        });
        var app = builder.Build();
        app.Use(async (context, next) =>
        {
            context.Response.Headers.CacheControl = "no-store";
            await next();
        });

        app.MapGet("/offline-health", () => Results.Json(new
        {
            status = "ok",
            mode = "offline",
            project_id = projectId,
            ue_project_id = ueProjectId
        }));
        app.MapGet("/api/health", () => Results.Json(new { status = "ok", mode = "offline" }));
        app.MapGet("/api/v2/ue/binding_status", () => JsonBytes(binding));
        app.MapGet("/api/v2/state/snapshots", () => JsonBytes(snapshots));
        app.MapGet("/api/v2/state/snapshot_changes", (HttpRequest request) =>
            string.IsNullOrWhiteSpace(request.Query["cursor"])
                ? JsonBytes(reset)
                : JsonBytes(delta));
        app.MapGet("/api/v2/scene-interactions/runtime", () => JsonBytes(scene));
        app.MapPost("/api/v2/scene-interactions/runtime", () => OfflineAccepted());
        app.MapGet("/api/v2/web-interactions/runtime", (HttpRequest request) =>
        {
            return int.TryParse(request.Query["known_revision"], out var known)
                   && known == webRevision
                ? Results.Json(new { status = "unchanged", project_id = projectId, revision = webRevision })
                : JsonBytes(web);
        });
        app.MapPost("/api/v2/web-interactions/runtime-events", () => OfflineAccepted());
        app.MapGet("/api/v2/external-data/realtime", () => Results.Json(new
        {
            status = "ok", enabled = false, websocket_enabled = false, mode = "offline"
        }));
        app.MapGet("/api/v2/ue/assets/scan-requests/pending", () =>
            Results.Json(new { status = "ok", requests = Array.Empty<object>() }));
        app.MapGet("/api/v2/scene-interactions/narration-assets/{assetId}",
            (string assetId) => ServeNamedAsset(runtimePack, "Audio", assetId, ".wav", "audio/wav"));
        app.MapGet("/api/v2/assets/download", (HttpRequest request) =>
            ServeModel(runtimePack, request.Query["id"].ToString()));
        app.MapPost("/api/v2/overlays/media/resolve", () =>
            Results.Json(new { error = "offline_media_not_embedded" }, statusCode: 404));

        foreach (var path in new[]
                 {
                     "/api/v2/state/writeback", "/api/v2/state/writeback/batch",
                     "/api/v2/state/material-writeback", "/api/v2/ue/bind_active_project"
                 })
        {
            app.MapMethods(path, new[] { "POST", "PUT", "DELETE" }, () =>
                Results.Json(new { error = "offline_read_only" }, statusCode: 403));
        }

        await app.StartAsync();
        await File.AppendAllTextAsync(
            logPath,
            $"[{DateTimeOffset.Now:O}] local runtime ready {listenUrl}{Environment.NewLine}",
            Encoding.UTF8);

        if (selfTest)
        {
            using var client = new HttpClient { BaseAddress = new Uri(listenUrl) };
            var health = await client.GetFromJsonAsync<JsonElement>("/offline-health");
            if (health.GetProperty("project_id").GetString() != projectId)
            {
                throw new InvalidDataException("本地服务自检返回了错误的数据集。 ");
            }
            var sceneResponse = await client.GetAsync("/api/v2/scene-interactions/runtime");
            var resetResponse = await client.GetAsync("/api/v2/state/snapshot_changes");
            if (!sceneResponse.IsSuccessStatusCode || !resetResponse.IsSuccessStatusCode
                || resetResponse.Content.Headers.ContentLength < 1_000_000)
            {
                throw new InvalidDataException("本地服务自检未能读取完整运行快照。 ");
            }
            await app.StopAsync(TimeSpan.FromSeconds(5));
            await File.AppendAllTextAsync(
                logPath,
                $"[{DateTimeOffset.Now:O}] self-test passed{Environment.NewLine}",
                Encoding.UTF8);
            return 0;
        }

        var ueArgs = new List<string>
        {
            $"-OntoTwinBackendBaseUrl=http://127.0.0.1:{listenPort}",
            "-OntoTwinIncrementalSnapshots=true"
        };
        ueArgs.AddRange(args.Where(arg => arg.StartsWith("-", StringComparison.Ordinal)
            && !arg.StartsWith("--listen-port=", StringComparison.OrdinalIgnoreCase)
            && !arg.Equals("--self-test", StringComparison.OrdinalIgnoreCase)));
        using var ue = Process.Start(new ProcessStartInfo
        {
            FileName = ueExecutable,
            Arguments = string.Join(" ", ueArgs.Select(QuoteArgument)),
            WorkingDirectory = Path.GetDirectoryName(ueExecutable)!,
            UseShellExecute = false
        }) ?? throw new InvalidOperationException("无法启动 ZHHZ_NEW。 ");

        await File.AppendAllTextAsync(
            logPath,
            $"[{DateTimeOffset.Now:O}] ue pid={ue.Id}{Environment.NewLine}",
            Encoding.UTF8);
        await ue.WaitForExitAsync();
        await app.StopAsync(TimeSpan.FromSeconds(5));
        await File.AppendAllTextAsync(
            logPath,
            $"[{DateTimeOffset.Now:O}] ue exit={ue.ExitCode}{Environment.NewLine}",
            Encoding.UTF8);
        return ue.ExitCode;
    }

    private static IResult JsonBytes(byte[] bytes) => Results.Bytes(bytes, "application/json; charset=utf-8");

    private static IResult OfflineAccepted() => Results.Json(new
    {
        status = "ok", accepted = true, persisted = false, mode = "offline"
    });

    private static async Task<byte[]> LoadVerifiedAsync(
        string root,
        string name,
        JsonElement manifest)
    {
        var path = Path.Combine(root, name);
        RequireFile(path, $"离线数据文件缺失：{name}");
        var bytes = await File.ReadAllBytesAsync(path);
        var expected = manifest.GetProperty("files").EnumerateArray()
            .FirstOrDefault(item => item.TryGetProperty("path", out var filePath)
                                    && filePath.GetString() == name);
        if (expected.ValueKind == JsonValueKind.Undefined)
        {
            throw new InvalidDataException($"清单未登记离线数据文件：{name}");
        }
        var actualHash = Convert.ToHexString(SHA256.HashData(bytes)).ToLowerInvariant();
        if (!string.Equals(actualHash, expected.GetProperty("sha256").GetString(), StringComparison.Ordinal))
        {
            throw new InvalidDataException($"离线数据文件校验失败：{name}");
        }
        return bytes;
    }

    private static IResult ServeNamedAsset(
        string runtimePack,
        string directory,
        string assetId,
        string extension,
        string contentType)
    {
        if (!IsSafeName(assetId)) return Results.BadRequest();
        var path = Path.Combine(runtimePack, directory, assetId + extension);
        return File.Exists(path) ? Results.File(path, contentType) : Results.NotFound();
    }

    private static IResult ServeModel(string runtimePack, string assetId)
    {
        if (!IsSafeName(assetId)) return Results.BadRequest();
        var models = Path.Combine(runtimePack, "Models");
        if (!Directory.Exists(models)) return Results.NotFound();
        var fileName = Path.GetFileName(assetId);
        var candidate = Directory.EnumerateFiles(models, fileName, SearchOption.AllDirectories)
            .FirstOrDefault();
        return candidate is null
            ? Results.NotFound()
            : Results.File(candidate, "model/gltf-binary", enableRangeProcessing: true);
    }

    private static bool IsSafeName(string value) =>
        !string.IsNullOrWhiteSpace(value)
        && value.IndexOfAny(Path.GetInvalidFileNameChars()) < 0
        && !value.Contains("..", StringComparison.Ordinal)
        && !value.Contains('/')
        && !value.Contains('\\');

    private static void RequireFile(string path, string message)
    {
        if (!File.Exists(path)) throw new FileNotFoundException(message, path);
    }

    private static string QuoteArgument(string value) =>
        value.Contains(' ') ? $"\"{value.Replace("\"", "\\\"")}\"" : value;

    private static int ReadIntArgument(string[] args, string prefix, int fallback)
    {
        var value = args.FirstOrDefault(arg => arg.StartsWith(prefix, StringComparison.OrdinalIgnoreCase));
        return value is not null && int.TryParse(value[prefix.Length..], out var parsed)
            ? parsed
            : fallback;
    }

    private static int SelectAvailableLoopbackPort(int preferredPort)
    {
        if (CanBindLoopback(preferredPort))
        {
            return preferredPort;
        }

        using var listener = new TcpListener(IPAddress.Loopback, 0);
        listener.Start();
        var selectedPort = ((IPEndPoint)listener.LocalEndpoint).Port;
        listener.Stop();
        return selectedPort;
    }

    private static bool CanBindLoopback(int port)
    {
        try
        {
            using var listener = new TcpListener(IPAddress.Loopback, port);
            listener.Start();
            listener.Stop();
            return true;
        }
        catch (SocketException)
        {
            return false;
        }
    }

    private static void WriteEmergencyLog(Exception ex)
    {
        try
        {
            var logDir = Path.Combine(AppContext.BaseDirectory, "Logs");
            Directory.CreateDirectory(logDir);
            File.AppendAllText(
                Path.Combine(logDir, "offline-host-error.log"),
                $"[{DateTimeOffset.Now:O}] {ex}{Environment.NewLine}",
                Encoding.UTF8);
        }
        catch
        {
            // The MessageBox remains the last-resort diagnostic channel.
        }
    }
}
