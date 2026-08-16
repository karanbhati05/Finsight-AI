# FinSight V2 — Complete File Structure

Create every file listed here. Do not add extras, do not skip any.

```
finsight-v2/
│
├── backend/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py                    ← FastAPI app, CORS, startup
│   │   ├── dependencies.py            ← shared instances (chatbot, model)
│   │   ├── websocket.py               ← live price WebSocket handler
│   │   └── routers/
│   │       ├── __init__.py
│   │       ├── market.py              ← GET /api/market/indices, /sectors
│   │       ├── news.py                ← GET /api/news/{ticker}
│   │       ├── sentiment.py           ← GET /api/sentiment/{ticker}
│   │       ├── prediction.py          ← GET /api/predict/{ticker}
│   │       ├── chat.py                ← POST /api/chat
│   │       ├── watchlist.py           ← CRUD /api/watchlist
│   │       └── portfolio.py           ← CRUD /api/portfolio
│   ├── cache/
│   │   ├── __init__.py
│   │   └── redis_client.py            ← Redis cache wrapper
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py                 ← Pydantic request/response models
│   └── requirements_backend.txt
│
├── frontend/
│   ├── index.html
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── package.json
│   └── src/
│       ├── main.jsx                   ← React entry point
│       ├── App.jsx                    ← Router setup
│       ├── index.css                  ← Tailwind directives + Inter font
│       │
│       ├── api/
│       │   ├── client.js              ← Axios instance with base URL
│       │   ├── market.js              ← market API calls
│       │   ├── news.js                ← news API calls
│       │   ├── chat.js                ← chat API calls
│       │   ├── prediction.js          ← prediction API calls
│       │   └── portfolio.js           ← portfolio/watchlist API calls
│       │
│       ├── store/
│       │   ├── marketStore.js         ← Zustand: indices, sectors
│       │   ├── watchlistStore.js      ← Zustand: watchlist stocks
│       │   ├── portfolioStore.js      ← Zustand: portfolio holdings
│       │   └── researchStore.js       ← Zustand: chat history
│       │
│       ├── hooks/
│       │   ├── useMarketData.js       ← fetch + poll market indices
│       │   ├── useSentiment.js        ← fetch sentiment for ticker
│       │   ├── usePrediction.js       ← fetch ML prediction
│       │   ├── useNews.js             ← fetch news feed
│       │   └── useWebSocket.js        ← live price WebSocket
│       │
│       ├── components/
│       │   ├── layout/
│       │   │   ├── AppShell.jsx       ← three-column grid wrapper
│       │   │   ├── Sidebar.jsx        ← left panel (280px)
│       │   │   ├── MainFeed.jsx       ← center content area
│       │   │   ├── ResearchPanel.jsx  ← right panel (380px)
│       │   │   └── TopBar.jsx         ← search bar + user avatar
│       │   │
│       │   ├── market/
│       │   │   ├── MarketTabs.jsx     ← US/India/Crypto tabs
│       │   │   ├── IndexCard.jsx      ← single index card
│       │   │   ├── IndexGrid.jsx      ← four index cards in row
│       │   │   ├── SparklineChart.jsx ← 40px mini chart
│       │   │   ├── SectorList.jsx     ← equity sectors list
│       │   │   └── SectorRow.jsx      ← single sector row
│       │   │
│       │   ├── news/
│       │   │   ├── NewsFeed.jsx       ← list of news stories
│       │   │   ├── NewsCard.jsx       ← single expandable story
│       │   │   ├── NewsHeader.jsx     ← story title + sources count
│       │   │   ├── NewsBody.jsx       ← expanded story content
│       │   │   ├── SentimentBadge.jsx ← colored positive/negative pill
│       │   │   └── DiveDeepButton.jsx ← "Dive deeper with AI" button
│       │   │
│       │   ├── research/
│       │   │   ├── ResearchChat.jsx   ← full chat interface
│       │   │   ├── ChatMessage.jsx    ← single message bubble
│       │   │   ├── ChatInput.jsx      ← input + send button
│       │   │   ├── SuggestedQueries.jsx ← clickable question chips
│       │   │   ├── SourceCitation.jsx ← expandable source list
│       │   │   └── QuickActions.jsx   ← Create portfolio, Deep Search etc
│       │   │
│       │   ├── prediction/
│       │   │   ├── PredictionCard.jsx ← UP/DOWN hero card
│       │   │   ├── ProbabilityGauge.jsx ← circular confidence gauge
│       │   │   ├── ProbabilityChart.jsx ← history line chart
│       │   │   └── FeatureImportance.jsx← horizontal bar chart
│       │   │
│       │   ├── portfolio/
│       │   │   ├── PortfolioList.jsx  ← holdings list
│       │   │   ├── PortfolioRow.jsx   ← single holding
│       │   │   ├── AddStockModal.jsx  ← add new position
│       │   │   └── PortfolioPnL.jsx   ← total P&L card
│       │   │
│       │   ├── watchlist/
│       │   │   ├── WatchlistPanel.jsx ← watchlist section
│       │   │   ├── WatchlistRow.jsx   ← single watched stock
│       │   │   └── AddToWatchlist.jsx ← add stock input
│       │   │
│       │   └── common/
│       │       ├── Skeleton.jsx       ← loading skeleton blocks
│       │       ├── Badge.jsx          ← reusable colored badge
│       │       ├── Button.jsx         ← reusable button
│       │       ├── Modal.jsx          ← reusable modal wrapper
│       │       ├── SearchBar.jsx      ← global search with autocomplete
│       │       ├── PriceChange.jsx    ← colored +/-% display
│       │       └── Tooltip.jsx        ← hover tooltip
│       │
│       └── pages/
│           ├── Dashboard.jsx          ← main Google Finance layout
│           ├── StockDetail.jsx        ← deep dive single stock
│           └── Portfolio.jsx          ← portfolio management page
│
├── docker-compose.yml                 ← runs everything together
├── .env.example                       ← all required env vars
└── README.md                          ← setup instructions
```
