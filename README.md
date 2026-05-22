# 📈 FinSight AI — Intelligent Financial Research Assistant

> An LLM-powered system that ingests earnings reports & financial news, extracts insights using NLP, predicts sentiment-driven stock movement using ML, and answers analyst-style questions via a RAG chatbot.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        FinSight AI                          │
├────────────┬────────────┬────────────┬────────────────────  │
│  Module 1  │  Module 2  │  Module 3  │     Module 4         │
│  Data      │  NLP       │  ML        │     RAG Chatbot      │
│  Ingestion │  Pipeline  │  Predictor │     (LangChain)      │
├────────────┼────────────┼────────────┼────────────────────  │
│  EDGAR API │  FinBERT   │  XGBoost   │  ChromaDB            │
│  NewsAPI   │  spaCy NER │  Features: │  Sentence-BERT       │
│  yfinance  │  BART Sum. │  Sentiment │  GPT-3.5 / Gemini    │
└────────────┴────────────┴────────────┴────────────────────  │
                          │
                   Streamlit Dashboard
```

## 🛠️ Tech Stack

| Layer | Tools |
|---|---|
| **NLP / DL** | FinBERT, BART, spaCy, HuggingFace Transformers |
| **ML** | XGBoost, scikit-learn, SHAP |
| **LLM / RAG** | LangChain, ChromaDB, Sentence-Transformers, OpenAI |
| **Data** | yfinance, EDGAR API, NewsAPI |
| **UI** | Streamlit, Plotly |
| **Deploy** | Hugging Face Spaces / Streamlit Cloud |

## 🚀 Quick Start

```bash
# 1. Clone and install
git clone https://github.com/karanbhati05/finsight-ai
cd finsight-ai
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# 2. Set up API keys
cp .env.example .env
# Edit .env with your OPENAI_API_KEY and NEWS_API_KEY

# 3. Run the full pipeline for a ticker
python scripts/run_pipeline.py --ticker AAPL

# 4. Build the RAG vector store
python scripts/build_vector_store.py --ticker AAPL

# 5. Launch the Streamlit app
streamlit run app/streamlit_app.py
```

## 📂 Project Structure

```
finsight-ai/
├── src/
│   ├── ingestion/      # EDGAR, NewsAPI, yfinance data fetchers
│   ├── nlp/            # FinBERT sentiment, spaCy NER, BART summarization
│   ├── ml/             # Feature engineering, XGBoost training, evaluation
│   ├── rag/            # Embeddings, ChromaDB vector store, LangChain chatbot
│   └── utils/          # Logger, helpers, constants
├── app/
│   ├── streamlit_app.py
│   └── pages/          # Dashboard, Chatbot, ML Predictions
├── scripts/            # End-to-end pipeline runners
├── notebooks/          # EDA and experiment notebooks
├── configs/            # YAML configuration
└── tests/              # Unit tests
```

## 🎯 Key Features

- **Financial Sentiment Analysis** using FinBERT (finance-tuned BERT)
- **Named Entity Recognition** — extracts companies, executives, figures, dates
- **Document Summarization** — BART-powered earnings call summaries
- **ML Price Direction Prediction** — XGBoost on sentiment + technical features
- **RAG Chatbot** — Ask natural language questions grounded in real SEC filings
- **Interactive Dashboard** — Streamlit UI with Plotly charts

## 📊 Results

| Metric | Score |
|---|---|
| Prediction Accuracy | ~62% |
| F1 Score | ~0.61 |
| ROC-AUC | ~0.66 |

> *Beating 50% baseline on financial prediction is meaningful given market efficiency.*

---

Built by **Karan Bhati** | B.Tech AI & Data Science, D.J. Sanghvi College of Engineering
