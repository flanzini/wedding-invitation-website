@echo off
setlocal
cd /d "%~dp0"

set "PYTHON=C:\Users\filip\Miniconda3\envs\expenses\python.exe"

"%PYTHON%" refresh_invitee_reports.py
if errorlevel 1 (
    echo.
    echo Refresh failed. Review the error above.
    pause
    exit /b 1
)

echo.
echo Invitee reports refreshed successfully.
pause
