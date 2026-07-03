# PORT Variable Fix for Railway

## Issue
Railway was not expanding the `$PORT` environment variable properly in the Dockerfile CMD, causing this error:
```
Error: Invalid value for '--server.port': '$PORT' is not a valid integer.
```

## Solution
Created a startup shell script ([start.sh](start.sh)) that properly handles environment variable expansion.

## Changes Made

### 1. Created [start.sh](start.sh)
A bash script that:
- Reads Railway's `PORT` environment variable
- Defaults to `8080` if `PORT` is not set
- Properly expands the variable when starting Streamlit

### 2. Updated [Dockerfile](Dockerfile)
- Changed from inline CMD to calling `start.sh`
- Added `chmod +x start.sh` to make it executable
- Simplified structure for better Railway compatibility

### 3. Updated [railway.json](railway.json)
- Removed redundant `startCommand` (now handled by Dockerfile CMD)
- Kept restart policy configuration

## Files Changed
- ✓ `Dockerfile` - Now uses `start.sh` script
- ✓ `start.sh` - New startup script (properly handles PORT)
- ✓ `railway.json` - Simplified configuration

## Deploy Now

```bash
# Commit the fix
git add Dockerfile start.sh railway.json PORT_FIX.md
git commit -m "Fix PORT variable expansion for Railway"
git push origin main
```

Railway will automatically redeploy and the PORT error should be resolved.

## Verification

After deployment, check Railway logs. You should see:
```
Starting Streamlit on port 8080...
```

Instead of the previous error about `$PORT` not being a valid integer.

## Local Testing

Test the fix locally:

```bash
# Build Docker image
docker build -t kapi-test .

# Run with custom PORT
docker run -p 9000:9000 -e PORT=9000 -e OPENAI_API_KEY=your_key kapi-test

# Should see: "Starting Streamlit on port 9000..."
```

## Why This Works

The issue was that Docker's exec form `CMD ["streamlit", "run", ...]` doesn't perform shell variable expansion. The fix uses:

1. **Shell script** (`start.sh`) - Bash properly expands `${PORT:-8080}`
2. **exec form calling script** - `CMD ["./start.sh"]` executes the script as PID 1
3. **Proper variable handling** - Script reads environment variable at runtime

## Alternative Solutions (Not Used)

We could have used:
```dockerfile
CMD ["sh", "-c", "streamlit run app.py --server.port=$PORT ..."]
```

But a separate script is cleaner and easier to debug.

---

**Status**: Ready to deploy ✅
