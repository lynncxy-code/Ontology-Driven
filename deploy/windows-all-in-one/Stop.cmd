@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\Stop-OntoTwinZHHZ.ps1"
if errorlevel 1 pause
