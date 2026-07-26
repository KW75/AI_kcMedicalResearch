@echo off
setlocal EnableDelayedExpansion
title AI kcMedical Research - First-Run Setup

:: ── locate the folder this bat lives in ──────────────────────────────────────
set "PROJECT_DIR=%~dp0"
if "%PROJECT_DIR:~-1%"=="\" set "PROJECT_DIR=%PROJECT_DIR:~0,-1%"

echo.
echo  ================================================
echo    AI kcMedical Research - Setup
echo    Project: %PROJECT_DIR%
echo  ================================================
echo.

:: ── 1. Check Python ───────────────────────────────────────────────────────────
echo [1/6] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo  ERROR: Python not found on PATH.
    echo  Download from https://www.python.org/downloads/
    echo  Make sure to tick "Add Python to PATH" during install.
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo  Found: %%v

:: ── 2. Check pip ──────────────────────────────────────────────────────────────
echo.
echo [2/6] Checking pip...
python -m pip --version >nul 2>&1
if errorlevel 1 (
    echo  ERROR: pip not available. Run: python -m ensurepip --upgrade
    pause
    exit /b 1
)
echo  pip OK.

:: ── 3. Create virtual environment if missing ──────────────────────────────────
echo.
echo [3/6] Virtual environment...
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

:: ── 4. Install / upgrade dependencies ─────────────────────────────────────────
echo.
echo [4/6] Installing dependencies from requirements.txt...
call "%PROJECT_DIR%\.venv\Scripts\activate.bat"
python -m pip install --upgrade pip --quiet
python -m pip install -r "%PROJECT_DIR%\requirements.txt"
if errorlevel 1 (
    echo  ERROR: pip install failed. Check requirements.txt and your internet connection.
    pause
    exit /b 1
)
echo  Dependencies installed.

:: ── 5. Create .streamlit/config.toml if missing ───────────────────────────────
echo.
echo [5/6] Checking Streamlit config...
if not exist "%PROJECT_DIR%\.streamlit" (
    mkdir "%PROJECT_DIR%\.streamlit"
)
if not exist "%PROJECT_DIR%\.streamlit\config.toml" (
    echo [theme]> "%PROJECT_DIR%\.streamlit\config.toml"
    echo baseFontSize = 18>> "%PROJECT_DIR%\.streamlit\config.toml"
    echo  Created .streamlit\config.toml with baseFontSize = 18.
) else (
    echo  .streamlit\config.toml already exists.
)

:: ── 6. Check .env ─────────────────────────────────────────────────────────────
echo.
echo [6/6] Checking .env file...
if exist "%PROJECT_DIR%\.env" (
    echo  .env found.
) else (
    echo  WARNING: .env not found.
    echo  Copy your .env file to: %PROJECT_DIR%\.env
    echo  Minimum required for Ollama (local):
    echo    OLLAMA_URL=http://localhost:11434
    echo    OLLAMA_MODEL=llama3
    echo.
    echo  For cloud providers add the relevant API keys:
    echo    OPENAI_API_KEY=sk-...
    echo    ANTHROPIC_API_KEY=sk-ant-...
    echo    DEEPSEEK_API_KEY=...
    echo    GROQ_API_KEY=...
    echo    QWEN_API_KEY=...
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
