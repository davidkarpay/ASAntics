# SAO Contact Manager - PowerShell Launcher
# Run as Administrator for best security

Write-Host "==========================================" -ForegroundColor Blue
Write-Host "   SAO Contact Manager - Desktop Version" -ForegroundColor Blue  
Write-Host "==========================================" -ForegroundColor Blue
Write-Host ""

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "WARNING: Not running as Administrator" -ForegroundColor Yellow
    Write-Host "For enhanced security, consider running as Administrator" -ForegroundColor Yellow
    Write-Host ""
}

# Check Python installation
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python not found. Please install Python from https://python.org" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Check and install dependencies
Write-Host "Checking dependencies..." -ForegroundColor Yellow
try {
    python -c "import streamlit, pandas, fitz" 2>$null
    Write-Host "All dependencies found" -ForegroundColor Green
} catch {
    Write-Host "Installing required packages..." -ForegroundColor Yellow
    pip install streamlit pandas PyMuPDF
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to install packages" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

# Set security environment variables
$env:STREAMLIT_SERVER_HEADLESS = "true"
$env:STREAMLIT_BROWSER_GATHER_USAGE_STATS = "false"
$env:STREAMLIT_SERVER_PORT = "8501"

# Generate random port for extra security
$randomPort = Get-Random -Minimum 8500 -Maximum 8600
$env:STREAMLIT_SERVER_PORT = $randomPort.ToString()

Write-Host ""
Write-Host "Starting SAO Contact Manager..." -ForegroundColor Green
Write-Host ""
Write-Host "Application URL: http://localhost:$randomPort" -ForegroundColor Cyan
Write-Host ""
Write-Host "Security Features Enabled:" -ForegroundColor Yellow
Write-Host "- Headless mode (no external access)" -ForegroundColor Gray
Write-Host "- Usage stats disabled" -ForegroundColor Gray
Write-Host "- Random port assignment" -ForegroundColor Gray
Write-Host "- Local-only binding" -ForegroundColor Gray
Write-Host ""
Write-Host "To stop the application, press Ctrl+C or close this window" -ForegroundColor Yellow
Write-Host ""

# Start Streamlit with security options
try {
    streamlit run sao_contact_manager.py --server.headless true --server.port $randomPort --browser.gatherUsageStats false --server.address localhost
} catch {
    Write-Host "ERROR: Failed to start application" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
}

Write-Host ""
Write-Host "Application stopped." -ForegroundColor Yellow
Read-Host "Press Enter to exit"