# 🚀 FinSight AI — Institutional Financial Research & Intelligence Terminal

<div align="center">

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/Frontend-React_19-61DAFB.svg?style=for-the-badge&logo=react)](https://react.dev)
[![Gemini](https://img.shields.io/badge/AI_Engine-Google_Gemini_2.5_Flash-4285F4.svg?style=for-the-badge&logo=google)](https://aistudio.google.com)
[![TailwindCSS](https://img.shields.io/badge/Styles-Tailwind_CSS-38B2AC.svg?style=for-the-badge&logo=tailwind-css)](https://tailwindcss.com)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg?style=for-the-badge&logo=docker)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](LICENSE)

**FinSight AI** is a next-generation institutional financial research terminal that merges **real-time market data**, **multi-source macroeconomic indicators**, **XGBoost ML directional forecasting**, and **multimodal Google Gemini 2.5 Flash AI** into a Google Finance inspired interface.

[Live Demo](https://finsight-ai.vercel.app) • [API Documentation](https://finsight-backend-bf13.onrender.com/docs) • [Deployment Guide](DEPLOYMENT_GUIDE.md)

</div>

---

## 🌟 Key Highlights & Capabilities

### 1. 🤖 Conversational Research AI & Multimodal Intelligence
- **Google Gemini 2.5 Flash / 2.0 Engine**: Deep financial Q&A grounded in live SEC 10-K/10-Q filings, valuation metrics, and market conditions.
- **🎙️ Live Voice Speech-to-Text**: Dictate complex financial questions using built-in browser speech recognition.
- **📎 Multimodal Document & Chart Upload**: Ingest **PDF annual reports**, Word documents, CSV spreadsheets, and **chart screenshots / earnings slides** for instant AI breakdown.
- **Structured Intelligence Cards**: Synthesizes complex answers into categorized insight blocks with highlighted financial figures and source citations.
- **🔊 Text-to-Speech (TTS)**: One-click audio briefing reads analyst reports aloud.

### 2. 🏛️ Federal Reserve (FRED) Macroeconomic Radar
- **10Y / 2Y Yield Curve Inversion Alert**: Real-time spread calculation tracking economic recession signals.
- **Key Indicators**: 10-Year Treasury Yield, Fed Funds Effective Rate, CPI Inflation, US Unemployment Rate, and M2 Money Supply.

### 3. 🪙 CoinGecko Cryptocurrency & Forex Hub
- **Top 20 Crypto Assets**: Live prices, 24h changes, market caps, 24h trading volume, and 7-day sparkline waves.
- **World Forex Matrix**: Global currency exchange pairs against USD with real-time rate conversion.

### 4. 📈 Precision Stock Charts & Financial Statements
- **High-Resolution Area Charts**: Interactive price action with a **dotted horizontal previous close baseline** and timeframe selectors (`1D`, `5D`, `1M`, `6M`, `YTD`, `1Y`, `5Y`, `MAX`).
- **5-Year Financial Statements (FMP)**: Income statements, revenue growth, net profit margins, and balance sheet capitalization.
- **Alpha Vantage Technical Oscillators**: 14-Day RSI, MACD trend momentum, and 50-day EMA support levels.

### 5. 🔮 XGBoost ML Directional Price Forecasting
- **Next-Day Price Predictions**: Multi-feature directional probability forecasting combining technical indicators and NLP news sentiment.
- **Confidence Gauge & Feature Importance**: Visualizes SHAP/feature weights for each prediction.

### 6. 💼 Portfolio & Automated Task Management
- **Live Portfolio Tracking**: Add positions with buy prices and share quantities; calculates real-time Market Value and Profit & Loss (P&L).
- **Automated Monitoring Tasks**: Set custom price alerts and schedule automated morning AI briefings.

---

## 🏗️ Architecture Overview

```
                 ┌─────────────────────────────────────────┐
                 │       FinSight AI React Frontend        │
                 │   (Vite + TailwindCSS + Recharts + WS)  │
                 └────────────────────┬────────────────────┘
                                      │ HTTP / WebSocket
                                      ▼
                 ┌─────────────────────────────────────────┐
                 │        FastAPI Unified Backend          │
                 │   (Parallel ThreadPool Async Routers)   │
                 └──┬─────────────┬─────────────┬────────┬─┘
                    │             │             │        │
      ┌─────────────▼─┐     ┌─────▼─────┐ ┌─────▼────┐ ┌─▼──────────────┐
      │ Google Gemini │     │    FRED   │ │CoinGecko │ │ FMP & Alpha    │
      │ 2.5 Flash RAG │     │Macro Radar│ │Crypto Hub│ │ Vantage Data   │
      └───────────────┘     └───────────┘ └──────────┘ └────────────────┘
```

---

## ⚡ Quick Start (Local Setup)

### 1. Clone & Configure Environment
```bash
git clone https://github.com/karanbhati05/Finsight-AI.git
cd Finsight-AI

# Create .env from template
cp .env.example .env
```

Add your API keys to `.env`:
```env
GOOGLE_API_KEY=your_gemini_api_key
FRED_API_KEY=your_fred_api_key
ALPHAVANTAGE_API_KEY=your_alphavantage_key
FMP_API_KEY=your_fmp_key
FINNHUB_API_KEY=your_finnhub_key
COINGECKO_API_KEY=your_coingecko_key
NEWS_API_KEY=your_news_key
```

---

### 2. Option A: Run with Docker Compose (Recommended)
```bash
docker compose up --build -d
```
- **Frontend UI**: `http://localhost:5173`
- **FastAPI Interactive Docs**: `http://localhost:8000/docs`

---

### 3. Option B: Run Locally Without Docker

#### Backend:
```bash
# Create and activate virtual environment
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start backend server
uvicorn backend.api.main:app --reload --port 8000
```

#### Frontend:
```bash
cd frontend
npm install
npm run dev
```

---

## ☁️ 1-Click Production Cloud Deployment

### 1. Backend on [Render](https://render.com) (Free Tier)
1. Create a **New Web Service** pointing to your GitHub repository.
2. Set Environment to **Python** (or **Docker**).
3. Add your environment keys under **Environment Variables**.
4. Set Build Command to `pip install -r requirements.txt` and Start Command to `uvicorn backend.api.main:app --host 0.0.0.0 --port $PORT`.

### 2. Frontend on [Vercel](https://vercel.com) (Free Tier)
1. Import your GitHub repository into Vercel.
2. Set **Root Directory** to `frontend` and Framework Preset to **Vite**.
3. Add the environment variable:
   ```env
   VITE_API_URL=https://<your-render-backend>.onrender.com/api
   ```
4. Click **Deploy**!

*(For full step-by-step details, see [`DEPLOYMENT_GUIDE.md`](DEPLOYMENT_GUIDE.md)).*

---

## 📚 API Endpoints Reference

| Route | Method | Description |
|---|---|---|
| `/api/chat` | `POST` | Google Gemini 2.5 Flash financial research assistant |
| `/api/chat/upload` | `POST` | Upload PDF/Doc/Image for multimodal analysis |
| `/api/market/indices` | `GET` | Real-time global market indices with sparklines |
| `/api/market/sectors` | `GET` | Equity sector performance and daily trends |
| `/api/analyst/report/{ticker}` | `GET/POST` | Dynamic AI valuation summary & price targets |
| `/api/macro/dashboard` | `GET` | FRED 10Y/2Y Treasury spread, CPI & Fed funds rate |
| `/api/crypto/top` | `GET` | Top 20 cryptocurrencies from CoinGecko |
| `/api/crypto/forex` | `GET` | Global currency exchange rate matrix |
| `/api/predict/{ticker}` | `GET` | XGBoost directional price prediction & confidence |
| `/api/portfolio` | `GET/POST/DELETE` | Institutional portfolio holdings & P&L calculation |
| `/ws/prices` | `WebSocket` | Real-time live streaming price feed |

---

## 📄 License
Distributed under the MIT License. See `LICENSE` for more information.

---

<div align="center">
  <sub>Built with ❤️ for institutional analysts, quantitative researchers, and individual investors.</sub>
</div>
