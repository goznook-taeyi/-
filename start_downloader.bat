@echo off
setlocal
cd /d "%~dp0"

set "PY="
where py >nul 2>nul && set "PY=py"
if not defined PY ( where python >nul 2>nul && set "PY=python" )
if not defined PY (
  echo.
  echo [!] Python not found on this PC.
  echo     Install it from https://www.python.org/downloads/
  echo     During setup, CHECK "Add Python to PATH".
  echo.
  pause
  exit /b 1
)

echo [1/3] Installing required packages...
%PY% -m pip install -q -r "server\requirements.txt"
if errorlevel 1 (
  echo.
  echo [!] Package install failed. Check your internet connection and try again.
  pause
  exit /b 1
)

echo [2/3] Opening the dashboard in your browser...
start "" http://127.0.0.1:8756/

echo [3/3] Server running. KEEP THIS WINDOW OPEN ^(closing it stops downloads^).
%PY% "server\app.py"
pause
