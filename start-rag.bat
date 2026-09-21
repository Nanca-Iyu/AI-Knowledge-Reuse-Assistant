@echo off
setlocal
rem Only this backend process bypasses inherited local proxy variables.
set "HTTP_PROXY="
set "HTTPS_PROXY="
set "ALL_PROXY="
set "http_proxy="
set "https_proxy="
set "all_proxy="
cd /d "%~dp0backend"
python -m uvicorn server:app --host 127.0.0.1 --port 8000
pause
