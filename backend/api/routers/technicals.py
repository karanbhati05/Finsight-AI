"""
backend/api/routers/technicals.py
Technical Indicators & 5-Year Historical Daily Candlesticks.
"""

from fastapi import APIRouter
from backend.providers.fmp_client import FMPClient
from backend.providers.alphavantage_client import TechnicalAnalysisClient

router = APIRouter()


@router.get("/candlesticks/{ticker}")
async def get_candlesticks(ticker: str, period: str = "1y", interval: str = "1d"):
    """Get real audited OHLCV Candlestick data for interactive charting."""
    candles = await FMPClient.get_historical_candlesticks(ticker)
    return {"ticker": ticker.upper(), "candlesticks": candles}


@router.get("/indicators/{ticker}")
async def get_indicators(ticker: str):
    """Get RSI 14, MACD, EMAs (20, 50, 200), and Bollinger Bands."""
    data = await TechnicalAnalysisClient.get_technical_indicators(ticker)
    return data
