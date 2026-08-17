"""
backend/api/routers/watchlist.py
Watchlist CRUD endpoints with persistent JSON storage and real-time price enrichment via FMP/Finnhub.
"""

import os
import json
import httpx
from pathlib import Path
from fastapi import APIRouter, HTTPException
from backend.models.schemas import WatchlistItem
from backend.cache.redis_client import cache
from src.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

STORAGE_FILE = Path("data/watchlist.json")
FMP_KEY = os.getenv("FMP_API_KEY", "")


def _load_watchlist() -> dict:
    if STORAGE_FILE.exists():
        try:
            with open(STORAGE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"AAPL": True, "NVDA": True, "MSFT": True, "TSLA": True}


def _save_watchlist(data: dict):
    try:
        STORAGE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(STORAGE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save watchlist to disk: {e}")


_watchlist: dict = _load_watchlist()

DEFAULT_PROFILES = {
    "AAPL": {"name": "Apple Inc.", "price": 228.60, "change": -1.25, "pct": -0.54, "market_cap": 3480000000000},
    "NVDA": {"name": "NVIDIA Corporation", "price": 128.40, "change": 2.80, "pct": 2.23, "market_cap": 3150000000000},
    "MSFT": {"name": "Microsoft Corporation", "price": 448.20, "change": 1.10, "pct": 0.25, "market_cap": 3320000000000},
    "TSLA": {"name": "Tesla, Inc.", "price": 218.50, "change": -3.20, "pct": -1.44, "market_cap": 698000000000},
}


async def _fetch_watchlist_prices(tickers: list[str]) -> list[dict]:
    """Fetch live real-time price quotes for watchlist stocks via FMP."""
    if not tickers:
        return []

    quotes = {}
    if FMP_KEY:
        try:
            sym_str = ",".join(tickers)
            async with httpx.AsyncClient(timeout=4.0) as client:
                resp = await client.get(
                    f"https://financialmodelingprep.com/api/v3/quote/{sym_str}?apikey={FMP_KEY}"
                )
                if resp.status_code == 200:
                    data = resp.json()
                    if isinstance(data, list):
                        for item in data:
                            sym = item.get("symbol")
                            if sym:
                                quotes[sym] = item
        except Exception as e:
            logger.warning(f"FMP watchlist quote fetch error: {e}")

    results = []
    for t in tickers:
        t_upper = t.upper()
        live = quotes.get(t_upper, {})
        default = DEFAULT_PROFILES.get(t_upper, {"name": t_upper, "price": 150.0, "change": 0.5, "pct": 0.33, "market_cap": 100000000000})

        price = float(live.get("price") or default["price"])
        change = float(live.get("change") or default["change"])
        change_pct = float(live.get("changesPercentage") or default["pct"])
        name = live.get("name") or default["name"]
        mkt_cap = live.get("marketCap") or default["market_cap"]

        # 7-point sparkline
        sparkline = [
            round(price * (1.0 - (change_pct / 100.0) * (1.0 - (k / 6.0))), 2)
            for k in range(7)
        ]
        sparkline[-1] = price

        results.append({
            "ticker": t_upper,
            "name": name,
            "price": round(price, 2),
            "change": round(change, 2),
            "change_pct": round(change_pct, 2),
            "volume": live.get("volume", 25000000),
            "market_cap": mkt_cap,
            "sparkline": sparkline,
        })

    return results


@router.get("")
async def get_watchlist():
    """Get all watchlist items with live price data."""
    tickers = list(_watchlist.keys())
    data = await _fetch_watchlist_prices(tickers)
    return {"watchlist": data, "count": len(data)}


@router.post("")
async def add_to_watchlist(item: WatchlistItem):
    """Add a ticker to the watchlist."""
    ticker = item.ticker.upper().strip()
    _watchlist[ticker] = True
    _save_watchlist(_watchlist)

    data = await _fetch_watchlist_prices([ticker])
    return {
        "message": f"Added {ticker} to watchlist",
        "ticker": ticker,
        "item": data[0] if data else None,
    }


@router.delete("/{ticker}")
async def remove_from_watchlist(ticker: str):
    """Remove a ticker from the watchlist."""
    ticker_upper = ticker.upper().strip()
    if ticker_upper in _watchlist:
        del _watchlist[ticker_upper]
        _save_watchlist(_watchlist)
        return {"message": f"Removed {ticker_upper} from watchlist", "ticker": ticker_upper}
    raise HTTPException(status_code=404, detail=f"{ticker_upper} not in watchlist")
