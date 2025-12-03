@echo off

REM ============================================================================
REM Local Mode - Run everything on this machine (requires local GPU)
REM ============================================================================

echo ===============================================================
echo   WAN Video Generation - LOCAL MODE
echo   (Runs on your local GPU)
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

REM Force local mode
set USE_REMOTE_GPU=false
set HOST=127.0.0.1
set PORT=8000

echo Configuration:
echo   Mode:        LOCAL (using local GPU)
echo   Port:        %PORT%
echo.
echo Web interface: http://127.0.0.1:%PORT%
echo.
echo Press Ctrl+C to stop
echo ===============================================================
echo.

python -m backend.main
