"""
backend/models/schemas.py
Pydantic request/response models for all API endpoints.

These define the exact JSON shapes the frontend expects.
FastAPI auto-validates incoming requests and auto-documents
response shapes in /docs (Swagger UI).
"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any


# ── Market ───────────────────────────────────────────────────────────────────

class IndexData(BaseModel):
    symbol:       str
    name:         str
    value:        float
    change:       float
    change_pct:   float
    direction:    str
    sparkline:    List[float]
    last_updated: str


class SectorData(BaseModel):
    symbol:     str
    name:       str
    label:      str
    value:      float
    change_pct: float
    direction:  str
    sparkline:  List[float]


# ── News ─────────────────────────────────────────────────────────────────────

class ArticleData(BaseModel):
    id:              str
    title:           str
    summary:         str
    source:          str
    source_count:    int
    published_at:    str
    url:             str
    sentiment_label: str
    sentiment_score: float
    entities:        Dict[str, List[str]]


class NewsResponse(BaseModel):
    ticker:         str
    articles:       List[ArticleData]
    market_summary: str
    avg_sentiment:  float


# ── Sentiment ────────────────────────────────────────────────────────────────

class SentimentDayData(BaseModel):
    date:           str
    avg_score:      float
    article_count:  int
    positive_ratio: float
    negative_ratio: float


class SentimentSummary(BaseModel):
    avg_score:      float
    trend:          str
    score_delta:    float
    total_articles: int


class SentimentTrendResponse(BaseModel):
    ticker:          str
    sentiment_trend: List[SentimentDayData]
    summary:         SentimentSummary


# ── Prediction ───────────────────────────────────────────────────────────────

class PredictionResponse(BaseModel):
    ticker:              str
    date:                str
    prediction:          int
    label:               str
    probability:         float
    confidence:          str
    features:            Dict[str, float]
    model_metrics:       Dict[str, float]
    probability_history: List[Dict[str, Any]]


# ── Chat (RAG) ───────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    question:   str
    ticker:     Optional[str] = None
    top_k:      int = 5
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    answer:           str
    sources:          List[Dict[str, Any]]
    retrieved_chunks: int
    session_id:       Optional[str]


# ── Watchlist ────────────────────────────────────────────────────────────────

class WatchlistItem(BaseModel):
    ticker: str


class WatchlistStockData(BaseModel):
    ticker:     str
    name:       str
    price:      float
    change:     float
    change_pct: float
    direction:  str
    sparkline:  List[float]


# ── Portfolio ────────────────────────────────────────────────────────────────

class PortfolioItem(BaseModel):
    ticker:    str
    shares:    float
    buy_price: float


class PortfolioHolding(BaseModel):
    ticker:       str
    name:         str
    shares:       float
    buy_price:    float
    current:      float
    pnl:          float
    pnl_pct:      float
    direction:    str
    market_value: float
