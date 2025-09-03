#!/bin/bash

echo "🚀 Setting up DAVGPT..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
python -m pip install --upgrade pip

# Install requirements
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "🔑 Creating .env file..."
    cp .env.example .env
    echo "Please edit .env file with your API keys and configuration"
fi

# Run initial scraping
echo "🕷️ Running initial data scraping..."
python -c "from scraper import DAVScraper; scraper = DAVScraper(); scraper.scrape_all()"

echo "✅ Setup complete! Run './run.sh' to start the application."
