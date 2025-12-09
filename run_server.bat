@echo off
chcp 65001 >nul
echo ============================================================
echo 🚀 ĐANG KHỞI ĐỘNG SERVER...
echo ============================================================
cd /d "%~dp0"
python start_server.py
pause
