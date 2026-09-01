using System.IO;
using System.Text;
using System.Windows;
using System.Windows.Threading;
using Microsoft.Win32;

namespace OntoTwin.ZHHZ.Launcher;

public partial class App : Application
{
    internal static string DiagnosticLogPath { get; } = ResolveDiagnosticLogPath();

    public App()
    {
        DispatcherUnhandledException += OnDispatcherUnhandledException;
        AppDomain.CurrentDomain.UnhandledException += OnUnhandledException;
        TaskScheduler.UnobservedTaskException += OnUnobservedTaskException;
        Log($"Launcher process starting. Version={typeof(App).Assembly.GetName().Version}");
    }

    protected override void OnStartup(StartupEventArgs e)
    {
        try
        {
            base.OnStartup(e);
            var window = new MainWindow();
            MainWindow = window;
            window.Show();
            Log("Launcher main window shown.");
        }
        catch (Exception exception)
        {
            Log("Launcher startup failed.", exception);
            MessageBox.Show(
                $"灵云智启动失败。诊断日志：\n{DiagnosticLogPath}\n\n{exception.Message}",
                "灵云智 · 启动失败",
                MessageBoxButton.OK,
                MessageBoxImage.Error);
            Shutdown(1);
        }
    }

    internal static void Log(string message, Exception? exception = null)
    {
        try
        {
            var line = $"[{DateTimeOffset.Now:O}] {message}";
            if (exception is not null) line += Environment.NewLine + exception;
            File.AppendAllText(DiagnosticLogPath, line + Environment.NewLine, new UTF8Encoding(false));
        }
        catch
        {
            // Diagnostics must never prevent the launcher from opening.
        }
    }

    private void OnDispatcherUnhandledException(object sender, DispatcherUnhandledExceptionEventArgs e)
    {
        Log("Unhandled dispatcher exception.", e.Exception);
    }

    private static void OnUnhandledException(object? sender, UnhandledExceptionEventArgs e)
    {
        Log("Unhandled application-domain exception.", e.ExceptionObject as Exception);
    }

    private static void OnUnobservedTaskException(object? sender, UnobservedTaskExceptionEventArgs e)
    {
        Log("Unobserved task exception.", e.Exception);
    }

    private static string ResolveDiagnosticLogPath()
    {
        var candidates = new List<string>();
        try
        {
            using var key = Registry.LocalMachine.OpenSubKey(@"SOFTWARE\OntoTwin\ZHHZ");
            var configured = key?.GetValue("DataRoot") as string;
            if (!string.IsNullOrWhiteSpace(configured) && Path.IsPathFullyQualified(configured))
                candidates.Add(Path.Combine(configured, "Logs"));
        }
        catch
        {
            // Registry diagnostics must not prevent per-user logging.
        }
        candidates.Add(Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.CommonApplicationData), "OntoTwin-ZHHZ", "Logs"));
        candidates.Add(Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "OntoTwin-ZHHZ", "Logs"));

        foreach (var directory in candidates)
        {
            try
            {
                Directory.CreateDirectory(directory);
                var path = Path.Combine(directory, "launcher.log");
                using var stream = new FileStream(path, FileMode.OpenOrCreate, FileAccess.Write, FileShare.ReadWrite);
                stream.Seek(0, SeekOrigin.End);
                return path;
            }
            catch
            {
                // Try the next per-machine/per-user location.
            }
        }
        return Path.Combine(AppContext.BaseDirectory, "launcher.log");
    }
}
