#!/usr/bin/env bash

# FinSight V2 Development Launcher
echo "===================================================="
echo "          Starting FinSight AI Terminal            "
echo "===================================================="

# Check if .env exists
if [ ! -f ".env" ]; then
  echo "⚠️  .env file not found! Copying .env.example -> .env"
  cp .env.example .env
fi

# Start Redis if docker is available
if command -v docker &> /dev/null; then
  echo "🚀 Starting Redis in background..."
  docker run -d --name finsight_redis_dev -p 6379:6379 redis:7-alpine 2>/dev/null || true
fi

# Trap to kill background processes on CTRL+C
cleanup() {
  echo ""
  echo "🛑 Stopping FinSight..."
  kill $(jobs -p) 2>/dev/null
  exit
}
trap cleanup SIGINT SIGTERM

echo "📡 Starting FastAPI Backend on port 8000..."
uvicorn backend.api.main:app --reload --port 8000 &

echo "⚡ Starting Vite React Frontend on port 5173..."
cd frontend && npm run dev &

wait
