@echo off
rem 숏폼 솔팅기 + 다운로드 서버 실행 (더블클릭용)
rem 필요한 것: Python (python.org 에서 설치, "Add to PATH" 체크)
chcp 65001 >nul
cd /d "%~dp0"

where py >nul 2>nul && (set PY=py) || (set PY=python)

echo [1/3] 필요한 프로그램 설치 확인 중...
%PY% -m pip install -q -r server\requirements.txt
if errorlevel 1 (
    echo.
    echo Python이 설치되어 있지 않은 것 같습니다.
    echo https://www.python.org/downloads/ 에서 설치 후 다시 실행해 주세요.
    echo ^(설치할 때 "Add Python to PATH" 체크 필수^)
    pause
    exit /b 1
)

echo [2/3] 브라우저 열기...
start "" http://127.0.0.1:8756/

echo [3/3] 서버 실행 중 — 이 창을 닫으면 다운로드가 멈춥니다.
%PY% server\app.py
pause
