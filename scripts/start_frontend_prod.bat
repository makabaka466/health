@echo off
setlocal

for %%I in ("%~dp0..") do set "ROOT_DIR=%%~fI"

where npm >nul 2>nul
if errorlevel 1 (
  echo [ERROR] npm not found in PATH. Please install Node.js first.
  pause
  exit /b 1
)

if not "%FRONTEND_PORT%"=="" (
  set "PORT=%FRONTEND_PORT%"
) else (
  set "PORT=3000"
)

if not exist "%ROOT_DIR%\frontend\node_modules" (
  echo [INFO] frontend\node_modules missing. Running npm install...
  cd /d "%ROOT_DIR%\frontend"
  call npm install
  if errorlevel 1 (
    echo [ERROR] npm install failed.
    pause
    exit /b 1
  )
)

cd /d "%ROOT_DIR%\frontend"

if not exist "%ROOT_DIR%\frontend\dist\index.html" (
  echo [INFO] frontend dist not found. Building...
  call npm run build
  if errorlevel 1 (
    echo [ERROR] frontend build failed.
    pause
    exit /b 1
  )
)

echo [INFO] Frontend production preview mode
echo [INFO] port=%PORT%
call npm run preview -- --host 127.0.0.1 --port %PORT% --strictPort

endlocal
