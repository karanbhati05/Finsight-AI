# FinSight V2 — Existing V1 Code Reference

These modules are COMPLETE and WORKING. 
FastAPI routers must import and use them directly.
DO NOT rewrite or modify any of this code.

---

## How to import existing modules in FastAPI routers

All routers live in backend/api/routers/
The existing src/ folder is at the project root.
Add this to backend/api/main.py startup:

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
```

Then import normally:
```python
from src.nlp.sentiment import FinBERTSentiment
from src.ml.predict import load_model, predict_latest
from src.rag.chatbot import FinancialChatbot
from src.rag.vector_store import FinancialVectorStore
from src.ingestion.yfinance_fetcher import fetch_price_data
```

---

## Module 1: FinBERT Sentiment
File: src/nlp/sentiment.py

```python
# How to use:
model = FinBERTSentiment()

# Single text
result = model.predict("Apple reported record revenue")
# Returns:
# {
#   "label": "positive",
#   "score": 0.847,          ← use this as sentiment_score
#   "confidence": 0.923,
#   "prob_positive": 0.923,
#   "prob_negative": 0.042,
#   "prob_neutral": 0.035
# }

# DataFrame of news articles
df = model.analyze_dataframe(df, text_col="content_sentiment")
# Adds columns: sentiment_label, sentiment_score, sentiment_confidence
```

---

## Module 2: ML Prediction
File: src/ml/predict.py

```python
# How to use:
from src.ml.predict import load_model, predict_latest, get_prediction_history

# Load saved model
model_dict = load_model(ticker="AAPL")

# Latest prediction
result = predict_latest(
    ticker       = "AAPL",
    price_df     = price_df,     # from yfinance_fetcher
    sentiment_df = sentiment_df, # from news_enriched.csv
)
# Returns:
# {
#   "prediction":  1,
#   "probability": 0.673,
#   "label":       "UP ↑",
#   "confidence":  "High",
#   "features":    {...},
#   "date":        "2026-05-13"
# }

# History for chart
history_df = get_prediction_history("AAPL", price_df, sentiment_df)
# Returns DataFrame with: date, close, up_probability, prediction_label
```

---

## Module 3: RAG Chatbot
File: src/rag/chatbot.py

```python
# How to use:
chatbot = FinancialChatbot()  # loads Gemini + ChromaDB

result = chatbot.ask(
    question = "What are Apple's main risk factors?",
    ticker   = "AAPL",
    top_k    = 5,
)
# Returns:
# {
#   "answer":           "According to Apple's 10-K [Source 1]...",
#   "sources":          [{"source": "SEC 10-K", "date": "...", ...}],
#   "retrieved_chunks": 5,
#   "context_used":     "...",
#   "question":         "..."
# }

# Clear history between sessions
chatbot.clear_history()
```

---

## Module 4: Vector Store
File: src/rag/vector_store.py

```python
# How to use:
store = FinancialVectorStore()

stats = store.get_stats()
# Returns: {"total_chunks": 234, "tickers": ["AAPL"], "collection_name": "finsight_all"}

count = store.count()
# Returns: 234
```

---

## Module 5: Price Data
File: src/ingestion/yfinance_fetcher.py

```python
# How to use:
from src.ingestion.yfinance_fetcher import fetch_price_data, add_technical_indicators

df = fetch_price_data("AAPL", period="1y")
df = add_technical_indicators(df)
# Returns DataFrame with: date, open, high, low, close, volume,
#                         price_ma5, price_ma20, rsi_14,
#                         volume_change_pct, price_direction, daily_return

# For sparkline — last 30 closes
sparkline = df["close"].tail(30).tolist()
```

---

## Module 6: News Data
File: src/ingestion/finnhub_fetcher.py

```python
# How to use:
from src.ingestion.finnhub_fetcher import fetch_company_news

df = fetch_company_news(ticker="AAPL", days_back=7, max_articles=50)
# Returns DataFrame with: ticker, title, description, content,
#                         source, published_at, url, category
```

---

## Processed Data Files (already on disk)
After pipeline runs, these CSV files exist:

data/processed/{ticker}/news_enriched.csv
  Columns: ticker, title, content, source, published_at, url,
           content_sentiment, content_ner,
           sentiment_label, sentiment_score, sentiment_confidence,
           prob_positive, prob_negative, prob_neutral,
           entities, entity_orgs, summary

data/raw/{ticker}/price_data.csv
  Columns: date, open, high, low, close, volume, ticker,
           price_ma5, price_ma20, rsi_14,
           volume_change_pct, daily_return, price_direction

models/{ticker}_xgb_model.pkl
  Contents: {"model": Pipeline, "feature_cols": [...],
             "cv_mean_f1": 0.61, "test_metrics": {...}}

---

## Environment Variables Required
(All already in .env from V1)

GOOGLE_API_KEY=...      ← Gemini API
NEWS_API_KEY=...        ← NewsAPI
FINNHUB_API_KEY=...     ← Finnhub

New ones needed for V2:
REDIS_URL=redis://localhost:6379
DATABASE_URL=sqlite:///./finsight.db
FRONTEND_URL=http://localhost:5173
