#!/bin/bash
# Railway startup script for Streamlit

# Use Railway's PORT or default to 8080
PORT=${PORT:-8080}

echo "Starting Streamlit on port $PORT..."

exec streamlit run app.py \
    --server.port=$PORT \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --server.enableCORS=false \
    --server.enableXsrfProtection=false \
    --server.fileWatcherType=none \
    --server.maxUploadSize=50 \
    --browser.gatherUsageStats=false
