@echo off
:: =============================================================================
::  activate_venv.bat
::  (version parsed live from SOURCE_CODE/main.py - see banner below)
::  Open a PowerShell prompt with the project virtualenv active
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
set "MAIN_PY=!PROJECT_DIR!\SOURCE_CODE\main.py"

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

:: Banner is printed by PowerShell after it parses VERSION live from
:: main.py. Previously the version was hardcoded in an `echo` block
:: here and drifted three versions out of date between v2.4.6 and
:: v2.4.12 - the same failure shape as #43 (launcher banner) and #53
:: (test-count claim), fixed the same way: parse from a single source
:: of truth, do not display anything the file cannot re-verify.
:: -NoExit keeps the PowerShell session open; the interpreter-check
:: lines after `& $ACTIVATE` confirm which python resolves inside the
:: venv - a "(.venv)" prompt alone does not guarantee it.
PowerShell.exe -NoExit -NoLogo -ExecutionPolicy RemoteSigned -Command ^
  "$mainPy = '!MAIN_PY!';" ^
  "$v = 'unknown';" ^
  "if (Test-Path $mainPy) {" ^
  "  $match = Select-String -Path $mainPy -Pattern '^VERSION\s*=\s*[\"''](.+?)[\"'']' | Select-Object -First 1;" ^
  "  if ($match) { $v = $match.Matches[0].Groups[1].Value }" ^
  "}" ^
  "Write-Host '';" ^
  "Write-Host '  ============================================================';" ^
  "Write-Host ('   AI kcMedical Research  |  venv shell  |  v' + $v);" ^
  "Write-Host '  ============================================================';" ^
  "Write-Host ('   Project : ' + '!PROJECT_DIR!');" ^
  "Write-Host '  ============================================================';" ^
  "Write-Host '';" ^
  "& '!ACTIVATE!';" ^
  "Write-Host '';" ^
  "Write-Host 'python  : ' -NoNewline; python -c 'import sys; print(sys.executable)';" ^
  "Write-Host 'version : ' -NoNewline; python -c 'import sys; print(sys.version.split()[0])';" ^
  "Write-Host ''"

exit /b 0
