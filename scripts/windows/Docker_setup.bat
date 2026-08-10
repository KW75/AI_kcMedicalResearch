@echo off
setlocal EnableDelayedExpansion

:: =============================================================================
::  AI kcMedicalResearch - Complete Setup & Run
::  v1.0.0  |  One-click setup with Docker
:: =============================================================================

title AI kcMedicalResearch Setup
color 0A

:: ─────────────────────────────────────────────────────────────────────────────
::  1.  WELCOME
:: ─────────────────────────────────────────────────────────────────────────────
cls
echo.
echo   ============================================================
echo    AI kcMedicalResearch - Setup & Run
echo   ============================================================
echo.
echo   This will:
echo   1. Check if Docker is installed
echo   2. Let you choose C: or D: drive
echo   3. Clone the repository (if needed)
echo   4. Create .env file (if missing)
echo   5. Build Docker image (first time only)
echo   6. Run the app
echo.
echo   ============================================================
echo.

:: ─────────────────────────────────────────────────────────────────────────────
::  2.  CHECK DOCKER
:: ─────────────────────────────────────────────────────────────────────────────
echo   [CHECK] Checking Docker...
where docker >nul 2>&1
if errorlevel 1 (
    echo   [ERROR] Docker not found!
    echo.
    echo   Please install Docker Desktop:
    echo   https://www.docker.com/products/docker-desktop
    echo.
    pause
    exit /b 1
)

:: Check Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo   [ERROR] Docker is not running!
    echo.
    echo   Please start Docker Desktop first.
    echo   Look for the Docker icon in your system tray.
    echo.
    pause
    exit /b 1
)
echo   [OK] Docker is running.
echo.

:: ─────────────────────────────────────────────────────────────────────────────
::  3.  CHOOSE DRIVE
:: ─────────────────────────────────────────────────────────────────────────────
echo   ============================================================
echo    Where would you like to install?
echo   ============================================================
echo.
echo     [1]  C:\
echo     [2]  D:\
echo.
set /p "DRIVE_CHOICE=   Enter 1 or 2:  "

if "!DRIVE_CHOICE!"=="1" (
    set "INSTALL_DRIVE=C:"
    echo.
    echo   Installing to C:\
) else if "!DRIVE_CHOICE!"=="2" (
    set "INSTALL_DRIVE=D:"
    echo.
    echo   Installing to D:\
) else (
    echo.
    echo   [ERROR] Invalid choice. Please run again.
    pause
    exit /b 1
)

:: ─────────────────────────────────────────────────────────────────────────────
::  4.  NAVIGATE TO DRIVE
:: ─────────────────────────────────────────────────────────────────────────────
!INSTALL_DRIVE!
cd \

:: ─────────────────────────────────────────────────────────────────────────────
::  5.  CHECK IF ALREADY INSTALLED
:: ─────────────────────────────────────────────────────────────────────────────
if exist "!INSTALL_DRIVE!\AI_kcMedicalResearch" (
    echo.
    echo   [INFO] AI_kcMedicalResearch already exists.
    echo.
    echo   What would you like to do?
    echo.
    echo     [1]  Update (git pull) and run
    echo     [2]  Remove and reinstall fresh
    echo     [3]  Exit and do nothing
    echo.
    set /p "EXISTING_ACTION=   Enter 1, 2, or 3:  "

    if "!EXISTING_ACTION!"=="3" (
        echo.
        echo   Exiting...
        pause
        exit /b 0
    )

    if "!EXISTING_ACTION!"=="2" (
        echo.
        echo   Removing existing installation...
        rmdir /s /q "!INSTALL_DRIVE!\AI_kcMedicalResearch"
        echo   Removed.
        echo.
    ) else (
        echo.
        echo   Updating existing installation...
        cd "!INSTALL_DRIVE!\AI_kcMedicalResearch"
        git pull
        echo   Update complete.
        echo.
        goto :RUN_APP
    )
)

:: ─────────────────────────────────────────────────────────────────────────────
::  6.  CLONE REPOSITORY
:: ─────────────────────────────────────────────────────────────────────────────
echo.
echo   [CLONE] Cloning repository to !INSTALL_DRIVE!\AI_kcMedicalResearch...
echo.
git clone https://github.com/KW75/AI_kcMedicalResearch.git
if errorlevel 1 (
    echo.
    echo   [ERROR] Failed to clone repository.
    echo   Please check your internet connection.
    echo.
    pause
    exit /b 1
)
echo.
echo   [OK] Repository cloned successfully.
echo.

:: ─────────────────────────────────────────────────────────────────────────────
::  7.  ENTER DIRECTORY
:: ─────────────────────────────────────────────────────────────────────────────
cd "!INSTALL_DRIVE!\AI_kcMedicalResearch"

:: ─────────────────────────────────────────────────────────────────────────────
::  8.  CREATE .env FILE
:: ─────────────────────────────────────────────────────────────────────────────
if not exist ".env" (
    echo.
    echo   [CONFIG] Creating .env file...

    (
        echo # AI kcMedicalResearch - API Keys
        echo # ================================
        echo.
        echo # Local Ollama
        echo OLLAMA_HOST=http://localhost:11434
        echo OLLAMA_MODEL=llama3.2
        echo.
        echo # Cloud Providers - Add your API keys below
        echo # Get free key from: https://console.groq.com
        echo GROQ_API_KEY=
        echo.
        echo # Get key from: https://dashscope.aliyuncs.com
        echo DASHSCOPE_API_KEY=
        echo DASHSCOPE_BASE_URL=https://ws-uv5pi4kkqbrg1vpe.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1
        echo DASHSCOPE_ANTHROPIC_URL=https://ws-uv5pi4kkqbrg1vpe.ap-southeast-1.maas.aliyuncs.com/apps/anthropic
        echo.
        echo # Optional: OpenAI, Anthropic, DeepSeek
        echo # OPENAI_API_KEY=
        echo # ANTHROPIC_API_KEY=
        echo # DEEPSEEK_API_KEY=
    ) > .env

    echo.
    echo   [CONFIG] .env file created.
    echo   IMPORTANT: Edit .env to add your API keys before running!
    echo.

    :: Ask if they want to edit .env now
    echo   Would you like to edit .env now?
    echo     [Y] Yes - Open in Notepad
    echo     [N] No - I'll edit later
    echo.
    set /p "EDIT_ENV=   Enter Y or N:  "

    if /i "!EDIT_ENV!"=="Y" (
        echo.
        echo   Opening .env in Notepad...
        echo   Add your API keys, save, and close Notepad.
        echo.
        notepad .env
        echo.
        echo   [OK] .env saved.
    ) else (
        echo.
        echo   [INFO] Remember to edit .env before running!
        echo   Just open !INSTALL_DRIVE!\AI_kcMedicalResearch\.env
        echo.
    )
) else (
    echo.
    echo   [CONFIG] .env already exists. Keeping existing.
    echo.
)

:: ─────────────────────────────────────────────────────────────────────────────
::  9.  CREATE INPUT/OUTPUT DIRECTORIES
:: ─────────────────────────────────────────────────────────────────────────────
echo.
echo   [SETUP] Creating input/output directories...
mkdir input\coding 2>nul
mkdir input\writing 2>nul
mkdir input\appraisal 2>nul
mkdir input\search 2>nul
mkdir input\rct_search 2>nul
mkdir input\sr 2>nul
mkdir output\coding 2>nul
mkdir output\writing 2>nul
mkdir output\appraisal 2>nul
mkdir output\search 2>nul
mkdir output\rct_search 2>nul
mkdir output\sr 2>nul
mkdir reports 2>nul
mkdir data 2>nul
echo   [OK] Directories created.
echo.

:: ─────────────────────────────────────────────────────────────────────────────
::  10. BUILD DOCKER IMAGE (if not exists)
:: ─────────────────────────────────────────────────────────────────────────────
echo.
echo   [DOCKER] Checking for existing image...
docker images --format "{{.Repository}}" | findstr /i "ai-kcmedicalresearch" >nul
if errorlevel 1 (
    echo.
    echo   [DOCKER] Building Docker image (first time only)...
    echo   This may take 5-10 minutes...
    echo.
    docker build -t ai-kcmedicalresearch .
    if errorlevel 1 (
        echo.
        echo   [ERROR] Failed to build Docker image.
        pause
        exit /b 1
    )
    echo.
    echo   [OK] Docker image built successfully.
    echo.
) else (
    echo.
    echo   [DOCKER] Image already exists. Skipping build.
    echo.
)

:: ─────────────────────────────────────────────────────────────────────────────
::  11. RUN THE APP
:: ─────────────────────────────────────────────────────────────────────────────
:RUN_APP
echo.
echo   ============================================================
echo    SETUP COMPLETE!
echo   ============================================================
echo.
echo   Installation location: !INSTALL_DRIVE!\AI_kcMedicalResearch
echo.
echo   Choose how to run:
echo.
echo     [1]  CLI Mode  (interactive menu)
echo     [2]  UI Mode   (Streamlit web interface)
echo.
set /p "RUN_CHOICE=   Enter 1 or 2:  "

echo.
echo   ============================================================
echo    Starting AI kcMedicalResearch...
echo   ============================================================
echo.

if "!RUN_CHOICE!"=="2" (
    echo   UI Mode starting...
    echo   Browser will open at: http://localhost:8501
    echo   Press Ctrl+C to stop
    echo.
    start http://localhost:8501

    docker run -it --rm ^
        -p 8501:8501 ^
        -v "!INSTALL_DRIVE!\AI_kcMedicalResearch\input:/app/input" ^
        -v "!INSTALL_DRIVE!\AI_kcMedicalResearch\output:/app/output" ^
        -v "!INSTALL_DRIVE!\AI_kcMedicalResearch\data:/app/data" ^
        -v "!INSTALL_DRIVE!\AI_kcMedicalResearch\reports:/app/reports" ^
        --env-file .env ^
        --add-host host.docker.internal:host-gateway ^
        ai-kcmedicalresearch ^
        streamlit run src/ui/app.py --server.port=8501 --server.address=0.0.0.0
) else (
    echo   CLI Mode starting...
    echo   Use the menu to select pipeline and provider
    echo.

    docker run -it --rm ^
        -v "!INSTALL_DRIVE!\AI_kcMedicalResearch\input:/app/input" ^
        -v "!INSTALL_DRIVE!\AI_kcMedicalResearch\output:/app/output" ^
        -v "!INSTALL_DRIVE!\AI_kcMedicalResearch\data:/app/data" ^
        -v "!INSTALL_DRIVE!\AI_kcMedicalResearch\reports:/app/reports" ^
        --env-file .env ^
        --add-host host.docker.internal:host-gateway ^
        ai-kcmedicalresearch ^
        python launcher.py
)

echo.
echo   ============================================================
echo    AI kcMedicalResearch stopped.
echo   ============================================================
pause