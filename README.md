# FinSight AI — Intelligent Financial Research Terminal

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/Frontend-React_19-61DAFB.svg?style=flat&logo=react)](https://react.dev)
[![TailwindCSS](https://img.shields.io/badge/Styles-Tailwind_CSS-38B2AC.svg?style=flat&logo=tailwind-css)](https://tailwindcss.com)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB.svg?style=flat&logo=python)](https://python.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg?style=flat&logo=docker)](https://docker.com)

**FinSight AI** is a financial intelligence platform that combines **NLP sentiment analysis (FinBERT)**, **Machine Learning stock directional forecasting (XGBoost)**, and a **RAG Conversational Research Assistant (Gemini 2.5 + SEC EDGAR Filings)** into an interface inspired by Google Finance.

---

## ⚡ Quick Start (Setup in 5 Commands)

```bash
# 1. Clone repository
git clone https://github.com/your-username/finsight-ai.git
cd finsight-ai

# 2. Configure Environment Keys
cp .env.example .env

# 3. Start full stack with Docker Compose
docker-compose up --build
```
> App runs at **`http://localhost:5173`** (Frontend) and **`http://localhost:8000/docs`** (Interactive API Docs).

---

## 🛠️ Architecture Overview

```
                 ┌───────────────────────────────┐
                 │       FinSight AI React       │
                 │      Frontend (Port 5173)     │
                 └──────────────┬────────────────┘
                                │ HTTP / WebSocket
                                ▼
                 ┌───────────────────────────────┐
                 │        FastAPI Backend        │
                 │          (Port 8000)          │
                 └──┬───────────┬─────────────┬──┘
                    │           │             │
        ┌───────────▼┐   ┌──────▼──────┐  ┌───▼───────────┐
        │ Redis Cache│   │ ChromaDB /  │  │ XGBoost &     │
        │(Port 6379) │   │ Gemini RAG  │  │ FinBERT NLP   │
        └────────────┘   └─────────────┘  └───────────────┘
```

---

## 💻 Local Development (Without Docker)

### Prerequisites
- **Python 3.11+**
- **Node.js 20+**
- **Redis** (optional, fallback in-memory caching is enabled if unavailable)

### 1. Backend Setup
```bash
# Create and activate virtual environment
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
pip install -r backend/requirements_backend.txt
python -m spacy download en_core_web_sm

# Start FastAPI server
uvicorn backend.api.main:app --reload --port 8000
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

---

## 🧪 Running the AI Pipeline

To train the machine learning models and populate vector embeddings locally:

```bash
# 1. Fetch historical stock & news dataset
python scripts/run_pipeline.py --ticker AAPL --days 90

# 2. Extract FinBERT sentiment and train XGBoost
python -m src.models.trainer --ticker AAPL

# 3. Ingest SEC 10-K filings into ChromaDB vector store
python -m src.rag.ingest --ticker AAPL
```

---

## 🌐 Deploy to Production

### 1. Deploy Frontend to Vercel
1. Import the repository in [Vercel](https://vercel.com).
2. Set root directory to `.` (the root [`vercel.json`](./vercel.json) handles building the frontend).
3. Set environment variable `VITE_API_URL` to your production backend URL.

### 2. Deploy Backend to Railway
1. Create a new project in [Railway](https://railway.app).
2. Select **Deploy from GitHub repo**.
3. Add a **Redis** service from the Railway dashboard.
4. Set environment variables in Railway:
   - `GOOGLE_API_KEY`
   - `NEWS_API_KEY`
   - `FINNHUB_API_KEY`
   - `REDIS_URL` (use `${{Redis.REDIS_URL}}`)
5. Railway uses [`railway.json`](./railway.json) to deploy the backend automatically.

---

## 🔒 Environment Variables

| Variable | Description | Required |
|---|---|:---:|
| `GOOGLE_API_KEY` | Google Gemini API key for RAG chatbot | Yes |
| `NEWS_API_KEY` | NewsAPI.org key for global financial news | Yes |
| `FINNHUB_API_KEY` | Finnhub.io key for market feeds | Yes |
| `REDIS_URL` | Redis connection URL | Optional |
| `DATABASE_URL` | SQLite / PostgreSQL database URL | Optional |

---

## 📄 License
MIT License. Created with ❤️ for advanced financial engineering & research.
