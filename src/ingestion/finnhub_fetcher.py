# src/ingestion/finnhub_fetcher.py

import os
import time
import requests
import pandas as pd
from datetime import datetime, timedelta
from src.utils.logger import get_logger
from src.utils.helpers import clean_text, save_dataframe

logger = get_logger(__name__)

FINNHUB_BASE = "https://finnhub.io/api/v1"


def fetch_company_news(
    ticker:       str,
    days_back:    int = 365,
    max_articles: int = 500,
) -> pd.DataFrame:
    """
    Fetch company news from Finnhub.

    Finnhub advantages over NewsAPI:
        - Up to 1 year of history (NewsAPI free = 30 days)
        - Finance-specific sources only
        - Already filtered to company-relevant news
        - No boolean query needed — just pass the ticker

    Args:
        ticker:       stock symbol e.g. "AAPL"
        days_back:    how many days of history to fetch (max 365 on free tier)
        max_articles: cap on total articles returned

    Returns:
        DataFrame with columns matching NewsAPI output format
        so the rest of the pipeline works unchanged
    """
    api_key = os.getenv("FINNHUB_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "FINNHUB_API_KEY not set in .env file.\n"
            "Get your free key at: https://finnhub.io"
        )

    # Finnhub uses Unix timestamps for date range
    to_date   = datetime.today()
    from_date = to_date - timedelta(days=days_back)

    from_str = from_date.strftime("%Y-%m-%d")
    to_str   = to_date.strftime("%Y-%m-%d")

    logger.info(
        f"Fetching Finnhub news | ticker={ticker} | "
        f"from={from_str} | to={to_str}"
    )

    url = f"{FINNHUB_BASE}/company-news"
    params = {
        "symbol": ticker,
        "from":   from_str,
        "to":     to_str,
        "token":  api_key,
    }

    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        articles = response.json()
    except requests.exceptions.Timeout:
        logger.error("Finnhub request timed out")
        return pd.DataFrame()
    except requests.exceptions.HTTPError as e:
        logger.error(f"Finnhub HTTP error: {e}")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Finnhub fetch failed: {e}")
        return pd.DataFrame()

    if not articles:
        logger.warning(f"No articles returned from Finnhub for {ticker}")
        return pd.DataFrame()

    # Cap at max_articles — take most recent
    articles = articles[:max_articles]

    records = []
    for article in articles:
        headline = article.get("headline", "") or ""
        summary  = article.get("summary",  "") or ""

        if not headline:
            continue

        # Convert Unix timestamp to ISO format
        ts = article.get("datetime", 0)
        try:
            published = datetime.utcfromtimestamp(ts).strftime("%Y-%m-%dT%H:%M:%SZ")
        except Exception:
            published = ""

        records.append({
            "ticker":       ticker,
            "title":        clean_text(headline),
            "description":  clean_text(summary),
            # Finnhub doesn't give full content — use summary as content
            "content":      clean_text(summary),
            "source":       article.get("source", "Finnhub"),
            "published_at": published,
            "url":          article.get("url", ""),
            "category":     article.get("category", ""),
        })

    df = pd.DataFrame(records)

    if df.empty:
        logger.warning(f"No valid articles parsed for {ticker}")
        return df

    # Convert to datetime with UTC timezone
    df["published_at"] = pd.to_datetime(
        df["published_at"], utc=True, errors="coerce"
    )

    # Sort newest first
    df = df.sort_values("published_at", ascending=False).reset_index(drop=True)

    logger.info(f"Fetched {len(df)} articles from Finnhub for {ticker}")
    return df


def fetch_market_sentiment(ticker: str) -> dict:
    """
    Fetch Finnhub's own sentiment score for a ticker.

    Finnhub computes sentiment from news automatically.
    We can use this as an additional feature or cross-validation
    against our FinBERT scores.

    Returns:
        Dict with buzz score, sentiment score, weekly/monthly sentiment
    """
    api_key = os.getenv("FINNHUB_API_KEY")
    url     = f"{FINNHUB_BASE}/news-sentiment"
    params  = {"symbol": ticker, "token": api_key}

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        return {
            "buzz_articles_last_week":  data.get("buzz", {}).get("articlesInLastWeek", 0),
            "buzz_weekly_average":      data.get("buzz", {}).get("weeklyAverage", 0),
            "buzz_score":               data.get("buzz", {}).get("buzz", 0),
            "company_news_score":       data.get("companyNewsScore", 0),
            "sector_avg_bullish":       data.get("sectorAverageBullishPercent", 0),
            "sector_avg_score":         data.get("sectorAverageNewsScore", 0),
            "sentiment_bearish":        data.get("sentiment", {}).get("bearishPercent", 0),
            "sentiment_bullish":        data.get("sentiment", {}).get("bullishPercent", 0),
        }
    except Exception as e:
        logger.error(f"Finnhub sentiment fetch failed: {e}")
        return {}


def save_finnhub_news(
    df:       pd.DataFrame,
    ticker:   str,
    save_dir: str = "data/raw",
) -> str:
    """Save Finnhub news to CSV."""
    path = f"{save_dir}/{ticker}/finnhub_news.csv"
    save_dataframe(df, path)
    return path