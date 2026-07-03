#!/bin/bash
# Railway startup script for Streamlit

# Use Railway's PORT or default to 8080
export PORT=${PORT:-8080}

# Force Streamlit to use the correct port and address
export STREAMLIT_SERVER_PORT=$PORT
export STREAMLIT_SERVER_ADDRESS="0.0.0.0"
export STREAMLIT_SERVER_HEADLESS=true

echo "Starting Streamlit on 0.0.0.0:$PORT..."

exec streamlit run app.py \
    --server.port=$PORT \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --server.enableCORS=false \
    --server.enableXsrfProtection=false \
    --server.fileWatcherType=none \
    --server.maxUploadSize=50 \
    --browser.gatherUsageStats=false
