@echo off
set "PROJECT_DIR=%~dp0"
if "%PROJECT_DIR:~-1%"=="\" set "PROJECT_DIR=%PROJECT_DIR:~0,-1%"
if not exist "%PROJECT_DIR%\.venv\Scripts\python.exe" (
    echo ERROR: .venv not found. Run AI_kcMedicalResearch_setup.bat first.
    pause
    exit /b 1
)
title AI kcMedical Research
"%PROJECT_DIR%\.venv\Scripts\python.exe" "%PROJECT_DIR%\launcher.py"
exit /b 0
