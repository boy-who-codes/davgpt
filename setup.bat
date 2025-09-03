@echo off
echo 🚀 Setting up DAVGPT...

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed. Please install Python 3.8+ first.
    pause
    exit /b 1
)

REM Create virtual environment
echo 📦 Creating virtual environment...
python -m venv venv

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo ⬆️ Upgrading pip...
python -m pip install --upgrade pip

REM Install requirements
echo 📚 Installing dependencies...
pip install -r requirements.txt

REM Create .env file if it doesn't exist
if not exist .env (
    echo 🔑 Creating .env file...
    copy .env.example .env
    echo Please edit .env file with your API keys and configuration
)

REM Database setup
echo 🗄️ Setting up database...
if exist davgpt.db (
    echo Database already exists.
    set /p choice="Do you want to create a new database? This will delete existing data. (y/N): "
    if /i "%choice%"=="y" (
        del davgpt.db
        echo Creating new database...
        python -c "from app import app, db; app.app_context().push(); db.create_all(); print('✅ New database created')"
    ) else (
        echo Using existing database.
    )
) else (
    echo Creating new database...
    python -c "from app import app, db; app.app_context().push(); db.create_all(); print('✅ Database created')"
)

REM Run initial scraping
echo 🕷️ Running initial data scraping...
python -c "from scraper import DAVScraper; scraper = DAVScraper(); scraper.scrape_all()"

echo ✅ Setup complete! Run 'run.bat' to start the application.
pause
