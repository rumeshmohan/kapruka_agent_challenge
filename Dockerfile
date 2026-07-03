FROM python:3.12-slim

# Force Python to print logs instantly
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Make startup script executable
RUN chmod +x start.sh

# Railway provides PORT, default to 8080 if not set
ENV PORT=8080
EXPOSE $PORT

# Run startup script
CMD ["./start.sh"]