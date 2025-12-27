@echo off
REM Script để sync Facebook posts
REM Usage: sync_facebook.bat [limit] [status]

set LIMIT=%1
if "%LIMIT%"=="" set LIMIT=25

set STATUS=%2
if "%STATUS%"=="" set STATUS=published

echo Đang đồng bộ Facebook posts...
echo Limit: %LIMIT%
echo Status: %STATUS%

python folder_py\facebook_sync.py --limit %LIMIT% --status %STATUS%

pause

