@echo off
setlocal enabledelayedexpansion
REM ============================================================================
REM Restart Script - Kill all Python processes and start fresh (Windows)
REM ============================================================================

echo ===============================================================
echo             Restart Open-Sora Service
echo ===============================================================
echo.

REM Step 1: Kill all Python processes
echo [1/3] Stopping all Python processes...
echo.

taskkill /F /IM python.exe /T >nul 2>&1
taskkill /F /IM pythonw.exe /T >nul 2>&1

timeout /t 2 /nobreak >nul

echo [OK] All Python processes stopped
echo.

REM Step 2: Load environment from .env file if it exists
if exist "%~dp0.env" (
    echo Loading configuration from .env file...
    for /f "usebackq tokens=1,* delims==" %%a in ("%~dp0.env") do (
        set "line=%%a"
        REM Skip comments and empty lines
        if not "!line:~0,1!"=="#" (
            if not "%%a"=="" (
                set "%%a=%%b"
            )
        )
    )
    echo.
)

REM Step 3: Detect mode
echo [2/3] Detecting configuration...
echo.

set MODE=local
if not "%GPU_SERVICE_URL%"=="" set GPU_URL=%GPU_SERVICE_URL%
if "%GPU_URL%"=="" set GPU_URL=%GPU_SERVICE_URL%
set LOCAL_PORT=8000

REM Parse command line arguments
:parse_args
if "%~1"=="" goto end_parse
if /I "%~1"=="--local" (
    set MODE=local
    shift
    goto parse_args
)
if /I "%~1"=="--gpu-service" (
    set MODE=gpu_service
    shift
    goto parse_args
)
if /I "%~1"=="--gpu-url" (
    set GPU_URL=%~2
    shift
    shift
    goto parse_args
)
if /I "%~1"=="--api-key" (
    set GPU_API_KEY=%~2
    shift
    shift
    goto parse_args
)
if /I "%~1"=="--port" (
    set LOCAL_PORT=%~2
    shift
    shift
    goto parse_args
)
echo Unknown option: %~1
echo.
echo Usage:
echo   Local backend with remote GPU:
echo     restart.bat --local --gpu-url http://lambda-ip:8001
echo.
echo   Or set environment variable first:
echo     set GPU_SERVICE_URL=http://lambda-ip:8001
echo     restart.bat
exit /b 1

:end_parse

REM Check if GPU URL is set
if "%MODE%"=="local" (
    if "%GPU_URL%"=="" (
        echo ERROR: GPU service URL not specified
        echo.
        echo Usage:
        echo   restart.bat --gpu-url http://your-lambda-ip:8001
        echo.
        echo Or set environment variable:
        echo   set GPU_SERVICE_URL=http://your-lambda-ip:8001
        exit /b 1
    )
)

echo Mode: %MODE%
echo.

REM Step 3: Start service
echo [3/3] Starting service...
echo.

cd /d %~dp0

if "%MODE%"=="local" (
    echo Starting Local Backend (Remote GPU Mode)
    echo ===============================================================
    echo.
    echo Configuration:
    echo   GPU Service: %GPU_URL%
    echo   Local Port:  %LOCAL_PORT%
    if not "%GPU_API_KEY%"=="" (
        echo   API Key:     [SET]
    ) else (
        echo   API Key:     [NOT SET]
    )
    echo.
    echo Open browser at: http://localhost:%LOCAL_PORT%
    echo.
    echo Press Ctrl+C to stop
    echo ===============================================================
    echo.

    set USE_REMOTE_GPU=true
    set GPU_SERVICE_URL=%GPU_URL%
    set HOST=127.0.0.1
    set PORT=%LOCAL_PORT%
    if not "%GPU_API_KEY%"=="" set GPU_API_KEY=%GPU_API_KEY%

    python backend\main.py

) else if "%MODE%"=="gpu_service" (
    echo GPU service mode is not supported on Windows
    echo Please use this on Linux/Lambda instance
    exit /b 1
)
