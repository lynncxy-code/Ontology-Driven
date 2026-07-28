using System.Diagnostics;
using System.Drawing;
using System.Net.Sockets;
using System.Text;
using System.Text.Json;
using Microsoft.Win32;

namespace OntoTwin.ZHHZ.Launcher;

internal static class Program
{
    [STAThread]
    private static void Main()
    {
        Application.EnableVisualStyles();
        Application.SetCompatibleTextRenderingDefault(false);
        Application.Run(new LauncherForm());
    }
}

internal sealed class LauncherForm : Form
{
    private const int ControlPort = 48073;
    private readonly Label _statusLabel;
    private readonly TextBox _logBox;
    private readonly Button[] _operationButtons;
    private readonly string _installRoot;
    private readonly string _diagnosticLogPath;
    private bool _busy;

    public LauncherForm()
    {
        Text = "OntoTwin ZHHZ 控制中心";
        StartPosition = FormStartPosition.CenterScreen;
        MinimumSize = new Size(780, 520);
        Size = new Size(920, 640);
        Font = new Font("Microsoft YaHei UI", 10F, FontStyle.Regular, GraphicsUnit.Point);
        BackColor = Color.FromArgb(245, 247, 250);

        _installRoot = ResolveInstallRoot();
        var dataRoot = ResolveDataRoot();
        var logDirectory = Path.Combine(dataRoot, "Logs");
        try
        {
            Directory.CreateDirectory(logDirectory);
        }
        catch
        {
            // Keep the control center usable so it can show the service error
            // even when the configured data volume is temporarily unavailable.
            logDirectory = Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                "OntoTwin-ZHHZ",
                "Logs");
            Directory.CreateDirectory(logDirectory);
        }
        _diagnosticLogPath = Path.Combine(logDirectory, "launcher.log");

        var title = new Label
        {
            Text = "OntoTwin · ZHHZ",
            AutoSize = true,
            Font = new Font(Font.FontFamily, 22F, FontStyle.Bold),
            ForeColor = Color.FromArgb(24, 32, 47),
            Location = new Point(28, 24)
        };
        var subtitle = new Label
        {
            Text = "一体化客户版 · 无需 WSL 或 Docker Desktop · 实时 WebSocket 已关闭",
            AutoSize = true,
            ForeColor = Color.FromArgb(91, 101, 119),
            Location = new Point(31, 68)
        };
        _statusLabel = new Label
        {
            Text = "状态：正在检查…",
            AutoSize = true,
            Font = new Font(Font.FontFamily, 11F, FontStyle.Bold),
            ForeColor = Color.FromArgb(130, 85, 0),
            Location = new Point(31, 105)
        };

        var startButton = CreateButton("启动系统", 31, Color.FromArgb(20, 122, 78));
        var stopButton = CreateButton("停止系统", 177, Color.FromArgb(176, 50, 50));
        var consoleButton = CreateButton("打开控制台", 323, Color.FromArgb(42, 91, 160));
        var backupButton = CreateButton("立即备份", 469, Color.FromArgb(103, 75, 155));
        var refreshButton = CreateButton("刷新状态", 615, Color.FromArgb(80, 91, 108));
        _operationButtons = [startButton, stopButton, consoleButton, backupButton, refreshButton];

        startButton.Click += async (_, _) => await StartSystemAsync();
        stopButton.Click += async (_, _) => await StopSystemAsync();
        consoleButton.Click += (_, _) => OpenConsole();
        backupButton.Click += async (_, _) => await RunServiceOperationAsync("backup", "备份数据");
        refreshButton.Click += async (_, _) => await RefreshStatusAsync();

        _logBox = new TextBox
        {
            Multiline = true,
            ReadOnly = true,
            ScrollBars = ScrollBars.Both,
            WordWrap = false,
            BackColor = Color.FromArgb(22, 29, 39),
            ForeColor = Color.FromArgb(215, 223, 235),
            BorderStyle = BorderStyle.FixedSingle,
            Font = new Font("Consolas", 9.5F),
            Location = new Point(31, 176),
            Anchor = AnchorStyles.Top | AnchorStyles.Bottom | AnchorStyles.Left | AnchorStyles.Right,
            Size = new Size(840, 385)
        };

        Controls.AddRange([
            title, subtitle, _statusLabel,
            startButton, stopButton, consoleButton, backupButton, refreshButton,
            _logBox
        ]);
        Shown += async (_, _) => await RefreshStatusAsync();
    }

    private Button CreateButton(string text, int left, Color color) => new()
    {
        Text = text,
        Location = new Point(left, 132),
        Size = new Size(128, 34),
        FlatStyle = FlatStyle.Flat,
        BackColor = color,
        ForeColor = Color.White,
        Cursor = Cursors.Hand,
        UseVisualStyleBackColor = false
    };

    private static string ResolveInstallRoot()
    {
        var launcherDirectory = new DirectoryInfo(AppContext.BaseDirectory.TrimEnd(Path.DirectorySeparatorChar));
        return launcherDirectory.Parent?.FullName ?? launcherDirectory.FullName;
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

    private async Task StartSystemAsync()
    {
        var response = await RunServiceOperationAsync("start", "启动后台", refreshAfter: false);
        if (response is null || !response.Ok) { await RefreshStatusAsync(); return; }
        try
        {
            var runtimePath = ResolveRuntimePath();
            if (!File.Exists(runtimePath)) throw new FileNotFoundException("ZHHZ 程序文件缺失。", runtimePath);
            var existing = FindRuntimeProcesses();
            if (existing.Count == 0)
            {
                var startInfo = new ProcessStartInfo
                {
                    FileName = runtimePath,
                    WorkingDirectory = Path.GetDirectoryName(runtimePath)!,
                    UseShellExecute = true
                };
                startInfo.ArgumentList.Add("-OntoTwinBackendBaseUrl=http://127.0.0.1:5000");
                startInfo.ArgumentList.Add("-OntoTwinRealtimeWebSocket=false");
                startInfo.ArgumentList.Add("-OntoTwinPollInterval=2.0");
                Process.Start(startInfo);
                AppendLog("ZHHZ 已启动。");
            }
            else AppendLog("ZHHZ 已经在运行。");
            OpenConsole();
        }
        catch (Exception exception)
        {
            WriteDiagnostic(exception);
            AppendLog("ZHHZ 启动失败：" + exception.Message);
            MessageBox.Show(this, exception.Message, "ZHHZ 启动失败", MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
        await RefreshStatusAsync();
    }

    private async Task StopSystemAsync()
    {
        foreach (var process in FindRuntimeProcesses())
        {
            try
            {
                if (process.MainWindowHandle != IntPtr.Zero) process.CloseMainWindow();
                if (!process.WaitForExit(10_000)) process.Kill(entireProcessTree: true);
            }
            catch (Exception exception) { AppendLog(exception.Message); }
            finally { process.Dispose(); }
        }
        await RunServiceOperationAsync("stop", "停止后台");
    }

    private List<Process> FindRuntimeProcesses()
    {
        var results = new List<Process>();
        var runtimeDirectory = Path.GetDirectoryName(ResolveRuntimePath())! + Path.DirectorySeparatorChar;
        foreach (var process in Process.GetProcesses())
        {
            try
            {
                var path = process.MainModule?.FileName;
                if (path is not null && path.StartsWith(runtimeDirectory, StringComparison.OrdinalIgnoreCase)) results.Add(process);
                else process.Dispose();
            }
            catch { process.Dispose(); }
        }
        return results;
    }

    private async Task<ControlResponse?> RunServiceOperationAsync(string action, string title, bool refreshAfter = true)
    {
        if (_busy) return null;
        SetBusy(true, $"状态：正在{title}…");
        AppendLog($"> {title}");
        try
        {
            var response = action.Equals("start", StringComparison.OrdinalIgnoreCase)
                ? await SendStartRequestWithProgressAsync()
                : await SendRequestAsync(action, TimeSpan.FromMinutes(15));
            AppendLog(response.Message);
            AppendLog(response.Output);
            if (!response.Ok)
                MessageBox.Show(this, response.Message, "操作失败", MessageBoxButtons.OK, MessageBoxIcon.Error);
            return response;
        }
        catch (Exception exception)
        {
            WriteDiagnostic(exception);
            AppendLog("后台服务连接失败：" + exception.Message);
            MessageBox.Show(this,
                $"OntoTwin 后台管理服务暂时不可用。控制中心已尝试自动重连。若仍失败，请把诊断日志交给技术支持：\n{_diagnosticLogPath}\n\n{exception.Message}",
                "后台服务不可用", MessageBoxButtons.OK, MessageBoxIcon.Error);
            return null;
        }
        finally
        {
            SetBusy(false, "状态：检查中…");
            if (refreshAfter) await RefreshStatusAsync();
        }
    }

    private async Task<ControlResponse> SendStartRequestWithProgressAsync()
    {
        const int maximumAttempts = 3;
        var startedAt = DateTime.Now;
        for (var attempt = 1; attempt <= maximumAttempts; attempt++)
        {
            try
            {
                // Provisioning can include a system-disk refresh (about 2 GB),
                // a 10-minute guest bootstrap window and a final health check.
                // Keep the UI request above that bounded server-side maximum.
                var operation = SendRequestAsync("start", TimeSpan.FromMinutes(20));
                while (true)
                {
                    var completed = await Task.WhenAny(operation, Task.Delay(TimeSpan.FromSeconds(15)));
                    if (completed == operation) return await operation;

                    var elapsed = DateTime.Now - startedAt;
                    var progress = "后台首次初始化中";
                    try
                    {
                        var status = await SendRequestAsync("status", TimeSpan.FromSeconds(10));
                        progress = ExtractBootstrapProgress(status.Output) ?? progress;
                    }
                    catch { }
                    _statusLabel.Text = $"状态：{progress}（{elapsed.Minutes:D2}:{elapsed.Seconds:D2}）";
                    AppendLog($"{progress}，已等待 {elapsed.Minutes:D2}:{elapsed.Seconds:D2}");
                }
            }
            catch (Exception exception) when (IsTransientConnectionFailure(exception) && attempt < maximumAttempts)
            {
                WriteDiagnostic(exception);
                AppendLog($"后台管理服务连接中断，正在自动重连（{attempt}/{maximumAttempts - 1}）。");
                await WaitForServiceAsync(TimeSpan.FromSeconds(45));
                try
                {
                    var status = await SendRequestAsync("status", TimeSpan.FromSeconds(10));
                    if (status.BackendReady)
                        return status with { Ok = true, Message = "后台已就绪（连接已自动恢复）" };
                }
                catch { }
            }
        }
        throw new IOException("后台管理服务连续中断，自动重连未成功。");
    }

    private static bool IsTransientConnectionFailure(Exception exception) =>
        exception is IOException or SocketException or TimeoutException or OperationCanceledException ||
        exception.InnerException is SocketException;

    private static async Task WaitForServiceAsync(TimeSpan timeout)
    {
        var deadline = DateTime.UtcNow + timeout;
        while (DateTime.UtcNow < deadline)
        {
            try
            {
                _ = await SendRequestAsync("status", TimeSpan.FromSeconds(5));
                return;
            }
            catch { await Task.Delay(TimeSpan.FromSeconds(2)); }
        }
    }

    private static string? ExtractBootstrapProgress(string? output)
    {
        if (string.IsNullOrWhiteSpace(output)) return null;
        const string prefix = "BootstrapProgress:";
        return output.Split(new[] { "\r\n", "\n" }, StringSplitOptions.RemoveEmptyEntries)
            .Reverse()
            .FirstOrDefault(line => line.TrimStart().StartsWith(prefix, StringComparison.OrdinalIgnoreCase))?
            .Trim()[prefix.Length..].Trim();
    }

    private async Task RefreshStatusAsync()
    {
        if (_busy) return;
        SetBusy(true, "状态：正在检查…");
        try
        {
            var response = await SendRequestAsync("status", TimeSpan.FromSeconds(20));
            var runtimeRunning = FindRuntimeProcesses();
            var hasRuntime = runtimeRunning.Count > 0;
            runtimeRunning.ForEach(process => process.Dispose());
            if (response.BackendReady && hasRuntime)
            {
                _statusLabel.Text = "状态：系统运行正常";
                _statusLabel.ForeColor = Color.FromArgb(20, 122, 78);
            }
            else if (response.BackendReady)
            {
                _statusLabel.Text = "状态：后台已就绪，ZHHZ 未运行";
                _statusLabel.ForeColor = Color.FromArgb(130, 85, 0);
            }
            else
            {
                _statusLabel.Text = response.VmState == "Running" ? "状态：后台正在准备" : "状态：系统未启动";
                _statusLabel.ForeColor = Color.FromArgb(91, 101, 119);
            }
        }
        catch (Exception exception)
        {
            AppendLog(exception.Message);
            _statusLabel.Text = "状态：后台管理服务不可用";
            _statusLabel.ForeColor = Color.FromArgb(176, 50, 50);
        }
        finally { SetBusy(false, _statusLabel.Text); }
    }

    private static async Task<ControlResponse> SendRequestAsync(string action, TimeSpan timeout)
    {
        using var cancellation = new CancellationTokenSource(timeout);
        using var client = new TcpClient();
        await client.ConnectAsync("127.0.0.1", ControlPort, cancellation.Token);
        await using var stream = client.GetStream();
        await using var writer = new StreamWriter(stream, new UTF8Encoding(false), 4096, leaveOpen: true) { AutoFlush = true };
        using var reader = new StreamReader(stream, new UTF8Encoding(false), false, 4096, leaveOpen: true);
        await writer.WriteLineAsync(JsonSerializer.Serialize(new ControlRequest(action), JsonOptions.Default));
        var line = await reader.ReadLineAsync(cancellation.Token);
        return JsonSerializer.Deserialize<ControlResponse>(line ?? "", JsonOptions.Default)
            ?? throw new InvalidDataException("后台服务返回了无效响应。");
    }

    private static void OpenConsole()
    {
        Process.Start(new ProcessStartInfo("http://127.0.0.1:5000/nexus") { UseShellExecute = true });
    }

    private string ResolveRuntimePath() =>
        Path.Combine(ResolveAppRoot(_installRoot), "ZHHZ", "ZHHZ.exe");

    private void SetBusy(bool busy, string status)
    {
        _busy = busy;
        _statusLabel.Text = status;
        foreach (var button in _operationButtons) button.Enabled = !busy;
        UseWaitCursor = busy;
    }

    private void AppendLog(string? message)
    {
        if (!string.IsNullOrWhiteSpace(message))
        {
            var line = $"[{DateTime.Now:HH:mm:ss}] {message.TrimEnd()}";
            _logBox.AppendText(line + Environment.NewLine);
            try { File.AppendAllText(_diagnosticLogPath, line + Environment.NewLine, new UTF8Encoding(false)); }
            catch { }
        }
    }

    private void WriteDiagnostic(Exception exception)
    {
        try
        {
            File.AppendAllText(_diagnosticLogPath,
                $"[{DateTime.Now:O}] {exception}{Environment.NewLine}", new UTF8Encoding(false));
        }
        catch { }
    }
}

internal sealed record ControlRequest(string Action);
internal sealed record ControlResponse(bool Ok, string Message, string Output, bool BackendReady, string VmState, string? BackupPath);

internal static class JsonOptions
{
    public static readonly JsonSerializerOptions Default = new(JsonSerializerDefaults.Web);
}
