@echo off
:: =============================================================================
::  docker_quick_start.bat - Quick Docker CLI Launcher
::  v2.0.0  |  Updated for SOURCE_CODE structure
:: =============================================================================

:: Navigate to project root
cd /d "%~dp0.."

:: Quick start - just run the CLI
docker run -it --rm ^
    -v "%cd%\input:/app/input" ^
    -v "%cd%\output:/app/output" ^
    -v "%cd%\data:/app/data" ^
    -v "%cd%\reports:/app/reports" ^
    --env-file .env ^
    --add-host host.docker.internal:host-gateway ^
    ai-kcmedicalresearch ^
    python SOURCE_CODE/main.py