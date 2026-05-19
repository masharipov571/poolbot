# STAGE 1: Build the React Frontend Dashboard
FROM node:20-alpine AS frontend-builder
WORKDIR /frontend

# Copy package configurations and install
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install

# Copy frontend source and build static assets
COPY frontend/ ./
RUN npm run build

# STAGE 2: Build the FastAPI + Aiogram Python Backend
FROM python:3.10-slim
WORKDIR /app

# Install system dependencies for PostgreSQL and building
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python requirements
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY backend/ .

# Copy compiled static frontend dashboard assets from Stage 1
COPY --from=frontend-builder /backend/static ./static

# Expose FastAPI port
EXPOSE 8000

# Run uvicorn server (concurrently launching FastAPI and Telegram Bot)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
