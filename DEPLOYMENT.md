# Railway Deployment Guide

## Issue Fixed
The app was crashing on Railway when Streamlit events were triggered due to:
1. **Unsafe `st.rerun()` calls** causing infinite loops in production
2. **Missing error handling** in the main query processing loop
3. **PORT configuration issues** with Railway's dynamic port assignment

## Changes Made

### 1. Fixed Streamlit Reruns ([ui/app.py](ui/app.py))
- Changed all `st.rerun()` to `st.rerun(scope="app")` for safer reruns
- Removed the final `st.rerun()` after chat message processing (unnecessary)
- Added comprehensive try-catch blocks around query processing

### 2. Updated Dockerfile ([Dockerfile](Dockerfile))
- Added `PYTHONDONTWRITEBYTECODE=1` environment variable
- Improved PORT handling with Railway's `$PORT` variable
- Added `--server.headless=true` for production mode
- Increased stability with additional Streamlit flags

### 3. Created Railway Configuration ([railway.json](railway.json))
- Configured restart policy for crash recovery
- Specified Dockerfile build method

### 4. Enhanced Streamlit Config ([.streamlit/config.toml](.streamlit/config.toml))
- Disabled file watcher (not needed in production)
- Disabled usage stats collection
- Enabled fast reruns for better performance
- Set appropriate logging level

### 5. Added .dockerignore ([.dockerignore](.dockerignore))
- Reduces Docker build size and time
- Excludes unnecessary files from the image

## Deployment Steps

### Step 1: Set Environment Variables in Railway

Go to your Railway project → Variables tab and add:

```bash
OPENAI_API_KEY=your_actual_openai_key
GROQ_API_KEY=your_actual_groq_key
OPENROUTER_API_KEY=your_actual_openrouter_key
GEMINI_API_KEY=your_actual_gemini_key
COHERE_API_KEY=your_actual_cohere_key
```

**Important:** Set at least one API key (required by your agents)

### Step 2: Deploy to Railway

#### Option A: GitHub Integration (Recommended)
1. Push your code to GitHub:
   ```bash
   git add .
   git commit -m "Fix Railway deployment crashes"
   git push origin main
   ```

2. In Railway:
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository
   - Railway will auto-detect the Dockerfile and deploy

#### Option B: Railway CLI
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Link to project
railway link

# Deploy
railway up
```

### Step 3: Configure Railway Settings

In your Railway project:
1. **Settings → Domains**: Add a custom domain or use Railway's domain
2. **Settings → Health Check**: 
   - Path: `/`
   - Interval: 30 seconds
   - Timeout: 10 seconds

### Step 4: Monitor Logs

After deployment, watch the logs:
```bash
railway logs
```

Or in the Railway dashboard → Deployments → View Logs

## Testing the Deployment

1. Wait for the deployment to complete (usually 2-3 minutes)
2. Open the Railway-provided URL
3. Test the following scenarios:
   - ✅ Chat query (e.g., "Show me chocolates")
   - ✅ Add item to cart
   - ✅ Remove item from cart
   - ✅ Sidebar filters
   - ✅ Clear cart
   - ✅ Buy now

## Troubleshooting

### App Still Crashes?

1. **Check Logs for Specific Errors:**
   ```bash
   railway logs --tail 100
   ```

2. **Common Issues:**

   **Missing API Keys:**
   ```
   ValueError: API key not found for openai. Check .env!
   ```
   → Add the API key in Railway's Variables tab

   **Port Binding Issues:**
   ```
   OSError: [Errno 98] Address already in use
   ```
   → Railway should handle this automatically. Restart the deployment.

   **Memory Issues:**
   ```
   Killed (out of memory)
   ```
   → Upgrade your Railway plan or optimize memory usage

   **Import Errors:**
   ```
   ModuleNotFoundError: No module named 'X'
   ```
   → Check [requirements.txt](requirements.txt) includes all dependencies

3. **Enable Debug Logging:**
   
   Add to Railway Variables:
   ```
   STREAMLIT_LOG_LEVEL=debug
   ```

### Performance Optimization

If the app is slow on Railway:

1. **Reduce Model Calls:** Check [config/model.yaml](config/model.yaml) and use faster models
2. **Add Caching:** Streamlit's `@st.cache_data` and `@st.cache_resource`
3. **Optimize Queries:** Review agent pipeline in [main.py](main.py:15)

### Database/File Storage

If you need persistent storage:
- Railway ephemeral storage resets on each deployment
- Use Railway's PostgreSQL addon or external storage (S3, etc.)
- Update [data/profiles.json](data/profiles.json) handling to use database

## Local Testing with Docker

Test the exact production environment locally:

```bash
# Build the image
docker build -t kapi-app .

# Run with environment variables
docker run -p 8080:8080 \
  -e OPENAI_API_KEY=your_key \
  -e GROQ_API_KEY=your_key \
  kapi-app
```

Open http://localhost:8080

## Rollback

If the deployment fails:

```bash
# Via Railway CLI
railway rollback

# Or in Railway Dashboard
Deployments → Previous Deployment → Redeploy
```

## Support

- Railway Docs: https://docs.railway.app
- Streamlit Docs: https://docs.streamlit.io
- Project Issues: Create an issue in your repository
