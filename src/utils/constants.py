# src/utils/constants.py

# ── Ticker → Full company name mapping ──────────────────────────────────────
# Used by news_fetcher to build better search queries
# e.g. searching "Apple OR AAPL stock" finds more articles than just "AAPL"
TICKER_COMPANY_MAP = {
    "AAPL": "Apple",
    "MSFT": "Microsoft",
    "GOOGL": "Alphabet",
    "AMZN": "Amazon",
    "TSLA": "Tesla",
    "JPM":  "JPMorgan Chase",
    "GS":   "Goldman Sachs",
    "MS":   "Morgan Stanley",
    "BAC":  "Bank of America",
    "C":    "Citigroup",
    "WFC":  "Wells Fargo",
    "BLK":  "BlackRock",
}

# ── Supported SEC filing types ───────────────────────────────────────────────
# 10-K = annual report, 10-Q = quarterly, 8-K = major event disclosure
SEC_FORM_TYPES = ["10-K", "10-Q", "8-K"]

# ── FinBERT output labels ────────────────────────────────────────────────────
SENTIMENT_LABELS = ["positive", "negative", "neutral"]

# Used by Streamlit dashboard for coloring sentiment badges
SENTIMENT_COLOR_MAP = {
    "positive": "#22c55e",   # green
    "negative": "#ef4444",   # red
    "neutral":  "#94a3b8",   # gray
}

# ── ML feature columns ───────────────────────────────────────────────────────
# Single source of truth — used in feature_engineering.py, train.py, predict.py
# If you add a new feature, add it here and it flows everywhere automatically
FEATURE_COLS = [
    "sentiment_score",
    "sentiment_magnitude",
    "rolling_avg_sentiment_3d",
    "rolling_avg_sentiment_7d",
    "volume_change_pct",
    "price_ma5",
    "price_ma20",
    "rsi_14",
    "positive_ratio",
    "negative_ratio",
    "article_count",
]

TARGET_COL = "price_direction"  # binary: 1 = price went up next day, 0 = down

# ── Paths ────────────────────────────────────────────────────────────────────
RAW_DATA_DIR       = "data/raw"
PROCESSED_DATA_DIR = "data/processed"
EMBEDDINGS_DIR     = "data/embeddings"
MODELS_DIR         = "models"
LOGS_DIR           = "logs"