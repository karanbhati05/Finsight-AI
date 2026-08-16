"""
backend/api/routers/market.py
Market data endpoints — indices, sectors, and stock search.

Uses yfinance for real-time quotes and 30-day sparkline history.
Caches results in Redis for 5 minutes to avoid hammering Yahoo Finance.
"""

import yfinance as yf
import pandas as pd
from fastapi import APIRouter, Query, HTTPException
from typing import List
from backend.cache.redis_client import cache
from src.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

# ── Region → Indices/Sectors mapping ─────────────────────────────────────────
# Each region has a set of indices and (optionally) sector indices.
# These are the symbols that appear as cards in the frontend IndexGrid.

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
            {"symbol": "NIFTY_FMCG.NS",     "name": "NIFTY_FMCG",    "label": "Consumer Staples"},
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
    },
    "europe": {
        "indices": [
            {"symbol": "^FTSE",  "name": "FTSE 100"},
            {"symbol": "^GDAXI", "name": "DAX"},
            {"symbol": "^FCHI",  "name": "CAC 40"},
            {"symbol": "^STOXX", "name": "Euro Stoxx 50"},
        ],
        "sectors": []
    },
    "currencies": {
        "indices": [
            {"symbol": "USDINR=X", "name": "USD/INR"},
            {"symbol": "EURUSD=X", "name": "EUR/USD"},
            {"symbol": "GBPUSD=X", "name": "GBP/USD"},
            {"symbol": "USDJPY=X", "name": "USD/JPY"},
        ],
        "sectors": []
    },
    "futures": {
        "indices": [
            {"symbol": "GC=F",  "name": "Gold"},
            {"symbol": "SI=F",  "name": "Silver"},
            {"symbol": "CL=F",  "name": "Crude Oil"},
            {"symbol": "NG=F",  "name": "Natural Gas"},
        ],
        "sectors": []
    },
}


def get_quote(symbol: str, name: str) -> dict:
    """
    Fetch current quote and 30-day sparkline for a symbol.

    Returns a dict matching the IndexData schema, or None on failure.
    Uses yfinance history() for reliable close prices.
    """
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
    """
    Get market indices for a region with sparkline data.
    Cached for 5 minutes to avoid rate limiting by Yahoo Finance.
    """
    region_lower = region.lower()
    cache_key = f"market:indices:{region_lower}"

    # Check cache first
    cached = cache.get(cache_key)
    if cached:
        return cached

    region_data = REGIONS.get(region_lower)
    if not region_data:
        raise HTTPException(status_code=404, detail=f"Region '{region}' not found")

    indices = []
    for idx in region_data["indices"]:
        quote = get_quote(idx["symbol"], idx["name"])
        if quote:
            indices.append(quote)

    result = {"region": region, "indices": indices}

    # Cache for 5 minutes
    cache.set(cache_key, result, ttl=300)

    return result


@router.get("/sectors")
async def get_sectors(region: str = Query(default="india")):
    """
    Get sector indices for a region (primarily India — Nifty sectoral indices).
    Cached for 5 minutes.
    """
    region_lower = region.lower()
    cache_key = f"market:sectors:{region_lower}"

    cached = cache.get(cache_key)
    if cached:
        return cached

    region_data = REGIONS.get(region_lower)
    if not region_data:
        raise HTTPException(status_code=404, detail=f"Region '{region}' not found")

    sectors = []
    for sec in region_data.get("sectors", []):
        quote = get_quote(sec["symbol"], sec["name"])
        if quote:
            quote["label"] = sec["label"]
            sectors.append(quote)

    result = {"sectors": sectors}
    cache.set(cache_key, result, ttl=300)

    return result


@router.get("/search")
async def search_stocks(q: str = Query(..., min_length=1)):
    """
    Search for stocks by ticker or company name.
    Uses yfinance Search API — returns up to 8 results.
    """
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
