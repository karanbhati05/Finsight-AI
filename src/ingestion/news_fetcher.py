# src/ingestion/news_fetcher.py

import os
import time
import requests
import pandas as pd
from datetime import datetime, timedelta
from src.utils.logger import get_logger
from src.utils.helpers import clean_text, save_dataframe
from src.utils.constants import TICKER_COMPANY_MAP

logger = get_logger(__name__)

NEWS_API_BASE = "https://newsapi.org/v2/everything"

# NewsAPI free tier limits: 100 requests/day, 1 request/second
# We respect this with a small delay between calls
REQUEST_DELAY_SECONDS = 1.2


def build_query(ticker: str) -> str:
    """
    Build a search query that finds financial news about a company.

    Why not just search the ticker symbol?
    Searching "AAPL" misses articles that say "Apple reported earnings..."
    Searching "Apple" alone returns articles about fruit.
    Combining both with financial keywords gets the best results.

    Args:
        ticker: stock symbol e.g. "AAPL"

    Returns:
        query string optimised for financial news
    """
    company = TICKER_COMPANY_MAP.get(ticker, ticker)

    # NewsAPI supports boolean operators: OR, AND, quotes for exact match
    query = f'("{company}" OR "{ticker}") AND (earnings OR revenue OR stock OR analyst OR forecast)'

    return query


def fetch_news(
    ticker:        str,
    days_back:     int = 30,
    max_articles:  int = 50,
    language:      str = "en",
) -> pd.DataFrame:
    """
    Fetch recent news articles for a stock ticker.

    Args:
        ticker:       stock symbol e.g. "AAPL"
        days_back:    how many days of news to fetch (free tier max: 30)
        max_articles: cap on number of articles (NewsAPI max per request: 100)
        language:     article language filter

    Returns:
        DataFrame with columns: ticker, title, description, content,
        source, published_at, url
    """
    api_key = os.getenv("NEWS_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "NEWS_API_KEY not found in environment.\n"
            "Add it to your .env file and run: from dotenv import load_dotenv; load_dotenv()"
        )

    from_date = (datetime.today() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    query     = build_query(ticker)

    params = {
        "q":        query,
        "from":     from_date,
        "sortBy":   "publishedAt",       # most recent first
        "language": language,
        "pageSize": min(max_articles, 100),  # API hard cap is 100
        "apiKey":   api_key,
    }

    logger.info(f"Fetching news | ticker={ticker} | from={from_date} | max={max_articles}")

    try:
        response = requests.get(NEWS_API_BASE, params=params, timeout=10)
        response.raise_for_status()   # raises HTTPError for 4xx/5xx responses
    except requests.exceptions.Timeout:
        logger.error("NewsAPI request timed out after 10 seconds")
        return pd.DataFrame()
    except requests.exceptions.HTTPError as e:
        logger.error(f"NewsAPI HTTP error: {e}")
        return pd.DataFrame()

    data     = response.json()
    articles = data.get("articles", [])

    if not articles:
        logger.warning(f"No articles returned for {ticker}. Check your API key and query.")
        return pd.DataFrame()

    # ── Parse articles into a clean DataFrame ────────────────────────────────
    records = []
    for article in articles:

        # Skip articles with no title or removed content
        title = article.get("title", "") or ""
        if not title or title == "[Removed]":
            continue

        records.append({
            "ticker":       ticker,
            "title":        clean_text(title),
            "description":  clean_text(article.get("description", "") or ""),
            "content":      clean_text(article.get("content",     "") or ""),
            "source":       article.get("source", {}).get("name", "Unknown"),
            "published_at": article.get("publishedAt", ""),
            "url":          article.get("url", ""),
        })

    df = pd.DataFrame(records)

    # Convert published_at to datetime for easier time-based operations later
    df["published_at"] = pd.to_datetime(df["published_at"], errors="coerce", utc=True)

    # Sort newest first
    df = df.sort_values("published_at", ascending=False).reset_index(drop=True)

    logger.info(f"Fetched {len(df)} valid articles for {ticker}")

    # Respect API rate limit
    time.sleep(REQUEST_DELAY_SECONDS)

    return df


def fetch_multiple_tickers(
    tickers:      list[str],
    days_back:    int = 30,
    max_articles: int = 50,
) -> pd.DataFrame:
    """
    Fetch news for a list of tickers and combine into one DataFrame.
    Used by data_pipeline.py when processing the full watchlist.

    Args:
        tickers:      list of stock symbols e.g. ["AAPL", "MSFT", "JPM"]
        days_back:    lookback window in days
        max_articles: per-ticker article cap

    Returns:
        Combined DataFrame with a 'ticker' column to distinguish rows
    """
    all_dfs = []

    for i, ticker in enumerate(tickers):
        logger.info(f"Processing ticker {i+1}/{len(tickers)}: {ticker}")
        df = fetch_news(ticker, days_back=days_back, max_articles=max_articles)

        if not df.empty:
            all_dfs.append(df)

    if not all_dfs:
        logger.warning("No news fetched for any ticker.")
        return pd.DataFrame()

    combined = pd.concat(all_dfs, ignore_index=True)
    logger.info(f"Total articles fetched: {len(combined)} across {len(tickers)} tickers")

    return combined


def save_news(df: pd.DataFrame, ticker: str, save_dir: str = "data/raw") -> str:
    """
    Save fetched news to CSV under data/raw/{ticker}/news.csv

    Returns:
        path where the file was saved
    """
    path = f"{save_dir}/{ticker}/news.csv"
    save_dataframe(df, path)
    return path