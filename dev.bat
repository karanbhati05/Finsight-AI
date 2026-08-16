@echo off
echo ====================================================
echo           Starting FinSight AI Terminal            
echo ====================================================

if not exist .env (
    echo [.env] not found. Creating from .env.example...
    copy .env.example .env
)

echo Starting FastAPI Backend on http://localhost:8000 ...
start cmd /k "uvicorn backend.api.main:app --reload --port 8000"

echo Starting Vite React Frontend on http://localhost:5173 ...
start cmd /k "cd frontend && npm run dev"

echo Done! Both servers are starting up.
