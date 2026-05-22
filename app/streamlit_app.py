# app/streamlit_app.py

import sys
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

# Add project root to Python path — must be before any src/ or pages/ imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st

st.set_page_config(
    page_title = "FinSight AI",
    page_icon  = "📈",
    layout     = "wide",
    initial_sidebar_state = "expanded",
)

# ── Sidebar ───────────────────────────────────────────────────────────────────

st.sidebar.markdown(
    """
    <div style="text-align:center;padding:10px 0;">
        <div style="font-size:40px;">📈</div>
        <div style="font-size:20px;font-weight:600;">FinSight AI</div>
        <div style="font-size:12px;color:#64748b;">
            Intelligent Financial Research Assistant
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.divider()

# ── Ticker selector ───────────────────────────────────────────────────────────

ticker = st.sidebar.selectbox(
    "Select Ticker",
    ["AAPL", "MSFT", "GOOGL", "JPM", "GS", "TSLA", "AMZN", "BAC", "MS", "WFC"],
    index = 0,
    help  = "Choose a stock to analyze",
)

st.sidebar.divider()

# ── Page navigation ───────────────────────────────────────────────────────────

page = st.sidebar.radio(
    "Navigate",
    ["📊 Dashboard", "🤖 AI Chatbot", "📈 ML Predictions"],
    index = 0,
)

st.sidebar.divider()

# ── Pipeline status ───────────────────────────────────────────────────────────

st.sidebar.subheader("Pipeline Status")

from src.utils.constants import PROCESSED_DATA_DIR, RAW_DATA_DIR, MODELS_DIR

data_exists  = (Path(PROCESSED_DATA_DIR) / ticker / "news_enriched.csv").exists()
model_exists = (Path(MODELS_DIR) / f"{ticker}_xgb_model.pkl").exists()
price_exists = (Path(RAW_DATA_DIR) / ticker / "price_data.csv").exists()

st.sidebar.markdown(
    f"{'✅' if price_exists  else '❌'} Price data\n\n"
    f"{'✅' if data_exists   else '❌'} NLP pipeline\n\n"
    f"{'✅' if model_exists  else '❌'} ML model\n\n"
)

if not data_exists:
    st.sidebar.code(
        f"python scripts/run_pipeline.py\n--ticker {ticker} --skip-edgar\n--no-summarize",
        language="bash",
    )

st.sidebar.divider()

# ── Tech stack info ───────────────────────────────────────────────────────────

st.sidebar.caption(
    "Built with:\n"
    "FinBERT · spaCy · BART\n"
    "XGBoost · LangChain\n"
    "ChromaDB · Gemini · Streamlit"
)

# ── Route to pages ────────────────────────────────────────────────────────────

if page == "📊 Dashboard":
    from pages.dashboard import render
    render(ticker)

elif page == "🤖 AI Chatbot":
    from pages.chatbot import render
    render(ticker)

elif page == "📈 ML Predictions":
    from pages.ml_predictions import render
    render(ticker)