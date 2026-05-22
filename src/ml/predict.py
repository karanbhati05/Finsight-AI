# src/ml/predict.py

import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from src.ml.feature_engineering import build_feature_matrix, get_X_y
from src.utils.logger import get_logger
from src.utils.constants import MODELS_DIR, FEATURE_COLS

logger = get_logger(__name__)


def load_model(ticker: str, model_dir: str = MODELS_DIR) -> dict:
    """
    Load a saved model dict from disk.

    The saved dict contains:
        model:        fitted sklearn Pipeline (scaler + XGBoost)
        feature_cols: exact feature list used during training
        ticker:       stock symbol
        cv_mean_f1:   cross-validation F1 (reference metric)
        test_metrics: held-out test evaluation

    Args:
        ticker:    stock symbol e.g. "AAPL"
        model_dir: directory where .pkl files are stored

    Returns:
        Model dict with all components
    """
    path = Path(model_dir) / f"{ticker}_xgb_model.pkl"

    if not path.exists():
        raise FileNotFoundError(
            f"No trained model found for {ticker}.\n"
            f"Run first: python scripts/train_model.py --ticker {ticker}"
        )

    with open(path, "rb") as f:
        model_dict = pickle.load(f)

    logger.info(
        f"Model loaded | ticker={ticker} | "
        f"CV F1={model_dict.get('cv_mean_f1', 'N/A'):.3f}"
    )
    return model_dict


def predict_single(
    model_dict:    dict,
    features:      dict,
) -> dict:
    """
    Predict price direction for a single set of feature values.

    Used by the Streamlit dashboard to make a real-time prediction
    when a user selects a ticker.

    Args:
        model_dict: loaded model dict from load_model()
        features:   dict mapping feature_name → value
                    e.g. {"sentiment_score": 0.42, "rsi_14": 68.5, ...}

    Returns:
        Dict with:
            prediction:  1 (up) or 0 (down)
            probability: confidence score (0.0 to 1.0)
            label:       "UP ↑" or "DOWN ↓"
            confidence:  "High" / "Medium" / "Low"
    """
    model       = model_dict["model"]
    feature_cols = model_dict["feature_cols"]

    # Build a single-row DataFrame in the exact column order used during training
    # Missing features default to 0.0 — safer than crashing
    row = {col: features.get(col, 0.0) for col in feature_cols}
    X   = pd.DataFrame([row])

    prediction  = int(model.predict(X)[0])
    probability = float(model.predict_proba(X)[0][1])   # P(price goes up)

    # Human-readable confidence tier
    if probability >= 0.65 or probability <= 0.35:
        confidence = "High"
    elif probability >= 0.55 or probability <= 0.45:
        confidence = "Medium"
    else:
        confidence = "Low"

    return {
        "prediction":  prediction,
        "probability": round(probability, 4),
        "label":       "UP ↑" if prediction == 1 else "DOWN ↓",
        "confidence":  confidence,
    }


def predict_batch(
    model_dict: dict,
    df:         pd.DataFrame,
) -> pd.DataFrame:
    """
    Run predictions on a full feature DataFrame.

    Used to generate the prediction history shown in the
    ML Predictions page of the Streamlit dashboard.

    Args:
        model_dict: loaded model dict from load_model()
        df:         feature matrix DataFrame

    Returns:
        Input DataFrame with added columns:
            predicted_direction: 0 or 1
            up_probability:      float 0.0 to 1.0
            prediction_label:    "UP ↑" or "DOWN ↓"
            prediction_confidence: "High" / "Medium" / "Low"
    """
    model        = model_dict["model"]
    feature_cols = model_dict["feature_cols"]

    # Only use columns that exist in both the model and the input DataFrame
    available = [c for c in feature_cols if c in df.columns]
    missing   = set(feature_cols) - set(available)

    if missing:
        logger.warning(
            f"Features missing from input (will default to 0): {missing}"
        )
        for col in missing:
            df[col] = 0.0

    X = df[feature_cols].fillna(0.0)

    predictions  = model.predict(X)
    probabilities = model.predict_proba(X)[:, 1]

    df = df.copy()
    df["predicted_direction"]    = predictions
    df["up_probability"]         = probabilities.round(4)
    df["prediction_label"]       = np.where(predictions == 1, "UP ↑", "DOWN ↓")
    # NEW
    df["prediction_confidence"] = pd.cut(
        probabilities,
        bins     = [0.0, 0.35, 0.45, 0.55, 0.65, 1.0],
        labels   = ["High (Down)", "Low (Down)", "Low (Up)", "Medium", "High (Up)"],
        ordered  = False,
    )

    logger.info(
        f"Batch predictions: {len(df)} rows | "
        f"Predicted up: {predictions.mean():.1%}"
    )

    return df


def predict_latest(
    ticker:       str,
    price_df:     pd.DataFrame,
    sentiment_df: pd.DataFrame,
    model_dir:    str = MODELS_DIR,
) -> dict:
    """
    Make a prediction for the LATEST available data point.

    This is the primary function called by the dashboard's
    "What's today's prediction?" card. It loads the model,
    builds features from the most recent data, and returns
    a single prediction.

    Args:
        ticker:       stock symbol
        price_df:     recent price data with technical indicators
        sentiment_df: recent news with sentiment scores
        model_dir:    where model files are stored

    Returns:
        Prediction dict + feature values used
    """
    logger.info(f"Generating latest prediction for {ticker}")

    # Load the saved model
    model_dict = load_model(ticker, model_dir)

    # Build feature matrix from latest data
    try:
        feature_df = build_feature_matrix(price_df, sentiment_df)
    except ValueError as e:
        logger.error(f"Feature matrix failed: {e}")
        return {"error": str(e)}

    if feature_df.empty:
        return {"error": "No feature data available for prediction"}

    # Take the most recent row
    latest_row    = feature_df.sort_values("date").iloc[-1]
    feature_cols  = model_dict["feature_cols"]

    features = {
        col: float(latest_row[col])
        for col in feature_cols
        if col in latest_row.index
    }

    # Make prediction
    result = predict_single(model_dict, features)

    # Enrich with context
    result["ticker"]   = ticker
    result["date"]     = str(latest_row.get("date", "unknown"))
    result["features"] = {k: round(v, 4) for k, v in features.items()}

    logger.info(
        f"Prediction for {ticker} | "
        f"{result['label']} | "
        f"P(up)={result['probability']:.3f} | "
        f"confidence={result['confidence']}"
    )

    return result


def get_prediction_history(
    ticker:       str,
    price_df:     pd.DataFrame,
    sentiment_df: pd.DataFrame,
    model_dir:    str = MODELS_DIR,
) -> pd.DataFrame:
    """
    Generate full prediction history for charting in the dashboard.

    Builds features for all available data then runs batch prediction.
    Used to draw the "Predicted probability over time" line chart.

    Args:
        ticker:       stock symbol
        price_df:     full historical price data
        sentiment_df: full historical sentiment data
        model_dir:    where model files are stored

    Returns:
        DataFrame with date, close, predicted_direction, up_probability
    """
    model_dict = load_model(ticker, model_dir)
    feature_df = build_feature_matrix(price_df, sentiment_df)

    if feature_df.empty:
        return pd.DataFrame()

    predictions_df = predict_batch(model_dict, feature_df)

    # Keep only the columns needed for the chart
    keep_cols = [
        "date", "close", "ticker",
        "predicted_direction", "up_probability",
        "prediction_label", "prediction_confidence",
        "sentiment_score", "rsi_14",
    ]
    available_cols = [c for c in keep_cols if c in predictions_df.columns]

    return predictions_df[available_cols].sort_values("date").reset_index(drop=True)