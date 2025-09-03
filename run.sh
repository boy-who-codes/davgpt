#!/bin/bash

echo "🤖 Starting DAVGPT..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run ./setup.sh first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️ .env file not found. Creating from example..."
    cp .env.example .env
    echo "Please edit .env file with your configuration"
fi

# Start the application
echo "🚀 Starting DAVGPT on http://localhost:5000"
echo "Press Ctrl+C to stop the server"
python app.py
