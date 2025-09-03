@echo off
echo 🤖 Starting DAVGPT...

REM Check if virtual environment exists
if not exist venv (
    echo ❌ Virtual environment not found. Please run setup.bat first.
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Check if .env exists
if not exist .env (
    echo ⚠️ .env file not found. Creating from example...
    copy .env.example .env
    echo Please edit .env file with your configuration
)

REM Start the application
echo 🚀 Starting DAVGPT on http://localhost:5000
echo Press Ctrl+C to stop the server
python app.py

pause
