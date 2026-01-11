@echo off
REM ORBIT Frontend Launcher
REM Starts Vite dev server for React UI

echo ================================================
echo   ORBIT Frontend - Luna UI
echo ================================================
echo.

cd /d "%~dp0frontend"

REM Check if node_modules exists
if not exist "node_modules\" (
    echo node_modules not found, installing dependencies...
    call npm install
    if %ERRORLEVEL% NEQ 0 (
        echo ERROR: npm install failed
        pause
        exit /b 1
    )
)

echo Starting Vite dev server...
echo.

REM Start dev server
call npm run dev

REM Keep window open on error
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Frontend stopped with error code %ERRORLEVEL%
    pause
)
