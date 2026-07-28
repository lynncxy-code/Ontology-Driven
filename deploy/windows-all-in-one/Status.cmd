@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\Get-OntoTwinZHHZStatus.ps1"
pause
