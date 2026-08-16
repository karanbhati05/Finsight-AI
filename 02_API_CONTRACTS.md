# FinSight V2 — Complete API Contracts

All endpoints the FastAPI backend must implement.
All response shapes the React frontend expects.

---

## Base URL
Development:  http://localhost:8000
Frontend:     http://localhost:5173

---

## 1. Market Indices
GET /api/market/indices?region=india

Response:
```json
{
  "region": "india",
  "indices": [
    {
      "symbol":        "^NSEI",
      "name":          "NIFTY 50",
      "value":         24366.00,
      "change":        -29.85,
      "change_pct":    -0.12,
      "direction":     "down",
      "sparkline":     [24100, 24200, 24350, 24300, 24366],
      "last_updated":  "2026-05-13T10:30:00Z"
    }
  ]
}
```

Supported regions: india, us, europe, crypto, futures, currencies

---

## 2. Market Sectors
GET /api/market/sectors?region=india

Response:
```json
{
  "sectors": [
    {
      "symbol":     "NIFTY_AUTO.NS",
      "name":       "NIFTY_AUTO",
      "label":      "Auto",
      "value":      29207.90,
      "change_pct": -0.63,
      "direction":  "down",
      "sparkline":  [29400, 29350, 29250, 29207]
    }
  ]
}
```

---

## 3. News Feed
GET /api/news/{ticker}?limit=20&days_back=7

Response:
```json
{
  "ticker": "AAPL",
  "articles": [
    {
      "id":              "abc123",
      "title":           "Apple reports record revenue",
      "summary":         "Apple Inc reported quarterly revenue...",
      "source":          "Reuters",
      "source_count":    3,
      "published_at":    "2026-05-13T08:00:00Z",
      "url":             "https://reuters.com/...",
      "sentiment_label": "positive",
      "sentiment_score": 0.742,
      "entities": {
        "companies": ["Apple", "Goldman Sachs"],
        "people":    ["Tim Cook"],
        "money":     ["$94.9 billion"]
      }
    }
  ],
  "market_summary": "Apple shares rose on strong earnings...",
  "avg_sentiment":  0.42
}
```

---

## 4. Sentiment Trend
GET /api/sentiment/{ticker}?days=30

Response:
```json
{
  "ticker": "AAPL",
  "sentiment_trend": [
    {
      "date":           "2026-05-01",
      "avg_score":      0.32,
      "article_count":  8,
      "positive_ratio": 0.62,
      "negative_ratio": 0.25
    }
  ],
  "summary": {
    "avg_score":      0.28,
    "trend":          "improving",
    "score_delta":    0.15,
    "total_articles": 92
  }
}
```

---

## 5. ML Prediction
GET /api/predict/{ticker}

Response:
```json
{
  "ticker":      "AAPL",
  "date":        "2026-05-13",
  "prediction":  1,
  "label":       "UP",
  "probability": 0.673,
  "confidence":  "High",
  "features": {
    "sentiment_score":          0.42,
    "rsi_14":                   58.3,
    "rolling_avg_sentiment_3d": 0.38,
    "price_ma5":                189.20,
    "price_ma20":               185.40
  },
  "model_metrics": {
    "cv_f1":   0.61,
    "roc_auc": 0.64
  },
  "probability_history": [
    {"date": "2026-05-01", "probability": 0.58},
    {"date": "2026-05-02", "probability": 0.61}
  ]
}
```

---

## 6. RAG Chat
POST /api/chat

Request:
```json
{
  "question":    "What are Apple's main risk factors?",
  "ticker":      "AAPL",
  "top_k":       5,
  "session_id":  "user_session_123"
}
```

Response:
```json
{
  "answer":   "According to Apple's 10-K filing [Source 1]...",
  "sources": [
    {
      "source":          "SEC 10-K",
      "ticker":          "AAPL",
      "date":            "2024-11-01",
      "source_type":     "filing",
      "sentiment_label": "",
      "relevance":       0.87
    }
  ],
  "retrieved_chunks": 5,
  "session_id":       "user_session_123"
}
```

---

## 7. Suggested Questions
GET /api/chat/suggestions/{ticker}

Response:
```json
{
  "ticker": "AAPL",
  "suggestions": [
    "What are the main risk factors Apple mentioned?",
    "How has Apple's revenue trended recently?",
    "What did analysts say about iPhone sales?",
    "What is Apple's outlook for next quarter?"
  ]
}
```

---

## 8. Watchlist
GET    /api/watchlist
POST   /api/watchlist        body: {"ticker": "AAPL"}
DELETE /api/watchlist/{ticker}

GET Response:
```json
{
  "watchlist": [
    {
      "ticker":     "AAPL",
      "name":       "Apple Inc.",
      "price":      189.25,
      "change":     1.45,
      "change_pct": 0.77,
      "direction":  "up",
      "sparkline":  [185, 186, 188, 189, 189.25]
    }
  ]
}
```

---

## 9. Portfolio
GET    /api/portfolio
POST   /api/portfolio        body: {"ticker": "AAPL", "shares": 10, "buy_price": 175.00}
DELETE /api/portfolio/{ticker}

GET Response:
```json
{
  "holdings": [
    {
      "ticker":      "AAPL",
      "name":        "Apple Inc.",
      "shares":      10,
      "buy_price":   175.00,
      "current":     189.25,
      "pnl":         142.50,
      "pnl_pct":     8.14,
      "direction":   "up",
      "market_value":1892.50
    }
  ],
  "total_value":  1892.50,
  "total_pnl":    142.50,
  "total_pnl_pct":8.14
}
```

---

## 10. WebSocket — Live Prices
ws://localhost:8000/ws/prices

Client sends:
```json
{"action": "subscribe", "tickers": ["AAPL", "MSFT", "^NSEI"]}
```

Server pushes every 10 seconds:
```json
{
  "type":   "price_update",
  "prices": {
    "AAPL": {"price": 189.30, "change": 1.50, "change_pct": 0.80},
    "MSFT": {"price": 415.20, "change": -0.80, "change_pct": -0.19}
  },
  "timestamp": "2026-05-13T10:30:45Z"
}
```

---

## CORS Configuration
Allow origins: http://localhost:5173
Allow methods: GET, POST, DELETE, OPTIONS
Allow headers: Content-Type, Authorization
