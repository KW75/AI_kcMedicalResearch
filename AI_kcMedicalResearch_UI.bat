@echo off
set "PROJECT_DIR=%~dp0"
if "%PROJECT_DIR:~-1%"=="\" set "PROJECT_DIR=%PROJECT_DIR:~0,-1%"
if not exist "%PROJECT_DIR%\.venv\Scripts\python.exe" (
    echo ERROR: .venv not found. Run AI_kcMedicalResearch_setup.bat first.
    pause
    exit /b 1
)
if not exist "%PROJECT_DIR%\src\ui\app.py" (
    echo ERROR: UI app not found at src\ui\app.py
    pause
    exit /b 1
)
title AI kcMedicalResearch UI
cd /d "%PROJECT_DIR%"
echo.
echo ============================================================
echo   AI kcMedicalResearch - Pipeline UI
echo ============================================================
echo.
echo   Launching Streamlit UI...
echo   Browser will open at http://localhost:8501
echo.
echo   =========================================================
echo   REMINDER: After pipeline runs finish in the terminal:
echo   Press Alt+Tab to return to the UI browser tab
echo   =========================================================
echo.
echo   Press Ctrl+C in this window to stop the UI server
echo ============================================================
echo.
"%PROJECT_DIR%\.venv\Scripts\python.exe" -m streamlit run "%PROJECT_DIR%\src\ui\app.py" --server.runOnSave false
pause
exit /b 0