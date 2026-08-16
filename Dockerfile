# FinSight AI - Backend Production Dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV USE_TF=0
ENV USE_TORCH=1
ENV PORT=8000
ENV PIP_DEFAULT_TIMEOUT=100

WORKDIR /app

# Install system build dependencies & C++ compilers
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    g++ \
    gcc \
    python3-dev \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install lightweight CPU-only PyTorch first (fast 150MB wheel, avoids 2.5GB CUDA download)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch==2.3.0 --index-url https://download.pytorch.org/whl/cpu

# Install remaining Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

EXPOSE 8000

# Bind dynamically to $PORT for Render, Railway, and local Docker
CMD uvicorn backend.api.main:app --host 0.0.0.0 --port ${PORT:-8000}
