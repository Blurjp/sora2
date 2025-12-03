@echo off
setlocal enabledelayedexpansion

REM ============================================================================
REM Remote Mode - Connect to a remote GPU server
REM ============================================================================

echo ===============================================================
echo   WAN Video Generation - REMOTE MODE
echo   (Connects to remote GPU server)
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

REM Allow command line override for GPU URL
if not "%1"=="" (
    set GPU_SERVICE_URL=%1
)

if "%GPU_SERVICE_URL%"=="" (
    echo ERROR: GPU service URL not specified
    echo.
    echo Usage:
    echo   run_remote.bat http://your-gpu-server:8001
    echo.
    echo Or set in .env file:
    echo   GPU_SERVICE_URL=http://your-gpu-server:8001
    exit /b 1
)

REM Force remote mode
set USE_REMOTE_GPU=true
set HOST=127.0.0.1
set PORT=8000

echo Configuration:
echo   Mode:        REMOTE (connecting to GPU server)
echo   GPU Server:  %GPU_SERVICE_URL%
echo   Local Port:  %PORT%
if not "%GPU_API_KEY%"=="" (
    echo   API Key:     [SET]
) else (
    echo   API Key:     [NOT SET]
)
echo.

REM Activate virtual environment if it exists
if exist "%~dp0venv\Scripts\activate.bat" (
    call "%~dp0venv\Scripts\activate.bat"
    echo Virtual environment activated.
) else (
    echo WARNING: Virtual environment not found at %~dp0venv
    echo Run: python -m venv venv
    echo Then: venv\Scripts\activate ^& pip install -r requirements.txt
    pause
    exit /b 1
)

echo.
echo Web interface: http://127.0.0.1:%PORT%
echo.
echo Press Ctrl+C to stop
echo ===============================================================
echo.

python -m backend.main
