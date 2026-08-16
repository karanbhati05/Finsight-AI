# FinSight V2 — Quick Reference Card

Print this and keep it next to you while building.

---

## Build Order (strict sequence)

```
BACKEND FIRST
  □ Prompt 1 → FastAPI backend (all routers + WebSocket)
  □ Test: curl http://localhost:8000/api/market/indices?region=india
  □ Test: curl http://localhost:8000/api/health
  □ Check: http://localhost:8000/docs (auto-generated API docs)

FRONTEND SECOND
  □ Prompt 2 → React layout shell (hardcoded data)
  □ Test: npm run dev → see Google Finance layout at localhost:5173

CONNECT DATA
  □ Prompt 3 → Market data (live index cards, sparklines, sectors)
  □ Prompt 4 → News feed with sentiment badges + Dive Deeper button
  □ Prompt 5 → Research panel (RAG chatbot with citations)
  □ Prompt 6 → ML Predictions panel (embedded in main feed)
  □ Prompt 7 → Portfolio + Watchlist (sidebar CRUD)

POLISH
  □ Prompt 8 → Live prices (WebSocket) + mobile + animations
  □ Prompt 9 → Docker + deployment
```

---

## Key URLs

```
Frontend:        http://localhost:5173
Backend API:     http://localhost:8000
API Docs:        http://localhost:8000/docs
Redis:           localhost:6379
WebSocket:       ws://localhost:8000/ws/prices
```

---

## Files Opus Gets Per Prompt

```
Prompt 1: 03_EXISTING_CODE.md + 02_API_CONTRACTS.md + 05_BACKEND_STARTER.md
Prompt 2: 04_DESIGN_SYSTEM.md + 06_FRONTEND_STARTER.md + screenshot
Prompt 3: output of Prompt 2 (working layout)
Prompt 4: output of Prompt 3 (working market data)
Prompt 5: output of Prompt 4 (working news feed)
Prompt 6: output of Prompt 5 (working chat)
Prompt 7: output of Prompt 6 (working predictions)
Prompt 8: output of Prompt 7 (complete app)
Prompt 9: output of Prompt 8 (polished app)
```

---

## Colors (memorize these)

```
Gain green:   #0f9d58  bg: #e6f4ea  text: #137333
Loss red:     #d93025  bg: #fce8e6  text: #c5221f
Primary blue: #1a73e8
Background:   #ffffff
Surface:      #f8f9fa
Border:       #e8eaed
Text:         #202124
Subtext:      #5f6368
```

---

## API Endpoints Cheat Sheet

```
GET  /api/health
GET  /api/market/indices?region=india
GET  /api/market/sectors?region=india
GET  /api/market/search?q=AAPL
GET  /api/news/{ticker}
GET  /api/sentiment/{ticker}
GET  /api/predict/{ticker}
POST /api/chat            body: {question, ticker, session_id}
GET  /api/chat/suggestions/{ticker}
DEL  /api/chat/{session_id}
GET  /api/watchlist
POST /api/watchlist       body: {ticker}
DEL  /api/watchlist/{ticker}
GET  /api/portfolio
POST /api/portfolio       body: {ticker, shares, buy_price}
DEL  /api/portfolio/{ticker}
WS   /ws/prices
```

---

## Component Hierarchy

```
App
└── Dashboard (page)
    └── AppShell
        ├── TopBar (search bar + avatar)
        ├── Sidebar (left, 280px)
        │   ├── PortfolioList
        │   │   └── PortfolioRow × N
        │   ├── WatchlistPanel
        │   │   └── WatchlistRow × N
        │   └── SectorList
        │       └── SectorRow × N
        ├── MainFeed (center, flex-1)
        │   ├── MarketTabs (US/India/Crypto)
        │   ├── IndexGrid
        │   │   └── IndexCard × 4
        │   ├── NewsFeed
        │   │   ├── MarketSummary
        │   │   └── NewsCard × N
        │   │       └── DiveDeepButton
        │   └── PredictionSection (collapsible)
        │       ├── PredictionCard
        │       ├── ProbabilityGauge
        │       ├── ProbabilityChart
        │       └── FeatureImportance
        └── ResearchPanel (right, 380px)
            ├── SuggestedQueries
            ├── QuickActions
            ├── ResearchChat
            │   └── ChatMessage × N
            │       └── SourceCitation
            └── ChatInput
```

---

## State Management (Zustand stores)

```
marketStore:
  activeRegion, activeTicker
  indices[], sectors[]
  indicesLoading, sectorsLoading
  setActiveRegion(), setActiveTicker()
  setIndices(), setSectors()

watchlistStore:
  watchlist[]
  addTicker(), removeTicker(), refresh()

portfolioStore:
  holdings[]
  totalValue, totalPnL, totalPnLPct
  addHolding(), removeHolding()

researchStore:
  messages[], sessionId, loading
  addMessage(), setLoading()
  clearHistory()
```

---

## Common Mistakes to Avoid

```
❌ Installing shadcn/MUI/Chakra — use only Tailwind + Recharts
❌ Hardcoding colors inline — use Tailwind classes (text-gain, text-loss)
❌ Fetching data inside components — use custom hooks
❌ Not handling loading states — every API call needs skeleton
❌ Not handling errors — every API call needs error state
❌ Re-fetching on every render — use Zustand cache
❌ Missing CORS — backend must allow http://localhost:5173
❌ Wrong WebSocket URL — use ws:// not http://
❌ Blocking startup — load models in lifespan(), not in router
```

---

## If Something Breaks

```
Backend won't start:
  → Check: python -c "from src.nlp.sentiment import FinBERTSentiment"
  → Check: all env vars in .env
  → Check: ChromaDB has data (run V1 pipeline first)

Frontend won't connect to backend:
  → Check: vite.config.js has proxy for /api and /ws
  → Check: backend running on port 8000
  → Check: CORS allows http://localhost:5173

WebSocket not connecting:
  → Check: ws:// not wss:// for local dev
  → Check: proxy in vite.config.js has ws: true

Models loading slowly:
  → Normal on first run — FinBERT downloads 440MB
  → After first run, cached in ~/.cache/huggingface

No data in chatbot:
  → Run V1 pipeline first: python scripts/run_pipeline.py --ticker AAPL
  → Check ChromaDB: python -c "from src.rag.vector_store import FinancialVectorStore; print(FinancialVectorStore().count())"
```

