@echo off
:: =============================================================================
::  AI_kcMedicalResearch_UI.bat
::  v2.4.13  |  Streamlit UI Launcher
::
::  Location: scripts\windows\   (resolves project root two levels up)
:: =============================================================================
setlocal EnableDelayedExpansion

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
    pause & exit /b 1
)

:: --- 2. CHECK / CREATE .venv -------------------------------------------------
if not exist "!PY!" (
    call :find_py311
    if not defined PY311 (
        call :install_message
        pause & exit /b 1
    )
    echo   Using Python: !PY311!
    echo.
    "!PY311!" -m venv .venv
    if !errorlevel! neq 0 (
        call :box_error "Could not create the app environment."
        pause & exit /b 1
    )

    echo   Setting up, please wait - this can take a few minutes.
    echo   The screen may look frozen. That is normal - do NOT close this window.
    echo.
    "!PIP!" install --upgrade pip
    "!PIP!" install -r requirements-local.txt
    if !errorlevel! neq 0 (
        call :box_error "Could not install the app's components."
        call :install_message
        pause & exit /b 1
    )
    echo.
    echo   Setup complete.
    echo.
)

:: --- 3. WARN IF .env MISSING -------------------------------------------------
if not exist "!PROJECT_DIR!\.env" (
    echo   ------------------------------------------------------------
    echo    NOTE: no .env file found.
    echo    To use a cloud provider (OpenAI, Anthropic, Qwen, Groq),
    echo    copy .env.example to .env and add your API key.
    echo    To use the free local option, set up Ollama (see README Step 2).
    echo   ------------------------------------------------------------
    echo.
)

:: --- 4. LAUNCH (Streamlit UI) ------------------------------------------------
echo   ------------------------------------------------------------
echo    Starting the web interface
echo    It will open in your browser at http://localhost:8501
echo    Stop : close this window or press Ctrl+C
echo   ------------------------------------------------------------
echo.

"!PY!" -m streamlit run "!APP!" --server.port=8501 --browser.gatherUsageStats=false
set "RC=!errorlevel!"

echo.
if !RC! neq 0 ( call :box_error "App exited with code !RC!" ) else ( echo   Session ended. )
echo.
pause
exit /b !RC!


:: =============================================================================
::  SUBROUTINES
:: =============================================================================

:print_header
echo.
echo   ============================================================
echo    AI kcMedical Research  ^|  Pipeline UI  ^|  v2.4.13
echo   ============================================================
echo    Project : !PROJECT_DIR!
echo   ============================================================
echo.
goto :eof

:find_py311
:: Find a genuine Python 3.11 via the py launcher; reject conda/anaconda.
set "PY311="
for /f "delims=" %%P in ('py -3.11 -c "import sys;print(sys.executable)" 2^>nul') do set "PY311=%%P"
if defined PY311 echo !PY311! | find /i "conda" >nul && set "PY311="
goto :eof

:install_message
echo.
echo   ------------------------------------------------------------
echo    This app needs Python 3.11.
echo.
echo    1. Download it here:
echo       https://www.python.org/downloads/release/python-3119/
echo       (choose the Windows installer^)
echo.
echo    2. Run the installer and tick "Add python.exe to PATH".
echo.
echo    3. Start this app again.
echo   ------------------------------------------------------------
echo.
goto :eof

:box_error
echo.
echo   ************************************************************
echo    ERROR: %~1
echo   ************************************************************
echo.
goto :eof
