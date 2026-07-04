# --- Stage 1: Compile the Modern React Client ---
FROM node:20-alpine AS frontend-builder
WORKDIR /frontend
COPY app/frontend/package*.json ./
RUN npm install
COPY app/frontend/ ./
RUN npm run build

# --- Stage 2: Finalize Production Containers ---
# UPDATE THIS LINE TO MATCH YOUR PYTHON 3.13 PROTOCOL
FROM python:3.13-slim
WORKDIR /code

# Install native compilation bindings
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Install python system requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Ensure server engine runtime requirements are ready
RUN pip install --no-cache-dir fastapi uvicorn staticfiles

# Transfer codebase structure elements
COPY . .

# Wire React static builds to python asset locations
RUN rm -rf app/frontend
COPY --from=frontend-builder /frontend/dist ./app/frontend/dist

# Expose container execution tracking targets
EXPOSE 7860

# Execute continuous async processing
CMD ["uvicorn", "app.backend.main:app", "--host", "0.0.0.0", "--port", "7860"]