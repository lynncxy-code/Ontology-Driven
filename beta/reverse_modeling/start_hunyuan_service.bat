@echo off
setlocal

rem One-click launcher for the local Hunyuan3D-2mv service used by this Beta.
set "HUNYUAN_ROOT=D:\AI\Hunyuan3D-2.1-local"
set "HUNYUAN_START=%HUNYUAN_ROOT%\start_hunyuan3d_multiview.bat"

if not exist "%HUNYUAN_START%" (
  echo [ERROR] Hunyuan3D multi-view launcher was not found:
  echo %HUNYUAN_START%
  echo.
  pause
  exit /b 1
)

echo OntoTwin Nexus Reverse Modeling Beta
echo Starting Hunyuan3D-2mv at http://127.0.0.1:8081/
echo Keep this window open while using the Beta page.
echo.

call "%HUNYUAN_START%"

endlocal
