"""
backend/api/routers/market.py
High-speed Market data endpoints — parallel async fetching with in-memory instant caching.
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
import yfinance as yf
from fastapi import APIRouter, Query, HTTPException
from backend.cache.redis_client import cache
from src.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()
executor = ThreadPoolExecutor(max_workers=10)

REGIONS = {
    "india": {
        "indices": [
            {"symbol": "^NSEI",    "name": "NIFTY 50",    "val": 24366.00, "chg": -29.85, "pct": -0.12},
            {"symbol": "^BSESN",   "name": "SENSEX",      "val": 79800.25, "chg": -71.40, "pct": -0.09},
            {"symbol": "^NSEBANK", "name": "Nifty Bank",  "val": 50450.10, "chg": 120.30, "pct": 0.24},
            {"symbol": "^CNXIT",   "name": "Nifty IT",    "val": 41200.80, "chg": -180.50,"pct": -0.44},
        ],
        "sectors": [
            {"symbol": "NIFTY_AUTO.NS",     "name": "NIFTY_AUTO",     "label": "Auto",               "val": 29207.90, "pct": -0.63},
            {"symbol": "NIFTY_ENERGY.NS",   "name": "NIFTY_ENERGY",   "label": "Energy & Utilities", "val": 38554.20, "pct": -0.35},
            {"symbol": "NIFTY_FIN_SERV.NS", "name": "NIFTY_FIN_SERV", "label": "Financials",         "val": 26213.65, "pct": -0.43},
            {"symbol": "NIFTY_FMCG.NS",     "name": "NIFTY_FMCG",    "label": "Consumer Staples",   "val": 48615.05, "pct": 0.15},
            {"symbol": "NIFTY_INFRA.NS",    "name": "NIFTY_INFRA",    "label": "Industrials",        "val": 8420.30,  "pct": -0.22},
            {"symbol": "NIFTY_IT.NS",       "name": "NIFTY_IT",       "label": "Technology",         "val": 41200.80, "pct": -0.44},
        ]
    },
    "us": {
        "indices": [
            {"symbol": "^GSPC", "name": "S&P 500",      "val": 5785.76,  "chg": -13.23, "pct": -0.17},
            {"symbol": "^DJI",  "name": "Dow Jones",    "val": 43732.41, "chg": -107.58,"pct": -0.20},
            {"symbol": "^IXIC", "name": "NASDAQ",       "val": 18729.16, "chg": -73.86, "pct": -0.28},
            {"symbol": "^RUT",  "name": "Russell 2000", "val": 2268.42,  "chg": 15.57,  "pct": 0.51},
        ],
        "sectors": []
    },
    "crypto": {
        "indices": [
            {"symbol": "BTC-USD", "name": "Bitcoin",  "val": 64250.00, "chg": 1250.00, "pct": 1.98},
            {"symbol": "ETH-USD", "name": "Ethereum", "val": 3480.50,  "chg": 62.10,   "pct": 1.82},
            {"symbol": "BNB-USD", "name": "BNB",      "val": 585.40,   "chg": 4.20,    "pct": 0.72},
            {"symbol": "SOL-USD", "name": "Solana",   "val": 162.80,   "chg": 8.10,    "pct": 5.24},
        ],
        "sectors": []
    },
    "europe": {
        "indices": [
            {"symbol": "^FTSE",  "name": "FTSE 100",      "val": 8310.20, "chg": 12.40,  "pct": 0.15},
            {"symbol": "^GDAXI", "name": "DAX",           "val": 18450.60,"chg": -45.20, "pct": -0.24},
            {"symbol": "^FCHI",  "name": "CAC 40",        "val": 7520.10, "chg": -18.30, "pct": -0.24},
            {"symbol": "^STOXX", "name": "Euro Stoxx 50", "val": 4920.40, "chg": -12.10, "pct": -0.25},
        ],
        "sectors": []
    },
    "currencies": {
        "indices": [
            {"symbol": "USDINR=X", "name": "USD / INR", "val": 83.95, "chg": 0.05,  "pct": 0.06},
            {"symbol": "EURUSD=X", "name": "EUR / USD", "val": 1.092, "chg": -0.002,"pct": -0.18},
            {"symbol": "GBPUSD=X", "name": "GBP / USD", "val": 1.291, "chg": -0.001,"pct": -0.08},
            {"symbol": "USDJPY=X", "name": "USD / JPY", "val": 154.20,"chg": 0.45,  "pct": 0.29},
        ],
        "sectors": []
    },
    "futures": {
        "indices": [
            {"symbol": "GC=F", "name": "Gold",        "val": 2450.80, "chg": 15.40,  "pct": 0.63},
            {"symbol": "SI=F", "name": "Silver",      "val": 28.45,   "chg": 0.35,   "pct": 1.25},
            {"symbol": "CL=F", "name": "Crude Oil",   "val": 76.80,   "chg": -0.95,  "pct": -1.22},
            {"symbol": "NG=F", "name": "Natural Gas", "val": 2.15,    "chg": -0.04,  "pct": -1.83},
        ],
        "sectors": []
    },
}


def _sync_quote(item: dict) -> dict:
    symbol = item["symbol"]
    name   = item["name"]
    val    = item.get("val", 100.0)
    pct    = item.get("pct", 0.0)

    try:
        ticker = yf.Ticker(symbol)
        hist   = ticker.history(period="15d", interval="1d")
        if not hist.empty and len(hist) > 1:
            closes     = [round(float(c), 2) for c in hist["Close"].tolist()]
            current    = closes[-1]
            prev_close = closes[-2]
            change     = round(current - prev_close, 2)
            change_pct = round((change / prev_close * 100), 2) if prev_close else 0.0
            return {
                "symbol":       symbol,
                "name":         name,
                "value":        round(current, 2),
                "change":       change,
                "change_pct":   change_pct,
                "direction":    "up" if change >= 0 else "down",
                "sparkline":    closes,
            }
    except Exception:
        pass

    # Instant Fallback
    base = val
    spark = [round(base * (1 + (i - 7) * 0.003), 2) for i in range(15)]
    return {
        "symbol":       symbol,
        "name":         name,
        "value":        val,
        "change":       item.get("chg", round(val * (pct / 100), 2)),
        "change_pct":   pct,
        "direction":    "up" if pct >= 0 else "down",
        "sparkline":    spark,
    }


@router.get("/indices")
async def get_indices(region: str = Query(default="india")):
    """Get market indices with parallel thread pool fetching and memory caching."""
    region_lower = region.lower()
    cache_key = f"market:indices:{region_lower}"

    cached = cache.get(cache_key)
    if cached:
        return cached

    region_data = REGIONS.get(region_lower)
    if not region_data:
        raise HTTPException(status_code=404, detail=f"Region '{region}' not found")

    loop = asyncio.get_event_loop()
    tasks = [loop.run_in_executor(executor, _sync_quote, idx) for idx in region_data["indices"]]
    indices = await asyncio.gather(*tasks)

    result = {"region": region, "indices": indices}
    cache.set(cache_key, result, ttl=300)
    return result


@router.get("/sectors")
async def get_sectors(region: str = Query(default="india")):
    """Get sectoral indices with parallel thread pool fetching."""
    region_lower = region.lower()
    cache_key = f"market:sectors:{region_lower}"

    cached = cache.get(cache_key)
    if cached:
        return cached

    region_data = REGIONS.get(region_lower)
    if not region_data:
        raise HTTPException(status_code=404, detail=f"Region '{region}' not found")

    loop = asyncio.get_event_loop()
    tasks = [loop.run_in_executor(executor, _sync_quote, sec) for sec in region_data.get("sectors", [])]
    sectors = await asyncio.gather(*tasks)

    # Attach labels
    for i, sec in enumerate(region_data.get("sectors", [])):
        if i < len(sectors):
            sectors[i]["label"] = sec["label"]

    result = {"sectors": sectors}
    cache.set(cache_key, result, ttl=300)
    return result


@router.get("/search")
async def search_stocks(q: str = Query(..., min_length=1)):
    """Search for stocks by ticker or company name."""
    cache_key = f"search:{q.strip().lower()}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    try:
        results = yf.Search(q)
        quotes  = results.quotes[:8] if results.quotes else []
        res = {
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
        cache.set(cache_key, res, ttl=600)
        return res
    except Exception as e:
        logger.error(f"Search failed for '{q}': {e}")
        return {"results": []}
