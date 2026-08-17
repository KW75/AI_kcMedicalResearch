@echo off
:: =============================================================================
::  AI_kcMedicalResearch_UI.bat
::  v2.4.6  |  Streamlit UI Launcher
::
::  Location: scripts\windows\   (resolves project root two levels up)
:: =============================================================================
setlocal EnableDelayedExpansion

:: UTF-8 console so box-drawing characters and non-ASCII paths render correctly.
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

title AI kcMedical Research - UI - !PROJECT_DIR!
cd /d "!PROJECT_DIR!"

set "PY=!PROJECT_DIR!\.venv\Scripts\python.exe"
set "PIP=!PROJECT_DIR!\.venv\Scripts\pip.exe"
set "APP=!PROJECT_DIR!\SOURCE_CODE\ui\app.py"

call :print_header

:: --- 1. GUARD: app present ---------------------------------------------------
if not exist "!APP!" (
    call :box_error "UI app not found at SOURCE_CODE\ui\app.py"
    echo    Project root : !PROJECT_DIR!
    echo    Expected     : !APP!
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

:: --- 3. CHECK STREAMLIT ------------------------------------------------------
"!PY!" -c "import streamlit" >nul 2>&1
if !errorlevel! neq 0 (
    echo   Streamlit not found in .venv. Installing...
    "!PIP!" install streamlit --quiet
    if !errorlevel! neq 0 (
        call :box_error "Failed to install streamlit."
        pause & exit /b 1
    )
    echo   Streamlit installed OK.
    echo.
)

:: --- 4. LAUNCH ---------------------------------------------------------------
echo   ------------------------------------------------------------
echo    Launching Streamlit UI
echo    Browser : http://localhost:8501  - opens automatically
echo    Startup : ~7 seconds - please wait
echo    Stop    : Press Ctrl+C in this window
echo   ------------------------------------------------------------
echo.

:: Streamlit opens the browser itself once the server is actually listening.
:: Do NOT add a separate "start http://localhost:8501" here - that produces a
:: second tab, and it fires before the server is up (connection refused).
"!PY!" -m streamlit run "!APP!" ^
    "--server.headless=false" ^
    "--server.runOnSave=false" ^
    "--browser.gatherUsageStats=false"

set "RC=!errorlevel!"

:: --- 5. DONE -----------------------------------------------------------------
echo.
if !RC! neq 0 (
    call :box_error "Streamlit exited with code !RC!"
) else (
    echo   Streamlit UI stopped.
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
echo    AI kcMedical Research  ^|  Pipeline UI  ^|  v2.4.6
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
