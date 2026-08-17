@echo off
:: =============================================================================
::  AI_kcMedicalResearch_CLI.bat
::  v2.4.6  |  Menu-driven CLI Launcher (scripts\launcher.py)
::
::  Location: scripts\windows\   (resolves project root two levels up)
:: =============================================================================
setlocal EnableDelayedExpansion

:: UTF-8 console so the launcher's box-drawing menu renders correctly.
chcp 65001 >nul 2>&1

:: --- 0. RESOLVE PROJECT ROOT -------------------------------------------------
set "SCRIPT_DIR=%~dp0"
if "!SCRIPT_DIR:~-1!"=="\" set "SCRIPT_DIR=!SCRIPT_DIR:~0,-1!"
set "PROJECT_DIR=!SCRIPT_DIR!\..\.."

pushd "!PROJECT_DIR!" 2>nul
if errorlevel 1 (
    echo ERROR: Cannot find project root from "!SCRIPT_DIR!".
    pause & exit /b 1
)
set "PROJECT_DIR=%CD%"
popd

title AI kcMedical Research - CLI - !PROJECT_DIR!
cd /d "!PROJECT_DIR!"

set "PY=!PROJECT_DIR!\.venv\Scripts\python.exe"
set "PIP=!PROJECT_DIR!\.venv\Scripts\pip.exe"
set "LAUNCHER=!PROJECT_DIR!\scripts\launcher.py"

call :print_header

:: --- 1. GUARD: launcher present ----------------------------------------------
if not exist "!LAUNCHER!" (
    call :box_error "Launcher not found at scripts\launcher.py"
    echo    Project root : !PROJECT_DIR!
    echo    Expected     : !LAUNCHER!
    pause & exit /b 1
)

:: --- 2. CHECK / CREATE .venv -------------------------------------------------
if not exist "!PY!" (
    echo   [SETUP] .venv not found. Checking system Python...

    where python >nul 2>&1
    if !errorlevel! neq 0 (
        call :box_error "Python not found on PATH. Install Python 3.10+ first."
        pause & exit /b 1
    )
    echo   [SETUP] Creating .venv...
    echo.
    python -m venv .venv
    if !errorlevel! neq 0 (
        call :box_error "Failed to create .venv."
        pause & exit /b 1
    )

    echo   [SETUP] Installing dependencies - this takes a few minutes...
    "!PIP!" install --upgrade pip --quiet
    "!PIP!" install -r requirements.txt --quiet
    if !errorlevel! neq 0 (
        call :box_error "Failed to install dependencies. Check your internet connection."
        pause & exit /b 1
    )
    echo   [SETUP] Dependencies installed OK.
    echo.
)

:: --- 3. WARN IF .env MISSING -------------------------------------------------
if not exist "!PROJECT_DIR!\.env" (
    echo   ------------------------------------------------------------
    echo    NOTE: no .env file found in the project root.
    echo    Cloud providers need API keys. Copy .env.example to .env
    echo    and fill in your keys, or use --provider ollama offline.
    echo   ------------------------------------------------------------
    echo.
)

:: --- 4. LAUNCH ---------------------------------------------------------------
echo   ------------------------------------------------------------
echo    Starting menu launcher
echo    Startup : ~7 seconds while dependencies load - please wait
echo    Stop    : Ctrl+C inside a session returns to the menu
echo   ------------------------------------------------------------
echo.

:: Run in the foreground of THIS console so interactive prompts (PICO
:: selection, sub-mode choices) receive a real TTY. Do not wrap in start/cmd /c.
"!PY!" "!LAUNCHER!"

set "RC=!errorlevel!"

:: --- 5. DONE -----------------------------------------------------------------
echo.
if !RC! neq 0 (
    call :box_error "Launcher exited with code !RC!"
) else (
    echo   Session ended.
)
echo.
pause
exit /b !RC!


:: =============================================================================
::  SUBROUTINES
:: =============================================================================

:print_header
echo.
echo   ============================================================
echo    AI kcMedical Research  ^|  CLI Launcher  ^|  v2.4.6
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
