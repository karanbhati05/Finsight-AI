# FinSight V2 — Backend Starter Code

Complete starter files for the FastAPI backend.
Build these FIRST before touching the frontend.

---

## backend/requirements_backend.txt

```
fastapi==0.111.0
uvicorn[standard]==0.30.1
websockets==12.0
redis==5.0.4
sqlalchemy==2.0.30
aiosqlite==0.20.0
pydantic==2.7.1
python-multipart==0.0.9
httpx==0.27.0
python-dotenv==1.0.1
```

---

## backend/api/main.py

```python
import sys
from pathlib import Path

# Add project root so we can import src/
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / ".env")

from backend.api.routers import market, news, sentiment, prediction, chat, watchlist, portfolio
from backend.api.websocket import router as ws_router
from backend.api.dependencies import startup_models, shutdown_models

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load heavy models once at startup — not on every request
    await startup_models()
    yield
    await shutdown_models()

app = FastAPI(
    title       = "FinSight AI API",
    description = "Intelligent Financial Research Assistant",
    version     = "2.0.0",
    lifespan    = lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["http://localhost:5173", "http://localhost:3000"],
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)

# Include all routers
app.include_router(market.router,     prefix="/api/market",     tags=["Market"])
app.include_router(news.router,       prefix="/api/news",       tags=["News"])
app.include_router(sentiment.router,  prefix="/api/sentiment",  tags=["Sentiment"])
app.include_router(prediction.router, prefix="/api/predict",    tags=["Prediction"])
app.include_router(chat.router,       prefix="/api/chat",       tags=["Chat"])
app.include_router(watchlist.router,  prefix="/api/watchlist",  tags=["Watchlist"])
app.include_router(portfolio.router,  prefix="/api/portfolio",  tags=["Portfolio"])
app.include_router(ws_router)

@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "2.0.0"}
```

---

## backend/api/dependencies.py

```python
"""
Shared model instances — loaded ONCE at startup, reused across all requests.
Heavy models (FinBERT, XGBoost, ChromaDB) take 10-30 seconds to load.
Storing them here avoids reloading on every API call.
"""

from src.nlp.sentiment    import FinBERTSentiment
from src.rag.chatbot      import FinancialChatbot
from src.rag.vector_store import FinancialVectorStore
from src.utils.logger     import get_logger

logger = get_logger(__name__)

# Global instances
_sentiment_model: FinBERTSentiment  = None
_chatbot:         FinancialChatbot  = None
_vector_store:    FinancialVectorStore = None


async def startup_models():
    global _sentiment_model, _chatbot, _vector_store
    logger.info("Loading AI models at startup...")

    _vector_store    = FinancialVectorStore()
    _sentiment_model = FinBERTSentiment()
    _chatbot         = FinancialChatbot(vector_store=_vector_store)

    logger.info("All models loaded and ready")


async def shutdown_models():
    logger.info("Shutting down models...")


def get_sentiment_model() -> FinBERTSentiment:
    return _sentiment_model


def get_chatbot() -> FinancialChatbot:
    return _chatbot


def get_vector_store() -> FinancialVectorStore:
    return _vector_store
```

---

## backend/api/models/schemas.py

```python
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


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


class WatchlistItem(BaseModel):
    ticker: str


class PortfolioItem(BaseModel):
    ticker:    str
    shares:    float
    buy_price: float
```

---

## backend/api/routers/market.py

```python
import yfinance as yf
import pandas as pd
from fastapi import APIRouter, Query, HTTPException
from typing import List
from src.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

REGIONS = {
    "india": {
        "indices": [
            {"symbol": "^NSEI",    "name": "NIFTY 50"},
            {"symbol": "^BSESN",   "name": "SENSEX"},
            {"symbol": "^NSEBANK", "name": "Nifty Bank"},
            {"symbol": "^CNXIT",   "name": "Nifty IT"},
        ],
        "sectors": [
            {"symbol": "NIFTY_AUTO.NS",     "name": "NIFTY_AUTO",     "label": "Auto"},
            {"symbol": "NIFTY_ENERGY.NS",   "name": "NIFTY_ENERGY",   "label": "Energy & Utilities"},
            {"symbol": "NIFTY_FIN_SERV.NS", "name": "NIFTY_FIN_SERV", "label": "Financials"},
            {"symbol": "NIFTY_FMCG.NS",     "name": "NIFTY_FMCG",     "label": "Consumer Staples"},
            {"symbol": "NIFTY_INFRA.NS",    "name": "NIFTY_INFRA",    "label": "Industrials"},
            {"symbol": "NIFTY_IT.NS",       "name": "NIFTY_IT",       "label": "Technology"},
        ]
    },
    "us": {
        "indices": [
            {"symbol": "^GSPC", "name": "S&P 500"},
            {"symbol": "^DJI",  "name": "Dow Jones"},
            {"symbol": "^IXIC", "name": "NASDAQ"},
            {"symbol": "^RUT",  "name": "Russell 2000"},
        ],
        "sectors": []
    },
    "crypto": {
        "indices": [
            {"symbol": "BTC-USD", "name": "Bitcoin"},
            {"symbol": "ETH-USD", "name": "Ethereum"},
            {"symbol": "BNB-USD", "name": "BNB"},
            {"symbol": "SOL-USD", "name": "Solana"},
        ],
        "sectors": []
    }
}


def get_quote(symbol: str, name: str) -> dict:
    """Fetch current quote and 30-day sparkline for a symbol."""
    try:
        ticker = yf.Ticker(symbol)
        hist   = ticker.history(period="30d", interval="1d")

        if hist.empty:
            return None

        closes     = hist["Close"].tolist()
        current    = closes[-1] if closes else 0
        prev_close = closes[-2] if len(closes) > 1 else current
        change     = current - prev_close
        change_pct = (change / prev_close * 100) if prev_close else 0

        return {
            "symbol":       symbol,
            "name":         name,
            "value":        round(current, 2),
            "change":       round(change, 2),
            "change_pct":   round(change_pct, 2),
            "direction":    "up" if change >= 0 else "down",
            "sparkline":    [round(c, 2) for c in closes[-30:]],
            "last_updated": str(hist.index[-1]),
        }
    except Exception as e:
        logger.error(f"Failed to fetch quote for {symbol}: {e}")
        return None


@router.get("/indices")
async def get_indices(region: str = Query(default="india")):
    region_data = REGIONS.get(region.lower())
    if not region_data:
        raise HTTPException(status_code=404, detail=f"Region '{region}' not found")

    indices = []
    for idx in region_data["indices"]:
        quote = get_quote(idx["symbol"], idx["name"])
        if quote:
            indices.append(quote)

    return {"region": region, "indices": indices}


@router.get("/sectors")
async def get_sectors(region: str = Query(default="india")):
    region_data = REGIONS.get(region.lower())
    if not region_data:
        raise HTTPException(status_code=404, detail=f"Region '{region}' not found")

    sectors = []
    for sec in region_data.get("sectors", []):
        quote = get_quote(sec["symbol"], sec["name"])
        if quote:
            quote["label"] = sec["label"]
            sectors.append(quote)

    return {"sectors": sectors}


@router.get("/search")
async def search_stocks(q: str = Query(..., min_length=1)):
    """Search for stocks by ticker or company name."""
    try:
        results = yf.Search(q)
        quotes  = results.quotes[:8] if results.quotes else []
        return {
            "results": [
                {
                    "symbol":   r.get("symbol", ""),
                    "name":     r.get("shortname", r.get("longname", "")),
                    "type":     r.get("quoteType", ""),
                    "exchange": r.get("exchange", ""),
                }
                for r in quotes
            ]
        }
    except Exception as e:
        logger.error(f"Search failed for '{q}': {e}")
        return {"results": []}
```

---

## backend/api/routers/chat.py

```python
from fastapi import APIRouter, Depends, HTTPException
from backend.api.dependencies import get_chatbot
from backend.api.models.schemas import ChatRequest, ChatResponse
from src.rag.chatbot import FinancialChatbot
from src.utils.logger import get_logger
import uuid

logger = get_logger(__name__)
router = APIRouter()

# Per-session chatbot instances for conversation history
_sessions: dict = {}

SUGGESTED_QUESTIONS = {
    "AAPL": [
        "What are the main risk factors Apple mentioned in their 10-K?",
        "How has Apple's revenue trended recently?",
        "What did analysts say about iPhone sales?",
        "What is Apple's outlook for next quarter?",
    ],
    "MSFT": [
        "What is Microsoft's Azure cloud growth strategy?",
        "How is Microsoft performing in the AI space?",
        "What are Microsoft's main risk factors?",
        "What did Microsoft say about Copilot adoption?",
    ],
    "DEFAULT": [
        "Summarize recent news sentiment for this company.",
        "What are the main risk factors mentioned?",
        "What financial figures were highlighted recently?",
        "What is the overall analyst sentiment?",
    ]
}


@router.post("", response_model=ChatResponse)
async def chat(
    request:    ChatRequest,
    chatbot_:   FinancialChatbot = Depends(get_chatbot),
):
    session_id = request.session_id or str(uuid.uuid4())

    # Get or create session chatbot
    if session_id not in _sessions:
        from src.rag.chatbot import FinancialChatbot
        _sessions[session_id] = FinancialChatbot()

    session_bot = _sessions[session_id]

    try:
        result = session_bot.ask(
            question = request.question,
            ticker   = request.ticker,
            top_k    = request.top_k,
        )
        return ChatResponse(
            answer           = result["answer"],
            sources          = result["sources"],
            retrieved_chunks = result["retrieved_chunks"],
            session_id       = session_id,
        )
    except Exception as e:
        logger.error(f"Chat failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{session_id}")
async def clear_session(session_id: str):
    if session_id in _sessions:
        del _sessions[session_id]
    return {"cleared": True}


@router.get("/suggestions/{ticker}")
async def get_suggestions(ticker: str):
    questions = SUGGESTED_QUESTIONS.get(
        ticker.upper(),
        SUGGESTED_QUESTIONS["DEFAULT"]
    )
    return {"ticker": ticker, "suggestions": questions}
```

---

## backend/api/websocket.py

```python
import asyncio
import json
import yfinance as yf
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from src.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        self.active.remove(ws)

    async def send(self, ws: WebSocket, data: dict):
        await ws.send_text(json.dumps(data))


manager = ConnectionManager()


def fetch_prices(tickers: list[str]) -> dict:
    prices = {}
    for ticker in tickers:
        try:
            t    = yf.Ticker(ticker)
            info = t.fast_info
            prices[ticker] = {
                "price":      round(float(info.last_price or 0), 2),
                "change":     round(float(info.last_price or 0) - float(info.previous_close or 0), 2),
                "change_pct": round(
                    ((float(info.last_price or 0) - float(info.previous_close or 0))
                     / float(info.previous_close or 1)) * 100, 2
                ),
            }
        except Exception:
            prices[ticker] = {"price": 0, "change": 0, "change_pct": 0}
    return prices


@router.websocket("/ws/prices")
async def websocket_prices(websocket: WebSocket):
    await manager.connect(websocket)
    subscribed_tickers = []

    try:
        while True:
            try:
                # Wait for subscription message (non-blocking)
                data = await asyncio.wait_for(
                    websocket.receive_text(), timeout=1.0
                )
                msg = json.loads(data)
                if msg.get("action") == "subscribe":
                    subscribed_tickers = msg.get("tickers", [])
                    logger.info(f"WebSocket subscribed to: {subscribed_tickers}")

            except asyncio.TimeoutError:
                pass  # No message, continue to price push

            # Push prices every 10 seconds if subscribed
            if subscribed_tickers:
                prices = fetch_prices(subscribed_tickers)
                await manager.send(websocket, {
                    "type":      "price_update",
                    "prices":    prices,
                    "timestamp": str(asyncio.get_event_loop().time()),
                })

            await asyncio.sleep(10)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("WebSocket client disconnected")
```

---

## Run Backend

```bash
cd finsight-v2
uvicorn backend.api.main:app --reload --port 8000

# API docs at: http://localhost:8000/docs
```

