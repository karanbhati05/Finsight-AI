# src/ingestion/yfinance_fetcher.py

import yfinance as yf
import pandas as pd
import numpy as np
from src.utils.logger import get_logger
from src.utils.helpers import save_dataframe

logger = get_logger(__name__)


def fetch_price_data(ticker: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
    """
    Fetch historical OHLCV data for a stock ticker.

    OHLCV = Open, High, Low, Close, Volume — the standard format
    for any financial time series. Every trading system in the world
    uses this format.

    Args:
        ticker:   stock symbol e.g. "AAPL"
        period:   how far back to go — "1y", "2y", "6mo", "max"
        interval: bar size — "1d" daily, "1h" hourly, "1wk" weekly
    """
    logger.info(f"Fetching price data | ticker={ticker} | period={period}")

    stock = yf.Ticker(ticker)
    df = stock.history(period=period, interval=interval)

    if df.empty:
        raise ValueError(f"No price data returned for {ticker}. Check the ticker symbol.")

    # yfinance returns DatetimeIndex — reset to a clean integer index
    df.reset_index(inplace=True)

    # Standardize column names to lowercase
    df.columns = [c.lower().replace(" ", "_") for c in df.columns]

    # Add ticker column so we can merge multiple tickers later
    df["ticker"] = ticker

    logger.info(f"Fetched {len(df)} rows for {ticker}")
    return df


def fetch_company_info(ticker: str) -> dict:
    """
    Fetch fundamental company metadata.
    Used for context in the RAG chatbot and dashboard header cards.

    Returns things like: sector, industry, market cap, P/E ratio,
    52-week high/low, analyst target price.
    """
    stock = yf.Ticker(ticker)
    info = stock.info

    # Extract only the fields we care about
    # (yfinance returns 100+ fields — we keep the useful ones)
    fields = [
        "longName", "sector", "industry", "marketCap",
        "trailingPE", "forwardPE", "dividendYield",
        "fiftyTwoWeekHigh", "fiftyTwoWeekLow",
        "targetMeanPrice", "recommendationMean",
        "numberOfAnalystOpinions",
    ]

    return {k: info.get(k) for k in fields}


def add_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute technical indicators from raw OHLCV data.
    These become features in the ML model alongside sentiment scores.

    Indicators computed:
        - price_ma5    : 5-day moving average (short-term trend)
        - price_ma20   : 20-day moving average (medium-term trend)
        - volume_change_pct : daily volume change % (unusual activity signal)
        - rsi_14       : Relative Strength Index, 14-day (momentum oscillator)
        - price_direction : TARGET variable — did price go UP next day? (1/0)

    Why these specific indicators?
        MA crossovers (ma5 crossing ma20) are one of the oldest trading signals.
        RSI above 70 = overbought, below 30 = oversold — widely used in quant finance.
        Volume spikes often precede price moves — hence volume_change_pct.
    """
    df = df.copy().sort_values("date").reset_index(drop=True)

    # ── Moving Averages ──────────────────────────────────────────────────────
    df["price_ma5"]  = df["close"].rolling(window=5,  min_periods=1).mean()
    df["price_ma20"] = df["close"].rolling(window=20, min_periods=1).mean()

    # MA crossover signal: 1 when short-term trend is above long-term
    df["ma_crossover"] = (df["price_ma5"] > df["price_ma20"]).astype(int)

    # ── Volume ───────────────────────────────────────────────────────────────
    # pct_change() computes (current - previous) / previous
    # fill_value=0 avoids NaN on first row
    # NEW
    df["volume_change_pct"] = (
        df["volume"]
        .pct_change()
        .replace([float('inf'), float('-inf')], 0)
        .fillna(0) * 100
    )

    # ── RSI (Relative Strength Index, 14-day) ────────────────────────────────
    # RSI measures momentum: how fast is price moving up vs down?
    # Formula: RSI = 100 - (100 / (1 + avg_gain / avg_loss))
    delta = df["close"].diff()                        # daily price changes
    gain  = delta.clip(lower=0)                       # keep only positive moves
    loss  = (-delta).clip(lower=0)                    # keep only negative moves (as positive)

    avg_gain = gain.rolling(window=14, min_periods=1).mean()
    avg_loss = loss.rolling(window=14, min_periods=1).mean()

    # Avoid division by zero when avg_loss is 0 (all gains, no losses)
    rs = avg_gain / avg_loss.replace(0, np.nan)
    df["rsi_14"] = (100 - (100 / (1 + rs))).fillna(100)

    # ── Daily Return ─────────────────────────────────────────────────────────
    df["daily_return"] = df["close"].pct_change().fillna(0) * 100

    # ── TARGET VARIABLE ──────────────────────────────────────────────────────
    # Did the closing price go UP the NEXT day?
    # shift(-1) moves tomorrow's price into today's row
    # We predict this from today's features (no lookahead bias)
    df["price_direction"] = (df["close"].shift(-1) > df["close"]).astype(int)

    # Drop the last row — it has no next-day price to predict
    df = df[:-1].copy()

    # Drop rows where indicators couldn't be computed cleanly
    df = df.dropna(subset=["price_ma20", "rsi_14"]).reset_index(drop=True)

    logger.info(f"Technical indicators added | {len(df)} rows remaining after cleaning")
    return df


def fetch_and_save(
    ticker: str,
    period: str = "1y",
    save_dir: str = "data/raw"
) -> pd.DataFrame:
    """
    Full fetch → process → save pipeline for one ticker.
    Called by data_pipeline.py for each ticker in the watchlist.
    """
    df = fetch_price_data(ticker, period=period)
    df = add_technical_indicators(df)
    save_dataframe(df, f"{save_dir}/{ticker}/price_data.csv")
    return df