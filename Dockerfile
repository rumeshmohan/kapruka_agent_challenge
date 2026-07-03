FROM python:3.12-slim

# Force Python to print logs instantly
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Railway provides PORT, default to 8080 if not set
ENV PORT=8080
EXPOSE $PORT

# Disable CORS, XSRF, and the volatile File Watcher
# Added headless mode and increased server timeout for stability
CMD streamlit run app.py \
    --server.port=$PORT \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --server.enableCORS=false \
    --server.enableXsrfProtection=false \
    --server.fileWatcherType=none \
    --server.maxUploadSize=50 \
    --browser.gatherUsageStats=false