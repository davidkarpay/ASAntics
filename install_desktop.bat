@echo off
title SAO Contact Manager - Desktop Installation
echo.
echo =========================================
echo    SAO Contact Manager - Desktop Setup
echo =========================================
echo.
echo This will install the SAO Contact Manager for desktop use
echo with enhanced security and isolation features.
echo.
pause

REM Check administrator privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo WARNING: Not running as Administrator
    echo For best security, run as Administrator
    echo.
)

REM Check if Python is installed
echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed
    echo.
    echo Please install Python 3.8+ from:
    echo https://www.python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
) else (
    for /f "tokens=2" %%i in ('python --version') do echo Python %%i found
)

echo.
echo Installing required packages...
pip install --upgrade streamlit pandas PyMuPDF psutil

if errorlevel 1 (
    echo ERROR: Failed to install packages
    echo Check your internet connection and try again
    pause
    exit /b 1
)

echo.
echo Setting up desktop configuration...
python desktop_config.py

echo.
echo Creating data directories...
if not exist "data" mkdir data
if not exist "logs" mkdir logs

echo.
echo Setting folder permissions (Windows)...
icacls data /inheritance:r /grant:r "%USERNAME%:(OI)(CI)F" >nul 2>&1
icacls logs /inheritance:r /grant:r "%USERNAME%:(OI)(CI)F" >nul 2>&1

echo.
echo Installation complete!
echo.
echo To start the SAO Contact Manager:
echo   1. Double-click "run_sao_manager.bat"
echo   2. Or run "run_sao_manager.ps1" in PowerShell
echo.
echo Security features enabled:
echo   - Local-only access (no network exposure)
echo   - Enhanced folder permissions  
echo   - Random port assignment
echo   - Usage tracking disabled
echo.
echo Would you like to create a desktop shortcut? (y/n)
set /p createShortcut="Enter choice: "

if /i "%createShortcut%"=="y" (
    python desktop_config.py --create-shortcut
    echo Desktop shortcut attempt completed
)

echo.
echo Setup finished! You can now run the SAO Contact Manager.
echo.
pause