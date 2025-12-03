@echo off

REM ============================================================================
REM Remote Mode - Connect to a remote GPU server
REM ============================================================================

echo ===============================================================
echo   WAN Video Generation - REMOTE MODE
echo   (Connects to remote GPU server)
echo ===============================================================
echo.

cd /d "%~dp0"

REM Create virtual environment if it doesn't exist
if not exist "venv\Scripts\activate.bat" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo Virtual environment created.
    echo.
)

REM Activate virtual environment
call venv\Scripts\activate.bat
echo Virtual environment activated.
echo.

REM Install dependencies if fastapi is not installed
python -c "import fastapi" 2>nul
if errorlevel 1 (
    echo Installing dependencies...
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
    echo Dependencies installed.
    echo.
)

REM Load environment from .env file if it exists
if exist ".env" (
    echo Loading configuration from .env file...
    for /f "usebackq tokens=1,* delims==" %%a in (".env") do (
        set "line=%%a"
        if not "%%a"=="" if not "!line:~0,1!"=="#" set "%%a=%%b"
    )
    echo.
)

REM Allow command line override for GPU URL
if not "%1"=="" set GPU_SERVICE_URL=%1

if "%GPU_SERVICE_URL%"=="" (
    echo ERROR: GPU service URL not specified
    echo.
    echo Usage:
    echo   run_remote.bat http://your-gpu-server:8001
    echo.
    echo Or set in .env file:
    echo   GPU_SERVICE_URL=http://your-gpu-server:8001
    pause
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
echo.
echo Web interface: http://127.0.0.1:%PORT%
echo.
echo Press Ctrl+C to stop
echo ===============================================================
echo.

python -m backend.main
