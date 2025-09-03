#!/bin/bash

echo "🚀 Starting DAVGPT in production mode..."

# Activate virtual environment
source venv/bin/activate

# Run with gunicorn
echo "🌐 Starting with Gunicorn on port 5000"
gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 120 wsgi:app
