@echo off
:: =============================================================================
::  activate_venv.bat
::  v2.4.6  |  Open a PowerShell prompt with the project virtualenv active
::
::  Location: scripts\windows\   (resolves project root two levels up)
:: =============================================================================
setlocal EnableDelayedExpansion

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

set "ACTIVATE=!PROJECT_DIR!\.venv\Scripts\Activate.ps1"

if not exist "!ACTIVATE!" (
    echo.
    echo   ************************************************************
    echo    ERROR: .venv not found.
    echo   ************************************************************
    echo.
    echo    Expected : !ACTIVATE!
    echo.
    echo    Run one of the launchers first to create it:
    echo      scripts\windows\AI_kcMedicalResearch_CLI.bat
    echo.
    pause & exit /b 1
)

title AI kcMedical Research - venv - !PROJECT_DIR!
cd /d "!PROJECT_DIR!"

echo.
echo   ============================================================
echo    AI kcMedical Research  ^|  venv shell  ^|  v2.4.6
echo   ============================================================
echo    Project : !PROJECT_DIR!
echo   ============================================================
echo.

:: -NoExit keeps the PowerShell session open. Activate, then confirm which
:: interpreter is actually in use - a "(.venv)" prompt alone does not guarantee
:: python resolves inside the venv if PATH is unusual.
PowerShell.exe -NoExit -NoLogo -ExecutionPolicy RemoteSigned -Command ^
  "& '!ACTIVATE!'; Write-Host ''; Write-Host 'python  : ' -NoNewline; python -c 'import sys; print(sys.executable)'; Write-Host 'version : ' -NoNewline; python -c 'import sys; print(sys.version.split()[0])'; Write-Host ''"

exit /b 0
