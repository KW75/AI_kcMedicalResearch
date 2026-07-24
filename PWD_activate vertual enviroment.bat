@echo off
cd /d "%~dp0"
PowerShell.exe -NoExit -ExecutionPolicy Bypass -Command "& '.venv\Scripts\Activate.ps1'"
pause





