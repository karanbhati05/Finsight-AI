"""
backend/api/routers/news.py
News feed endpoint — fetches news articles for a ticker, enriches with
FinBERT sentiment analysis and spaCy NER, returns the API contract shape.

Data flow:
    1. Check for cached enriched news on disk (data/processed/{ticker}/news_enriched.csv)
    2. If stale or missing → fetch live from Finnhub API
    3. Run FinBERT sentiment on each headline
    4. Return articles with sentiment labels/scores and extracted entities
"""

import hashlib
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from fastapi import APIRouter, Query, Depends, HTTPException
from typing import Optional
from backend.api.dependencies import get_sentiment_model
from backend.cache.redis_client import cache
from src.nlp.sentiment import FinBERTSentiment
from src.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent


def _load_enriched_news(ticker: str) -> pd.DataFrame:
    """
    Load pre-processed enriched news from disk.
    These files are created by the V1 data pipeline.
    """
    path = PROJECT_ROOT / "data" / "processed" / ticker / "news_enriched.csv"
    if path.exists():
        try:
            df = pd.read_csv(path)
            logger.info(f"Loaded {len(df)} enriched articles for {ticker} from disk")
            return df
        except Exception as e:
            logger.error(f"Failed to load enriched news for {ticker}: {e}")
    return pd.DataFrame()


def _load_raw_news(ticker: str) -> pd.DataFrame:
    """
    Load raw Finnhub news from disk as fallback.
    """
    path = PROJECT_ROOT / "data" / "raw" / ticker / "finnhub_news.csv"
    if path.exists():
        try:
            df = pd.read_csv(path)
            logger.info(f"Loaded {len(df)} raw articles for {ticker} from disk")
            return df
        except Exception as e:
            logger.error(f"Failed to load raw news for {ticker}: {e}")
    return pd.DataFrame()


def _fetch_live_news(ticker: str, days_back: int = 7, max_articles: int = 50) -> pd.DataFrame:
    """
    Fetch live news from Finnhub API.
    Uses the existing V1 fetcher — no code duplication.
    """
    try:
        from src.ingestion.finnhub_fetcher import fetch_company_news
        df = fetch_company_news(ticker=ticker, days_back=days_back, max_articles=max_articles)
        return df
    except Exception as e:
        logger.error(f"Live news fetch failed for {ticker}: {e}")
        return pd.DataFrame()


def _parse_entities(row: pd.Series) -> dict:
    """Extract entity lists from a news row."""
    entities = {
        "companies": [],
        "people":    [],
        "money":     [],
    }

    # If enriched data has entity columns from the V1 pipeline
    if "entity_orgs" in row.index and pd.notna(row.get("entity_orgs", "")):
        orgs = str(row["entity_orgs"])
        if orgs and orgs != "nan":
            entities["companies"] = [o.strip() for o in orgs.split(",") if o.strip()]

    if "entities" in row.index and pd.notna(row.get("entities", "")):
        ent_str = str(row["entities"])
        if ent_str and ent_str != "nan" and ent_str != "{}":
            # Try to parse entity string
            try:
                import ast
                ent_dict = ast.literal_eval(ent_str)
                if isinstance(ent_dict, dict):
                    entities["companies"] = ent_dict.get("ORG", [])[:5]
                    entities["people"]    = ent_dict.get("PERSON", [])[:3]
                    entities["money"]     = ent_dict.get("MONEY", [])[:3]
            except Exception:
                pass

    return entities


@router.get("/{ticker}")
async def get_news(
    ticker:    str,
    limit:     int = Query(default=20, ge=1, le=100),
    days_back: int = Query(default=7, ge=1, le=365),
    sentiment_model: FinBERTSentiment = Depends(get_sentiment_model),
):
    """
    Get news articles for a ticker with sentiment analysis.

    Priority:
      1. Enriched news from disk (pre-processed by V1 pipeline)
      2. Raw Finnhub news from disk
      3. Live fetch from Finnhub API + real-time FinBERT analysis

    Returns the NewsResponse contract with articles, market_summary, avg_sentiment.
    """
    cache_key = f"news:{ticker}:{limit}:{days_back}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    ticker_upper = ticker.upper()

    # ── Strategy 1: Use enriched news from V1 pipeline ───────────────────
    df = _load_enriched_news(ticker_upper)

    # ── Strategy 2: Use raw news from disk ───────────────────────────────
    if df.empty:
        df = _load_raw_news(ticker_upper)

    # ── Strategy 3: Fetch live from Finnhub ──────────────────────────────
    if df.empty:
        df = _fetch_live_news(ticker_upper, days_back=days_back, max_articles=limit)

    if df.empty:
        return {
            "ticker":         ticker_upper,
            "articles":       [],
            "market_summary": f"No news articles found for {ticker_upper}.",
            "avg_sentiment":  0.0,
        }

    # ── Run sentiment analysis if not already present ────────────────────
    has_sentiment = "sentiment_label" in df.columns and "sentiment_score" in df.columns
    if not has_sentiment and sentiment_model:
        # Use title + description for sentiment
        text_col = None
        for col in ["content_sentiment", "content", "description", "title"]:
            if col in df.columns:
                text_col = col
                break

        if text_col:
            texts = df[text_col].fillna("").tolist()
            results = sentiment_model.predict_batch(texts[:limit])
            for i, r in enumerate(results):
                if i < len(df):
                    df.loc[df.index[i], "sentiment_label"] = r["label"]
                    df.loc[df.index[i], "sentiment_score"] = r["score"]

    # ── Build response articles ──────────────────────────────────────────
    articles = []
    for _, row in df.head(limit).iterrows():
        # Generate a stable article ID from title
        title = str(row.get("title", ""))
        article_id = hashlib.md5(title.encode()).hexdigest()[:12]

        # Get summary text
        summary = str(row.get("summary", row.get("description", row.get("content", ""))))
        if summary == "nan":
            summary = title

        # Parse published date
        published = str(row.get("published_at", ""))
        if published == "nan":
            published = ""

        articles.append({
            "id":              article_id,
            "title":           title,
            "summary":         summary[:500],
            "source":          str(row.get("source", "Unknown")),
            "source_count":    1,
            "published_at":    published,
            "url":             str(row.get("url", "")),
            "sentiment_label": str(row.get("sentiment_label", "neutral")),
            "sentiment_score": round(float(row.get("sentiment_score", 0.0)), 3),
            "entities":        _parse_entities(row),
        })

    # ── Compute aggregate sentiment ──────────────────────────────────────
    scores = [a["sentiment_score"] for a in articles if a["sentiment_score"] != 0]
    avg_sentiment = round(sum(scores) / len(scores), 3) if scores else 0.0

    # ── Generate market summary ──────────────────────────────────────────
    pos = sum(1 for a in articles if a["sentiment_label"] == "positive")
    neg = sum(1 for a in articles if a["sentiment_label"] == "negative")
    total = len(articles)

    if avg_sentiment > 0.2:
        mood = "predominantly positive"
    elif avg_sentiment < -0.2:
        mood = "predominantly negative"
    else:
        mood = "mixed"

    market_summary = (
        f"Based on {total} recent articles, sentiment for {ticker_upper} is {mood}. "
        f"{pos} positive, {neg} negative articles found."
    )

    result = {
        "ticker":         ticker_upper,
        "articles":       articles,
        "market_summary": market_summary,
        "avg_sentiment":  avg_sentiment,
    }

    # Cache for 10 minutes
    cache.set(cache_key, result, ttl=600)

    return result
