@echo off
REM Vehicle Detection Web Server Startup Script (Windows)
echo.
echo ================================================================================
echo   SmartPark - Vehicle Detection Web Interface
echo   YOLOv8-based Video Processing System
echo ================================================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

echo [*] Checking Python environment...
python --version

REM Install requirements if needed
echo.
echo [*] Installing/updating requirements...
pip install --upgrade -r requirements.txt

if errorlevel 1 (
    echo.
    echo ERROR: Failed to install requirements
    pause
    exit /b 1
)

echo.
echo ================================================================================
echo [+] Starting Vehicle Detection Web Server...
echo ================================================================================
echo.
echo  Opening: http://localhost:5000
echo  Press Ctrl+C to stop the server
echo.

REM Start Flask app
python app.py

pause
