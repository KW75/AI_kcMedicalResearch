@echo off
setlocal EnableDelayedExpansion
title AI kcMedical Research

:: ── locate project folder (works from any drive/path) ────────────────────────
set "PROJECT_DIR=%~dp0"
if "%PROJECT_DIR:~-1%"=="\" set "PROJECT_DIR=%PROJECT_DIR:~0,-1%"

:: ── activate virtual environment ─────────────────────────────────────────────
if not exist "%PROJECT_DIR%\.venv\Scripts\activate.bat" (
    echo  ERROR: .venv not found. Run AI_kcMedicalResearch_setup.bat first.
    pause
    exit /b 1
)
call "%PROJECT_DIR%\.venv\Scripts\activate.bat"

:: ── change to project directory ──────────────────────────────────────────────
cd /d "%PROJECT_DIR%"

:: ── clear screen ─────────────────────────────────────────────────────────────
cls

:: ── logo ─────────────────────────────────────────────────────────────────────
echo.
echo  +=======================================================+
echo  ^|                                                       ^|
echo  ^|        ###    ###                                     ^|
echo  ^|       ## ##  ## ##                                    ^|
echo  ^|      ##  ## ##  ##   AI kcMedical Research           ^|
echo  ^|     #########  ##   Version 2.1.0                   ^|
echo  ^|    ##      ##  ##   258 tests passing                ^|
echo  ^|   ##       ## ##                                     ^|
echo  ^|  ##         ###    Medical AI  ^|  Research  ^|  Review ^|
echo  ^|                                                       ^|
echo  +=======================================================+
echo.
echo   Modes:  coding  writing  appraisal  search  rct_search  sr
echo   Providers: ollama (default)  openai  anthropic  deepseek  groq
echo.
echo   For help:  python src\main.py --help-guide
echo.

:: ── pause so user can read the logo ──────────────────────────────────────────
pause

:: ── launch ───────────────────────────────────────────────────────────────────
python src\main.py %*

:: ── keep window open after exit ──────────────────────────────────────────────
echo.
echo  Session ended.
pause
endlocal
