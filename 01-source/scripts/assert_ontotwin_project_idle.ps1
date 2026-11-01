function Assert-OntoTwinProjectIdle([string]$ProjectFile) {
    $projectRoot=(Split-Path -Parent $ProjectFile).TrimEnd('\','/')+'\'
    $rootKey=$projectRoot.Replace('/','\')
    foreach ($editor in @(Get-CimInstance Win32_Process -Filter "Name='UnrealEditor.exe' OR Name='UnrealEditor-Cmd.exe'")) {
        if (-not $editor.CommandLine) { throw "无法识别 UE 进程 $($editor.ProcessId) 使用的工程，请关闭该编辑器后安装。" }
        $command=$editor.CommandLine.Replace('/','\')
        if ($command.IndexOf($rootKey,[StringComparison]::OrdinalIgnoreCase) -ge 0) { throw "目标工程正在运行，请关闭该工程后安装：$ProjectFile" }
        # A different project may still have loaded a DLL via a directory junction.
        $process=Get-Process -Id $editor.ProcessId -ErrorAction SilentlyContinue
        if ($process) {
            foreach ($module in $process.Modules) {
                if ($module.FileName.Replace('/','\').StartsWith($rootKey,[StringComparison]::OrdinalIgnoreCase)) {
                    throw "UE 进程 $($editor.ProcessId) 正在使用目标工程文件，请关闭该编辑器后安装。"
                }
            }
        }
    }
}
