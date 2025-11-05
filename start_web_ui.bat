@echo off
REM Zimbra Migration Tool - Web UI Startup Script (Windows)

echo ================================================
echo   Zimbra Migration Tool - Web UI
echo ================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if config.ini exists
if not exist config.ini (
    echo Warning: config.ini not found
    if exist config.ini.example (
        echo Creating config.ini from config.ini.example...
        copy config.ini.example config.ini
        echo Please edit config.ini with your server details before using the migration tool
    ) else (
        echo Error: config.ini.example not found
        pause
        exit /b 1
    )
)

REM Check if virtual environment exists
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/update dependencies
echo Installing dependencies...
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

REM Set port (default 5000)
if not defined PORT set PORT=5000

echo.
echo ================================================
echo   Starting Web UI on http://localhost:%PORT%
echo ================================================
echo.
echo Press Ctrl+C to stop the server
echo.

REM Start the web application
python web_app.py

REM Deactivate virtual environment on exit
call venv\Scripts\deactivate.bat
pause
