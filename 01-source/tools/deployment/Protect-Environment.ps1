param([Parameter(Mandatory=$true)][string]$EnvironmentPath)
$ErrorActionPreference='Stop'
$target=(Resolve-Path -LiteralPath $EnvironmentPath).Path
$acl=New-Object System.Security.AccessControl.DirectorySecurity
$acl.SetAccessRuleProtection($true,$false)
$owner=[System.Security.Principal.WindowsIdentity]::GetCurrent().User
foreach ($identity in @($owner,(New-Object System.Security.Principal.SecurityIdentifier('S-1-5-18')))) {
    $rule=New-Object System.Security.AccessControl.FileSystemAccessRule($identity,'FullControl','ContainerInherit,ObjectInherit','None','Allow')
    $acl.AddAccessRule($rule)
}
[System.IO.Directory]::SetAccessControl($target,$acl)
