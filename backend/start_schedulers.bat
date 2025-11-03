@echo off
REM Windows Batch Script to Start All Schedulers
REM This script starts all data collectors automatically

echo ============================================
echo Starting X Fin Data Collectors
echo ============================================

cd /d "%~dp0"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.7+ and add it to PATH
    pause
    exit /b 1
)

REM Start the master scheduler
echo Starting all schedulers...
python start_all_schedulers.py

pause

