@echo off
setlocal enabledelayedexpansion

REM ============================================================================
REM  Open-Sora Video Generation Service - Lambda Labs Setup Helper (Windows)
REM  This wrapper locates a POSIX shell (Git Bash / WSL / MSYS) and runs
REM  lambda_setup.sh so Windows users can kick off the automated install with a
REM  single command.
REM ============================================================================

set "SCRIPT_NAME=lambda_setup.sh"
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_PATH=%SCRIPT_DIR%%SCRIPT_NAME%"

if not exist "%SCRIPT_PATH%" (
    echo [ERROR] %SCRIPT_NAME% not found next to %~nx0.
    echo Make sure you run this script from the project root.
    exit /b 1
)

REM ---------------------------------------------------------------------------
REM 1. Prefer Git Bash (known location) or another non-WSL bash on PATH
REM ---------------------------------------------------------------------------
set "BASH_EXE="

if exist "%ProgramFiles%\Git\bin\bash.exe" (
    set "BASH_EXE=%ProgramFiles%\Git\bin\bash.exe"
    goto :run_with_bash
)
if exist "%ProgramFiles(x86)%\Git\bin\bash.exe" (
    set "BASH_EXE=%ProgramFiles(x86)%\Git\bin\bash.exe"
    goto :run_with_bash
)

for /f "delims=" %%P in ('where bash.exe 2^>nul') do (
    echo %%P | find /I "\System32\bash.exe" >nul
    if errorlevel 1 (
        set "BASH_EXE=%%P"
        goto :run_with_bash
    )
)

REM ---------------------------------------------------------------------------
REM 2. Fall back to WSL
REM ---------------------------------------------------------------------------
where wsl.exe >nul 2>&1
if not errorlevel 1 (
    goto :run_with_wsl
)

echo [ERROR] Could not locate bash nor wsl.exe.
echo Install Git for Windows (https://git-scm.com/download/win) or enable WSL,
echo then re-run this script.
exit /b 1

:run_with_bash
echo [INFO] Running lambda_setup.sh via "%BASH_EXE%"

REM Git Bash understands Windows paths, but MSYS likes forward slashes.
set "SCRIPT_UNIX=%SCRIPT_PATH:\=/%"

"%BASH_EXE%" "%SCRIPT_UNIX%" %*
exit /b %errorlevel%

:run_with_wsl
echo [INFO] Running lambda_setup.sh inside WSL

REM Convert Windows paths to WSL paths
for /f "usebackq delims=" %%I in (`wsl wslpath "%SCRIPT_DIR%"`) do set "WSL_DIR=%%I"
if not defined WSL_DIR (
    echo [ERROR] Unable to resolve WSL path for "%SCRIPT_DIR%"
    exit /b 1
)

REM Preserve original WSLENV so we can append temporarily
set "ORIG_WSLENV=%WSLENV%"
if defined ORIG_WSLENV (
    set "WSLENV=%ORIG_WSLENV%;SETUP_ARGS/u"
) else (
    set "WSLENV=SETUP_ARGS/u"
)

set "SETUP_ARGS=%*"

if defined SETUP_ARGS (
    wsl bash -lc "cd '%WSL_DIR%' && chmod +x %SCRIPT_NAME% && ./%SCRIPT_NAME% $SETUP_ARGS"
) else (
    wsl bash -lc "cd '%WSL_DIR%' && chmod +x %SCRIPT_NAME% && ./%SCRIPT_NAME%"
)
set "EXIT_CODE=%ERRORLEVEL%"

REM Restore original WSLENV
set "WSLENV=%ORIG_WSLENV%"
exit /b %EXIT_CODE%
