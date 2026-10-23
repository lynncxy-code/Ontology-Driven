[CmdletBinding()]
param(
    [string]$InfrastructureRoot = "D:\tmp\pixel-streaming-infra-UE5.6\PixelStreamingInfrastructure-UE5.6",
    [string]$RuntimeExe = $env:ONTOTWIN_PIXEL_STREAMING_RUNTIME,
    [ValidateRange(1, 65535)]
    [int]$PlayerPort = 8888,
    [ValidateRange(1, 65535)]
    [int]$StreamerPort = 8889,
    [ValidateRange(1, 65535)]
    [int]$SfuPort = 8890,
    [ValidateRange(1, 100)]
    [int]$MaxPlayers = 1,
    [ValidateRange(320, 7680)]
    [int]$Width = 1280,
    [ValidateRange(240, 4320)]
    [int]$Height = 720,
    [switch]$SkipRuntime,
    [switch]$OpenPlayer,
    [switch]$PreflightOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$serverRoot = Join-Path $InfrastructureRoot "SignallingWebServer"
$serverEntry = Join-Path $serverRoot "dist\index.js"
$playerPage = Join-Path $serverRoot "www\player.html"
$stateRoot = Join-Path $env:LOCALAPPDATA "OntoTwin\PixelStreaming"
$stateFile = Join-Path $stateRoot "local-session.json"
$serverLogRoot = Join-Path $stateRoot "server-logs"
$stdoutLog = Join-Path $stateRoot "signalling.stdout.log"
$stderrLog = Join-Path $stateRoot "signalling.stderr.log"
$playerUrl = "http://127.0.0.1:$PlayerPort/"
$streamerUrl = "ws://127.0.0.1:$StreamerPort"

function Assert-PortAvailable {
    param([int]$Port, [string]$Purpose)

    $listener = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if ($listener) {
        throw "$Purpose port $Port is already in use by PID $($listener.OwningProcess)."
    }
}

function Test-TcpReady {
    param([int]$Port)

    $client = [System.Net.Sockets.TcpClient]::new()
    try {
        $pending = $client.BeginConnect("127.0.0.1", $Port, $null, $null)
        if (-not $pending.AsyncWaitHandle.WaitOne(300)) {
            return $false
        }
        $client.EndConnect($pending)
        return $true
    } catch {
        return $false
    } finally {
        $client.Dispose()
    }
}

function Get-UserProxyEnabled {
    try {
        $settings = Get-ItemProperty "HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings"
        return [bool]$settings.ProxyEnable
    } catch {
        return $false
    }
}

function Get-ManagedRuntimeProcesses {
    param([string]$ExePath, [string]$ConnectionUrl)

    $runtimeRoot = Split-Path -Parent $ExePath
    return @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
        $_.ExecutablePath -and
        $_.ExecutablePath.StartsWith($runtimeRoot, [System.StringComparison]::OrdinalIgnoreCase) -and
        $_.CommandLine -like "*-PixelStreamingURL=$ConnectionUrl*"
    })
}

function Start-DetachedRuntime {
    param([string]$ExePath, [string[]]$Arguments)

    if (-not ("OntoTwin.DetachedProcess" -as [type])) {
        Add-Type -TypeDefinition @'
using System;
using System.ComponentModel;
using System.Runtime.InteropServices;
using System.Text;

namespace OntoTwin
{
    public static class DetachedProcess
    {
        [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
        private struct STARTUPINFO
        {
            public int cb;
            public string lpReserved;
            public string lpDesktop;
            public string lpTitle;
            public int dwX;
            public int dwY;
            public int dwXSize;
            public int dwYSize;
            public int dwXCountChars;
            public int dwYCountChars;
            public int dwFillAttribute;
            public int dwFlags;
            public short wShowWindow;
            public short cbReserved2;
            public IntPtr lpReserved2;
            public IntPtr hStdInput;
            public IntPtr hStdOutput;
            public IntPtr hStdError;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct PROCESS_INFORMATION
        {
            public IntPtr hProcess;
            public IntPtr hThread;
            public uint dwProcessId;
            public uint dwThreadId;
        }

        [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
        private static extern bool CreateProcess(
            string lpApplicationName,
            StringBuilder lpCommandLine,
            IntPtr lpProcessAttributes,
            IntPtr lpThreadAttributes,
            bool bInheritHandles,
            uint dwCreationFlags,
            IntPtr lpEnvironment,
            string lpCurrentDirectory,
            ref STARTUPINFO lpStartupInfo,
            out PROCESS_INFORMATION lpProcessInformation);

        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern bool CloseHandle(IntPtr hObject);

        public static uint Start(string exePath, string commandLine, string workingDirectory)
        {
            const uint DETACHED_PROCESS = 0x00000008;
            const uint CREATE_NEW_PROCESS_GROUP = 0x00000200;
            const uint CREATE_UNICODE_ENVIRONMENT = 0x00000400;

            STARTUPINFO startup = new STARTUPINFO();
            startup.cb = Marshal.SizeOf(startup);
            PROCESS_INFORMATION process;
            bool created = CreateProcess(
                exePath,
                new StringBuilder(commandLine),
                IntPtr.Zero,
                IntPtr.Zero,
                false,
                DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP | CREATE_UNICODE_ENVIRONMENT,
                IntPtr.Zero,
                workingDirectory,
                ref startup,
                out process);
            if (!created)
            {
                throw new Win32Exception(Marshal.GetLastWin32Error());
            }

            try
            {
                return process.dwProcessId;
            }
            finally
            {
                CloseHandle(process.hThread);
                CloseHandle(process.hProcess);
            }
        }
    }
}
'@
    }

    $quote = [char]34
    $commandLine = "$quote$ExePath$quote " + ($Arguments -join " ")
    $processId = [OntoTwin.DetachedProcess]::Start(
        $ExePath,
        $commandLine,
        (Split-Path -Parent $ExePath)
    )
    return Get-Process -Id $processId -ErrorAction Stop
}

if (($PlayerPort -eq $StreamerPort) -or
    ($PlayerPort -eq $SfuPort) -or
    ($StreamerPort -eq $SfuPort)) {
    throw "Player, streamer, and SFU ports must be different."
}

$node = Get-Command node -ErrorAction SilentlyContinue
if (-not $node) {
    throw "Node.js is required to run the Pixel Streaming signalling server."
}
if (-not (Test-Path -LiteralPath $serverEntry -PathType Leaf)) {
    throw "Pixel Streaming Infrastructure is not built: $serverEntry"
}
if (-not (Test-Path -LiteralPath $playerPage -PathType Leaf)) {
    throw "Pixel Streaming player page was not found: $playerPage"
}
if ((-not $SkipRuntime) -and [string]::IsNullOrWhiteSpace($RuntimeExe)) {
    throw "RuntimeExe is required. Pass -RuntimeExe '<path-to-packaged-ue.exe>' or set ONTOTWIN_PIXEL_STREAMING_RUNTIME."
}
if ((-not $SkipRuntime) -and (-not (Test-Path -LiteralPath $RuntimeExe -PathType Leaf))) {
    throw "UE runtime was not found: $RuntimeExe"
}

$reuseServer = $false
$existingServer = $null
$existingRuntimeProcesses = @()
if (-not $SkipRuntime) {
    $existingRuntimeProcesses = @(Get-ManagedRuntimeProcesses -ExePath $RuntimeExe -ConnectionUrl $streamerUrl)
}
if (Test-Path -LiteralPath $stateFile -PathType Leaf) {
    try {
        $existingState = Get-Content -Raw -LiteralPath $stateFile | ConvertFrom-Json
        $serverProcess = Get-CimInstance Win32_Process -Filter "ProcessId=$($existingState.server_pid)" -ErrorAction SilentlyContinue
        $samePorts = ([int]$existingState.player_port -eq $PlayerPort) -and
            ([int]$existingState.streamer_port -eq $StreamerPort) -and
            ([int]$existingState.sfu_port -eq $SfuPort)
        if ($serverProcess -and $samePorts -and $serverProcess.CommandLine -match 'dist[/\\]index\.js') {
            $existingServer = Get-Process -Id $existingState.server_pid -ErrorAction Stop
            $reuseServer = $true
        }
    } catch {
        $reuseServer = $false
        $existingServer = $null
    }
}

if (-not $reuseServer) {
    Assert-PortAvailable -Port $PlayerPort -Purpose "Player"
    Assert-PortAvailable -Port $StreamerPort -Purpose "Streamer"
    Assert-PortAvailable -Port $SfuPort -Purpose "SFU"
}

Write-Host "Pixel Streaming local preflight passed." -ForegroundColor Green
Write-Host "Player URL : $playerUrl"
Write-Host "UE URL     : $streamerUrl"
Write-Host "Max players: $MaxPlayers"
Write-Host "Runtime    : $(if ($SkipRuntime) { 'skipped' } else { $RuntimeExe })"
if (Get-UserProxyEnabled) {
    Write-Warning "A Windows user proxy is enabled. Disable VPN/global proxy or bypass localhost before manual acceptance."
}

if ($PreflightOnly) {
    if ($reuseServer) {
        Write-Host "An existing managed signalling server will be reused (PID $($existingServer.Id))."
    }
    Write-Host "Preflight only; no process was started."
    return
}


if ($reuseServer -and ($SkipRuntime -or $existingRuntimeProcesses.Count -gt 0)) {
    Write-Host "Pixel Streaming session is already running." -ForegroundColor Green
    Write-Host "Signalling PID : $($existingServer.Id)"
    if ($existingRuntimeProcesses.Count -gt 0) {
        Write-Host "UE process IDs: $($existingRuntimeProcesses.ProcessId -join ', ')"
    }
    Write-Host "Player URL     : $playerUrl"
    if ($OpenPlayer) {
        Start-Process $playerUrl
    }
    return
}

New-Item -ItemType Directory -Path $stateRoot -Force | Out-Null
New-Item -ItemType Directory -Path $serverLogRoot -Force | Out-Null

$serverArgs = @(
    "dist/index.js",
    "--serve",
    "--console_messages", "verbose",
    "--log_config",
    "--player_port", "$PlayerPort",
    "--streamer_port", "$StreamerPort",
    "--sfu_port", "$SfuPort",
    "--max_players", "$MaxPlayers",
    "--http_root", "www",
    "--homepage", "player.html",
    "--rest_api",
    "--log_folder", "`"$serverLogRoot`""
)

$serverStartedHere = $false
if ($reuseServer) {
    $server = $existingServer
    $ready = $true
    Write-Host "Reusing signalling server (PID $($server.Id))." -ForegroundColor Green
} else {
    $server = Start-Process -FilePath $node.Source `
        -ArgumentList $serverArgs `
        -WorkingDirectory $serverRoot `
        -WindowStyle Hidden `
        -RedirectStandardOutput $stdoutLog `
        -RedirectStandardError $stderrLog `
        -PassThru
    $serverStartedHere = $true

    $ready = $false
    for ($attempt = 0; $attempt -lt 30; $attempt++) {
        if ($server.HasExited) {
            $tail = if (Test-Path -LiteralPath $stderrLog) {
                (Get-Content -LiteralPath $stderrLog -Tail 20) -join [Environment]::NewLine
            } else {
                "No signalling error log was produced."
            }
            throw "Pixel Streaming signalling server exited during startup.`n$tail"
        }
        if (Test-TcpReady -Port $PlayerPort) {
            $ready = $true
            break
        }
        Start-Sleep -Milliseconds 200
    }
}

if (-not $ready) {
    if ($serverStartedHere) {
        Stop-Process -Id $server.Id -Force -ErrorAction SilentlyContinue
    }
    throw "Pixel Streaming player did not listen on port $PlayerPort within 6 seconds."
}

$runtime = $null
try {
    if (-not $SkipRuntime) {
        $runtimeArgs = @(
            "-RenderOffscreen",
            "-ForceRes",
            "-ResX=$Width",
            "-ResY=$Height",
            "-AudioMixer",
            "-PixelStreamingURL=$streamerUrl",
            "-ExecCmds=DisableAllScreenMessages",
            "-log",
            "-httpproxy="
        )
        $runtime = Start-DetachedRuntime -ExePath $RuntimeExe -Arguments $runtimeArgs
    }

    $state = [ordered]@{
        started_at = (Get-Date).ToString("o")
        server_pid = $server.Id
        runtime_pid = if ($runtime) { $runtime.Id } else { $null }
        runtime_exe = $RuntimeExe
        player_url = $playerUrl
        streamer_url = $streamerUrl
        player_port = $PlayerPort
        streamer_port = $StreamerPort
        sfu_port = $SfuPort
        max_players = $MaxPlayers
        stdout_log = $stdoutLog
        stderr_log = $stderrLog
    }
    $state | ConvertTo-Json | Set-Content -LiteralPath $stateFile -Encoding UTF8
} catch {
    if ($serverStartedHere) {
        Stop-Process -Id $server.Id -Force -ErrorAction SilentlyContinue
    }
    throw
}

if ($serverStartedHere) {
    Write-Host "Pixel Streaming signalling server started (PID $($server.Id))." -ForegroundColor Green
}
if ($runtime) {
    Write-Host "UE runtime started as a detached process (launcher PID $($runtime.Id))." -ForegroundColor Green
}
Write-Host "Player URL : $playerUrl"
Write-Host "State file : $stateFile"
Write-Host "Status     : .\scripts\pixel_streaming\Get-LocalPixelStreamingStatus.ps1"
Write-Host "Stop       : .\scripts\pixel_streaming\Stop-LocalPixelStreaming.ps1"

if ($OpenPlayer) {
    Start-Process $playerUrl
}
