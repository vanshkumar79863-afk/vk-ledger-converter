@echo off
REM VK LEDGUR CONVERTER - Run Script for Windows

echo.
echo =========================================
echo VK LEDGUR CONVERTER - Flask Application
echo =========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please download Python from https://www.python.org/
    pause
    exit /b 1
)

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -q -r requirements.txt

REM Run the Flask app
echo.
echo =========================================
echo Starting VK LEDGUR CONVERTER...
echo =========================================
echo.
echo Visit: http://localhost:5000
echo.
echo Press CTRL+C to stop the server
echo.

python app.py

pause
