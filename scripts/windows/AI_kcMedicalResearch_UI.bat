@echo off
:: =============================================================================
::  AI_kcMedicalResearch_UI.bat
::  v2.3.2  |  Global / Shared Streamlit UI Launcher  |  Updated for SOURCE_CODE
:: =============================================================================
setlocal EnableDelayedExpansion

:: --- 0. RESOLVE PROJECT ROOT -------------------------------------------------
set "PROJECT_DIR=%~dp0.."
if "!PROJECT_DIR:~-1!"=="\" set "PROJECT_DIR=!PROJECT_DIR:~0,-1!"
title AI kcMedical Research - UI - %PROJECT_DIR%
cd /d "%PROJECT_DIR%"

call :print_header

:: --- 1. GUARD: .venv present? ------------------------------------------------
if not exist "%PROJECT_DIR%\.venv\Scripts\python.exe" (
    call :box_error ".venv not found. Run AI_kcMedicalResearch_CLI.bat first."
    pause & exit /b 1
)

:: --- 2. GUARD: app.py present? -----------------------------------------------
if not exist "%PROJECT_DIR%\SOURCE_CODE\ui\app.py" (
    call :box_error "UI app not found at SOURCE_CODE\ui\app.py"
    pause & exit /b 1
)

:: --- 3. CHECK STREAMLIT INSTALLED --------------------------------------------
"%PROJECT_DIR%\.venv\Scripts\python.exe" -c "import streamlit" >nul 2>&1
if !errorlevel! neq 0 (
    echo   Streamlit not found. Installing now...
    "%PROJECT_DIR%\.venv\Scripts\pip.exe" install streamlit --quiet
    if !errorlevel! neq 0 (
        call :box_error "Failed to install streamlit. Check your internet connection."
        pause & exit /b 1
    )
    echo   Streamlit installed OK.
    echo.
)

:: --- 4. LAUNCH INFO ----------------------------------------------------------
echo   ------------------------------------------------------------
echo    Launching Streamlit UI
echo    Browser : http://localhost:8501
echo    Stop    : Press Ctrl+C in this window
echo   ------------------------------------------------------------
echo.

:: --- 5. WAIT 3s THEN OPEN BROWSER -------------------------------------------
ping -n 4 127.0.0.1 >nul
start "" "http://localhost:8501"

:: --- 6. START STREAMLIT ------------------------------------------------------
set "APP=%PROJECT_DIR%\SOURCE_CODE\ui\app.py"
set "PY=%PROJECT_DIR%\.venv\Scripts\python.exe"

"%PY%" -m streamlit run "%APP%" ^
    "--server.runOnSave=false" ^
    "--server.headless=false" ^
    "--browser.gatherUsageStats=false"

:: --- 7. DONE -----------------------------------------------------------------
echo.
echo   Streamlit UI stopped.
echo.
pause
exit /b 0


:: =============================================================================
::  SUBROUTINES
:: =============================================================================

:print_header
echo.
echo   ============================================================
echo    AI kcMedical Research  ^|  Pipeline UI  ^|  v2.3.2
echo   ============================================================
echo    Project : %PROJECT_DIR%
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