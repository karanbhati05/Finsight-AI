# FinSight AI - Backend Production Dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV USE_TF=0
ENV USE_TORCH=1
ENV PORT=8000

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

EXPOSE 8000

# Bind dynamically to $PORT for Render, Railway, and local Docker
CMD uvicorn backend.api.main:app --host 0.0.0.0 --port ${PORT:-8000}
