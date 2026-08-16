"""
backend/api/main.py
FastAPI application — entry point for the FinSight V2 API.

Responsibilities:
    - Add project root to sys.path so src/ modules are importable
    - Load .env variables before any other imports
    - Register CORS middleware for frontend dev server
    - Include all API routers with correct prefixes
    - Manage AI model lifecycle via lifespan events
"""
import os
os.environ["USE_TF"] = "0"
os.environ["USE_TORCH"] = "1"
os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"


import sys
from pathlib import Path

# Add project root so we can import src/
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables BEFORE any src/ imports that need API keys
load_dotenv(Path(__file__).parent.parent.parent / ".env")

from backend.api.routers import market, news, sentiment, prediction, chat, watchlist, portfolio
from backend.api.websocket import router as ws_router
from backend.api.dependencies import startup_models, shutdown_models


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager — runs once at startup and once at shutdown.

    Heavy models (FinBERT ~440MB, ChromaDB, XGBoost) take 10-30 seconds
    to load. We load them once here and store as global singletons in
    dependencies.py, so every request reuses them without reloading.
    """
    await startup_models()
    yield
    await shutdown_models()


app = FastAPI(
    title       = "FinSight AI API",
    description = "Intelligent Financial Research Assistant — REST API + WebSockets",
    version     = "2.0.0",
    lifespan    = lifespan,
)

# ── CORS ─────────────────────────────────────────────────────────────────────
# Allow the React dev server (Vite) to make cross-origin requests.
# In production, restrict allow_origins to the actual domain.
app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["http://localhost:5173", "http://localhost:3000"],
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)

# ── Routers ──────────────────────────────────────────────────────────────────
app.include_router(market.router,     prefix="/api/market",     tags=["Market"])
app.include_router(news.router,       prefix="/api/news",       tags=["News"])
app.include_router(sentiment.router,  prefix="/api/sentiment",  tags=["Sentiment"])
app.include_router(prediction.router, prefix="/api/predict",    tags=["Prediction"])
app.include_router(chat.router,       prefix="/api/chat",       tags=["Chat"])
app.include_router(watchlist.router,  prefix="/api/watchlist",  tags=["Watchlist"])
app.include_router(portfolio.router,  prefix="/api/portfolio",  tags=["Portfolio"])
app.include_router(ws_router)


# ── Health Check ─────────────────────────────────────────────────────────────
@app.get("/api/health")
async def health():
    """Simple health check endpoint for Docker/load balancer probes."""
    return {"status": "ok", "version": "2.0.0"}
