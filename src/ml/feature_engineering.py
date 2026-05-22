# src/ml/feature_engineering.py

import pandas as pd
import numpy as np
from src.utils.logger import get_logger
from src.utils.constants import FEATURE_COLS, TARGET_COL

logger = get_logger(__name__)


def aggregate_daily_sentiment(sentiment_df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate article-level sentiment scores to daily ticker-level features.

    We have multiple articles per day per ticker. The ML model needs
    one row per day per ticker. This function collapses many articles
    into one row of aggregated sentiment signals.

    Aggregations and why each matters:
        sentiment_score:     mean score — overall daily sentiment direction
        sentiment_magnitude: mean absolute score — how strong was the sentiment?
                             0.1 positive and 0.1 negative both have magnitude 0.1
                             Important: weak signals should be weighted less
        article_count:       how many articles? More coverage = more reliable signal
        positive_ratio:      fraction of positive articles (vs all articles)
        negative_ratio:      fraction of negative articles (vs all articles)

    Args:
        sentiment_df: DataFrame from sentiment.analyze_dataframe()
                      must have: ticker, published_at, sentiment_score,
                                 sentiment_label columns

    Returns:
        Daily aggregated DataFrame with one row per (ticker, date)
    """
    df = sentiment_df.copy()

    # Normalize published_at to date only (strip time component)
    # We match on date when merging with price data
    if pd.api.types.is_datetime64_any_dtype(df["published_at"]):
        df["date"] = df["published_at"].dt.date
    else:
        df["published_at"] = pd.to_datetime(df["published_at"], utc=True, errors="coerce")
        df["date"] = df["published_at"].dt.date

    daily = (
        df.groupby(["ticker", "date"])
        .agg(
            sentiment_score     = ("sentiment_score",    "mean"),
            sentiment_magnitude = ("sentiment_score",    lambda x: x.abs().mean()),
            article_count       = ("sentiment_score",    "count"),
            positive_ratio      = ("sentiment_label",    lambda x: (x == "positive").mean()),
            negative_ratio      = ("sentiment_label",    lambda x: (x == "negative").mean()),
            sentiment_std       = ("sentiment_score",    "std"),  # consistency signal
        )
        .reset_index()
    )

    # Fill NaN std (only 1 article that day) with 0
    daily["sentiment_std"] = daily["sentiment_std"].fillna(0)

    # Sort by ticker then date for rolling window calculations
    daily = daily.sort_values(["ticker", "date"]).reset_index(drop=True)

    return daily


def add_rolling_sentiment_features(daily_df: pd.DataFrame) -> pd.DataFrame:
    """
    Add rolling window sentiment features for each ticker.

    Why rolling windows?
        A single day's sentiment is noisy. Rolling averages smooth
        out noise and capture sentiment trends:
        - 3-day: catches short-term narrative shifts
        - 7-day: captures weekly sentiment momentum
        - A stock with rising 7-day sentiment is in a better position
          than one with flat daily but declining weekly sentiment.

    Args:
        daily_df: daily aggregated sentiment DataFrame

    Returns:
        DataFrame with added rolling features
    """
    df = daily_df.copy()

    # Process each ticker separately to avoid rolling windows bleeding
    # across ticker boundaries (AAPL's 7-day average shouldn't include JPM's data)
    ticker_dfs = []
    for ticker in df["ticker"].unique():
        ticker_df = df[df["ticker"] == ticker].copy().sort_values("date")

        # Rolling sentiment averages
        ticker_df["rolling_avg_sentiment_3d"] = (
            ticker_df["sentiment_score"]
            .rolling(window=3, min_periods=1)
            .mean()
        )
        ticker_df["rolling_avg_sentiment_7d"] = (
            ticker_df["sentiment_score"]
            .rolling(window=7, min_periods=1)
            .mean()
        )

        # Sentiment momentum: is today's sentiment better or worse than last week?
        # Positive momentum = improving narrative
        ticker_df["sentiment_momentum"] = (
            ticker_df["sentiment_score"] -
            ticker_df["sentiment_score"].shift(7).fillna(0)
        )

        # Sentiment change from yesterday
        ticker_df["sentiment_change_1d"] = ticker_df["sentiment_score"].diff().fillna(0)

        ticker_dfs.append(ticker_df)

    return pd.concat(ticker_dfs, ignore_index=True)


def merge_price_and_sentiment(
    price_df:     pd.DataFrame,
    sentiment_df: pd.DataFrame,
) -> pd.DataFrame:

    price_df     = price_df.copy()
    sentiment_df = sentiment_df.copy()

    # Convert everything to simple date strings YYYY-MM-DD for safe merging
    price_df["date"] = pd.to_datetime(
        price_df["date"], utc=True, errors="coerce"
    ).dt.strftime("%Y-%m-%d")

    sentiment_df["date"] = pd.to_datetime(
        sentiment_df["date"], utc=True, errors="coerce"
    ).dt.strftime("%Y-%m-%d")

    logger.info(f"Price date range: {price_df['date'].min()} to {price_df['date'].max()}")
    logger.info(f"Sentiment date range: {sentiment_df['date'].min()} to {sentiment_df['date'].max()}")

    # Left join on string dates — no timezone issues possible
    merged = pd.merge(
        price_df,
        sentiment_df,
        on  = ["ticker", "date"],
        how = "left",
    )

    logger.info(f"Rows after merge: {len(merged)}")

    # Forward fill sentiment across all price dates
    sentiment_cols = [
        "sentiment_score", "sentiment_magnitude", "article_count",
        "positive_ratio", "negative_ratio", "sentiment_std",
        "rolling_avg_sentiment_3d", "rolling_avg_sentiment_7d",
        "sentiment_momentum", "sentiment_change_1d",
    ]

    for col in sentiment_cols:
        if col in merged.columns:
            merged[col] = merged[col].ffill().bfill()

    # Fill remaining NaN with neutral defaults
    neutral_defaults = {
        "sentiment_score":          0.0,
        "sentiment_magnitude":      0.0,
        "article_count":            0.0,
        "positive_ratio":           0.33,
        "negative_ratio":           0.33,
        "sentiment_std":            0.0,
        "rolling_avg_sentiment_3d": 0.0,
        "rolling_avg_sentiment_7d": 0.0,
        "sentiment_momentum":       0.0,
        "sentiment_change_1d":      0.0,
    }
    for col, default in neutral_defaults.items():
        if col in merged.columns:
            merged[col] = merged[col].fillna(default)

    if len(merged) == 0:
        raise ValueError(
            "Merge produced 0 rows. Check ticker symbols match."
        )

    logger.info(
        f"Merge complete | "
        f"price rows: {len(price_df)} | "
        f"sentiment rows: {len(sentiment_df)} | "
        f"merged rows: {len(merged)}"
    )

    return merged


def build_feature_matrix(
    price_df:     pd.DataFrame,
    sentiment_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Full pipeline: raw price + raw sentiment → ML-ready feature matrix.

    This is the single function called by train.py and scripts/run_pipeline.py.
    Executes the full feature engineering sequence:
        1. Aggregate article-level sentiment to daily level
        2. Add rolling window features
        3. Merge with price technical indicators
        4. Final cleaning and validation

    Args:
        price_df:     raw price DataFrame from yfinance_fetcher
        sentiment_df: sentiment-scored news DataFrame from sentiment.py

    Returns:
        Clean feature matrix with FEATURE_COLS + TARGET_COL columns
    """
    logger.info("Building feature matrix...")

    # Step 1: Aggregate sentiment to daily
    daily_sentiment = aggregate_daily_sentiment(sentiment_df)
    logger.info(f"Daily sentiment: {len(daily_sentiment)} rows")

    # Step 2: Add rolling features
    daily_sentiment = add_rolling_sentiment_features(daily_sentiment)

    # Step 3: Merge with price data
    feature_df = merge_price_and_sentiment(price_df, daily_sentiment)

    # Step 4: Drop rows with any missing feature values
    # This is safer than imputation for financial ML
    # Missing data usually means a data pipeline problem — not random missingness
    import numpy as np
    before = len(feature_df)
    feature_df = feature_df.dropna(subset=FEATURE_COLS + [TARGET_COL])
    after = len(feature_df)

    if before - after > 0:
        logger.warning(f"Dropped {before - after} rows with missing feature values")

    # Step 5: Validate target distribution
    # If > 65% of days are "up" or "down", the dataset is imbalanced
    # This would skew the model toward always predicting the majority class
    target_dist = feature_df[TARGET_COL].value_counts(normalize=True)
    logger.info(f"Target distribution: {target_dist.to_dict()}")

    if target_dist.max() > 0.65:
        logger.warning(
            f"Target imbalance detected: {target_dist.to_dict()}. "
            f"Consider using class_weight='balanced' in the model."
        )

    logger.info(
        f"Feature matrix ready | "
        f"rows={len(feature_df)} | "
        f"features={len(FEATURE_COLS)} | "
        f"target_col={TARGET_COL}"
    )

    return feature_df.reset_index(drop=True)


def get_X_y(df: pd.DataFrame) -> tuple:
    """
    Split feature matrix into X (features) and y (target).

    Only includes columns defined in FEATURE_COLS from constants.py.
    This ensures the exact same feature set is used in training and prediction.

    Args:
        df: feature matrix from build_feature_matrix()

    Returns:
        X: DataFrame of feature columns
        y: Series of target column (0 or 1)
    """
    # Only use features that actually exist in the DataFrame
    # (some may be missing if data was sparse)
    available_features = [c for c in FEATURE_COLS if c in df.columns]

    missing = set(FEATURE_COLS) - set(available_features)
    if missing:
        logger.warning(f"Missing features (will be excluded): {missing}")

    X = df[available_features]
    y = df[TARGET_COL]

    logger.info(f"X shape: {X.shape} | y distribution: {y.value_counts().to_dict()}")
    return X, y