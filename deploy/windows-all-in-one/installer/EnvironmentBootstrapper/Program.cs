using System.Diagnostics;

var script = Path.Combine(AppContext.BaseDirectory, "Enable-HyperV.ps1");
if (!File.Exists(script))
{
    Console.Error.WriteLine($"Hyper-V setup script is missing: {script}");
    return 2;
}

var startInfo = new ProcessStartInfo
{
    FileName = "powershell.exe",
    UseShellExecute = false,
    RedirectStandardOutput = true,
    RedirectStandardError = true,
    CreateNoWindow = true
};
foreach (var argument in new[] { "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", script })
    startInfo.ArgumentList.Add(argument);

using var process = Process.Start(startInfo) ?? throw new InvalidOperationException("Unable to start PowerShell.");
var stdout = process.StandardOutput.ReadToEndAsync();
var stderr = process.StandardError.ReadToEndAsync();
await process.WaitForExitAsync();
Console.Write(await stdout);
Console.Error.Write(await stderr);
return process.ExitCode;
