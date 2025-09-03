# 🚀 Manual Vercel Deployment Guide

Since you have Vercel CLI 44.4.1 installed, follow these steps to deploy D.A.V GPT:

## 📋 Pre-Deployment Checklist

✅ Vercel CLI installed (44.4.1)  
✅ Project files ready  
✅ Environment variables prepared  

## 🌐 Deploy to Vercel

### Step 1: Navigate to Project
```bash
cd "/mnt/d/0000Paid Projects/davgpt"
```

### Step 2: Deploy
```bash
vercel --prod
```

### Step 3: Follow Prompts
- **Set up and deploy?** → Yes
- **Which scope?** → Your account
- **Link to existing project?** → No
- **Project name?** → davgpt (or your preferred name)
- **Directory?** → ./ (current directory)
- **Override settings?** → No

## 🔑 Environment Variables

After deployment, set these in Vercel Dashboard:

### Required Variables:
```
WEBSITE_URL=http://davkoylanagar.com/
GEMINI_API_KEY=your_gemini_api_key_here
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
DATABASE_URL=sqlite:///tmp/davgpt.db
```

### How to Set Variables:
1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Select your project
3. Go to **Settings** → **Environment Variables**
4. Add each variable with its value
5. Redeploy: `vercel --prod`

## 🎯 Post-Deployment

### Test Your Deployment:
1. **Chat Interface**: `https://your-project.vercel.app`
2. **Admin Panel**: `https://your-project.vercel.app/admin`
3. **Login**: admin / dav2024

### Verify Features:
- [ ] Chat responses working
- [ ] File upload functional
- [ ] Admin panel accessible
- [ ] Calendar system working
- [ ] Holiday queries responding

## 🔧 Troubleshooting

### Common Issues:

**Build Errors:**
```bash
# Check build logs in Vercel dashboard
# Ensure all dependencies in requirements.txt
```

**Environment Variable Issues:**
```bash
# Verify all 5 variables are set
# Check for typos in variable names
# Redeploy after setting variables
```

**Database Issues:**
```bash
# Vercel uses ephemeral storage
# Database resets on each deployment
# Consider external database for production
```

## 🎉 Success!

Your D.A.V GPT is now live on Vercel! 

**Next Steps:**
1. Share the URL with users
2. Monitor usage in Vercel dashboard
3. Set up custom domain (optional)
4. Configure analytics (optional)

---

**Need Help?** Check the [documentation](documentation/index.html) or Vercel support.
