# NB Downloader Deployment Guide

This guide provides step-by-step instructions for deploying the NB Downloader application to production.

## Prerequisites

- GitHub account
- Render.com account (for backend)
- Vercel account (for frontend)
- ffmpeg installed on your system (for local testing)

## Backend Deployment (Render.com)

### Step 1: Prepare Your Repository

1. **Push your code to GitHub**:
   ```bash
   git init
   git add .
   git commit -m "Initial commit: NB Downloader"
   git branch -M main
   git remote add origin https://github.com/yourusername/nb-downloader.git
   git push -u origin main
   ```

### Step 2: Deploy to Render.com

1. **Go to [Render.com](https://render.com)** and sign in
2. **Click "New +"** and select **"Web Service"**
3. **Connect your GitHub repository**:
   - Select your `nb-downloader` repository
   - Choose the main branch

4. **Configure the service**:
   - **Name**: `nb-downloader-backend`
   - **Root Directory**: `backend` (important!)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app:app --host 0.0.0.0 --port $PORT`

5. **Add Environment Variables**:
   - Click on "Environment" tab
   - Add the following variables:
     ```
     FFMPEG_PATH=/usr/bin/ffmpeg
     MAX_FILE_SIZE=2147483648
     TEMP_DIR=/tmp
     ```

6. **Deploy**:
   - Click "Create Web Service"
   - Wait for the build to complete (usually 5-10 minutes)

7. **Get your backend URL**:
   - Once deployed, copy the URL (e.g., `https://nb-downloader-backend.onrender.com`)

### Step 3: Test Backend

1. **Test the health endpoint**:
   ```bash
   curl https://your-backend-url.onrender.com/health
   ```

2. **Test the preview endpoint**:
   ```bash
   curl "https://your-backend-url.onrender.com/preview?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ"
   ```

## Frontend Deployment (Vercel)

### Step 1: Deploy to Vercel

1. **Go to [Vercel.com](https://vercel.com)** and sign in
2. **Click "New Project"**
3. **Import your GitHub repository**:
   - Select your `nb-downloader` repository
   - Click "Import"

4. **Configure the project**:
   - **Framework Preset**: Other
   - **Root Directory**: `frontend`
   - **Build Command**: Leave empty (static files)
   - **Output Directory**: `.`
   - **Install Command**: Leave empty

5. **Add Environment Variables**:
   - Click "Environment Variables"
   - Add:
     ```
     VITE_API_URL=https://your-backend-url.onrender.com
     ```

6. **Deploy**:
   - Click "Deploy"
   - Wait for deployment to complete

### Step 2: Update Frontend Configuration

1. **Update the API URL** in `frontend/script.js`:
   ```javascript
   getApiBaseUrl() {
       // Replace with your actual backend URL
       return 'https://your-backend-url.onrender.com';
   }
   ```

2. **Redeploy** if needed:
   - Push changes to GitHub
   - Vercel will automatically redeploy

## Alternative: Railway.app Deployment

If you prefer Railway.app over Render.com:

### Backend on Railway.app

1. **Go to [Railway.app](https://railway.app)**
2. **Create new project** → "Deploy from GitHub repo"
3. **Select your repository**
4. **Configure**:
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app:app --host 0.0.0.0 --port $PORT`

5. **Add Environment Variables**:
   ```
   FFMPEG_PATH=/usr/bin/ffmpeg
   MAX_FILE_SIZE=2147483648
   TEMP_DIR=/tmp
   ```

## Local Development Setup

### Backend Setup

1. **Navigate to backend directory**:
   ```bash
   cd backend
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Install ffmpeg**:
   - **macOS**: `brew install ffmpeg`
   - **Ubuntu/Debian**: `sudo apt-get install ffmpeg`
   - **Windows**: Download from https://ffmpeg.org/download.html

5. **Run the server**:
   ```bash
   uvicorn app:app --reload --host 0.0.0.0 --port 8000
   ```

### Frontend Setup

1. **Navigate to frontend directory**:
   ```bash
   cd frontend
   ```

2. **Serve the files**:
   ```bash
   # Using Python
   python -m http.server 3000
   
   # Or using Node.js
   npx serve .
   
   # Or using PHP
   php -S localhost:3000
   ```

3. **Open in browser**: `http://localhost:3000`

## Environment Variables

### Backend Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FFMPEG_PATH` | Path to ffmpeg executable | `/usr/bin/ffmpeg` |
| `MAX_FILE_SIZE` | Maximum file size in bytes | `2147483648` (2GB) |
| `TEMP_DIR` | Temporary directory for processing | `/tmp` |

### Frontend Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `VITE_API_URL` | Backend API URL | `https://your-backend.onrender.com` |

## Troubleshooting

### Common Issues

1. **Backend fails to start**:
   - Check if ffmpeg is installed
   - Verify environment variables
   - Check logs in Render/Railway dashboard

2. **CORS errors**:
   - Backend CORS is configured to allow all origins
   - If issues persist, update CORS settings in `backend/app.py`

3. **Download fails**:
   - Check if video URL is valid
   - Verify backend is running
   - Check browser console for errors

4. **Large file downloads fail**:
   - Increase `MAX_FILE_SIZE` environment variable
   - Check platform file size limits

### Performance Optimization

1. **Enable caching**:
   - Add Redis for session storage
   - Implement video metadata caching

2. **Load balancing**:
   - Deploy multiple backend instances
   - Use a load balancer

3. **CDN**:
   - Use Cloudflare or similar for static assets
   - Implement video streaming CDN

## Security Considerations

1. **Rate limiting**: Implement rate limiting to prevent abuse
2. **File size limits**: Set appropriate file size limits
3. **Input validation**: Validate all user inputs
4. **HTTPS**: Always use HTTPS in production
5. **CORS**: Configure CORS properly for your domain

## Monitoring

1. **Set up logging**:
   - Use structured logging
   - Monitor error rates

2. **Health checks**:
   - Backend has `/health` endpoint
   - Set up uptime monitoring

3. **Performance monitoring**:
   - Monitor response times
   - Track download success rates

## Support

For issues and questions:
1. Check the logs in your deployment platform
2. Review the troubleshooting section
3. Open an issue on GitHub
4. Check the main README.md for more information
