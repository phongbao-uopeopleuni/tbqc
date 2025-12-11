# PowerShell script to restart Flask server
# Usage: .\restart_server.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "RESTART FLASK SERVER" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Step 1: Stop all Python processes using port 5000
Write-Host "`n[1/4] Stopping processes on port 5000..." -ForegroundColor Yellow

$processes = Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique

if ($processes) {
    foreach ($processId in $processes) {
        try {
            $proc = Get-Process -Id $processId -ErrorAction SilentlyContinue
            if ($proc) {
                Write-Host "  Stopping process $processId ($($proc.ProcessName))..." -ForegroundColor Gray
                Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
            }
        } catch {
            Write-Host "  Could not stop process $processId" -ForegroundColor Red
        }
    }
    Write-Host "  [OK] Processes stopped" -ForegroundColor Green
} else {
    Write-Host "  [INFO] No processes found on port 5000" -ForegroundColor Gray
}

# Step 2: Wait a bit
Write-Host "`n[2/4] Waiting 2 seconds..." -ForegroundColor Yellow
Start-Sleep -Seconds 2

# Step 3: Change to project directory
Write-Host "`n[3/4] Changing to project directory..." -ForegroundColor Yellow
$projectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectDir
Write-Host "  Current directory: $projectDir" -ForegroundColor Gray

# Step 4: Start server
Write-Host "`n[4/4] Starting Flask server..." -ForegroundColor Yellow
Write-Host "  Command: python start_server.py" -ForegroundColor Gray
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "SERVER STARTING..." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "`nPress Ctrl+C to stop the server`n" -ForegroundColor Yellow

# Start server
python start_server.py

