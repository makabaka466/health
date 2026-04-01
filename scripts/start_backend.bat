@echo off
setlocal

for %%I in ("%~dp0..") do set "ROOT_DIR=%%~fI"
set "PY_EXE=%ROOT_DIR%\.venv\Scripts\python.exe"

if not exist "%PY_EXE%" (
  echo [ERROR] Python venv not found: "%PY_EXE%"
  pause
  exit /b 1
)

cd /d "%ROOT_DIR%\backend"
"%PY_EXE%" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

endlocal
