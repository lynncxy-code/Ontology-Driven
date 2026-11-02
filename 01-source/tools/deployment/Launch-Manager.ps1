[CmdletBinding()]
param([string]$EngineRoot,[string]$EnvironmentPath)
$ErrorActionPreference='Stop'
try {
    if (-not $EngineRoot) {
        foreach ($key in @('HKLM:\SOFTWARE\EpicGames\Unreal Engine\5.6','HKLM:\SOFTWARE\WOW6432Node\EpicGames\Unreal Engine\5.6')) {
            if (Test-Path $key) { $EngineRoot=(Get-ItemProperty $key).InstalledDirectory; if ($EngineRoot) { break } }
        }
    }
    if (-not $EngineRoot) {
        Add-Type -AssemblyName System.Windows.Forms
        $picker=New-Object System.Windows.Forms.FolderBrowserDialog
        $picker.Description='Select Unreal Engine 5.6 installation folder'
        if ($picker.ShowDialog() -ne 'OK') { exit 1 }
        $EngineRoot=$picker.SelectedPath
    }
    $python=Join-Path $EngineRoot 'Engine\Binaries\ThirdParty\Python3\Win64\pythonw.exe'
    if (-not (Test-Path -LiteralPath $python)) { throw 'UE bundled Python was not found. Select the UE 5.6 installation folder.' }
    $script=Join-Path $PSScriptRoot 'gui.py'
    $arguments=@(('"'+$script+'"'))
    if ($EnvironmentPath) { $arguments+=@('--home',('"'+$EnvironmentPath+'"')) }
    Start-Process -FilePath $python -ArgumentList $arguments -WindowStyle Hidden
} catch {
    Add-Type -AssemblyName System.Windows.Forms
    [System.Windows.Forms.MessageBox]::Show($_.Exception.Message,'OntoTwin Deployment Manager') | Out-Null
    exit 1
}
