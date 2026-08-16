# FinSight V2 — Master Build Prompt for Opus 4.6

## Your Mission
Build FinSight V2 — a Google Finance-level financial intelligence dashboard.
You are upgrading an existing working AI system (FinSight V1) with a 
professional React frontend and FastAPI backend.

## What Already Exists (DO NOT REBUILD)
The following Python modules are complete and working. You only wrap them in APIs:
- src/nlp/sentiment.py      → FinBERT sentiment analysis
- src/nlp/ner.py            → spaCy named entity recognition  
- src/ml/predict.py         → XGBoost price direction prediction
- src/rag/chatbot.py        → LangChain + Gemini RAG chatbot
- src/rag/vector_store.py   → ChromaDB vector database
- src/ingestion/            → All data fetchers (yfinance, Finnhub, EDGAR)

## What You Are Building
1. FastAPI backend — REST API + WebSockets wrapping existing AI modules
2. React frontend — Google Finance UI with three-column layout
3. Redis caching — fast responses without hitting AI models every request
4. Docker Compose — one command to run everything

## Visual Reference
Match this layout EXACTLY (Google Finance style):
- Left sidebar: Portfolios, Watchlist, Equity Sectors with sparklines
- Center: Search bar, Market tabs, Index cards, News feed with AI buttons
- Right panel: Research AI chat, Suggested questions, Quick actions

## Non-Negotiable Rules
1. NO UI component libraries except Tailwind CSS and Recharts
2. Build ALL components from scratch — no shadcn, no MUI, no Chakra
3. Use these exact colors:
   - Gains:      #0f9d58 (green)
   - Losses:     #d93025 (red)
   - Background: #ffffff
   - Surface:    #f8f9fa
   - Border:     #e8eaed
   - Primary:    #1a73e8 (Google blue)
   - Text:       #202124
   - Subtext:    #5f6368
4. Font: Inter (import from Google Fonts)
5. Every component must have loading skeleton state
6. Mobile responsive — single column below 768px

## Build Order
Follow this EXACT sequence. Do not skip steps.
Step 1 → FastAPI backend (backend/api/)
Step 2 → React layout shell (three columns, no data)
Step 3 → Market data components (index cards, sparklines, sectors)
Step 4 → News feed with sentiment badges
Step 5 → Research panel (RAG chatbot)
Step 6 → ML Predictions panel
Step 7 → Portfolio and Watchlist
Step 8 → WebSocket live prices
Step 9 → Polish, animations, mobile
Step 10 → Docker Compose

## File Structure to Create
See 01_FILE_STRUCTURE.md for complete tree.

## Data Contracts
See 02_API_CONTRACTS.md for all request/response shapes.

## Existing Code Reference
See 03_EXISTING_CODE.md for V1 modules you must integrate with.
