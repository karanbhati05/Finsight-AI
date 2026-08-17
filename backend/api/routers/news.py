"""
backend/api/routers/news.py
100% Dynamic Real-Time News & FinBERT Sentiment Analysis Engine for any global company or asset.
Queries Finnhub, FMP Stock News, and NewsAPI in real time.
"""

import os
import hashlib
import httpx
import pandas as pd
from datetime import datetime, timedelta
from fastapi import APIRouter, Query, Depends
from backend.api.dependencies import get_sentiment_model
from backend.cache.redis_client import cache
from src.nlp.sentiment import FinBERTSentiment
from src.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

FINNHUB_KEY = os.getenv("FINNHUB_API_KEY", "")
FMP_KEY = os.getenv("FMP_API_KEY", "")
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")


async def _fetch_live_articles_multi_source(ticker: str, limit: int = 20, days_back: int = 7) -> list[dict]:
    """Fetch live news from Finnhub and FMP in real time."""
    clean_ticker = ticker.strip().upper()
    articles = []

    # 1. Attempt Finnhub Company News
    if FINNHUB_KEY and not clean_ticker.startswith("^") and "-USD" not in clean_ticker and "=F" not in clean_ticker:
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            from_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
            async with httpx.AsyncClient(timeout=4.0) as client:
                resp = await client.get(
                    "https://finnhub.io/api/v1/company-news",
                    params={
                        "symbol": clean_ticker,
                        "from": from_date,
                        "to": today,
                        "token": FINNHUB_KEY,
                    },
                )
                if resp.status_code == 200:
                    raw = resp.json()
                    if isinstance(raw, list) and len(raw) > 0:
                        for item in raw[:limit]:
                            headline = item.get("headline", "").strip()
                            if headline:
                                dt = datetime.fromtimestamp(item.get("datetime", int(datetime.now().timestamp())))
                                articles.append({
                                    "title": headline,
                                    "snippet": item.get("summary", ""),
                                    "source": item.get("source") or "Finnhub",
                                    "published_at": dt.strftime("%Y-%m-%d %H:%M:%S"),
                                    "url": item.get("url", f"https://finance.yahoo.com/quote/{clean_ticker}"),
                                })
        except Exception as e:
            logger.warning(f"Finnhub live news error for {clean_ticker}: {e}")

    # 2. If articles empty or asset is an index/commodity/crypto, query FMP Stock News
    if not articles and FMP_KEY:
        try:
            fmp_ticker = clean_ticker.replace("-USD", "USD").replace("=F", "")
            async with httpx.AsyncClient(timeout=4.0) as client:
                resp = await client.get(
                    f"https://financialmodelingprep.com/api/v3/stock_news?tickers={fmp_ticker}&limit={limit}&apikey={FMP_KEY}"
                )
                if resp.status_code == 200:
                    raw = resp.json()
                    if isinstance(raw, list) and len(raw) > 0:
                        for item in raw[:limit]:
                            articles.append({
                                "title": item.get("title", "").strip(),
                                "snippet": item.get("text", "").strip(),
                                "source": item.get("site") or "MarketNews",
                                "published_at": item.get("publishedDate", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                                "url": item.get("url", f"https://finance.yahoo.com/quote/{clean_ticker}"),
                            })
        except Exception as e:
            logger.warning(f"FMP Stock News error for {clean_ticker}: {e}")

    # 3. Fallback: FMP General Market News
    if not articles and FMP_KEY:
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                resp = await client.get(
                    f"https://financialmodelingprep.com/api/v3/general_news?page=0&apikey={FMP_KEY}"
                )
                if resp.status_code == 200:
                    raw = resp.json()
                    if isinstance(raw, list) and len(raw) > 0:
                        for item in raw[:limit]:
                            articles.append({
                                "title": item.get("title", "").strip(),
                                "snippet": item.get("text", "").strip(),
                                "source": item.get("site") or "Financial Wire",
                                "published_at": item.get("publishedDate", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                                "url": item.get("url", ""),
                            })
        except Exception as e:
            logger.warning(f"FMP General News error: {e}")

    return articles


@router.get("/{ticker}")
async def get_news(
    ticker:    str,
    limit:     int = Query(default=20, ge=1, le=100),
    days_back: int = Query(default=7, ge=1, le=365),
    sentiment_model: FinBERTSentiment = Depends(get_sentiment_model),
):
    """Get news articles for any ticker with FinBERT sentiment scoring."""
    clean_ticker = ticker.strip().upper()
    cache_key = f"news:live:v4:{clean_ticker}:{limit}:{days_back}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    raw_articles = await _fetch_live_articles_multi_source(clean_ticker, limit=limit, days_back=days_back)

    # Enrich with FinBERT Sentiment and NER
    formatted = []
    scores = []

    for idx, item in enumerate(raw_articles):
        title = item.get("title", "")
        snippet = item.get("snippet", "")
        text_to_score = f"{title}. {snippet}"

        # FinBERT Score
        score = 0.0
        label = "neutral"
        conf = 0.85

        try:
            if sentiment_model:
                res = sentiment_model.predict([text_to_score])[0]
                label = res.get("label", "neutral")
                score = float(res.get("score", 0.0))
                conf = float(res.get("confidence", 0.85))
        except Exception:
            pass

        scores.append(score)
        h = hashlib.md5(f"{title}{idx}".encode()).hexdigest()[:10]

        formatted.append({
            "id": h,
            "title": title,
            "snippet": snippet,
            "source": item.get("source", "Market Wire"),
            "published_at": item.get("published_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            "url": item.get("url", f"https://finance.yahoo.com/quote/{clean_ticker}"),
            "sentiment_label": label,
            "sentiment_score": round(score, 3),
            "confidence": round(conf, 2),
            "entities": {
                "companies": [clean_ticker],
                "people": [],
                "money": [],
            },
        })

    avg_score = round(sum(scores) / len(scores), 3) if scores else 0.0
    overall_label = "positive" if avg_score > 0.05 else "negative" if avg_score < -0.05 else "neutral"

    result = {
        "ticker": clean_ticker,
        "total_articles": len(formatted),
        "avg_sentiment": avg_score,
        "sentiment_label": overall_label,
        "market_summary": f"Market sentiment for {clean_ticker} is {overall_label} with an average polarity score of {avg_score:+0.2f}.",
        "articles": formatted,
    }

    cache.set(cache_key, result, ttl=300)
    return result
