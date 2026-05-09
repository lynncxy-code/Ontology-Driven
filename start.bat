@echo off
cd /d "%~dp0"
echo.
echo [OntoTwin Nexus] Starting Docker containers...
echo.

docker compose up -d --build
if errorlevel 1 (
    echo.
    echo [ERROR] Docker failed. Is Docker Desktop running?
    pause
    exit /b 1
)

echo.
echo [OK] Containers started. Opening browser...
timeout /t 4 /nobreak >nul
start "" "http://localhost:5000/nexus"

echo.
echo Frontend : http://localhost:5000/nexus
echo Stop     : docker compose down
echo Logs     : docker compose logs -f
echo.
pause
