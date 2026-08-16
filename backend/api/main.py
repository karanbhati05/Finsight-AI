"""
backend/api/main.py
FastAPI application — entry point for the FinSight AI Unified Terminal API.
Includes:
  - Core Market, News, NLP Sentiment, Predictions, and RAG Chat
  - FMP Deep Fundamentals & Statements
  - Alpha Vantage Technicals & Candlestick series
  - FRED Macroeconomic Radar
  - CoinGecko Crypto & Forex Hub
  - Multi-Agent Equity Research Memo Generator
  - WebSockets Real-time Price Streaming
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

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent.parent.parent / ".env")

from backend.api.routers import (
    market,
    news,
    sentiment,
    prediction,
    chat,
    watchlist,
    portfolio,
    fundamentals,
    technicals,
    macro,
    crypto,
    analyst,
)
from backend.api.websocket import router as ws_router
from backend.api.dependencies import startup_models, shutdown_models


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager — loads AI models once at startup with failover guards."""
    await startup_models()
    yield
    await shutdown_models()


app = FastAPI(
    title       = "FinSight AI API",
    description = "Next-Gen Multi-Source Financial Research Terminal API",
    version     = "2.5.0",
    lifespan    = lifespan,
)

# ── CORS Middleware ───────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)

# ── Mount All Routers ─────────────────────────────────────────────────────────
app.include_router(market.router,        prefix="/api/market",       tags=["Market"])
app.include_router(news.router,          prefix="/api/news",         tags=["News"])
app.include_router(sentiment.router,     prefix="/api/sentiment",    tags=["Sentiment"])
app.include_router(prediction.router,    prefix="/api/predict",      tags=["Prediction"])
app.include_router(chat.router,          prefix="/api/chat",         tags=["Chat"])
app.include_router(watchlist.router,     prefix="/api/watchlist",    tags=["Watchlist"])
app.include_router(portfolio.router,     prefix="/api/portfolio",    tags=["Portfolio"])
app.include_router(fundamentals.router,  prefix="/api/fundamentals", tags=["Fundamentals"])
app.include_router(technicals.router,    prefix="/api/technicals",   tags=["Technicals"])
app.include_router(macro.router,         prefix="/api/macro",        tags=["Macro"])
app.include_router(crypto.router,        prefix="/api/crypto",       tags=["Crypto"])
app.include_router(analyst.router,       prefix="/api/analyst",      tags=["Analyst"])
app.include_router(ws_router)


# ── Health Check ─────────────────────────────────────────────────────────────
@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "2.5.0", "engine": "FinSight AI Multi-Source Hub"}
