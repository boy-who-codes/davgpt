#!/bin/bash

echo "🚀 Deploying D.A.V GPT to Vercel..."

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "📦 Installing Vercel CLI..."
    npm install -g vercel
fi

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️ .env file not found. Creating from example..."
    cp .env.example .env
    echo "Please edit .env file with your configuration before deploying"
    exit 1
fi

# Run initial scraping if knowledge base doesn't exist
if [ ! -f knowledge_base.json ]; then
    echo "🕷️ Running initial data scraping..."
    source venv/bin/activate 2>/dev/null || python3 -m venv venv && source venv/bin/activate
    pip install -r requirements.txt
    python -c "from scraper import DAVScraper; scraper = DAVScraper(); scraper.scrape_all()"
fi

# Deploy to Vercel
echo "🌐 Deploying to Vercel..."
vercel --prod

echo "✅ Deployment complete!"
echo ""
echo "📋 Next steps:"
echo "1. Set environment variables in Vercel dashboard:"
echo "   - WEBSITE_URL"
echo "   - GEMINI_API_KEY"
echo "   - MAIL_USERNAME"
echo "   - MAIL_PASSWORD"
echo "   - DATABASE_URL"
echo ""
echo "2. Your D.A.V GPT is now live on Vercel!"
