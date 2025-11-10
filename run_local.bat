@echo off
setlocal enabledelayedexpansion
REM Windows batch file for running local backend with remote GPU

echo ===============================================================
echo   Open-Sora Local Backend (Remote GPU Mode)
echo ===============================================================
echo.

REM Load environment from .env file if it exists
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

if "%GPU_SERVICE_URL%"=="" (
    if "%1"=="" (
        echo ERROR: GPU service URL not specified
        echo.
        echo Usage:
        echo   run_local.bat http://your-lambda-ip:8001
        echo.
        echo Or set environment variable:
        echo   set GPU_SERVICE_URL=http://your-lambda-ip:8001
        echo.
        echo Or add to .env file:
        echo   GPU_SERVICE_URL=http://your-lambda-ip:8001
        exit /b 1
    )
    set GPU_SERVICE_URL=%1
)

echo Configuration:
echo   GPU Service: %GPU_SERVICE_URL%
echo   Local Port:  8000
if not "%GPU_API_KEY%"=="" (
    echo   API Key:     [SET]
) else (
    echo   API Key:     [NOT SET]
)
echo.
echo Starting local backend...
echo.
echo Open your browser at:
echo   http://localhost:8000
echo.
echo Press Ctrl+C to stop
echo ===============================================================
echo.

REM Export environment variables
set USE_REMOTE_GPU=true
set HOST=127.0.0.1
set PORT=8000

REM Run the backend as a module
python -m backend.main
