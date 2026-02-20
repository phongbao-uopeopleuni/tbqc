# Script to install requests module
Write-Host "Installing requests module..." -ForegroundColor Yellow

# Check if pip is available
try {
    $pipVersion = python -m pip --version
    Write-Host "Found pip: $pipVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: pip not found. Please install Python with pip." -ForegroundColor Red
    exit 1
}

# Install requests
Write-Host "Running: python -m pip install requests" -ForegroundColor Cyan
python -m pip install requests

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n[SUCCESS] requests module installed successfully!" -ForegroundColor Green
    Write-Host "You can now run: python test_fix_fm_id.py" -ForegroundColor Green
} else {
    Write-Host "`n[ERROR] Failed to install requests module." -ForegroundColor Red
    Write-Host "Try running manually: python -m pip install requests" -ForegroundColor Yellow
}

