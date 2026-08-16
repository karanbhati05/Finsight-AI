"""
backend/providers/alphavantage_client.py
Technical Indicators & Candlestick OHLCV Data Client (Alpha Vantage + yfinance math).
Computes:
  - Intraday & Daily Candlesticks (Open, High, Low, Close, Volume)
  - Exponential Moving Averages (EMA 20, 50, 200)
  - Relative Strength Index (RSI 14)
  - Moving Average Convergence Divergence (MACD 12, 26, 9)
  - Bollinger Bands (Upper, Middle, Lower 20, 2)
"""

import os
import httpx
import numpy as np
import pandas as pd
import yfinance as yf
from backend.cache.redis_client import cache
from src.utils.logger import get_logger

logger = get_logger(__name__)

ALPHAVANTAGE_API_KEY = os.getenv("ALPHAVANTAGE_API_KEY", "")


class TechnicalAnalysisClient:
    """Computes high-performance technical indicators and candlestick streams."""

    @staticmethod
    async def get_candlesticks(ticker: str, period: str = "3mo", interval: str = "1d") -> list[dict]:
        """Fetch OHLCV candlestick series."""
        cache_key = f"tech:candles:{ticker.upper()}:{period}:{interval}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        try:
            t = yf.Ticker(ticker)
            df = t.history(period=period, interval=interval)
            if df.empty:
                return []

            candles = []
            for idx, row in df.iterrows():
                time_str = idx.strftime("%Y-%m-%d %H:%M") if interval in ["1m", "5m", "15m", "1h"] else idx.strftime("%Y-%m-%d")
                candles.append({
                    "time": time_str,
                    "open": round(float(row["Open"]), 2),
                    "high": round(float(row["High"]), 2),
                    "low": round(float(row["Low"]), 2),
                    "close": round(float(row["Close"]), 2),
                    "volume": int(row["Volume"]),
                })

            cache.set(cache_key, candles, ttl=60)
            return candles
        except Exception as e:
            logger.error(f"Failed to fetch candlesticks for {ticker}: {e}")
            return []

    @staticmethod
    async def get_technical_indicators(ticker: str) -> dict:
        """Compute full suite of technical indicators: EMA, RSI, MACD, Bollinger Bands."""
        cache_key = f"tech:indicators:{ticker.upper()}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        try:
            t = yf.Ticker(ticker)
            df = t.history(period="1y", interval="1d")
            if df.empty or len(df) < 30:
                return {}

            close = df["Close"]

            # 1. EMAs
            ema20 = close.ewm(span=20, adjust=False).mean()
            ema50 = close.ewm(span=50, adjust=False).mean()
            ema200 = close.ewm(span=200, adjust=False).mean() if len(close) >= 200 else close.ewm(span=len(close), adjust=False).mean()

            # 2. RSI (14)
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / (loss + 1e-9)
            rsi = 100 - (100 / (1 + rs))

            # 3. MACD (12, 26, 9)
            ema12 = close.ewm(span=12, adjust=False).mean()
            ema26 = close.ewm(span=26, adjust=False).mean()
            macd_line = ema12 - ema26
            signal_line = macd_line.ewm(span=9, adjust=False).mean()
            macd_hist = macd_line - signal_line

            # 4. Bollinger Bands (20, 2)
            sma20 = close.rolling(window=20).mean()
            std20 = close.rolling(window=20).std()
            upper_bb = sma20 + (std20 * 2)
            lower_bb = sma20 - (std20 * 2)

            # Build historical time-series alignment for charts
            history = []
            for i in range(max(0, len(df) - 60), len(df)):
                idx = df.index[i]
                history.append({
                    "date": idx.strftime("%Y-%m-%d"),
                    "close": round(float(close.iloc[i]), 2),
                    "ema20": round(float(ema20.iloc[i]), 2) if not pd.isna(ema20.iloc[i]) else None,
                    "ema50": round(float(ema50.iloc[i]), 2) if not pd.isna(ema50.iloc[i]) else None,
                    "rsi": round(float(rsi.iloc[i]), 2) if not pd.isna(rsi.iloc[i]) else 50.0,
                    "macd": round(float(macd_line.iloc[i]), 2) if not pd.isna(macd_line.iloc[i]) else 0.0,
                    "signal": round(float(signal_line.iloc[i]), 2) if not pd.isna(signal_line.iloc[i]) else 0.0,
                    "hist": round(float(macd_hist.iloc[i]), 2) if not pd.isna(macd_hist.iloc[i]) else 0.0,
                    "bb_upper": round(float(upper_bb.iloc[i]), 2) if not pd.isna(upper_bb.iloc[i]) else None,
                    "bb_lower": round(float(lower_bb.iloc[i]), 2) if not pd.isna(lower_bb.iloc[i]) else None,
                })

            current_rsi = float(rsi.dropna().iloc[-1]) if not rsi.dropna().empty else 50.0
            current_macd = float(macd_line.dropna().iloc[-1]) if not macd_line.dropna().empty else 0.0
            current_signal = float(signal_line.dropna().iloc[-1]) if not signal_line.dropna().empty else 0.0

            summary = {
                "rsi_14": round(current_rsi, 2),
                "rsi_signal": "Oversold (Buy)" if current_rsi < 30 else "Overbought (Sell)" if current_rsi > 70 else "Neutral",
                "macd_line": round(current_macd, 2),
                "macd_signal_line": round(current_signal, 2),
                "macd_trend": "Bullish Crossover" if current_macd > current_signal else "Bearish Trend",
                "ema20": round(float(ema20.iloc[-1]), 2),
                "ema50": round(float(ema50.iloc[-1]), 2),
                "ema200": round(float(ema200.iloc[-1]), 2),
                "trend": "Bullish (Above 50 EMA)" if close.iloc[-1] > ema50.iloc[-1] else "Bearish (Below 50 EMA)",
                "series": history,
            }

            cache.set(cache_key, summary, ttl=120)
            return summary
        except Exception as e:
            logger.error(f"Failed to compute technical indicators for {ticker}: {e}")
            return {}
