param([Parameter(Mandatory=$true)][string]$ProjectsJson)
$ErrorActionPreference='Stop'
$projects=@($ProjectsJson | ConvertFrom-Json)
foreach ($editor in @(Get-CimInstance Win32_Process -Filter "Name='UnrealEditor.exe' OR Name='UnrealEditor-Cmd.exe'")) {
    if (-not $editor.CommandLine) { throw 'Cannot identify running UE project. Close UE before updating.' }
    $command=$editor.CommandLine.Replace('/','\')
    $process=Get-Process -Id $editor.ProcessId -ErrorAction Stop
    $modules=@($process.Modules | ForEach-Object {$_.FileName.Replace('/','\')})
    foreach ($project in $projects) {
        $root=(Split-Path -Parent $project).TrimEnd('\','/')+'\'
        if ($command.IndexOf($root,[StringComparison]::OrdinalIgnoreCase) -ge 0) { throw "Close UE project before updating: $project" }
        foreach ($module in $modules) {
            if ($module.StartsWith($root,[StringComparison]::OrdinalIgnoreCase)) { throw "UE is using project files: $project" }
        }
    }
}
