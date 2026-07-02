FROM python:3.12-slim

# Fix 1: Force Python to print logs instantly (no buffering) so we catch the exact error
ENV PYTHONUNBUFFERED=1

WORKDIR /app
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 7860

# Fix 2: Disable CORS and XSRF protection so Railway's proxy doesn't drop the Streamlit WebSockets
CMD sh -c "streamlit run app.py --server.port=${PORT:-7860} --server.address=0.0.0.0 --server.enableCORS=false --server.enableXsrfProtection=false"