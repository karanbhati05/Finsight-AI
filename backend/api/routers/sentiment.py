"""
backend/api/routers/sentiment.py
Sentiment trend endpoint — returns daily aggregated sentiment scores
for a ticker over a configurable time window.

Reads from the enriched news CSV produced by the V1 data pipeline.
Groups articles by date, computes daily averages, and calculates
the overall trend (improving / declining / stable).
"""

import pandas as pd
from pathlib import Path
from fastapi import APIRouter, Query, HTTPException
from backend.cache.redis_client import cache
from src.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent


def _load_sentiment_data(ticker: str) -> pd.DataFrame:
    """Load enriched news with sentiment scores from disk."""
    path = PROJECT_ROOT / "data" / "processed" / ticker / "news_enriched.csv"
    if not path.exists():
        return pd.DataFrame()

    try:
        df = pd.read_csv(path)
        if "sentiment_score" not in df.columns:
            return pd.DataFrame()
        return df
    except Exception as e:
        logger.error(f"Failed to load sentiment data for {ticker}: {e}")
        return pd.DataFrame()


def _compute_trend(daily_data: list) -> dict:
    """
    Compute overall trend summary from daily sentiment data.

    Compares first-half average vs second-half average to determine
    if sentiment is improving, declining, or stable.
    """
    if not daily_data:
        return {
            "avg_score":      0.0,
            "trend":          "stable",
            "score_delta":    0.0,
            "total_articles": 0,
        }

    scores = [d["avg_score"] for d in daily_data]
    counts = [d["article_count"] for d in daily_data]

    avg_score = round(sum(scores) / len(scores), 3)
    total_articles = sum(counts)

    # Compare first half vs second half for trend direction
    mid = len(scores) // 2
    if mid > 0:
        first_half_avg  = sum(scores[:mid]) / mid
        second_half_avg = sum(scores[mid:]) / (len(scores) - mid)
        score_delta = round(second_half_avg - first_half_avg, 3)
    else:
        score_delta = 0.0

    if score_delta > 0.05:
        trend = "improving"
    elif score_delta < -0.05:
        trend = "declining"
    else:
        trend = "stable"

    return {
        "avg_score":      avg_score,
        "trend":          trend,
        "score_delta":    score_delta,
        "total_articles": total_articles,
    }


@router.get("/{ticker}")
async def get_sentiment_trend(
    ticker: str,
    days:   int = Query(default=30, ge=1, le=365),
):
    """
    Get daily sentiment trend for a ticker.

    Response includes:
        - Daily breakdown: date, avg_score, article_count, positive/negative ratios
        - Summary: overall avg, trend direction, score delta, total articles
    """
    cache_key = f"sentiment:{ticker}:{days}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    ticker_upper = ticker.upper()
    df = _load_sentiment_data(ticker_upper)

    if df.empty:
        return {
            "ticker": ticker_upper,
            "sentiment_trend": [],
            "summary": {
                "avg_score":      0.0,
                "trend":          "stable",
                "score_delta":    0.0,
                "total_articles": 0,
            }
        }

    # ── Parse dates and filter to requested window ───────────────────────
    if "published_at" in df.columns:
        df["date"] = pd.to_datetime(df["published_at"], errors="coerce").dt.date
    elif "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
    else:
        return {
            "ticker": ticker_upper,
            "sentiment_trend": [],
            "summary": _compute_trend([]),
        }

    df = df.dropna(subset=["date", "sentiment_score"])

    # Filter to last N days
    if not df.empty:
        max_date = df["date"].max()
        cutoff   = max_date - pd.Timedelta(days=days)
        df = df[df["date"] >= cutoff]

    # ── Group by date and compute daily aggregates ───────────────────────
    daily_data = []
    for date, group in df.groupby("date"):
        scores = group["sentiment_score"].tolist()
        labels = group["sentiment_label"].tolist() if "sentiment_label" in group.columns else []

        total      = len(scores)
        pos_count  = sum(1 for l in labels if l == "positive")
        neg_count  = sum(1 for l in labels if l == "negative")

        daily_data.append({
            "date":           str(date),
            "avg_score":      round(sum(scores) / total, 3),
            "article_count":  total,
            "positive_ratio": round(pos_count / total, 2) if total else 0.0,
            "negative_ratio": round(neg_count / total, 2) if total else 0.0,
        })

    # Sort by date ascending
    daily_data.sort(key=lambda x: x["date"])

    # ── Compute summary ──────────────────────────────────────────────────
    summary = _compute_trend(daily_data)

    result = {
        "ticker":          ticker_upper,
        "sentiment_trend": daily_data,
        "summary":         summary,
    }

    # Cache for 15 minutes
    cache.set(cache_key, result, ttl=900)

    return result
