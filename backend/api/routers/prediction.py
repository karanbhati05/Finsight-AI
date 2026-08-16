"""
backend/api/routers/prediction.py
ML Prediction endpoint — returns the XGBoost price direction prediction
for a ticker along with feature importance and probability history.

Wraps the existing V1 predict.py module:
    1. Loads saved XGBoost model from models/{ticker}_xgb_model.pkl
    2. Loads price data and sentiment data from disk
    3. Builds feature matrix and runs predict_latest()
    4. Optionally generates probability history for charting
"""

import pandas as pd
from pathlib import Path
from fastapi import APIRouter, HTTPException
from backend.cache.redis_client import cache
from src.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent


def _load_price_data(ticker: str) -> pd.DataFrame:
    """Load price CSV with technical indicators."""
    path = PROJECT_ROOT / "data" / "raw" / ticker / "price_data.csv"
    if path.exists():
        try:
            df = pd.read_csv(path)
            logger.info(f"Loaded {len(df)} price rows for {ticker}")
            return df
        except Exception as e:
            logger.error(f"Failed to load price data for {ticker}: {e}")
    return pd.DataFrame()


def _load_sentiment_data(ticker: str) -> pd.DataFrame:
    """Load enriched news with sentiment scores."""
    path = PROJECT_ROOT / "data" / "processed" / ticker / "news_enriched.csv"
    if path.exists():
        try:
            df = pd.read_csv(path)
            logger.info(f"Loaded {len(df)} sentiment rows for {ticker}")
            return df
        except Exception as e:
            logger.error(f"Failed to load sentiment data for {ticker}: {e}")
    return pd.DataFrame()


def _load_model_metrics(ticker: str) -> dict:
    """Load model evaluation metrics from the saved pickle."""
    try:
        from src.ml.predict import load_model
        model_dict = load_model(ticker)
        return {
            "cv_f1":   round(float(model_dict.get("cv_mean_f1", 0)), 3),
            "roc_auc": round(float(
                model_dict.get("test_metrics", {}).get("roc_auc",
                model_dict.get("cv_mean_f1", 0))
            ), 3),
        }
    except Exception:
        return {"cv_f1": 0.0, "roc_auc": 0.0}


@router.get("/{ticker}")
async def get_prediction(ticker: str):
    """
    Get ML price direction prediction for a ticker.

    Returns:
        - prediction: 0 (down) or 1 (up)
        - label: "UP" / "DOWN"
        - probability: confidence score 0.0-1.0
        - features: dict of feature values used for prediction
        - model_metrics: cross-validation F1 and ROC AUC
        - probability_history: list of {date, probability} for charting
    """
    cache_key = f"prediction:{ticker}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    ticker_upper = ticker.upper()

    # ── Load data from disk ──────────────────────────────────────────────
    price_df     = _load_price_data(ticker_upper)
    sentiment_df = _load_sentiment_data(ticker_upper)

    if price_df.empty:
        raise HTTPException(
            status_code=404,
            detail=f"No price data found for {ticker_upper}. Run the data pipeline first."
        )

    if sentiment_df.empty:
        raise HTTPException(
            status_code=404,
            detail=f"No sentiment data found for {ticker_upper}. Run the data pipeline first."
        )

    # ── Run prediction using V1 module ───────────────────────────────────
    try:
        from src.ml.predict import predict_latest, get_prediction_history

        # Latest prediction
        result = predict_latest(
            ticker       = ticker_upper,
            price_df     = price_df,
            sentiment_df = sentiment_df,
        )

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        # Clean up label for frontend (remove arrow emoji)
        label = result.get("label", "")
        if "UP" in label:
            label = "UP"
        elif "DOWN" in label:
            label = "DOWN"

        # Probability history for chart
        try:
            history_df = get_prediction_history(
                ticker_upper, price_df, sentiment_df
            )
            probability_history = [
                {
                    "date":        str(row.get("date", "")),
                    "probability": round(float(row.get("up_probability", 0.5)), 3),
                }
                for _, row in history_df.tail(30).iterrows()
            ] if not history_df.empty else []
        except Exception as e:
            logger.warning(f"Could not generate probability history: {e}")
            probability_history = []

        # Model metrics
        model_metrics = _load_model_metrics(ticker_upper)

        response = {
            "ticker":              ticker_upper,
            "date":                result.get("date", ""),
            "prediction":          result.get("prediction", 0),
            "label":               label,
            "probability":         round(result.get("probability", 0.5), 3),
            "confidence":          result.get("confidence", "Low"),
            "features":            result.get("features", {}),
            "model_metrics":       model_metrics,
            "probability_history": probability_history,
        }

        # Cache for 30 minutes (predictions don't change frequently)
        cache.set(cache_key, response, ttl=1800)

        return response

    except FileNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail=f"No trained model found for {ticker_upper}. {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prediction failed for {ticker_upper}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
