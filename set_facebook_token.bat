@echo off
REM Script để set Facebook Access Token trên Windows CMD
REM Chạy script này sau khi copy token từ Graph API Explorer

echo ========================================
echo SET FACEBOOK ACCESS TOKEN
echo ========================================
echo.

set /p TOKEN="Paste Facebook Page Access Token (tu Graph API Explorer): "

if "%TOKEN%"=="" (
    echo Token khong duoc de trong!
    exit /b 1
)

REM Set environment variables cho session hiện tại
set FB_ACCESS_TOKEN=%TOKEN%
set FB_PAGE_ID=PhongTuyBienQuanCong

echo.
echo [OK] Da set token cho session hien tai!
echo.
echo Token da duoc set:
echo FB_ACCESS_TOKEN = %TOKEN:~0,20%...
echo FB_PAGE_ID = PhongTuyBienQuanCong
echo.
echo [LUU Y] Token nay chi co hieu luc trong CMD session hien tai.
echo    Neu dong CMD, token se mat. De set vinh vien, them vao file .env
echo.
echo Bay gio ban co the:
echo 1. Restart Flask server (neu dang chay)
echo 2. Vao /admin/activities va click 'Import tu Facebook'
echo.

pause

