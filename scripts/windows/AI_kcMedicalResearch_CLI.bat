@echo off
:: =============================================================================
::  AI_kcMedicalResearch_CLI.bat
::  v2.3.2  |  Global / Shared CLI Launcher  |  Uses launcher.py
:: =============================================================================
setlocal EnableDelayedExpansion

:: --- 0. RESOLVE PROJECT ROOT -------------------------------------------------
set "SCRIPT_DIR=%~dp0"
if "!SCRIPT_DIR:~-1!"=="\" set "SCRIPT_DIR=!SCRIPT_DIR:~0,-1!"
set "PROJECT_DIR=!SCRIPT_DIR!\..\.."
pushd "!PROJECT_DIR!" 2>nul
if errorlevel 1 (
    echo ERROR: Cannot find project root.
    pause & exit /b 1
)
set "PROJECT_DIR=%CD%"
popd

title AI kcMedical Research - CLI - !PROJECT_DIR!
cd /d "!PROJECT_DIR!"

call :print_header

:: --- 1. CHECK / CREATE .venv ------------------------------------------------
if not exist "!PROJECT_DIR!\.venv\Scripts\python.exe" (
    echo   [SETUP] .venv not found. Creating virtual environment...
    echo.
    python -m venv .venv
    if !errorlevel! neq 0 (
        call :box_error "Failed to create .venv. Ensure Python 3.10+ is installed."
        pause & exit /b 1
    )
    echo   [SETUP] .venv created OK.
    echo   [SETUP] Installing dependencies...
    echo.
    "!PROJECT_DIR!\.venv\Scripts\pip.exe" install -r requirements.txt --quiet
    if !errorlevel! neq 0 (
        call :box_error "Failed to install dependencies. Check internet connection."
        pause & exit /b 1
    )
    echo   [SETUP] Dependencies installed OK.
    echo.
    echo   ============================================================
    echo    SETUP COMPLETE! You can now run the CLI.
    echo   ============================================================
    echo.
)

:: --- 2. GUARD: launcher.py present? -----------------------------------------
if not exist "!PROJECT_DIR!\scripts\launcher.py" (
    call :box_error "launcher.py not found at scripts\launcher.py"
    echo   Current directory: !PROJECT_DIR!
    echo   Expected: !PROJECT_DIR!\scripts\launcher.py
    pause & exit /b 1
)

:: --- 3. LAUNCH INFO ----------------------------------------------------------
echo   ------------------------------------------------------------
echo    Launching CLI
echo    Using   : launcher.py
echo   ------------------------------------------------------------
echo.

:: --- 4. START LAUNCHER -------------------------------------------------------
set "LAUNCHER=!PROJECT_DIR!\scripts\launcher.py"
set "PY=!PROJECT_DIR!\.venv\Scripts\python.exe"

"!PY!" "!LAUNCHER!" %*

:: --- 5. DONE -----------------------------------------------------------------
echo.
echo   CLI session ended.
echo.
pause
exit /b 0


:: =============================================================================
::  SUBROUTINES
:: =============================================================================

:print_header
echo.
echo   ============================================================
echo    AI kcMedical Research  ^|  CLI  ^|  v2.3.2
echo   ============================================================
echo    Project : !PROJECT_DIR!
echo   ============================================================
echo.
goto :eof

:box_error
echo.
echo   ************************************************************
echo    ERROR: %~1
echo   ************************************************************
echo.
goto :eof