using System.Diagnostics;
using System.Collections.Concurrent;
using System.Net;
using System.Net.Http.Headers;
using System.Net.Sockets;
using System.ServiceProcess;
using System.Text;
using System.Text.Json;
using Microsoft.Win32;

namespace OntoTwin.ZHHZ.HostService;

internal static class Program
{
    private const string ProductKey = @"SOFTWARE\OntoTwin\ZHHZ";

    private static void Main(string[] args)
    {
        var guardedRemoveIndex = Array.FindIndex(
            args,
            argument => argument.Equals("--remove-backend-if-version", StringComparison.OrdinalIgnoreCase));
        if (guardedRemoveIndex >= 0)
        {
            if (guardedRemoveIndex + 1 >= args.Length || string.IsNullOrWhiteSpace(args[guardedRemoveIndex + 1]))
            {
                Console.Error.WriteLine("--remove-backend-if-version requires an expected payload version.");
                Environment.ExitCode = 2;
                return;
            }
            var expected = args[guardedRemoveIndex + 1].Trim();
            using var key = Registry.LocalMachine.OpenSubKey(ProductKey);
            var registered = (key?.GetValue("PayloadVersion") as string)?.Trim();
            if (!string.Equals(registered, expected, StringComparison.OrdinalIgnoreCase))
            {
                Console.WriteLine(
                    $"Skipping backend removal because payload ownership changed. " +
                    $"Expected={expected}; Registered={registered ?? "<missing>"}.");
                Environment.ExitCode = 0;
                return;
            }
        }

        var runtime = new HostRuntime();
        if (guardedRemoveIndex >= 0)
        {
            Environment.ExitCode = runtime.RunOneShotAsync("Remove").GetAwaiter().GetResult();
            return;
        }
        if (args.Contains("--remove-backend", StringComparer.OrdinalIgnoreCase))
        {
            Environment.ExitCode = runtime.RunOneShotAsync("Remove").GetAwaiter().GetResult();
            return;
        }
        if (args.Contains("--console", StringComparer.OrdinalIgnoreCase))
        {
            Console.CancelKeyPress += (_, eventArgs) =>
            {
                eventArgs.Cancel = true;
                runtime.Stop();
            };
            runtime.RunAsync().GetAwaiter().GetResult();
            return;
        }

        ServiceBase.Run(new OntoTwinHostService(runtime));
    }
}

internal sealed class OntoTwinHostService : ServiceBase
{
    private readonly HostRuntime _runtime;

    public OntoTwinHostService(HostRuntime runtime)
    {
        _runtime = runtime;
        ServiceName = "OntoTwinZHHZHost";
        CanStop = true;
        CanShutdown = true;
    }

    protected override void OnStart(string[] args) => _runtime.Start();

    protected override void OnStop()
    {
        RequestAdditionalTime(120_000);
        _runtime.Stop();
    }

    protected override void OnShutdown()
    {
        RequestAdditionalTime(120_000);
        _runtime.Stop();
    }
}

internal sealed class HostRuntime
{
    private const int ControlPort = 48073;
    private const int GuestControlPort = 49274;
    // Keep the bootstrap listener below Windows' default dynamic TCP range.
    // Hyper-V/HNS commonly reserves blocks beginning at 49152, which makes
    // ports in those blocks fail with SocketError.AccessDenied.
    private const int PayloadPort = 48075;
    private const string GuestAddress = "172.28.251.2";
    private const string HostAddress = "172.28.251.1";

    private readonly CancellationTokenSource _stopping = new();
    private readonly SemaphoreSlim _operationLock = new(1, 1);
    private readonly ConcurrentDictionary<int, Task> _clientTasks = new();
    private readonly ConcurrentDictionary<int, Process> _childProcesses = new();
    private readonly string _installRoot;
    private readonly string _appRoot;
    private readonly string _dataRoot;
    private readonly string _hostScript;
    private readonly string _payloadRoot;
    private readonly string _logPath;
    private Task? _serverTask;
    private TcpListener? _listener;
    private string _bootstrapProgress = "等待虚拟机启动";
    private int _nextClientTaskId;
    private int _stopStarted;

    public HostRuntime()
    {
        var serviceDirectory = AppContext.BaseDirectory.TrimEnd(Path.DirectorySeparatorChar);
        _installRoot = Directory.GetParent(serviceDirectory)?.FullName ?? serviceDirectory;
        _appRoot = ResolveAppRoot(_installRoot);
        _dataRoot = ResolveDataRoot();
        _hostScript = Path.Combine(_installRoot, "Host", "HostControl.ps1");
        _payloadRoot = Path.Combine(_appRoot, "BackendPayload");
        var logDirectory = Path.Combine(_dataRoot, "Logs");
        Directory.CreateDirectory(logDirectory);
        _logPath = Path.Combine(logDirectory, "host-service.log");
    }

    private static string ResolveAppRoot(string installRoot)
    {
        using var key = Registry.LocalMachine.OpenSubKey(@"SOFTWARE\OntoTwin\ZHHZ");
        var configured = key?.GetValue("AppRoot") as string;
        return string.IsNullOrWhiteSpace(configured)
            ? Path.Combine(installRoot, "App")
            : Path.GetFullPath(configured);
    }

    private static string ResolveDataRoot()
    {
        var legacy = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.CommonApplicationData),
            "OntoTwin-ZHHZ");
        using var key = Registry.LocalMachine.OpenSubKey(@"SOFTWARE\OntoTwin\ZHHZ");
        var configured = key?.GetValue("DataRoot") as string;
        if (string.IsNullOrWhiteSpace(configured)) return Path.GetFullPath(legacy);
        if (!Path.IsPathFullyQualified(configured))
            throw new InvalidDataException($"The configured OntoTwin DataRoot is not an absolute path: {configured}");
        return Path.GetFullPath(configured);
    }

    public void Start()
    {
        _serverTask = Task.Run(RunAsync);
        _ = _serverTask.ContinueWith(task =>
        {
            Log("Fatal host-service listener failure: " + task.Exception);
            // Let Windows Service Recovery restart a listener that unexpectedly died.
            Environment.Exit(1);
        }, CancellationToken.None, TaskContinuationOptions.OnlyOnFaulted, TaskScheduler.Default);
    }

    public void Stop()
    {
        if (Interlocked.Exchange(ref _stopStarted, 1) != 0) return;
        Log("OntoTwin ZHHZ host service is quiescing before shutdown.");
        _stopping.Cancel();
        _listener?.Stop();
        foreach (var process in _childProcesses.Values)
        {
            try
            {
                if (!process.HasExited) process.Kill(entireProcessTree: true);
            }
            catch (Exception exception) { Log("Could not stop host-control child process: " + exception.Message); }
        }
        try { Task.WaitAll(_clientTasks.Values.ToArray(), TimeSpan.FromSeconds(20)); } catch { }
        try { _serverTask?.Wait(TimeSpan.FromSeconds(10)); } catch { }

        // Stopping the Windows service is also the installer quiesce boundary.
        // Power the guest down cleanly so its databases and mounted seed media are
        // no longer active while an upgrade swaps the application payload.
        try
        {
            using var timeout = new CancellationTokenSource(TimeSpan.FromSeconds(90));
            var result = RunHostScriptAsync("Stop", timeout.Token).GetAwaiter().GetResult();
            if (result.ExitCode != 0) Log("Backend shutdown during service stop failed: " + result.Output);
        }
        catch (Exception exception) { Log("Backend shutdown during service stop failed: " + exception); }
    }

    public async Task<int> RunOneShotAsync(string action)
    {
        var result = await RunHostScriptAsync(action, CancellationToken.None);
        return result.ExitCode;
    }

    public async Task RunAsync()
    {
        Log($"OntoTwin ZHHZ host service started. Version={GetHostVersion()}, AppRoot={_appRoot}, DataRoot={_dataRoot}");
        _listener = new TcpListener(IPAddress.Loopback, ControlPort);
        _listener.Start();
        try
        {
            while (!_stopping.IsCancellationRequested)
            {
                TcpClient client;
                try
                {
                    client = await _listener.AcceptTcpClientAsync(_stopping.Token);
                }
                catch (OperationCanceledException) { break; }
                catch (ObjectDisposedException) { break; }
                catch (SocketException) when (_stopping.IsCancellationRequested) { break; }

                var id = Interlocked.Increment(ref _nextClientTaskId);
                var task = Task.Run(() => HandleClientAsync(client, _stopping.Token));
                _clientTasks[id] = task;
                _ = task.ContinueWith(completed =>
                {
                    _clientTasks.TryRemove(id, out _);
                    if (completed.IsFaulted) Log("Unhandled client task failure: " + completed.Exception);
                }, CancellationToken.None, TaskContinuationOptions.ExecuteSynchronously, TaskScheduler.Default);
            }
        }
        finally
        {
            _listener.Stop();
            Log("OntoTwin ZHHZ host service stopped.");
        }
    }

    private async Task HandleClientAsync(TcpClient client, CancellationToken cancellationToken)
    {
        await using var stream = client.GetStream();
        using var reader = new StreamReader(stream, new UTF8Encoding(false), false, 4096, leaveOpen: true);
        await using var writer = new StreamWriter(stream, new UTF8Encoding(false), 4096, leaveOpen: true) { AutoFlush = true };
        ControlResponse response;
        try
        {
            var line = await reader.ReadLineAsync(cancellationToken);
            if (string.IsNullOrWhiteSpace(line) || line.Length > 16_384)
            {
                throw new InvalidDataException("Invalid control request.");
            }
            var request = JsonSerializer.Deserialize<ControlRequest>(line, JsonOptions.Default)
                ?? throw new InvalidDataException("Empty control request.");
            response = await ExecuteAsync(request, cancellationToken);
        }
        catch (Exception exception)
        {
            Log(exception.ToString());
            response = new ControlResponse(false, exception.Message, exception.ToString(), false, "Unknown", null);
        }
        try { await writer.WriteLineAsync(JsonSerializer.Serialize(response, JsonOptions.Default)); }
        catch (Exception exception) when (exception is IOException or SocketException or ObjectDisposedException)
        {
            Log("Control client disconnected before receiving the response: " + exception.Message);
        }
    }

    private async Task<ControlResponse> ExecuteAsync(ControlRequest request, CancellationToken cancellationToken)
    {
        var action = request.Action?.Trim().ToLowerInvariant() ?? "";
        if (action == "status")
        {
            var status = await ReadStatusAsync(cancellationToken);
            return new ControlResponse(true, "状态检查完成", status.Output, status.BackendReady, status.VmState, null);
        }

        await _operationLock.WaitAsync(cancellationToken);
        try
        {
            return action switch
            {
                "start" => await StartBackendAsync(cancellationToken),
                "stop" => await RunActionAsync("Stop", "后台已停止", cancellationToken),
                "backup" => await BackupAsync(cancellationToken),
                "provision" => await ProvisionAsync(cancellationToken),
                _ => throw new InvalidOperationException($"Unsupported action: {request.Action}")
            };
        }
        finally
        {
            _operationLock.Release();
        }
    }

    private async Task<ControlResponse> ProvisionAsync(CancellationToken cancellationToken)
    {
        var result = await RunHostScriptAsync("Provision", cancellationToken);
        return new ControlResponse(result.ExitCode == 0, result.ExitCode == 0 ? "后台设备准备完成" : "后台设备准备失败",
            result.Output, false, "Off", null);
    }

    private async Task<ControlResponse> StartBackendAsync(CancellationToken cancellationToken)
    {
        SetBootstrapProgress("正在准备后台虚拟机");
        var provision = await RunHostScriptAsync("Provision", cancellationToken);
        if (provision.ExitCode != 0)
        {
            return new ControlResponse(false, "后台设备准备失败", provision.Output, false, "Unknown", null);
        }

        SetBootstrapProgress("正在启动虚拟机载荷服务");
        using var payloadServer = new PayloadServer(HostAddress, PayloadPort, _payloadRoot, EnsureToken(), SetBootstrapProgress);
        payloadServer.Start();
        SetBootstrapProgress("正在启动后台虚拟机");
        var result = await RunHostScriptAsync("Start", cancellationToken);
        var status = await ReadStatusAsync(cancellationToken);
        var ok = result.ExitCode == 0 && status.BackendReady;
        return new ControlResponse(ok, ok ? "后台已就绪" : "后台启动失败",
            provision.Output + Environment.NewLine + result.Output, status.BackendReady, status.VmState, null);
    }

    private async Task<ControlResponse> RunActionAsync(string action, string successMessage, CancellationToken cancellationToken)
    {
        var result = await RunHostScriptAsync(action, cancellationToken);
        var status = await ReadStatusAsync(cancellationToken);
        return new ControlResponse(result.ExitCode == 0, result.ExitCode == 0 ? successMessage : $"{action} 失败",
            result.Output, status.BackendReady, status.VmState, null);
    }

    private async Task<ControlResponse> BackupAsync(CancellationToken cancellationToken)
    {
        var status = await ReadStatusAsync(cancellationToken);
        if (!status.BackendReady)
        {
            return new ControlResponse(false, "请先启动后台再执行备份", status.Output, false, status.VmState, null);
        }

        var backupDirectory = Path.Combine(_dataRoot, "Backups");
        Directory.CreateDirectory(backupDirectory);
        var backupPath = Path.Combine(backupDirectory, $"OntoTwin-ZHHZ-{DateTime.Now:yyyyMMdd-HHmmss}.tar.gz");
        using var client = new HttpClient { Timeout = TimeSpan.FromMinutes(15) };
        client.DefaultRequestHeaders.Add("X-OntoTwin-Token", EnsureToken());
        try
        {
            using var response = await client.PostAsync($"http://{GuestAddress}:{GuestControlPort}/backup", null, cancellationToken);
            response.EnsureSuccessStatusCode();
            await using var destination = new FileStream(backupPath, FileMode.CreateNew, FileAccess.Write, FileShare.None);
            await response.Content.CopyToAsync(destination, cancellationToken);
        }
        catch
        {
            try { File.Delete(backupPath); } catch { }
            throw;
        }
        return new ControlResponse(true, "备份完成", backupPath, true, status.VmState, backupPath);
    }

    private async Task<(bool BackendReady, string VmState, string Output)> ReadStatusAsync(CancellationToken cancellationToken)
    {
        var result = await RunHostScriptAsync("Status", cancellationToken);
        var backendReady = false;
        try
        {
            using var client = new HttpClient { Timeout = TimeSpan.FromSeconds(3) };
            using var response = await client.GetAsync("http://127.0.0.1:5000/", cancellationToken);
            backendReady = response.IsSuccessStatusCode;
        }
        catch { }
        var vmState = result.Output.Contains("Running", StringComparison.OrdinalIgnoreCase) ? "Running" :
            result.Output.Contains("Off", StringComparison.OrdinalIgnoreCase) ? "Off" : "Unknown";
        var progress = Volatile.Read(ref _bootstrapProgress);
        var output = result.Output + Environment.NewLine +
                     "BootstrapProgress: " + progress + Environment.NewLine +
                     "HostVersion: " + GetHostVersion() + Environment.NewLine +
                     "AppRoot: " + _appRoot + Environment.NewLine +
                     "DataRoot: " + _dataRoot;
        return (backendReady, vmState, output.Trim());
    }

    private static string GetHostVersion() =>
        typeof(HostRuntime).Assembly.GetName().Version?.ToString() ?? "unknown";

    private async Task<ProcessResult> RunHostScriptAsync(string action, CancellationToken cancellationToken)
    {
        if (!File.Exists(_hostScript))
        {
            throw new FileNotFoundException("Host control script is missing.", _hostScript);
        }
        var startInfo = new ProcessStartInfo
        {
            FileName = "powershell.exe",
            UseShellExecute = false,
            CreateNoWindow = true,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            WorkingDirectory = Path.GetDirectoryName(_hostScript) ?? _installRoot
        };
        foreach (var argument in new[]
        {
            "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", _hostScript,
            "-Action", action, "-AppRoot", _appRoot, "-DataRoot", _dataRoot
        }) startInfo.ArgumentList.Add(argument);

        using var process = new Process { StartInfo = startInfo };
        process.Start();
        _childProcesses[process.Id] = process;
        try
        {
            var stdout = process.StandardOutput.ReadToEndAsync();
            var stderr = process.StandardError.ReadToEndAsync();
            try
            {
                await process.WaitForExitAsync(cancellationToken);
            }
            catch (OperationCanceledException)
            {
                try
                {
                    if (!process.HasExited) process.Kill(entireProcessTree: true);
                    await process.WaitForExitAsync(CancellationToken.None);
                }
                catch { }
                throw;
            }
            var output = (await stdout) + (await stderr);
            Log($"HostControl {action} exited {process.ExitCode}.{Environment.NewLine}{output}");
            return new ProcessResult(process.ExitCode, output.Trim());
        }
        finally
        {
            _childProcesses.TryRemove(process.Id, out _);
        }
    }

    private string EnsureToken()
    {
        var tokenPath = Path.Combine(_dataRoot, "control.token");
        if (File.Exists(tokenPath)) return File.ReadAllText(tokenPath).Trim();
        Directory.CreateDirectory(_dataRoot);
        var token = Convert.ToHexString(System.Security.Cryptography.RandomNumberGenerator.GetBytes(32)).ToLowerInvariant();
        File.WriteAllText(tokenPath, token, new UTF8Encoding(false));
        return token;
    }

    private void Log(string message)
    {
        try { File.AppendAllText(_logPath, $"[{DateTime.Now:O}] {message}{Environment.NewLine}", new UTF8Encoding(false)); }
        catch { }
    }

    private void SetBootstrapProgress(string message)
    {
        var progress = string.IsNullOrWhiteSpace(message) ? "正在初始化后台" : message.Trim();
        Volatile.Write(ref _bootstrapProgress, progress);
        Log("Bootstrap progress: " + progress);
    }

    private sealed record ProcessResult(int ExitCode, string Output);
}

internal sealed class PayloadServer : IDisposable
{
    private readonly HttpListener _listener = new();
    private readonly string _payloadRoot;
    private readonly string _token;
    private readonly Action<string> _reportProgress;
    private readonly CancellationTokenSource _stopping = new();
    private Task? _task;

    public PayloadServer(string address, int port, string payloadRoot, string token, Action<string> reportProgress)
    {
        _listener.Prefixes.Add($"http://{address}:{port}/");
        _payloadRoot = Path.GetFullPath(payloadRoot);
        _token = token;
        _reportProgress = reportProgress;
    }

    public void Start()
    {
        if (!Directory.Exists(_payloadRoot)) throw new DirectoryNotFoundException($"Backend payload is missing: {_payloadRoot}");
        _listener.Start();
        _task = Task.Run(RunAsync);
    }

    private async Task RunAsync()
    {
        while (!_stopping.IsCancellationRequested)
        {
            HttpListenerContext context;
            try { context = await _listener.GetContextAsync().WaitAsync(_stopping.Token); }
            catch (OperationCanceledException) { break; }
            catch (HttpListenerException) when (_stopping.IsCancellationRequested) { break; }
            _ = Task.Run(() => HandleAsync(context));
        }
    }

    private async Task HandleAsync(HttpListenerContext context)
    {
        try
        {
            var path = context.Request.Url?.AbsolutePath ?? "/";
            if (path.Equals("/bootstrap/token", StringComparison.OrdinalIgnoreCase))
            {
                await WriteTextAsync(context.Response, _token);
                return;
            }
            if (path.Equals("/bootstrap/ready", StringComparison.OrdinalIgnoreCase))
            {
                using var reader = new StreamReader(context.Request.InputStream, context.Request.ContentEncoding);
                _reportProgress("虚拟机初始化完成：" + await reader.ReadToEndAsync());
                await WriteTextAsync(context.Response, "ok");
                return;
            }
            if (path.Equals("/bootstrap/progress", StringComparison.OrdinalIgnoreCase))
            {
                using var reader = new StreamReader(context.Request.InputStream, context.Request.ContentEncoding);
                _reportProgress(await reader.ReadToEndAsync());
                await WriteTextAsync(context.Response, "ok");
                return;
            }
            if (!path.StartsWith("/payload/", StringComparison.OrdinalIgnoreCase))
            {
                context.Response.StatusCode = 404;
                context.Response.Close();
                return;
            }

            var relative = Uri.UnescapeDataString(path["/payload/".Length..]).Replace('/', Path.DirectorySeparatorChar);
            var fullPath = Path.GetFullPath(Path.Combine(_payloadRoot, relative));
            var allowedPrefix = _payloadRoot.TrimEnd(Path.DirectorySeparatorChar) + Path.DirectorySeparatorChar;
            if (!fullPath.StartsWith(allowedPrefix, StringComparison.OrdinalIgnoreCase) || !File.Exists(fullPath))
            {
                context.Response.StatusCode = 404;
                context.Response.Close();
                return;
            }
            var info = new FileInfo(fullPath);
            context.Response.ContentLength64 = info.Length;
            context.Response.ContentType = "application/octet-stream";
            await using var source = new FileStream(fullPath, FileMode.Open, FileAccess.Read, FileShare.Read, 1024 * 1024, true);
            await source.CopyToAsync(context.Response.OutputStream, _stopping.Token);
            context.Response.Close();
        }
        catch (Exception exception)
        {
            _reportProgress("载荷请求失败：" + exception.Message);
            try { context.Response.StatusCode = 500; context.Response.Close(); } catch { }
        }
    }

    private static async Task WriteTextAsync(HttpListenerResponse response, string text)
    {
        var bytes = Encoding.UTF8.GetBytes(text);
        response.ContentType = "text/plain; charset=utf-8";
        response.ContentLength64 = bytes.Length;
        await response.OutputStream.WriteAsync(bytes);
        response.Close();
    }

    public void Dispose()
    {
        _stopping.Cancel();
        _listener.Close();
        try { _task?.Wait(TimeSpan.FromSeconds(5)); } catch { }
        _stopping.Dispose();
    }
}

internal sealed record ControlRequest(string? Action);
internal sealed record ControlResponse(bool Ok, string Message, string Output, bool BackendReady, string VmState, string? BackupPath);

internal static class JsonOptions
{
    public static readonly JsonSerializerOptions Default = new(JsonSerializerDefaults.Web);
}
