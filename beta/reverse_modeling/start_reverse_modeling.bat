@echo off
setlocal

set "BETA_DIR=%~dp0"
set "HUNYUAN_PYTHON=D:\AI\Hunyuan3D-2.1-local\.venv\Scripts\python.exe"

if not exist "%HUNYUAN_PYTHON%" (
  echo [ERROR] Hunyuan3D Python environment was not found:
  echo %HUNYUAN_PYTHON%
  echo.
  echo Please verify the local Hunyuan3D installation before starting this Beta page.
  pause
  exit /b 1
)

echo OntoTwin Nexus - Reverse Modeling Beta
echo Page:   http://127.0.0.1:8766/
echo Engine: http://127.0.0.1:8081/  (Hunyuan3D-2mv)
echo.
echo Start D:\AI\Hunyuan3D-2.1-local\start_hunyuan3d_multiview.bat first.
echo Keep this window open while using the Beta page.
echo.

"%HUNYUAN_PYTHON%" "%BETA_DIR%server.py" --host 127.0.0.1 --port 8766 --backend http://127.0.0.1:8081

echo.
echo The Beta service has stopped.
pause
