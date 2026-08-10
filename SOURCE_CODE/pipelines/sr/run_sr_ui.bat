@echo off
:: =============================================================================
::  run_sr_ui.bat - SR Pipeline UI Launcher
:: =============================================================================
cd /d "%~dp0\..\.."
.venv\Scripts\streamlit.exe run SOURCE_CODE/pipelines/sr/src/ui/app.py
pause