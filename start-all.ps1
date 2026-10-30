# Start-all helper for Windows PowerShell
# - Activate .venv if present
# - Install dependencies if requested
# - Run the canonical launcher

param(
    [switch]$InstallMissing
)

$projectRoot = Split-Path -Path $MyInvocation.MyCommand.Definition -Parent
Set-Location $projectRoot

# Activate venv if it exists
if (Test-Path -Path "$projectRoot\.venv\Scripts\Activate.ps1") {
    Write-Host "Activating virtual environment..."
    & "$projectRoot\.venv\Scripts\Activate.ps1"
} else {
    Write-Host "No .venv found. Continuing with system Python"
}

if ($InstallMissing) {
    Write-Host "Installing missing packages via launcher flag..."
    & $env:PYTHONHOME -ArgumentList ('-m','bin.run_app_launcher','--install-missing')
} else {
    # Prefer explicit module invocation; fallback to run_app.py shim
    try {
        Write-Host "Starting canonical launcher..."
        py -m bin.run_app_launcher
    } catch {
        Write-Host "Falling back to root shim run_app.py"
        py .\run_app.py
    }
}

