@echo off
setlocal

set "ROOT_DIR=%~dp0"
cd /d "%ROOT_DIR%"

echo ==========================================
echo Health Management System - Production Start
echo Root: %ROOT_DIR%
echo ==========================================

if not exist "%ROOT_DIR%backend\app\main.py" (
  echo [ERROR] backend\app\main.py not found.
  pause
  exit /b 1
)

if not exist "%ROOT_DIR%frontend\package.json" (
  echo [ERROR] frontend\package.json not found.
  pause
  exit /b 1
)

set "PY_EXE=%ROOT_DIR%.venv\Scripts\python.exe"
if not exist "%PY_EXE%" (
  echo [ERROR] Python venv not found at .venv\Scripts\python.exe
  echo Create it first:
  echo   python -m venv .venv
  echo   .\.venv\Scripts\pip install -r backend\requirements.txt
  pause
  exit /b 1
)

where npm >nul 2>nul
if errorlevel 1 (
  echo [ERROR] npm not found in PATH. Please install Node.js first.
  pause
  exit /b 1
)

if "%BACKEND_WORKERS%"=="" (
  set "BACKEND_WORKERS=2"
)
if "%BACKEND_PORT%"=="" (
  set "BACKEND_PORT=8000"
)
if "%FRONTEND_PORT%"=="" (
  set "FRONTEND_PORT=3000"
)

if not exist "%ROOT_DIR%scripts\start_backend_prod.bat" (
  echo [ERROR] scripts\start_backend_prod.bat not found.
  pause
  exit /b 1
)
if not exist "%ROOT_DIR%scripts\start_frontend_prod.bat" (
  echo [ERROR] scripts\start_frontend_prod.bat not found.
  pause
  exit /b 1
)
if not exist "%ROOT_DIR%scripts\wait_http.ps1" (
  echo [ERROR] scripts\wait_http.ps1 not found.
  pause
  exit /b 1
)

echo [INFO] Starting backend (production) in a new window...
start "Health Backend PROD" cmd /k "set BACKEND_WORKERS=%BACKEND_WORKERS% && set BACKEND_PORT=%BACKEND_PORT% && call \"%ROOT_DIR%scripts\start_backend_prod.bat\""

echo [INFO] Starting frontend (production preview) in a new window...
start "Health Frontend PROD" cmd /k "set FRONTEND_PORT=%FRONTEND_PORT% && call \"%ROOT_DIR%scripts\start_frontend_prod.bat\""

echo [INFO] Waiting for backend health endpoint...
powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT_DIR%scripts\wait_http.ps1" -Url "http://127.0.0.1:%BACKEND_PORT%/api/health" -TimeoutSeconds 45 >nul
if errorlevel 1 (
  echo [WARN] Backend health check timeout: http://127.0.0.1:%BACKEND_PORT%/api/health
) else (
  echo [OK] Backend is up.
)

echo [INFO] Waiting for frontend endpoint...
powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT_DIR%scripts\wait_http.ps1" -Url "http://127.0.0.1:%FRONTEND_PORT%/" -TimeoutSeconds 60 >nul
if errorlevel 1 (
  echo [WARN] Frontend health check timeout: http://127.0.0.1:%FRONTEND_PORT%/
) else (
  echo [OK] Frontend is up.
)

echo.
echo [DONE] Production services launched.
echo Backend:  http://127.0.0.1:%BACKEND_PORT%/docs
echo Frontend: http://127.0.0.1:%FRONTEND_PORT%/
echo.
echo Optional env before run:
echo   set BACKEND_WORKERS=4
echo   set BACKEND_PORT=8000
echo   set FRONTEND_PORT=3000
echo.
echo Note: Qdrant / Ollama are not auto-started by this script.
pause

endlocal
