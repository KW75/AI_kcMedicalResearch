@echo off
cd /d "%~dp0.."
.venv\Scripts\streamlit.exe run sr/src/ui/app.py
pause
