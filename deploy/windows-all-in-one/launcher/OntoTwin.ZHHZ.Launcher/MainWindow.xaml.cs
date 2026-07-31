using System.Diagnostics;
using System.IO;
using System.Net.Sockets;
using System.Text;
using System.Text.Json;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using Microsoft.Win32;

namespace OntoTwin.ZHHZ.Launcher;

public partial class MainWindow : Window
{
    private const int ControlPort = 48073;
    private static readonly SolidColorBrush Blue = Brush("#0066CC");
    private static readonly SolidColorBrush Green = Brush("#00A383");
    private static readonly SolidColorBrush Amber = Brush("#D97706");
    private static readonly SolidColorBrush Red = Brush("#DC2626");
    private static readonly SolidColorBrush Muted = Brush("#94A3B8");

    private readonly Button[] _operationButtons;
    private readonly Border[] _steps;
    private readonly string _installRoot;
    private readonly string _diagnosticLogPath;
    private bool _busy;
    private bool _darkTheme;

    public MainWindow()
    {
        InitializeComponent();
        _operationButtons = [StartButton, StopButton, ConsoleButton, BackupButton, RefreshButton];
        _steps = [Step1, Step2, Step3, Step4, Step5];
        _installRoot = ResolveInstallRoot();

        var logDirectory = Path.Combine(ResolveDataRoot(), "Logs");
        try
        {
            Directory.CreateDirectory(logDirectory);
        }
        catch
        {
            logDirectory = Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                "OntoTwin-ZHHZ",
                "Logs");
            Directory.CreateDirectory(logDirectory);
        }
        _diagnosticLogPath = Path.Combine(logDirectory, "launcher.log");
        Loaded += async (_, _) => await RefreshStatusAsync();
    }

    private async void StartButton_Click(object sender, RoutedEventArgs e) => await StartSystemAsync();
    private async void StopButton_Click(object sender, RoutedEventArgs e) => await StopSystemAsync();
    private async void BackupButton_Click(object sender, RoutedEventArgs e) => await RunServiceOperationAsync("backup", "备份数据");
    private async void RefreshButton_Click(object sender, RoutedEventArgs e) => await RefreshStatusAsync();
    private void ConsoleButton_Click(object sender, RoutedEventArgs e) => OpenConsole();

    private void ThemeButton_Click(object sender, RoutedEventArgs e)
    {
        _darkTheme = !_darkTheme;
        SetResource("PageBackgroundBrush", _darkTheme ? "#000000" : "#EFF6FF");
        SetResource("SurfaceBrush", _darkTheme ? "#0F1E3C" : "#FFFFFF");
        SetResource("SurfaceSecondaryBrush", _darkTheme ? "#1E293B" : "#F8FAFC");
        SetResource("TextPrimaryBrush", _darkTheme ? "#F8FAFC" : "#0F172A");
        SetResource("TextSecondaryBrush", _darkTheme ? "#94A3B8" : "#64748B");
        SetResource("BorderBrush", _darkTheme ? "#243A59" : "#D7E3F1");
        ThemeButton.Content = _darkTheme ? "切换浅色模式" : "切换深色模式";
    }

    private static void SetResource(string key, string color) =>
        CurrentApp.Resources[key] = Brush(color);

    private static Application CurrentApp => Application.Current;

    private static SolidColorBrush Brush(string color)
    {
        var value = (Color)ColorConverter.ConvertFromString(color);
        var brush = new SolidColorBrush(value);
        brush.Freeze();
        return brush;
    }

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
        SetSteps(1);
        var response = await RunServiceOperationAsync("start", "启动后台", refreshAfter: false);
        if (response is null || !response.Ok)
        {
            await RefreshStatusAsync();
            return;
        }

        try
        {
            SetSteps(3);
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
            else
            {
                existing.ForEach(process => process.Dispose());
                AppendLog("ZHHZ 已经在运行。");
            }
            SetSteps(4);
            OpenConsole();
            SetSteps(5);
        }
        catch (Exception exception)
        {
            WriteDiagnostic(exception);
            AppendLog("ZHHZ 启动失败：" + exception.Message);
            MessageBox.Show(this, exception.Message, "ZHHZ 启动失败", MessageBoxButton.OK, MessageBoxImage.Error);
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
        SetBusy(true, $"正在{title}…");
        AppendLog($"> {title}");
        try
        {
            var response = action.Equals("start", StringComparison.OrdinalIgnoreCase)
                ? await SendStartRequestWithProgressAsync()
                : await SendRequestAsync(action, TimeSpan.FromMinutes(15));
            AppendLog(response.Message);
            AppendLog(response.Output);
            if (!response.Ok)
                MessageBox.Show(this, response.Message, "操作失败", MessageBoxButton.OK, MessageBoxImage.Error);
            return response;
        }
        catch (Exception exception)
        {
            WriteDiagnostic(exception);
            AppendLog("后台服务连接失败：" + exception.Message);
            SetStatus("后台服务不可用", "无法连接后台管理服务", "请重试；若仍失败，请将诊断日志交给技术支持。", StatusKind.Error);
            MessageBox.Show(this,
                $"OntoTwin 后台管理服务暂时不可用。控制中心已尝试自动重连。若仍失败，请把诊断日志交给技术支持：\n{_diagnosticLogPath}\n\n{exception.Message}",
                "后台服务不可用", MessageBoxButton.OK, MessageBoxImage.Error);
            return null;
        }
        finally
        {
            SetBusy(false, StatusLabel.Text);
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
                    SetStatus("启动中", progress, $"已等待 {elapsed.Minutes:D2}:{elapsed.Seconds:D2}，请保持窗口开启。", StatusKind.Warning);
                    SetSteps(2);
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
        SetBusy(true, "正在检查系统状态…");
        try
        {
            var response = await SendRequestAsync("status", TimeSpan.FromSeconds(20));
            var runtimeRunning = FindRuntimeProcesses();
            var hasRuntime = runtimeRunning.Count > 0;
            runtimeRunning.ForEach(process => process.Dispose());

            BackendDot.Fill = response.BackendReady ? Green : response.VmState == "Running" ? Amber : Muted;
            BackendStatusText.Text = response.BackendReady ? "已就绪" : response.VmState == "Running" ? "准备中" : "未启动";
            RuntimeDot.Fill = hasRuntime ? Green : Muted;
            RuntimeStatusText.Text = hasRuntime ? "运行中" : "未运行";

            if (response.BackendReady && hasRuntime)
            {
                SetStatus("运行正常", "系统已就绪", "ZHHZ 与 OntoTwin 后台均在运行。", StatusKind.Success);
                SetSteps(5);
            }
            else if (response.BackendReady)
            {
                SetStatus("待启动", "后台已就绪，ZHHZ 未运行", "点击“启动系统”继续。", StatusKind.Warning);
                SetSteps(3);
            }
            else if (response.VmState == "Running")
            {
                SetStatus("准备中", "后台设备正在准备", "首次初始化需要较长时间，请耐心等待。", StatusKind.Warning);
                SetSteps(2);
            }
            else
            {
                SetStatus("未启动", "系统尚未启动", "点击“启动系统”，控制中心会自动完成全部步骤。", StatusKind.Neutral);
                SetSteps(1);
            }
        }
        catch (Exception exception)
        {
            AppendLog(exception.Message);
            BackendDot.Fill = Red;
            BackendStatusText.Text = "不可用";
            RuntimeDot.Fill = Muted;
            RuntimeStatusText.Text = "未知";
            SetStatus("需要处理", "后台管理服务不可用", "请稍后重试；若持续失败，请联系技术支持。", StatusKind.Error);
            SetSteps(0);
        }
        finally { SetBusy(false, StatusLabel.Text); }
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

    private static void OpenConsole() =>
        Process.Start(new ProcessStartInfo("http://127.0.0.1:5000/nexus") { UseShellExecute = true });

    private string ResolveRuntimePath() =>
        Path.Combine(ResolveAppRoot(_installRoot), "ZHHZ", "ZHHZ.exe");

    private void SetBusy(bool busy, string status)
    {
        _busy = busy;
        if (!string.IsNullOrWhiteSpace(status)) StatusLabel.Text = status;
        foreach (var button in _operationButtons) button.IsEnabled = !busy;
        Cursor = busy ? System.Windows.Input.Cursors.Wait : null;
    }

    private void SetStatus(string badge, string title, string detail, StatusKind kind)
    {
        StatusBadgeText.Text = badge;
        StatusLabel.Text = title;
        StatusDetailText.Text = detail;
        var (dot, background, foreground) = kind switch
        {
            StatusKind.Success => (Green, Brush("#E5F7F3"), Brush("#007A63")),
            StatusKind.Warning => (Amber, Brush("#FFF4E5"), Brush("#9A5705")),
            StatusKind.Error => (Red, Brush("#FDECEC"), Brush("#B91C1C")),
            StatusKind.Info => (Blue, Brush("#E8F3FF"), Brush("#0058B0")),
            _ => (Muted, Brush("#F1F5F9"), Brush("#475569"))
        };
        StatusDot.Fill = dot;
        StatusBadge.Background = background;
        StatusBadgeText.Foreground = foreground;
    }

    private void SetSteps(int completed)
    {
        for (var index = 0; index < _steps.Length; index++)
            _steps[index].Background = index < completed ? (index == completed - 1 ? Blue : Green) : Muted;
    }

    private void AppendLog(string? message)
    {
        if (string.IsNullOrWhiteSpace(message)) return;
        var line = $"[{DateTime.Now:HH:mm:ss}] {message.TrimEnd()}";
        LogBox.AppendText(line + Environment.NewLine);
        LogBox.ScrollToEnd();
        try { File.AppendAllText(_diagnosticLogPath, line + Environment.NewLine, new UTF8Encoding(false)); }
        catch { }
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

    private enum StatusKind { Neutral, Info, Success, Warning, Error }
}

internal sealed record ControlRequest(string Action);
internal sealed record ControlResponse(bool Ok, string Message, string Output, bool BackendReady, string VmState, string? BackupPath);

internal static class JsonOptions
{
    public static readonly JsonSerializerOptions Default = new(JsonSerializerDefaults.Web);
}
