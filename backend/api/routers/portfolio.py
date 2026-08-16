"""
backend/api/routers/portfolio.py
Portfolio CRUD endpoints — in-memory storage with real-time P&L calculation.

Holdings are stored as {ticker: {shares, buy_price}} and enriched with
current market prices from yfinance to compute unrealized P&L.
"""

import yfinance as yf
from fastapi import APIRouter, HTTPException
from backend.models.schemas import PortfolioItem
from backend.cache.redis_client import cache
from src.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

# ── In-memory portfolio storage ──────────────────────────────────────────────
# Key: ticker (uppercase), Value: {"shares": float, "buy_price": float}
_portfolio: dict = {}


def _get_current_price(ticker: str) -> tuple:
    """
    Fetch current price and company name for a portfolio holding.
    Returns (current_price, company_name) or (None, None) on failure.
    """
    try:
        t    = yf.Ticker(ticker)
        hist = t.history(period="5d", interval="1d")

        if hist.empty:
            return None, None

        current = hist["Close"].tolist()[-1]

        try:
            info = t.info
            name = info.get("shortName", info.get("longName", ticker))
        except Exception:
            name = ticker

        return round(current, 2), name
    except Exception as e:
        logger.error(f"Failed to fetch price for {ticker}: {e}")
        return None, None


@router.get("")
async def get_portfolio():
    """
    Get all portfolio holdings with current prices and P&L.
    Computes unrealized profit/loss for each holding and totals.
    """
    if not _portfolio:
        return {
            "holdings":      [],
            "total_value":   0.0,
            "total_pnl":     0.0,
            "total_pnl_pct": 0.0,
        }

    holdings    = []
    total_value = 0.0
    total_cost  = 0.0

    for ticker, position in _portfolio.items():
        shares    = position["shares"]
        buy_price = position["buy_price"]
        cost      = shares * buy_price

        # Check cache first
        cache_key = f"portfolio:price:{ticker}"
        cached = cache.get(cache_key)

        if cached:
            current = cached["price"]
            name    = cached["name"]
        else:
            current, name = _get_current_price(ticker)
            if current is None:
                current = buy_price
                name    = ticker
            else:
                cache.set(cache_key, {"price": current, "name": name}, ttl=120)

        market_value = round(shares * current, 2)
        pnl          = round(market_value - cost, 2)
        pnl_pct      = round((pnl / cost * 100), 2) if cost else 0.0

        holdings.append({
            "ticker":       ticker,
            "name":         name,
            "shares":       shares,
            "buy_price":    buy_price,
            "current":      current,
            "pnl":          pnl,
            "pnl_pct":      pnl_pct,
            "direction":    "up" if pnl >= 0 else "down",
            "market_value": market_value,
        })

        total_value += market_value
        total_cost  += cost

    total_pnl     = round(total_value - total_cost, 2)
    total_pnl_pct = round((total_pnl / total_cost * 100), 2) if total_cost else 0.0

    return {
        "holdings":      holdings,
        "total_value":   round(total_value, 2),
        "total_pnl":     total_pnl,
        "total_pnl_pct": total_pnl_pct,
    }


@router.post("")
async def add_to_portfolio(item: PortfolioItem):
    """
    Add a new holding or update an existing position.
    If the ticker already exists, it adds to the existing position
    using weighted average cost basis.
    """
    ticker = item.ticker.upper()

    if ticker in _portfolio:
        # Update existing position with weighted average buy price
        existing = _portfolio[ticker]
        total_shares = existing["shares"] + item.shares
        total_cost   = (existing["shares"] * existing["buy_price"]) + (item.shares * item.buy_price)
        avg_price    = round(total_cost / total_shares, 2) if total_shares else item.buy_price

        _portfolio[ticker] = {
            "shares":    round(total_shares, 4),
            "buy_price": avg_price,
        }
        logger.info(f"Updated {ticker} position: {total_shares} shares @ ${avg_price}")
    else:
        _portfolio[ticker] = {
            "shares":    item.shares,
            "buy_price": item.buy_price,
        }
        logger.info(f"Added {ticker}: {item.shares} shares @ ${item.buy_price}")

    # Invalidate price cache
    cache.delete(f"portfolio:price:{ticker}")

    return {
        "message": f"{ticker} added to portfolio",
        "ticker":  ticker,
        "shares":  _portfolio[ticker]["shares"],
        "buy_price": _portfolio[ticker]["buy_price"],
    }


@router.delete("/{ticker}")
async def remove_from_portfolio(ticker: str):
    """Remove a holding from the portfolio."""
    ticker_upper = ticker.upper()

    if ticker_upper not in _portfolio:
        raise HTTPException(status_code=404, detail=f"{ticker_upper} not in portfolio")

    del _portfolio[ticker_upper]
    cache.delete(f"portfolio:price:{ticker_upper}")
    logger.info(f"Removed {ticker_upper} from portfolio")

    return {"message": f"{ticker_upper} removed from portfolio"}
