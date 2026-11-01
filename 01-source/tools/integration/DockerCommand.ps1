# Native stderr is data, not a PowerShell error record (Windows PowerShell 5.1).
function Invoke-OntoTwinDocker {
    param([string[]]$Arguments, [int]$TimeoutSeconds=120)
    $dockerCommand=Get-Command docker -CommandType Application -ErrorAction Stop | Select-Object -First 1
    $info=New-Object System.Diagnostics.ProcessStartInfo
    $info.FileName=$dockerCommand.Source
    $quoted=@($Arguments | ForEach-Object {
        '"'+[regex]::Replace([regex]::Replace($_, '(\\*)"', '$1$1\"'), '(\\+)$', '$1$1')+'"'
    })
    $info.Arguments=$quoted -join ' '
    $info.UseShellExecute=$false
    $info.CreateNoWindow=$true
    $info.RedirectStandardOutput=$true
    $info.RedirectStandardError=$true
    # Compose must use this package's .env, not an unrelated terminal's variables.
    if ($Arguments[0] -eq 'compose') {
        foreach ($key in @('INSTANCE_ID','PORT','DB_PASSWORD','BACKEND_IMAGE','DB_IMAGE','NEO4J_IMAGE','RELEASE_ID','COMPOSE_FILE','COMPOSE_PROJECT_NAME')) { $info.EnvironmentVariables.Remove($key) }
    }
    $process=New-Object System.Diagnostics.Process
    $process.StartInfo=$info
    try {
        [void]$process.Start()
        $stdout=$process.StandardOutput.ReadToEndAsync()
        $stderr=$process.StandardError.ReadToEndAsync()
        if (-not $process.WaitForExit($TimeoutSeconds*1000)) {
            $process.Kill()
            throw "Docker command timed out ($TimeoutSeconds seconds): $($Arguments[0]). Check Docker Desktop; do not reset or delete data."
        }
        [pscustomobject]@{ExitCode=$process.ExitCode;Output=$stdout.Result.Trim();Error=$stderr.Result.Trim()}
    } finally { $process.Dispose() }
}

function Run-Docker {
    param([string[]]$Arguments,[int]$TimeoutSeconds=120)
    $result=Invoke-OntoTwinDocker -Arguments $Arguments -TimeoutSeconds $TimeoutSeconds
    if ($result.ExitCode -ne 0) { throw "Docker $($Arguments[0]) failed ($($result.ExitCode)): $($result.Error)" }
    $result.Output
}
