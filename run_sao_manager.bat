@echo off
title SAO Contact Manager - Starting...
echo.
echo =========================================
echo    SAO Contact Manager - Desktop Version
echo =========================================
echo.
echo Starting application...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://python.org
    pause
    exit /b 1
)

REM Check if required packages are installed
echo Checking dependencies...
python -c "import streamlit, pandas, fitz" >nul 2>&1
if errorlevel 1 (
    echo Installing required packages...
    pip install streamlit pandas PyMuPDF
    if errorlevel 1 (
        echo ERROR: Failed to install packages
        pause
        exit /b 1
    )
)

REM Set security environment variables
set STREAMLIT_SERVER_HEADLESS=true
set STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
set STREAMLIT_SERVER_PORT=8501

echo.
echo Starting SAO Contact Manager...
echo.
echo Your application will open in your default browser at:
echo http://localhost:8501
echo.
echo To stop the application, close this window or press Ctrl+C
echo.

REM Start Streamlit
streamlit run sao_contact_manager.py --server.headless true --server.port 8501 --browser.gatherUsageStats false

pause