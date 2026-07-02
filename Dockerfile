FROM python:3.12-slim

# Force Python to print logs instantly
ENV PYTHONUNBUFFERED=1

WORKDIR /app
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 7860

# Disable CORS, XSRF, and the volatile File Watcher
CMD sh -c "streamlit run app.py --server.port=${PORT:-7860} --server.address=0.0.0.0 --server.enableCORS=false --server.enableXsrfProtection=false --server.fileWatcherType=none"