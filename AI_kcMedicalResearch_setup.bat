@echo off
setlocal EnableDelayedExpansion
title AI kcMedical Research - First-Run Setup

:: ── locate the folder this bat lives in (works from any drive/path) ──────────
set "PROJECT_DIR=%~dp0"
if "%PROJECT_DIR:~-1%"=="\" set "PROJECT_DIR=%PROJECT_DIR:~0,-1%"

echo.
echo  ================================================
echo    AI kcMedical Research - Setup
echo    Project: %PROJECT_DIR%
echo  ================================================
echo.

:: ── 1. Check Python ───────────────────────────────────────────────────────────
echo [1/5] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo  ERROR: Python not found on PATH.
    echo  Download from https://www.python.org/downloads/
    echo  Make sure to tick "Add Python to PATH" during install.
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo  Found: %%v

:: ── 2. Check pip ─────────────────────────────────────────────────────────────
echo.
echo [2/5] Checking pip...
python -m pip --version >nul 2>&1
if errorlevel 1 (
    echo  ERROR: pip not available. Run: python -m ensurepip --upgrade
    pause
    exit /b 1
)
echo  pip OK.

:: ── 3. Create virtual environment if missing ─────────────────────────────────
echo.
echo [3/5] Virtual environment...
if exist "%PROJECT_DIR%\.venv\Scripts\activate.bat" (
    echo  .venv already exists - skipping creation.
) else (
    echo  Creating .venv...
    python -m venv "%PROJECT_DIR%\.venv"
    if errorlevel 1 (
        echo  ERROR: Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo  .venv created.
)

:: ── 4. Install / upgrade dependencies ────────────────────────────────────────
echo.
echo [4/5] Installing dependencies from requirements.txt...
call "%PROJECT_DIR%\.venv\Scripts\activate.bat"
python -m pip install --upgrade pip --quiet
python -m pip install -r "%PROJECT_DIR%\requirements.txt"
if errorlevel 1 (
    echo  ERROR: pip install failed. Check requirements.txt and your internet connection.
    pause
    exit /b 1
)
echo  Dependencies installed.

:: ── 5. Check .env ─────────────────────────────────────────────────────────────
echo.
echo [5/5] Checking .env file...
if exist "%PROJECT_DIR%\.env" (
    echo  .env found.
) else (
    echo  WARNING: .env not found.
    echo  Copy your .env file to: %PROJECT_DIR%\.env
    echo  Minimum required for Ollama (local):
    echo    OLLAMA_URL=http://localhost:11434
    echo    OLLAMA_MODEL=llama3
)

:: ── Done ──────────────────────────────────────────────────────────────────────
echo.
echo  ================================================
echo    Setup complete.
echo    Run AI_kcMedicalResearch_run.bat to start.
echo  ================================================
echo.
pause
endlocal
