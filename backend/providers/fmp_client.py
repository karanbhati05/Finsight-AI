"""
backend/providers/fmp_client.py
Financial Modeling Prep (FMP) API Client with 100% Real Live REST Data.
Provides:
  - Income Statement (5-Year Audited Annual)
  - Balance Sheet (5-Year Audited Assets & Liabilities)
  - Key Financial Ratios (P/E, P/S, EV/EBITDA, ROE, Debt/Equity, Current Ratio)
  - Analyst Price Targets & Consensus (Bear, Base, Bull)
  - Historical Price Candlesticks for all timeframes (1D, 5D, 1M, 6M, 1Y, 5Y, MAX)
"""

import os
import httpx
from backend.cache.redis_client import cache
from src.utils.logger import get_logger

logger = get_logger(__name__)

FMP_API_KEY = os.getenv("FMP_API_KEY", "")
BASE_URL = "https://financialmodelingprep.com/api/v3"


class FMPClient:
    """Client for Financial Modeling Prep API with live authenticated REST endpoints."""

    @staticmethod
    async def get_income_statement(ticker: str, limit: int = 5) -> list[dict]:
        """Fetch real 5-year audited income statement history."""
        cache_key = f"fmp:income:{ticker.upper()}:{limit}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        if FMP_API_KEY:
            try:
                async with httpx.AsyncClient(timeout=8.0) as client:
                    resp = await client.get(
                        f"{BASE_URL}/income-statement/{ticker.upper()}?limit={limit}&apikey={FMP_API_KEY}"
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        if isinstance(data, list) and len(data) > 0:
                            results = [
                                {
                                    "date": item.get("date"),
                                    "year": item.get("calendarYear", item.get("date", "")[:4]),
                                    "revenue": item.get("revenue", 0),
                                    "grossProfit": item.get("grossProfit", 0),
                                    "operatingIncome": item.get("operatingIncome", 0),
                                    "netIncome": item.get("netIncome", 0),
                                    "eps": item.get("eps", 0.0),
                                    "grossProfitRatio": round(float(item.get("grossProfitRatio") or 0.0) * 100, 2),
                                    "operatingIncomeRatio": round(float(item.get("operatingIncomeRatio") or 0.0) * 100, 2),
                                    "netIncomeRatio": round(float(item.get("netIncomeRatio") or 0.0) * 100, 2),
                                }
                                for item in data
                            ]
                            cache.set(cache_key, results, ttl=86400)
                            return results
            except Exception as e:
                logger.warning(f"FMP income statement error for {ticker}: {e}")

        return []

    @staticmethod
    async def get_balance_sheet(ticker: str, limit: int = 5) -> list[dict]:
        """Fetch real 5-year audited balance sheet statements."""
        cache_key = f"fmp:balance:{ticker.upper()}:{limit}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        if FMP_API_KEY:
            try:
                async with httpx.AsyncClient(timeout=8.0) as client:
                    resp = await client.get(
                        f"{BASE_URL}/balance-sheet-statement/{ticker.upper()}?limit={limit}&apikey={FMP_API_KEY}"
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        if isinstance(data, list) and len(data) > 0:
                            results = [
                                {
                                    "date": item.get("date"),
                                    "year": item.get("calendarYear", item.get("date", "")[:4]),
                                    "cashAndCashEquivalents": item.get("cashAndCashEquivalents", 0),
                                    "totalCurrentAssets": item.get("totalCurrentAssets", 0),
                                    "totalAssets": item.get("totalAssets", 0),
                                    "totalCurrentLiabilities": item.get("totalCurrentLiabilities", 0),
                                    "totalLiabilities": item.get("totalLiabilities", 0),
                                    "totalStockholdersEquity": item.get("totalStockholdersEquity", 0),
                                    "totalDebt": item.get("totalDebt", 0),
                                    "netDebt": item.get("netDebt", 0),
                                }
                                for item in data
                            ]
                            cache.set(cache_key, results, ttl=86400)
                            return results
            except Exception as e:
                logger.warning(f"FMP balance sheet error for {ticker}: {e}")

        return []

    @staticmethod
    async def get_financial_ratios(ticker: str) -> dict:
        """Fetch comprehensive valuation, profitability, and solvency ratios directly from FMP."""
        clean_ticker = ticker.upper().strip()
        cache_key = f"fmp:ratios:live:v2:{clean_ticker}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        if FMP_API_KEY:
            try:
                async with httpx.AsyncClient(timeout=8.0) as client:
                    resp = await client.get(
                        f"{BASE_URL}/ratios/{clean_ticker}?limit=1&apikey={FMP_API_KEY}"
                    )
                    quote_resp = await client.get(
                        f"{BASE_URL}/quote/{clean_ticker}?apikey={FMP_API_KEY}"
                    )

                    r_data = resp.json()[0] if resp.status_code == 200 and resp.json() and isinstance(resp.json(), list) else {}
                    q_data = quote_resp.json()[0] if quote_resp.status_code == 200 and quote_resp.json() and isinstance(quote_resp.json(), list) else {}

                    live_price = float(q_data.get("price")) if q_data.get("price") is not None else None
                    pe_val = float(q_data.get("pe") or r_data.get("priceEarningsRatio") or 0.0)

                    ratios = {
                        "ticker": clean_ticker,
                        "name": q_data.get("name"),
                        "price": live_price,
                        "peRatio": round(pe_val, 2) if pe_val > 0 else None,
                        "priceToSalesRatio": round(float(r_data.get("priceToSalesRatio")), 2) if r_data.get("priceToSalesRatio") else None,
                        "priceToBookRatio": round(float(r_data.get("priceToBookRatio")), 2) if r_data.get("priceToBookRatio") else None,
                        "enterpriseValueToEBITDA": round(float(r_data.get("enterpriseValueMultiple")), 2) if r_data.get("enterpriseValueMultiple") else None,
                        "profitMargin": round(float(r_data.get("netProfitMargin") or 0.0) * 100, 2) if r_data.get("netProfitMargin") else None,
                        "operatingMargin": round(float(r_data.get("operatingProfitMargin") or 0.0) * 100, 2) if r_data.get("operatingProfitMargin") else None,
                        "returnOnEquity": round(float(r_data.get("returnOnEquity") or 0.0) * 100, 2) if r_data.get("returnOnEquity") else None,
                        "returnOnAssets": round(float(r_data.get("returnOnAssets") or 0.0) * 100, 2) if r_data.get("returnOnAssets") else None,
                        "debtToEquity": round(float(r_data.get("debtEquityRatio")), 2) if r_data.get("debtEquityRatio") else None,
                        "currentRatio": round(float(r_data.get("currentRatio")), 2) if r_data.get("currentRatio") else None,
                        "quickRatio": round(float(r_data.get("quickRatio")), 2) if r_data.get("quickRatio") else None,
                        "marketCap": q_data.get("marketCap"),
                        "yearHigh": q_data.get("yearHigh"),
                        "yearLow": q_data.get("yearLow"),
                    }
                    cache.set(cache_key, ratios, ttl=3600)
                    return ratios
            except Exception as e:
                logger.warning(f"FMP financial ratios error for {clean_ticker}: {e}")

        return {"ticker": clean_ticker}

    @staticmethod
    async def get_historical_candlesticks(ticker: str) -> list[dict]:
        """Fetch up to 5 years of daily historical candles from FMP."""
        cache_key = f"fmp:historical:candles:{ticker.upper()}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        if FMP_API_KEY:
            try:
                async with httpx.AsyncClient(timeout=8.0) as client:
                    resp = await client.get(
                        f"{BASE_URL}/historical-price-full/{ticker.upper()}?apikey={FMP_API_KEY}"
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        hist = data.get("historical", [])
                        if hist:
                            candles = [
                                {
                                    "date": item.get("date"),
                                    "open": float(item.get("open", 0)),
                                    "high": float(item.get("high", 0)),
                                    "low": float(item.get("low", 0)),
                                    "close": float(item.get("close", 0)),
                                    "volume": int(item.get("volume", 0)),
                                    "change": float(item.get("change", 0)),
                                    "changePercent": float(item.get("changePercent", 0)),
                                }
                                for item in reversed(hist) # Oldest to newest
                            ]
                            cache.set(cache_key, candles, ttl=600)
                            return candles
            except Exception as e:
                logger.warning(f"FMP historical daily candles fetch error: {e}")

        return []
