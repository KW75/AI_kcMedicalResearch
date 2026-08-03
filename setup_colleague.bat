@echo off
echo ============================================================
echo  AI kcMedicalResearch - Colleague Setup
echo ============================================================
echo.

:: Check for Git
where git >nul 2>&1
if errorlevel 1 (
    echo [X] Git not found. Please install Git first.
    echo     https://git-scm.com/download/win
    pause
    exit /b 1
)

:: Check for Python
where python >nul 2>&1
if errorlevel 1 (
    echo [X] Python not found. Please install Python first.
    echo     https://python.org/downloads
    pause
    exit /b 1
)

:: Clone if not exists
if not exist "AI_kcMedicalResearch" (
    echo [Downloading] Cloning repository...
    git clone https://github.com/KW75/AI_kcMedicalResearch.git
    cd AI_kcMedicalResearch
) else (
    cd AI_kcMedicalResearch
    echo [Update] Pulling latest changes...
    git pull
)

:: Setup Python virtual environment
echo [Python] Setting up Python environment...
if exist ".venv" (
    echo [Python] Virtual environment already exists.
) else (
    python -m venv .venv
    if errorlevel 1 (
        echo [X] Failed to create virtual environment.
        pause
        exit /b 1
    )
)

:: Install dependencies
echo [Python] Installing dependencies...
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip --quiet
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo [X] Failed to install dependencies.
    pause
    exit /b 1
)

:: Create .env template
if not exist ".env" (
    echo [Config] Creating .env file...
    echo # AI kcMedicalResearch - API Keys > .env
    echo # =================================== >> .env
    echo. >> .env
    echo # Ollama (local - free, no key needed) >> .env
    echo OLLAMA_HOST=http://localhost:11434 >> .env
    echo OLLAMA_MODEL=llama3.2 >> .env
    echo. >> .env
    echo # Cloud Providers - Add your API keys below >> .env
    echo # Get free key from: https://console.groq.com >> .env
    echo GROQ_API_KEY= >> .env
    echo. >> .env
    echo # Get key from: https://dashscope.aliyuncs.com >> .env
    echo DASHSCOPE_API_KEY= >> .env
    echo DASHSCOPE_BASE_URL=https://ws-uv5pi4kkqbrg1vpe.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1 >> .env
    echo DASHSCOPE_ANTHROPIC_URL=https://ws-uv5pi4kkqbrg1vpe.ap-southeast-1.maas.aliyuncs.com/apps/anthropic >> .env
    echo. >> .env
    echo # Optional: OpenAI, Anthropic, DeepSeek >> .env
    echo # OPENAI_API_KEY= >> .env
    echo # ANTHROPIC_API_KEY= >> .env
    echo # DEEPSEEK_API_KEY= >> .env
) else (
    echo [Config] .env file already exists. Keeping existing.
)

echo.
echo ============================================================
echo [SUCCESS] Setup complete!
echo.
echo ============================================================
echo  WAYS TO RUN THE APP
echo ============================================================
echo.
echo   OPTION 1 - LOCAL (Your computer)
echo   --------------------------------
echo   1. Edit .env and paste your API keys
echo   2. Run: AI_kcMedicalResearch_CLI.bat
echo   3. Select provider and mode
echo.
echo   OPTION 2 - WEB (Render.com - no setup needed)
echo   --------------------------------------------
echo   Just open: https://ai-kcmedicalresearch.onrender.com
echo   Enter your API keys in the sidebar
echo.
echo ============================================================
echo  GET FREE API KEYS
echo ============================================================
echo   * Ollama (local) - Free, no key needed
echo   * Groq: https://console.groq.com
echo   * Qwen: https://dashscope.aliyuncs.com
echo   * OpenAI: https://platform.openai.com/api-keys
echo.
echo ============================================================
echo  QUICK START
echo ============================================================
echo   # Run CLI
echo   .\AI_kcMedicalResearch_CLI.bat
echo.
echo   # Run UI
echo   .\AI_kcMedicalResearch_UI.bat
echo.
echo   # Run tests
echo   .venv\Scripts\pytest
echo.
echo ============================================================
pause