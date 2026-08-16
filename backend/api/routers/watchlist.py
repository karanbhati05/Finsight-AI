"""
backend/api/routers/watchlist.py
Watchlist CRUD endpoints with persistent JSON storage and real-time price enrichment.
"""

import json
from pathlib import Path
import yfinance as yf
from fastapi import APIRouter, HTTPException
from backend.models.schemas import WatchlistItem
from backend.cache.redis_client import cache
from src.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

STORAGE_FILE = Path("data/watchlist.json")

def _load_watchlist() -> dict:
    if STORAGE_FILE.exists():
        try:
            with open(STORAGE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"AAPL": True, "NVDA": True, "MSFT": True}

def _save_watchlist(data: dict):
    try:
        STORAGE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(STORAGE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save watchlist to disk: {e}")

_watchlist: dict = _load_watchlist()


def _get_stock_data(ticker: str) -> dict:
    """Fetch current price data for a watchlist stock."""
    try:
        t    = yf.Ticker(ticker)
        hist = t.history(period="30d", interval="1d")

        if hist.empty:
            return None

        closes     = hist["Close"].tolist()
        current    = closes[-1] if closes else 0
        prev_close = closes[-2] if len(closes) > 1 else current
        change     = current - prev_close
        change_pct = (change / prev_close * 100) if prev_close else 0

        try:
            info = t.info
            name = info.get("shortName", info.get("longName", ticker))
        except Exception:
            name = ticker

        return {
            "ticker":     ticker,
            "name":       name,
            "price":      round(current, 2),
            "change":     round(change, 2),
            "change_pct": round(change_pct, 2),
            "direction":  "up" if change >= 0 else "down",
            "sparkline":  [round(c, 2) for c in closes[-30:]],
        }
    except Exception as e:
        logger.error(f"Failed to fetch stock data for {ticker}: {e}")
        return None


@router.get("")
async def get_watchlist():
    """Get all watchlist stocks with current prices. Cached for 2 minutes."""
    watchlist_data = []

    for ticker in _watchlist:
        cache_key = f"watchlist:stock:{ticker}"
        cached = cache.get(cache_key)

        if cached:
            watchlist_data.append(cached)
        else:
            data = _get_stock_data(ticker)
            if data:
                cache.set(cache_key, data, ttl=120)
                watchlist_data.append(data)

    return {"watchlist": watchlist_data}


@router.post("")
async def add_to_watchlist(item: WatchlistItem):
    """Add a ticker to the watchlist and persist."""
    ticker = item.ticker.upper()

    if ticker in _watchlist:
        return {"message": f"{ticker} is already in your watchlist"}

    _watchlist[ticker] = True
    _save_watchlist(_watchlist)
    logger.info(f"Added {ticker} to watchlist")

    cache.delete(f"watchlist:stock:{ticker}")
    return {"message": f"{ticker} added to watchlist", "ticker": ticker}


@router.delete("/{ticker}")
async def remove_from_watchlist(ticker: str):
    """Remove a ticker from the watchlist and persist."""
    ticker_upper = ticker.upper()

    if ticker_upper not in _watchlist:
        raise HTTPException(status_code=404, detail=f"{ticker_upper} not in watchlist")

    del _watchlist[ticker_upper]
    _save_watchlist(_watchlist)
    cache.delete(f"watchlist:stock:{ticker_upper}")
    logger.info(f"Removed {ticker_upper} from watchlist")

    return {"message": f"{ticker_upper} removed from watchlist"}
