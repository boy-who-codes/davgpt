# 🚀 D.A.V GPT Vercel Deployment Guide

## Quick Deploy

### Option 1: Automated Script
```bash
chmod +x deploy-vercel.sh
./deploy-vercel.sh
```

### Option 2: Manual Deploy
```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
vercel --prod
```

## Environment Variables

Set these in your Vercel dashboard under **Settings > Environment Variables**:

| Variable | Description | Example |
|----------|-------------|---------|
| `WEBSITE_URL` | School website to scrape | `http://davkoylanagar.com/` |
| `GEMINI_API_KEY` | Google Gemini API key | `AIzaSy...` |
| `MAIL_USERNAME` | Gmail for notifications | `your-email@gmail.com` |
| `MAIL_PASSWORD` | Gmail app password | `your-app-password` |
| `DATABASE_URL` | SQLite database path | `sqlite:///tmp/davgpt.db` |

## Post-Deployment

1. **Test the deployment** at your Vercel URL
2. **Access admin panel** at `/admin` (admin/dav2024)
3. **Add events** in the calendar
4. **Test chat functionality**

## Features Available

✅ **Chat Interface** - AI-powered conversations  
✅ **File Upload** - PDF/DOCX processing  
✅ **Event Calendar** - Holiday management  
✅ **Admin Panel** - Content management  
✅ **Session Persistence** - 48-hour chat history  
✅ **Mobile Responsive** - Works on all devices  

## Troubleshooting

### Database Issues
- Vercel uses ephemeral storage
- Database resets on each deployment
- Consider using external database for production

### API Limits
- Gemini API has rate limits
- Monitor usage in Google AI Studio

### File Upload
- Vercel has 50MB limit per function
- Large files may timeout

## Support

For issues, check the Vercel deployment logs and ensure all environment variables are set correctly.
