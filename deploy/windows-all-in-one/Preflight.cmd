@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\Test-ReleaseIntegrity.ps1"
if errorlevel 1 goto :failed
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\Test-DeploymentEnvironment.ps1"
set "exitCode=%ERRORLEVEL%"
echo.
pause
exit /b %exitCode%

:failed
echo.
echo Release integrity check failed. Do not deploy this package.
pause
exit /b 2
