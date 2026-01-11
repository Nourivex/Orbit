@echo off
REM ORBIT Backend Launcher
REM Starts Python backend orchestrator

echo ================================================
echo   ORBIT Backend - Luna Agent
echo ================================================
echo.

cd /d "%~dp0"

REM Activate virtual environment
call backend\venv\Scripts\activate.bat

REM Check if activation succeeded
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to activate virtual environment
    echo Please run: cd backend ^&^& python -m venv venv
    pause
    exit /b 1
)

echo Virtual environment activated
echo Starting ORBIT orchestrator...
echo.

REM Run orchestrator
python main_v2.py

REM Keep window open on error
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: ORBIT stopped with error code %ERRORLEVEL%
    pause
)
