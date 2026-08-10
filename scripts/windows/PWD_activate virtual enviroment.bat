@echo off
:: =============================================================================
::  PWD_activate virtual enviroment.bat
::  Activate the Python virtual environment from anywhere
:: =============================================================================

:: Navigate to project root (2 levels up from scripts/windows/)
cd /d "%~dp0\..\.."

:: Activate the virtual environment
PowerShell.exe -NoExit -ExecutionPolicy Bypass -Command "& '.venv\Scripts\Activate.ps1'"

pause