@echo off
setlocal

set "ROOT_DIR=%~dp0"
cd /d "%ROOT_DIR%"

echo ==========================================
echo Health Management System - Quick Start
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

if not exist "%ROOT_DIR%frontend\node_modules" (
  echo [INFO] frontend\node_modules missing. Running npm install...
  pushd "%ROOT_DIR%frontend"
  call npm install
  if errorlevel 1 (
    popd
    echo [ERROR] npm install failed.
    pause
    exit /b 1
  )
  popd
)

if not exist "%ROOT_DIR%scripts\start_backend.bat" (
  echo [ERROR] scripts\start_backend.bat not found.
  pause
  exit /b 1
)

if not exist "%ROOT_DIR%scripts\start_frontend.bat" (
  echo [ERROR] scripts\start_frontend.bat not found.
  pause
  exit /b 1
)

echo [INFO] Starting backend in a new window...
start "Health Backend" "%ROOT_DIR%scripts\start_backend.bat"

echo [INFO] Starting frontend in a new window...
start "Health Frontend" "%ROOT_DIR%scripts\start_frontend.bat"

echo.
echo [DONE] Services are launching.
echo Backend:  http://127.0.0.1:8000/docs
echo Frontend: http://127.0.0.1:3000
echo.
echo Note: Qdrant / Ollama are not auto-started by this script.
echo If needed, start them separately.
pause
