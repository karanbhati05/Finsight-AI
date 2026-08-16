# FinSight V2 — Exact Prompts for Opus 4.6

Copy-paste these prompts to Opus IN ORDER.
Do not move to the next prompt until the current one is complete and working.

---

## PROMPT 1 — Backend Foundation
(Give Opus: 03_EXISTING_CODE.md + 02_API_CONTRACTS.md + 05_BACKEND_STARTER.md)

```
You are building FinSight V2 — an upgrade of an existing AI financial 
research system. The existing AI modules are complete and working.
Your job is to wrap them in a FastAPI backend.

Read the three attached documents carefully:
- 03_EXISTING_CODE.md  → what modules exist and how to call them
- 02_API_CONTRACTS.md  → exact request/response shapes needed
- 05_BACKEND_STARTER.md → starter code to build on

Build these files completely:
1. backend/api/main.py
2. backend/api/dependencies.py
3. backend/api/models/schemas.py
4. backend/api/routers/market.py      (indices + sectors + search)
5. backend/api/routers/news.py        (news feed with sentiment)
6. backend/api/routers/sentiment.py   (sentiment trend data)
7. backend/api/routers/prediction.py  (ML price prediction)
8. backend/api/routers/chat.py        (RAG chatbot)
9. backend/api/routers/watchlist.py   (CRUD watchlist)
10. backend/api/routers/portfolio.py  (CRUD portfolio with P&L)
11. backend/api/websocket.py          (live price WebSocket)
12. backend/cache/redis_client.py     (Redis cache wrapper)
13. backend/requirements_backend.txt

Rules:
- Import existing src/ modules directly — DO NOT rewrite them
- Add Redis caching to market.py: cache indices for 30 seconds, news for 5 minutes
- Every endpoint must handle exceptions gracefully and return meaningful errors
- Add startup logging that confirms each model loaded successfully
- Use async where possible for better performance

After building, show me how to run it and what the /docs page will look like.
```

---

## PROMPT 2 — React Layout Shell
(Give Opus: 04_DESIGN_SYSTEM.md + 06_FRONTEND_STARTER.md + the Google Finance screenshot)

```
Build the React frontend shell for FinSight V2.
Match the Google Finance layout in the attached screenshot EXACTLY.

Read the two attached documents:
- 04_DESIGN_SYSTEM.md  → exact colors, typography, component specs
- 06_FRONTEND_STARTER.md → starter code to build on

Build these files:
1. frontend/src/components/layout/AppShell.jsx     (three-column grid)
2. frontend/src/components/layout/TopBar.jsx        (search + avatar)
3. frontend/src/components/layout/Sidebar.jsx       (left panel)
4. frontend/src/components/layout/MainFeed.jsx      (center content)
5. frontend/src/components/layout/ResearchPanel.jsx (right panel)
6. frontend/src/components/market/MarketTabs.jsx    (US/India/Crypto tabs)
7. frontend/src/components/common/Skeleton.jsx      (loading states)
8. frontend/src/components/common/PriceChange.jsx   (colored +/-%)
9. frontend/src/pages/Dashboard.jsx                 (main page)
10. All config files: vite.config.js, tailwind.config.js, package.json

At this stage use HARDCODED mock data — no API calls yet.
Focus 100% on making it look exactly like Google Finance.

Mock data to use:
- 4 index cards: NIFTY 50 (24366, -0.12%), SENSEX (78009, -0.09%),
  Nifty Bank (57491, -0.25%), Nifty IT (31357, -0.31%)
- 6 sector rows with random sparklines
- 3 news items with hardcoded text
- Research panel with suggested questions and chat input

Rules:
- NO component libraries except Tailwind and Recharts
- Build everything from scratch
- Use exact colors from design system: #0f9d58 gain, #d93025 loss
- Every card must have hover state
- Sidebar and research panel must scroll independently
- Main feed scrolls in the center
```

---

## PROMPT 3 — Market Data Components
(Give Opus: the working layout from Prompt 2)

```
Now build the real market data components for FinSight V2.
Replace all hardcoded mock data with live API calls.

Build these components completely:

1. frontend/src/components/market/IndexCard.jsx
   - Shows: name, value (formatted with commas), change, change_pct
   - Sparkline chart (40px height, no axes, filled area)
   - Green/red color based on direction
   - Hover: subtle shadow + background change
   - Click: navigate to /stock/{symbol}
   - Loading skeleton when data not ready

2. frontend/src/components/market/IndexGrid.jsx
   - Renders 4 IndexCards in a responsive row
   - Gap 12px between cards
   - On mobile: 2x2 grid

3. frontend/src/components/market/SparklineChart.jsx
   - Recharts AreaChart, 40px height, no axes, no tooltips
   - Green fill (#e6f4ea) for positive, red fill (#fce8e6) for negative
   - strokeWidth 1.5
   - isAnimationActive={false} for performance

4. frontend/src/components/market/SectorList.jsx
   - Renders all sector rows
   - Section header: "Equity sectors" with collapse arrow

5. frontend/src/components/market/SectorRow.jsx
   - Left: sector name (bold) + label (small gray)
   - Center: 80px sparkline
   - Right: value + colored change_pct
   - Hover background

6. frontend/src/hooks/useMarketData.js
   - Calls GET /api/market/indices and /api/market/sectors
   - Refreshes every 60 seconds
   - Handles loading and error states

7. frontend/src/store/marketStore.js (Zustand)
   - Stores: activeRegion, indices, sectors, loading states

Wire up MarketTabs so clicking "US" fetches US indices,
clicking "India" fetches India indices etc.

Show loading skeletons while data is fetching.
Handle API errors gracefully with a retry button.
```

---

## PROMPT 4 — News Feed with AI
(Give Opus: working market components from Prompt 3)

```
Build the news feed components for FinSight V2.
This is the center piece of the main feed — make it look exactly like Google Finance.

Build these components:

1. frontend/src/components/news/NewsFeed.jsx
   - Fetches GET /api/news/{activeTicker}
   - Shows market summary text at top (bold, larger)
   - Lists NewsCard components below
   - Loading: 3 NewsCardSkeletons
   - Empty state: "No news available for {ticker}"

2. frontend/src/components/news/NewsCard.jsx
   - Collapsed view: title (bold, 2 lines max) + sources + time ago
   - Expanded view (click to expand): shows summary paragraph
   - "X sites" count badge (e.g. "Reuters · Bloomberg · 3 sites")
   - SentimentBadge showing FinBERT label + score
   - DiveDeepButton at bottom of expanded view
   - Smooth expand/collapse animation (max-height transition)

3. frontend/src/components/news/DiveDeepButton.jsx
   - Sparkle icon (✨) + "Dive deeper with AI" text
   - Google blue color (#1a73e8)
   - On click: sends article title to research panel chat
   - Shows loading spinner while AI processes

4. frontend/src/components/news/SentimentBadge.jsx
   - Pill badge: POSITIVE (green) / NEGATIVE (red) / NEUTRAL (gray)
   - Shows score: "+0.847"
   - Uppercase, small font

5. frontend/src/hooks/useNews.js
   - Fetches news for active ticker
   - Refreshes every 5 minutes
   - Returns: articles, marketSummary, avgSentiment, loading, error

6. Market Summary section
   - Bold headline above news list
   - "Indian benchmark indices snap winning streak..." style text
   - Source count badge ("TI X 3 sites")
   - Expand/collapse with chevron

Wire "Dive deeper with AI" button to send a message to the
ResearchPanel chat: "Summarize this article and its implications
for {ticker}: {article_title}"
The research panel should auto-open and show the AI response.
```

---

## PROMPT 5 — Research Panel (RAG Chatbot)
(Give Opus: working news feed from Prompt 4)

```
Build the Research Panel — the right sidebar AI chat interface.
This must feel like a real AI assistant, not just a basic chatbot.

Build these components:

1. frontend/src/components/research/ResearchPanel.jsx
   - Fixed right panel, 380px wide
   - Header: "Research" title + edit icon + menu icon
   - Suggested queries section (clickable)
   - "Explore what's possible" quick actions
   - Scrollable chat messages area
   - Fixed input at bottom

2. frontend/src/components/research/SuggestedQueries.jsx
   - Fetches GET /api/chat/suggestions/{activeTicker}
   - Shows 2 clickable query rows with search icon
   - Click sends query to chat
   - Refresh when ticker changes

3. frontend/src/components/research/QuickActions.jsx
   - Four buttons in 2x2 grid:
     "+ Create portfolio" / "⚙ Create task"
     "🔍 Deep Search"     / "📈 Analyse watchlist"
   - Rounded pill style buttons
   - Gray background, dark text

4. frontend/src/components/research/ResearchChat.jsx
   - Chat message list (scrollable)
   - Auto-scrolls to bottom on new message
   - User messages: right-aligned, blue background
   - AI messages: left-aligned, white with border
   - Loading: typing indicator (three dots animation)

5. frontend/src/components/research/ChatMessage.jsx
   - User bubble: bg #1a73e8, white text, right-align
   - AI bubble: bg white, border #e8eaed, left-align
   - AI messages show SourceCitation below if sources exist

6. frontend/src/components/research/SourceCitation.jsx
   - Expandable "X sources" button
   - Expands to show: source name, date, type (filing/news)
   - Filing sources highlighted: "SEC 10-K" badge
   - Link icon for news sources with URL

7. frontend/src/components/research/ChatInput.jsx
   - Full-width text input
   - Microphone icon on left
   - Send button on right (active when text entered)
   - Submit on Enter key
   - Disabled + spinner while AI is responding

8. frontend/src/store/researchStore.js
   - messages: [{role, content, sources, id, timestamp}]
   - sessionId: uuid (new session on ticker change)
   - loading: boolean
   - activeTicker: string

Wire everything:
- Clicking suggested query → sends to chat API → shows response
- "Dive deeper with AI" from news → pre-fills chat and sends
- Ticker change → clears chat history + new session
- Show "Powered by Gemini + SEC Filings" caption in empty state
```

---

## PROMPT 6 — ML Predictions Panel
(Give Opus: working research panel from Prompt 5)

```
Build the ML Predictions section for FinSight V2.
This replaces the old Streamlit ML page — embed it in the main feed
as a collapsible section below the news feed.

Build these components:

1. frontend/src/components/prediction/PredictionCard.jsx
   Today's prediction hero card:
   - Large UP ↑ or DOWN ↓ arrow (48px, colored)
   - Prediction label and probability percentage
   - Confidence tier: High / Medium / Low
   - Date of prediction
   - Thin colored border (green for UP, red for DOWN)
   - Hover: slight elevation shadow
   - Loading skeleton while fetching

2. frontend/src/components/prediction/ProbabilityGauge.jsx
   Semi-circle gauge showing probability:
   - 0% left (DOWN) to 100% right (UP)
   - 50% = neutral gray
   - Fill color transitions red→gray→green
   - Current probability marker
   - Build with SVG arc — do not use a library for this

3. frontend/src/components/prediction/ProbabilityChart.jsx
   Line chart of probability history:
   - Last 60 days of up_probability
   - Green shaded zone above 0.65: "Strong Buy Zone"
   - Red shaded zone below 0.35: "Strong Sell Zone"
   - Dashed line at 0.5 (neutral)
   - Recharts AreaChart, height 200px
   - Tooltip showing date + probability

4. frontend/src/components/prediction/FeatureImportance.jsx
   Horizontal bar chart of XGBoost feature importances:
   - Sorted descending by importance
   - Viridis color scale (most important = darkest)
   - Feature names on y-axis
   - Importance value labels on bars
   - Height: 280px
   - Recharts BarChart horizontal

5. frontend/src/hooks/usePrediction.js
   - Fetches GET /api/predict/{ticker}
   - Caches for 5 minutes (don't re-fetch on every render)
   - Returns: prediction, probability, confidence, features,
              probabilityHistory, modelMetrics, loading, error

6. Sharpe Ratio Comparison
   Two metric cards side by side:
   - "Strategy Sharpe: X.XX" vs "Buy & Hold Sharpe: X.XX"
   - Delta indicator showing which is better
   - Tooltip explaining Sharpe ratio

Embed the prediction section in MainFeed.jsx below the news feed.
Add a "📈 ML Prediction" collapsible section header.
Collapsed by default, expands on click.
Show model confidence badge in the collapsed header.
```

---

## PROMPT 7 — Portfolio & Watchlist
(Give Opus: working prediction panel from Prompt 6)

```
Build the Portfolio and Watchlist features for FinSight V2.
These live in the left sidebar and connect to the backend CRUD APIs.

Build these components:

1. frontend/src/components/watchlist/WatchlistPanel.jsx
   Sidebar section:
   - "Watchlist" header with + button to add stocks
   - Empty state: "This list is empty" (italic gray)
   - List of WatchlistRow components
   - Section is collapsible with chevron

2. frontend/src/components/watchlist/WatchlistRow.jsx
   Single watched stock row:
   - Ticker symbol (bold) + company name (small gray)
   - Current price
   - Change % colored green/red
   - 40px sparkline
   - Hover: remove button appears (trash icon)
   - Click: sets as active ticker in marketStore

3. frontend/src/components/watchlist/AddToWatchlist.jsx
   Add stock input:
   - Small text input with search icon
   - Calls GET /api/market/search for autocomplete
   - Dropdown shows matching stocks
   - Select → POST /api/watchlist
   - Close on escape or click outside

4. frontend/src/components/portfolio/PortfolioList.jsx
   Sidebar section:
   - "Portfolios" header with + button
   - "My Portfolio" sub-section
   - List of PortfolioRow components
   - Total P&L at top: "+$142.50 (+8.14%)" colored

5. frontend/src/components/portfolio/PortfolioRow.jsx
   Single holding:
   - Ticker + company name
   - Shares × current price = market value
   - P&L amount and percentage colored
   - Hover: remove button

6. frontend/src/components/portfolio/AddStockModal.jsx
   Modal to add a position:
   - Stock search input with autocomplete
   - Number of shares input
   - Buy price input (defaults to current price)
   - "Add to Portfolio" button
   - Cancel button

7. frontend/src/store/watchlistStore.js (Zustand)
   - watchlist: array of ticker data
   - addTicker(ticker): POST /api/watchlist
   - removeTicker(ticker): DELETE /api/watchlist/{ticker}
   - refresh(): GET /api/watchlist

8. frontend/src/store/portfolioStore.js (Zustand)
   - holdings: array with P&L computed
   - addHolding(ticker, shares, buyPrice)
   - removeHolding(ticker)
   - totalValue, totalPnL, totalPnLPct computed properties

Wire watchlist rows to update in real-time via WebSocket prices.
Clicking a watchlist stock should update the entire main feed
to show that stock's news, sentiment, and predictions.
```

---

## PROMPT 8 — Live Prices & Polish
(Give Opus: complete working app from Prompt 7)

```
Final polish pass for FinSight V2. Add live prices and visual polish.

1. WebSocket Integration
   Connect useWebSocket.js to live price updates:
   - Subscribe to all watchlist + portfolio tickers on connect
   - Update index card values in real-time (no page refresh)
   - Flash animation when price updates: green flash for up, red for down
   - Show "Live" badge with pulsing green dot in TopBar when connected
   - Reconnect automatically if connection drops

2. Search Bar (TopBar)
   - Pill-shaped search bar (like Google Finance)
   - Microphone icon on right
   - On focus: drops down autocomplete
   - Calls GET /api/market/search as user types (debounced 300ms)
   - Results show: symbol, company name, type (Stock/ETF/Index)
   - Click result: set as active ticker, update all panels
   - Keyboard navigation: arrow keys + enter

3. Price Flash Animation
   Add CSS animation to price values:
   ```css
   @keyframes flashGreen {
     0%   { background: #e6f4ea; }
     100% { background: transparent; }
   }
   @keyframes flashRed {
     0%   { background: #fce8e6; }
     100% { background: transparent; }
   }
   ```
   Trigger on WebSocket price update.

4. Mobile Responsive
   Below 768px:
   - Hide left sidebar (portfolio/watchlist)
   - Hide right research panel
   - Show bottom tab bar: Market | News | AI | Portfolio
   - Each tab shows the corresponding panel
   - Full-width layout

   Below 1200px:
   - Hide research panel
   - Show "Research" icon button in TopBar that slides panel in

5. Empty States
   Every section needs a proper empty state:
   - Watchlist empty: stock icon + "Add stocks to track"
   - Portfolio empty: chart icon + "Add your first position"
   - No news: newspaper icon + "No recent news for {ticker}"
   - Chat empty: sparkle icon + "Ask anything about {ticker}"

6. Error States
   Every API call needs error handling:
   - Network error: "Connection failed" with retry button
   - No data: appropriate empty state
   - API error: error message with support link

7. Performance
   - Memoize expensive components with React.memo
   - Debounce search input 300ms
   - Virtual scroll for long news feeds (>50 items)
   - Cache API responses in Zustand for 60 seconds

8. Final Visual Details
   - Add smooth page transitions between routes
   - Smooth expand/collapse for news cards (max-height CSS)
   - Skeleton loaders everywhere data can be loading
   - Consistent 8px grid spacing throughout
   - No layout shift when data loads (reserve space with skeletons)
```

---

## PROMPT 9 — Docker & Deployment
(Give Opus: complete working app from Prompt 8)

```
Set up Docker and deployment for FinSight V2.

Build these files:
1. docker-compose.yml        (redis + backend + frontend)
2. backend/Dockerfile
3. frontend/Dockerfile
4. .env.example              (all required variables)
5. README.md                 (setup in 5 commands)

Also set up for Vercel + Railway deployment:
6. vercel.json               (frontend config)
7. railway.json              (backend config)
8. frontend/.env.production  (VITE_API_URL=https://your-backend.railway.app)

The README must show:
- Local development (with and without Docker)
- Environment variables required
- How to run the pipeline first to generate data
- How to deploy to production

One command to run everything locally:
docker-compose up

One command to run in development:
./dev.sh  (script that starts backend + frontend in split terminal)
```

