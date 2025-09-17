# Netlify Deployment Guide for R_SIM

## 🚀 Quick Deployment Steps

### 1. Connect to Netlify
1. Go to [netlify.com](https://netlify.com) and sign up/login
2. Click "New site from Git"
3. Connect your GitHub account
4. Select the `R_SIM` repository
5. Netlify will auto-detect the build settings

### 2. Configure Build Settings
Netlify should auto-detect these settings from `netlify.toml`:
- **Build command**: `cd frontend && npm install && npm run build`
- **Publish directory**: `frontend/dist`
- **Node version**: `18`

### 3. Set Environment Variables
In the Netlify dashboard, go to Site settings > Environment variables:

```
VITE_API_URL = https://your-render-backend-url.onrender.com
VITE_GCP_FUNCTION_URL = https://us-central1-centered-scion-471523-a4.cloudfunctions.net/rocket-cfd-simulator
VITE_SUPABASE_URL = https://ovwgplglypjfuqsflyhc.supabase.co
VITE_SUPABASE_ANON_KEY = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im92d2dwbGdseXBqZnVxc2ZseWhjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTcyOTQ0MDgsImV4cCI6MjA3Mjg3MDQwOH0.YTjAKmshWQ5rFG9an2de8UHu9NA-03U8B6km8XLmjC0
```

### 4. Deploy
1. Click "Deploy site"
2. Netlify will build and deploy your site
3. You'll get a URL like `https://your-site-name.netlify.app`

## 🔧 Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Netlify       │    │   Supabase      │    │ Google Cloud    │
│                 │    │                 │    │                 │
│ • React Frontend│───▶│ • Database      │◀───│ • Cloud Function│
│ • Static Files  │    │ • File Storage  │    │ • CFD Processing│
│ • Global CDN    │    │ • Real-time     │    │ • OpenFOAM      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📋 Benefits of Netlify

- ✅ **Global CDN**: Faster loading worldwide
- ✅ **Automatic deployments**: Deploy on every git push
- ✅ **Branch previews**: Test different versions
- ✅ **Built-in Supabase integration**: Easy backend connection
- ✅ **Free tier**: 100GB bandwidth, 300 build minutes
- ✅ **HTTPS**: Automatic SSL certificates
- ✅ **Form handling**: Built-in form processing

## 🚀 Post-Deployment

1. **Test the site**: Visit your Netlify URL
2. **Check API calls**: Ensure frontend can reach backend
3. **Monitor performance**: Use Netlify analytics
4. **Set up custom domain**: (optional) Add your own domain

## 🔄 Continuous Deployment

Every time you push to the `main` branch:
1. Netlify automatically builds the frontend
2. Deploys the new version
3. Updates the live site

## 📞 Support

- **Netlify Docs**: [docs.netlify.com](https://docs.netlify.com)
- **Supabase Integration**: [docs.netlify.com/integrations/supabase](https://docs.netlify.com/integrations/supabase)
- **Vite Deployment**: [vitejs.dev/guide/static-deploy.html](https://vitejs.dev/guide/static-deploy.html)
