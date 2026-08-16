"""
backend/api/routers/technicals.py
Technical Indicators & Candlestick series (Powered by Alpha Vantage / Twelve Data math).
"""

from fastapi import APIRouter
from backend.providers.alphavantage_client import TechnicalAnalysisClient

router = APIRouter()


@router.get("/candlesticks/{ticker}")
async def get_candlesticks(ticker: str, period: str = "3mo", interval: str = "1d"):
    """Get OHLCV Candlestick data for interactive charting."""
    candles = await TechnicalAnalysisClient.get_candlesticks(ticker, period=period, interval=interval)
    return {"ticker": ticker.upper(), "candlesticks": candles}


@router.get("/indicators/{ticker}")
async def get_indicators(ticker: str):
    """Get RSI 14, MACD, EMAs (20, 50, 200), and Bollinger Bands."""
    data = await TechnicalAnalysisClient.get_technical_indicators(ticker)
    return data
