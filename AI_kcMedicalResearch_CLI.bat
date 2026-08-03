
@echo off
set "PROJECT_DIR=%~dp0"
if "%PROJECT_DIR:~-1%"=="\" set "PROJECT_DIR=%PROJECT_DIR:~0,-1%"
if not exist "%PROJECT_DIR%\.venv\Scripts\python.exe" (
    echo ERROR: .venv not found. Run AI_kcMedicalResearch_setup.bat first.
    pause
    exit /b 1
)
title AI kcMedical Research
cd /d "%PROJECT_DIR%"
echo.
echo ============================================================
echo   AI kcMedicalResearch - CLI Launcher
echo ============================================================
echo.
echo   Type '8' and press Enter to launch the Pipeline UI
echo   Alt+Tab to switch between CLI and UI browser
echo ============================================================
echo.
"%PROJECT_DIR%\.venv\Scripts\python.exe" "%PROJECT_DIR%\launcher.py"
exit /b 0