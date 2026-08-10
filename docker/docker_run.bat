@echo off
:: =============================================================================
::  docker_run.bat - AI kcMedicalResearch Docker Launcher
::  v2.0.0  |  Updated for SOURCE_CODE structure
:: =============================================================================
setlocal EnableDelayedExpansion

set "PROJECT_DIR=%~dp0.."
if "!PROJECT_DIR:~-1!"=="\" set "PROJECT_DIR=!PROJECT_DIR:~0,-1!"
cd /d "%PROJECT_DIR%"

echo.
echo ============================================================
echo  AI kcMedicalResearch - Docker Launcher
echo ============================================================
echo.

:: Check Docker
where docker >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker not found!
    echo.
    echo Please install Docker Desktop:
    echo https://www.docker.com/products/docker-desktop
    echo.
    pause
    exit /b 1
)

:: Check Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not running!
    echo.
    echo Please start Docker Desktop first.
    echo (Look for the Docker icon in your system tray)
    echo.
    pause
    exit /b 1
)

:: Check if .env exists - create template if missing
if not exist ".env" (
    echo [Setup] Creating .env file...
    copy .env.template .env
    echo [Setup] .env created. Edit it to add your API keys.
    echo.
)

:: Build image if missing
docker images --format "{{.Repository}}" | findstr /i "ai-kcmedicalresearch" >nul
if errorlevel 1 (
    echo [Setup] Building Docker image (first time only)...
    echo This may take 5-10 minutes...
    echo.
    docker build -f docker/Dockerfile -t ai-kcmedicalresearch .
    if errorlevel 1 (
        echo [ERROR] Failed to build Docker image.
        pause
        exit /b 1
    )
    echo [Setup] Build complete!
    echo.
)

:: Choose run mode
echo ============================================================
echo  Choose how to run:
echo.
echo   1) CLI Mode  (interactive menu)
echo   2) UI Mode   (Streamlit web interface)
echo.
set /p "CHOICE=  Enter 1 or 2:  "

if "!CHOICE!"=="2" (
    echo.
    echo ============================================================
    echo  Starting Streamlit UI...
    echo  Browser will open at: http://localhost:8501
    echo  Press Ctrl+C to stop
    echo ============================================================
    echo.

    start http://localhost:8501

    docker run -it --rm ^
        -p 8501:8501 ^
        -v "%cd%\input:/app/input" ^
        -v "%cd%\output:/app/output" ^
        -v "%cd%\data:/app/data" ^
        -v "%cd%\reports:/app/reports" ^
        --env-file .env ^
        --add-host host.docker.internal:host-gateway ^
        ai-kcmedicalresearch ^
        streamlit run SOURCE_CODE/ui/app.py --server.port=8501 --server.address=0.0.0.0
) else (
    echo.
    echo ============================================================
    echo  Starting CLI Launcher...
    echo  Use the menu to select pipeline and provider
    echo ============================================================
    echo.

    docker run -it --rm ^
        -v "%cd%\input:/app/input" ^
        -v "%cd%\output:/app/output" ^
        -v "%cd%\data:/app/data" ^
        -v "%cd%\reports:/app/reports" ^
        --env-file .env ^
        --add-host host.docker.internal:host-gateway ^
        ai-kcmedicalresearch ^
        python SOURCE_CODE/main.py
)

echo.
echo ============================================================
echo  AI kcMedicalResearch stopped.
echo ============================================================
pause