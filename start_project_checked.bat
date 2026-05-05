@echo off
setlocal

set "ROOT_DIR=%~dp0"
cd /d "%ROOT_DIR%"

echo ==========================================
echo Health Management System - Checked Start
echo Root: %ROOT_DIR%
echo ==========================================

if not exist "%ROOT_DIR%scripts\check_runtime_deps.ps1" (
  echo [ERROR] scripts\check_runtime_deps.ps1 not found.
  pause
  exit /b 1
)

if "%AUTOSTART_DEPS%"=="" set "AUTOSTART_DEPS=0"
if "%BACKEND_PORT%"=="" set "BACKEND_PORT=8000"
if "%FRONTEND_PORT%"=="" set "FRONTEND_PORT=3000"

echo [INFO] Checking runtime dependencies (Ollama + Ganache)...
if "%AUTOSTART_DEPS%"=="1" (
  powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT_DIR%scripts\check_runtime_deps.ps1" -AutoStart
) else (
  powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT_DIR%scripts\check_runtime_deps.ps1"
)
if errorlevel 1 (
  echo [WARN] Some dependencies are not ready.
  echo [WARN] Service startup will continue. AI/chain-related features may be unavailable.
)

if not exist "%ROOT_DIR%start_project.bat" (
  echo [ERROR] start_project.bat not found.
  pause
  exit /b 1
)

echo [INFO] Starting backend + frontend...
call "%ROOT_DIR%start_project.bat"

endlocal
