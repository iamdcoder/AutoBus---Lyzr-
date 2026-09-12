@echo off
setlocal
cd /d "%~dp0\.."
if not exist .env copy .env.example .env >nul
echo.
echo AutoBus Lyzr setup
echo ==================
echo Paste your Lyzr API key below. It will be written only to .env.
set /p LYZR_API_KEY=LYZR_API_KEY: 
powershell -NoProfile -Command "(Get-Content .env) -replace '^LYZR_API_KEY=.*$','LYZR_API_KEY=%LYZR_API_KEY%' | Set-Content .env"
set "LYZR_API_KEY="
echo.
echo Discovering agents...
set "PYTHONPATH=%CD%;%CD%\backend"
python -m agents.lyzr_bootstrap
echo.
echo Done. Open /api/lyzr/status to verify live mode.
endlocal
