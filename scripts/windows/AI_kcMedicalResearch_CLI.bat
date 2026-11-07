@echo off
:: =============================================================================
::  AI_kcMedicalResearch_CLI.bat
::  v2.5.0  |  Menu-driven CLI Launcher (scripts\launcher.py)
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

title AI kcMedical Research - CLI - !PROJECT_DIR!
cd /d "!PROJECT_DIR!"

set "PY=!PROJECT_DIR!\.venv\Scripts\python.exe"
set "LAUNCHER=!PROJECT_DIR!\scripts\launcher.py"

call :print_header

:: --- 1. GUARD: launcher present ----------------------------------------------
if not exist "!LAUNCHER!" (
    call :box_error "Launcher not found at scripts\launcher.py"
    pause & exit /b 1
)

:: --- 2a. MOVED FOLDER? -------------------------------------------------------
:: pip's .exe stub and the other console scripts in .venv store the absolute
:: path of the folder the venv was built in. After the app folder is moved
:: or renamed they fail ("Fatal error in launcher"). pyvenv.cfg's "command"
:: line records where the venv was built; if it is not this folder, offer a
:: rebuild. The old tree is kept as .venv.old until the new one installs.
set "VENV_CMD="
set "VENV_MOVED="
set "REBUILT="
if not exist "!PROJECT_DIR!\.venv\pyvenv.cfg" goto :venv_check_done
for /f "usebackq delims=" %%L in (`findstr /B /I /C:"command =" "!PROJECT_DIR!\.venv\pyvenv.cfg"`) do set "VENV_CMD=%%L"
if not defined VENV_CMD goto :venv_check_done
set "VENV_CHECK=!VENV_CMD:%PROJECT_DIR%\.venv=!"
if /I not "!VENV_CHECK!"=="!VENV_CMD!" goto :venv_check_done

echo   ------------------------------------------------------------
echo    This app folder was moved since setup.
echo    The app environment was built in: !VENV_CMD:*-m venv =!
echo    Tools such as pip and pytest will not start until it is rebuilt.
echo   ------------------------------------------------------------
if exist "!PROJECT_DIR!\.venv.old" (
    echo   A previous rebuild left the folder .venv.old behind.
    echo   Delete .venv.old, or rename it back to .venv, then start again.
    pause & exit /b 1
)
set "ANS="
set /p "ANS=  Rebuild the app environment now? [Y/n] "
if /I "!ANS!"=="n" goto :venv_check_done
if /I "!ANS!"=="no" goto :venv_check_done
ren "!PROJECT_DIR!\.venv" ".venv.old"
if errorlevel 1 (
    call :box_error "Could not rename .venv. Close VS Code and other windows using it, then try again."
    pause & exit /b 1
)
set "REBUILT=1"
:venv_check_done

:: --- 2b. CHECK / CREATE .venv ------------------------------------------------
if not exist "!PY!" (
    call :find_py311
    if not defined PY311 (
        call :install_message
        if defined REBUILT (
            ren "!PROJECT_DIR!\.venv.old" ".venv"
            echo   Your previous app environment was restored.
        )
        pause & exit /b 1
    )
    echo   Using Python: !PY311!
    echo.
    "!PY311!" -m venv .venv
    if !errorlevel! neq 0 (
        call :box_error "Could not create the app environment."
        if defined REBUILT (
            rmdir /s /q "!PROJECT_DIR!\.venv" 2>nul
            ren "!PROJECT_DIR!\.venv.old" ".venv"
            echo   Your previous app environment was restored.
        )
        pause & exit /b 1
    )

    echo   Setting up, please wait - this can take a few minutes.
    echo   The screen may look frozen. That is normal - do NOT close this window.
    echo.
    "!PY!" -m pip install --upgrade pip
    "!PY!" -m pip install -r requirements-local.txt
    if !errorlevel! neq 0 (
        call :box_error "Could not install the app's components."
        call :install_message
        if defined REBUILT (
            rmdir /s /q "!PROJECT_DIR!\.venv" 2>nul
            ren "!PROJECT_DIR!\.venv.old" ".venv"
            echo   Your previous app environment was restored.
        )
        pause & exit /b 1
    )
    if defined REBUILT (
        rmdir /s /q "!PROJECT_DIR!\.venv.old"
        echo   Old app environment removed.
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

:: --- 4. LAUNCH ---------------------------------------------------------------
echo   ------------------------------------------------------------
echo    Starting the app menu
echo    Startup : a few seconds while things load - please wait
echo    Stop    : Ctrl+C inside a session returns to the menu
echo   ------------------------------------------------------------
echo.

"!PY!" "!LAUNCHER!"
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
echo    AI kcMedical Research  ^|  CLI Launcher  ^|  v2.5.0
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
