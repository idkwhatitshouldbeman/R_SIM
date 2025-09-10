# R_SIM Platform - Render Deployment Guide

## Overview
This guide will help you deploy the R_SIM Rocket Simulation Platform to Render.com.

## Prerequisites
- Render.com account
- GitHub repository with your code
- Basic understanding of web deployment

## Deployment Steps

### 1. Connect Repository
1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click "New +" → "Blueprint"
3. Connect your GitHub repository
4. Select the repository containing this project

### 2. Automatic Deployment
The `render.yaml` file will automatically configure:
- **Backend Service**: Python Flask API
- **Frontend Service**: React static site
- **Database**: SQLite (local storage)
- **File Storage**: Render disk storage

### 3. Environment Variables
The following environment variables are automatically set:
- `FLASK_ENV=production`
- `FLASK_DEBUG=false`
- `PORT=5000`
- `PYTHONPATH=/opt/render/project/src`

### 4. Services Configuration

#### Backend Service
- **Runtime**: Python 3.11
- **Build Command**: `pip install -r backend/requirements.txt`
- **Start Command**: `python backend/f_backend.py`
- **Health Check**: `/api/simulation/status`
- **Plan**: Starter (Free tier)

#### Frontend Service
- **Runtime**: Static Site
- **Build Command**: `cd frontend && npm install && npm run build`
- **Publish Directory**: `frontend/dist`
- **Plan**: Starter (Free tier)

### 5. Custom Domain (Optional)
1. Go to your service settings
2. Click "Custom Domains"
3. Add your domain
4. Follow DNS configuration instructions

## Features Available After Deployment

### ✅ Working Features
- **Rocket Builder**: Drag-and-drop interface
- **Simulation Setup**: Weather presets and variable configuration
- **Real-time Validation**: Input validation with visual feedback
- **Custom Notifications**: Glassmorphism notification system
- **Responsive Design**: Works on desktop and mobile

### ⚠️ Limited Features (Free Tier)
- **Heavy CFD**: Requires Google Cloud Functions (separate setup)
- **File Storage**: Limited to 1GB on free tier
- **Performance**: May have cold starts on free tier

## Post-Deployment

### 1. Test the Application
- Visit your frontend URL
- Test rocket building functionality
- Verify simulation setup works
- Check notification system

### 2. Monitor Performance
- Check Render dashboard for service health
- Monitor build logs for any issues
- Review error logs if problems occur

### 3. Scale if Needed
- Upgrade to paid plans for better performance
- Add more disk storage if needed
- Configure custom domains

## Troubleshooting

### Common Issues
1. **Build Failures**: Check build logs in Render dashboard
2. **API Errors**: Verify backend service is running
3. **Static Files**: Ensure frontend build completed successfully
4. **Database Issues**: Check disk storage configuration

### Support
- Render Documentation: https://render.com/docs
- Render Community: https://community.render.com
- Project Issues: Check GitHub repository issues

## Cost Estimation
- **Free Tier**: $0/month (with limitations)
- **Starter Plan**: $7/month per service
- **Professional Plan**: $25/month per service

## Security Notes
- All API endpoints are public (no authentication implemented)
- Consider adding authentication for production use
- Environment variables are secure in Render dashboard
- HTTPS is automatically enabled

## Next Steps
1. Deploy to Render using this configuration
2. Test all functionality
3. Consider upgrading to paid plans for production use
4. Add authentication if needed
5. Set up monitoring and alerts
