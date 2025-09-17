@echo off
setlocal enabledelayedexpansion
title Rocket Simulation Platform Launcher

echo ========================================
echo    Rocket Simulation Platform Launcher
echo ========================================
echo.
echo Starting comprehensive system check...
echo Current directory: %CD%
echo Current user: %USERNAME%
echo Computer name: %COMPUTERNAME%
echo.

REM Create a log file for debugging
set LOG_FILE=%~dp0launcher_debug.log
echo Launcher started at %DATE% %TIME% > "%LOG_FILE%"
echo Current directory: %CD% >> "%LOG_FILE%"
echo Current user: %USERNAME% >> "%LOG_FILE%"

REM Function to log and echo
:log_and_echo
echo %~1
echo %~1 >> "%LOG_FILE%"
goto :eof

REM Navigate to project directory
call :log_and_echo "[1/8] Navigating to project directory..."
cd /d "C:\Users\arvin\Downloads\R_SIM" 2>>"%LOG_FILE%"
if not exist "package.json" (
    call :log_and_echo "ERROR: package.json not found! Are you in the right directory?"
    call :log_and_echo "Current directory: %CD%"
    call :log_and_echo "Files in current directory:"
    dir /b >> "%LOG_FILE%"
    pause
    exit /b 1
)
call :log_and_echo "[1/8] ✓ Navigated to project directory"

REM Check Node.js with multiple methods
call :log_and_echo "[2/8] Checking Node.js installation..."
node --version >nul 2>&1
if errorlevel 1 (
    call :log_and_echo "ERROR: Node.js is not installed! Please install Node.js first."
    call :log_and_echo "Download from: https://nodejs.org/"
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('node --version 2^>^&1') do set NODE_VERSION=%%i
call :log_and_echo "[2/8] ✓ Node.js is installed (version: !NODE_VERSION!)"

REM Check npm
call :log_and_echo "[3/8] Checking npm installation..."
npm --version >nul 2>&1
if errorlevel 1 (
    call :log_and_echo "ERROR: npm is not installed!"
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('npm --version 2^>^&1') do set NPM_VERSION=%%i
call :log_and_echo "[3/8] ✓ npm is installed (version: !NPM_VERSION!)"

REM Check pnpm with comprehensive error handling
call :log_and_echo "[4/8] Checking pnpm installation..."
set PNPM_WORKS=0
set USE_NPM=1

REM Try pnpm with timeout and error capture
echo Testing pnpm --version...
timeout /t 1 /nobreak >nul
pnpm --version >nul 2>&1
set PNPM_EXIT_CODE=%errorlevel%
call :log_and_echo "pnpm exit code: !PNPM_EXIT_CODE!"

if !PNPM_EXIT_CODE! equ 0 (
    for /f "tokens=*" %%i in ('pnpm --version 2^>^&1') do set PNPM_VERSION=%%i
    call :log_and_echo "pnpm version output: !PNPM_VERSION!"
    
    REM Test pnpm install capability
    call :log_and_echo "Testing pnpm install capability..."
    pnpm install --help >nul 2>&1
    if !errorlevel! equ 0 (
        set PNPM_WORKS=1
        set USE_NPM=0
        call :log_and_echo "[4/8] ✓ pnpm is working (version: !PNPM_VERSION!)"
    ) else (
        call :log_and_echo "pnpm --version works but pnpm install fails"
        set PNPM_WORKS=0
        set USE_NPM=1
    )
) else (
    call :log_and_echo "pnpm --version failed, trying to install..."
    
    REM Try to install pnpm
    call :log_and_echo "Installing pnpm globally..."
    npm install -g pnpm >nul 2>&1
    set NPM_INSTALL_EXIT=%errorlevel%
    call :log_and_echo "npm install -g pnpm exit code: !NPM_INSTALL_EXIT!"
    
    if !NPM_INSTALL_EXIT! equ 0 (
        REM Test installed pnpm
        timeout /t 2 /nobreak >nul
        pnpm --version >nul 2>&1
        if !errorlevel! equ 0 (
            for /f "tokens=*" %%i in ('pnpm --version 2^>^&1') do set PNPM_VERSION=%%i
            call :log_and_echo "[4/8] ✓ pnpm installed and working (version: !PNPM_VERSION!)"
            set PNPM_WORKS=1
            set USE_NPM=0
        ) else (
            call :log_and_echo "pnpm installation failed - will use npm"
            set PNPM_WORKS=0
            set USE_NPM=1
        )
    ) else (
        call :log_and_echo "Failed to install pnpm - will use npm"
        set PNPM_WORKS=0
        set USE_NPM=1
    )
)

REM Install frontend dependencies
call :log_and_echo "[5/8] Installing frontend dependencies..."
if !USE_NPM! equ 1 (
    call :log_and_echo "Using npm to install dependencies..."
    npm install
    if !errorlevel! neq 0 (
        call :log_and_echo "ERROR: npm install failed!"
        call :log_and_echo "Trying npm cache clean..."
        npm cache clean --force
        call :log_and_echo "Retrying npm install..."
        npm install
        if !errorlevel! neq 0 (
            call :log_and_echo "ERROR: npm install failed even after cache clean!"
            pause
            exit /b 1
        )
    )
    call :log_and_echo "[5/8] ✓ Frontend dependencies installed with npm"
) else (
    call :log_and_echo "Using pnpm to install dependencies..."
    pnpm install
    if !errorlevel! neq 0 (
        call :log_and_echo "pnpm install failed, trying npm as fallback..."
        npm install
        if !errorlevel! neq 0 (
            call :log_and_echo "ERROR: Both pnpm and npm install failed!"
            pause
            exit /b 1
        ) else (
            call :log_and_echo "[5/8] ✓ Frontend dependencies installed with npm (fallback)"
            set USE_NPM=1
        )
    ) else (
        call :log_and_echo "[5/8] ✓ Frontend dependencies installed with pnpm"
    )
)

REM Check Python with multiple methods
call :log_and_echo "[6/8] Checking Python installation..."
set PYTHON_CMD=
py --version >nul 2>&1
if !errorlevel! equ 0 (
    set PYTHON_CMD=py
    for /f "tokens=*" %%i in ('py --version 2^>^&1') do set PYTHON_VERSION=%%i
    call :log_and_echo "[6/8] ✓ Python is installed (version: !PYTHON_VERSION!)"
) else (
    python --version >nul 2>&1
    if !errorlevel! equ 0 (
        set PYTHON_CMD=python
        for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
        call :log_and_echo "[6/8] ✓ Python is installed (version: !PYTHON_VERSION!)"
    ) else (
        call :log_and_echo "ERROR: Python is not installed! Please install Python first."
        call :log_and_echo "Download from: https://python.org/"
        pause
        exit /b 1
    )
)

REM Setup Python virtual environment
call :log_and_echo "[7/8] Setting up Python backend..."
if not exist "backend\venv\Scripts\activate.bat" (
    call :log_and_echo "Creating Python virtual environment..."
    cd backend
    !PYTHON_CMD! -m venv venv
    if !errorlevel! neq 0 (
        call :log_and_echo "ERROR: Failed to create Python virtual environment!"
        pause
        exit /b 1
    )
    cd ..
)
call :log_and_echo "[7/8] ✓ Python virtual environment ready"

REM Start servers with comprehensive error handling
call :log_and_echo "[8/8] Starting servers..."

REM Start backend server
call :log_and_echo "Starting backend server on port 5011..."
set BACKEND_CMD=cd /d "C:\Users\arvin\Downloads\R_SIM\backend" ^&^& venv\Scripts\activate ^&^& pip install -r requirements.txt ^&^& !PYTHON_CMD! f_backend.py
start "Rocket Sim Backend" cmd /k "!BACKEND_CMD!"

REM Wait for backend
call :log_and_echo "Waiting for backend to start..."
timeout /t 5 /nobreak >nul

REM Start frontend server
call :log_and_echo "Starting frontend server on port 5001..."
if !USE_NPM! equ 1 (
    call :log_and_echo "Using npm to start frontend..."
    set FRONTEND_CMD=cd /d "C:\Users\arvin\Downloads\R_SIM" ^&^& npm run dev
) else (
    call :log_and_echo "Using pnpm to start frontend..."
    set FRONTEND_CMD=cd /d "C:\Users\arvin\Downloads\R_SIM" ^&^& pnpm dev
)
start "Rocket Sim Frontend" cmd /k "!FRONTEND_CMD!"

REM Wait for frontend
call :log_and_echo "Waiting for frontend to start..."
timeout /t 8 /nobreak >nul

REM Open browser
call :log_and_echo "Opening application in browser..."
start http://localhost:5001/

echo.
echo ========================================
echo    Application Started Successfully!
echo ========================================
echo Frontend: http://localhost:5001
echo Backend:  http://localhost:5011
echo.
echo Package Manager Used: 
if !USE_NPM! equ 1 (
    echo - npm (version: !NPM_VERSION!)
) else (
    echo - pnpm (version: !PNPM_VERSION!)
)
echo Python Command: !PYTHON_CMD! (version: !PYTHON_VERSION!)
echo.
echo Debug log saved to: %LOG_FILE%
echo.
echo Two new windows should have opened:
echo - "Rocket Sim Backend" (Python Flask server)
echo - "Rocket Sim Frontend" (React development server)
echo.
echo If the application doesn't load, check the backend window for errors.
echo.
echo Press any key to close this launcher window...
pause >nul
