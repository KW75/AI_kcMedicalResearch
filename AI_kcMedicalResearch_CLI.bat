@echo off
:: =============================================================================
::  AI_kcMedicalResearch_CLI.bat
::  v2.3.0  |  Global / Shared CLI Launcher
:: =============================================================================
setlocal EnableDelayedExpansion

:: ─────────────────────────────────────────────────────────────────────────────
::  0.  RESOLVE PROJECT ROOT
:: ─────────────────────────────────────────────────────────────────────────────
set "PROJECT_DIR=%~dp0"
if "!PROJECT_DIR:~-1!"=="\" set "PROJECT_DIR=!PROJECT_DIR:~0,-1!"
title AI kcMedical Research  ^|  CLI  ^|  %PROJECT_DIR%
cd /d "%PROJECT_DIR%"

:: ─────────────────────────────────────────────────────────────────────────────
::  1.  HEADER
:: ─────────────────────────────────────────────────────────────────────────────
call :print_header "CLI Launcher"

:: ─────────────────────────────────────────────────────────────────────────────
::  2.  DETECT / SET CLI_THEME  (persisted per-user, no admin needed)
:: ─────────────────────────────────────────────────────────────────────────────
call :detect_theme

:: ─────────────────────────────────────────────────────────────────────────────
::  3.  LOCATE PYTHON  (.venv first, then system PATH)
:: ─────────────────────────────────────────────────────────────────────────────
call :locate_python
if !errorlevel! neq 0 ( pause & exit /b 1 )

:: ─────────────────────────────────────────────────────────────────────────────
::  4.  FIRST-RUN SETUP  (only when .venv is missing)
:: ─────────────────────────────────────────────────────────────────────────────
if "!HAVE_VENV!"=="0" (
    call :first_run_setup
    if !errorlevel! neq 0 (
        call :box_error "Setup failed — see messages above."
        pause & exit /b 1
    )
    set "PYTHON_EXE=%PROJECT_DIR%\.venv\Scripts\python.exe"
)

:: ─────────────────────────────────────────────────────────────────────────────
::  5.  ENSURE colorama  (silent, one-liner)
:: ─────────────────────────────────────────────────────────────────────────────
"!PYTHON_EXE!" -c "import colorama" >nul 2>&1
if !errorlevel! neq 0 (
    echo   [setup] Installing colorama...
    "!PROJECT_DIR!\.venv\Scripts\pip.exe" install colorama --quiet
)

:: ─────────────────────────────────────────────────────────────────────────────
::  6.  LAUNCH INFO + PYTHON LAUNCHER
:: ─────────────────────────────────────────────────────────────────────────────
echo.
echo   ============================================================
echo    Theme    : !CLI_THEME!
echo    Python   : !PYTHON_EXE!
echo    venv     : %PROJECT_DIR%\.venv
echo   ------------------------------------------------------------
echo    TIP: Select option 8 in the menu to launch Pipeline UI
echo    TIP: Alt+Tab switches between the CLI and browser
echo   ============================================================
echo.

"!PYTHON_EXE!" "%PROJECT_DIR%\launcher.py"
set "EXIT_CODE=!errorlevel!"

:: ─────────────────────────────────────────────────────────────────────────────
::  7.  EXIT
:: ─────────────────────────────────────────────────────────────────────────────
if !EXIT_CODE! neq 0 (
    echo.
    call :box_error "Launcher exited with code !EXIT_CODE! — check logs above."
    pause
)
exit /b !EXIT_CODE!


:: =============================================================================
::  S U B R O U T I N E S   (shared — identical in both .bat files)
:: =============================================================================

:: ─────────────────────────────────────────────────────────────────────────────
:print_header  <subtitle>
:: ─────────────────────────────────────────────────────────────────────────────
echo.
echo   ============================================================
echo    AI kcMedical Research   ^|  %~1  ^|  v2.3.0
echo   ============================================================
echo    Project : %PROJECT_DIR%
echo   ============================================================
echo.
goto :eof


:: ─────────────────────────────────────────────────────────────────────────────
:detect_theme
::  Read CLI_THEME from HKCU registry (persistent across sessions).
::  If absent, ask the user once and save with SETX (user scope, no admin).
:: ─────────────────────────────────────────────────────────────────────────────
for /f "tokens=2*" %%A in (
    'reg query "HKCU\Environment" /v CLI_THEME 2^>nul'
) do set "CLI_THEME_STORED=%%B"

if defined CLI_THEME_STORED (
    set "CLI_THEME=!CLI_THEME_STORED!"
    goto :eof
)

echo.
echo   ============================================================
echo    FIRST-TIME THEME SETUP
echo   ============================================================
echo.
echo    What is the background colour of YOUR terminal window?
echo.
echo      D  =  Dark background   ^(black / dark grey — most common^)
echo      L  =  Light background  ^(white / light grey CMD window^)
echo.
echo    You will only be asked this ONCE.  To change later, run:
echo      setx CLI_THEME dark    ^(or light^)
echo.
set /p "THEME_CHOICE=   Enter D or L  [press Enter for Dark]:  "

if /i "!THEME_CHOICE!"=="L" ( set "CLI_THEME=light" ) else ( set "CLI_THEME=dark" )

setx CLI_THEME "!CLI_THEME!" >nul
echo.
echo   [theme] CLI_THEME=!CLI_THEME! saved to your user account.
echo.
goto :eof


:: ─────────────────────────────────────────────────────────────────────────────
:locate_python
::  Sets PYTHON_EXE and HAVE_VENV.
::  Returns errorlevel 1 if no Python found anywhere.
:: ─────────────────────────────────────────────────────────────────────────────
set "VENV_PYTHON=%PROJECT_DIR%\.venv\Scripts\python.exe"

if exist "%VENV_PYTHON%" (
    set "PYTHON_EXE=%VENV_PYTHON%"
    set "HAVE_VENV=1"
    goto :eof
)

set "HAVE_VENV=0"
where python >nul 2>&1
if !errorlevel! neq 0 (
    call :box_error "Python not found.  Install Python 3.11+ from python.org"
    exit /b 1
)
for /f "delims=" %%P in ('where python') do (
    set "PYTHON_EXE=%%P"
    goto :locate_python_done
)
:locate_python_done
goto :eof


:: ─────────────────────────────────────────────────────────────────────────────
:first_run_setup
::  Create .venv + install requirements.txt.
::  Only runs when .venv\Scripts\python.exe does not exist.
:: ─────────────────────────────────────────────────────────────────────────────
echo.
echo   ============================================================
echo    FIRST-RUN SETUP  (this only happens once per machine)
echo   ============================================================
echo.

if not exist "%PROJECT_DIR%\requirements.txt" (
    call :box_error "requirements.txt not found in %PROJECT_DIR%"
    exit /b 1
)

echo   [1/3]  Creating virtual environment...
"!PYTHON_EXE!" -m venv "%PROJECT_DIR%\.venv"
if !errorlevel! neq 0 ( call :box_error "Failed to create .venv" & exit /b 1 )
echo          Done.
echo.

echo   [2/3]  Upgrading pip...
"%PROJECT_DIR%\.venv\Scripts\pip.exe" install --upgrade pip --quiet
echo          Done.
echo.

echo   [3/3]  Installing requirements.txt  (may take a few minutes)...
echo.
"%PROJECT_DIR%\.venv\Scripts\pip.exe" install -r "%PROJECT_DIR%\requirements.txt"
if !errorlevel! neq 0 (
    call :box_error "pip install failed — check internet connection."
    exit /b 1
)

echo.
echo   ============================================================
echo    Setup complete!  Launching AI kcMedical Research...
echo   ============================================================
echo.
goto :eof


:: ─────────────────────────────────────────────────────────────────────────────
:box_error  <message>
:: ─────────────────────────────────────────────────────────────────────────────
echo.
echo   ************************************************************
echo    ERROR: %~1
echo   ************************************************************
echo.
goto :eof
