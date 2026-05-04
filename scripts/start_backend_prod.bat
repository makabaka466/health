@echo off
setlocal

for %%I in ("%~dp0..") do set "ROOT_DIR=%%~fI"
set "PY_EXE=%ROOT_DIR%\.venv\Scripts\python.exe"

if not exist "%PY_EXE%" (
  echo [ERROR] Python venv not found: "%PY_EXE%"
  pause
  exit /b 1
)

if "%BACKEND_WORKERS%"=="" (
  set "BACKEND_WORKERS=2"
)

if not "%BACKEND_PORT%"=="" (
  set "PORT=%BACKEND_PORT%"
) else (
  set "PORT=8000"
)

echo [INFO] Backend production mode
echo [INFO] workers=%BACKEND_WORKERS% port=%PORT%

cd /d "%ROOT_DIR%\backend"
"%PY_EXE%" -m uvicorn app.main:app --host 127.0.0.1 --port %PORT% --workers %BACKEND_WORKERS%

endlocal
