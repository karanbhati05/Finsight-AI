# app/pages/chatbot.py
"""
RAG Chatbot Page — Page 2 of the FinSight AI Streamlit app.

Shows:
    - Multi-turn financial Q&A powered by FinBERT + ChromaDB + GPT-3.5
    - Source citations with expandable details
    - Suggested questions for quick demo
    - Session export option
"""

import streamlit as st
from pathlib import Path
from src.utils.constants import TICKER_COMPANY_MAP, PROCESSED_DATA_DIR


# ── Suggested questions ────────────────────────────────────────────────────────

SUGGESTED_QUESTIONS = {
    "AAPL": [
        "What risks did Apple mention in their latest filing?",
        "How has Apple's revenue trended recently?",
        "What did analysts say about Apple's iPhone sales?",
        "What is Apple's outlook for next quarter?",
    ],
    "MSFT": [
        "What is Microsoft's Azure cloud growth strategy?",
        "How is Microsoft performing in the AI space?",
        "What are Microsoft's main risk factors?",
        "What did Microsoft say about Copilot adoption?",
    ],
    "JPM": [
        "What did JPMorgan say about interest rate risks?",
        "How is JPMorgan's investment banking division performing?",
        "What are JPMorgan's credit loss provisions?",
        "What is JPMorgan's outlook on the economy?",
    ],
    "GS": [
        "What is Goldman Sachs' revenue from trading?",
        "How is Goldman Sachs managing market risk?",
        "What did Goldman say about deal activity?",
        "What are Goldman Sachs' main business segments?",
    ],
}

DEFAULT_QUESTIONS = [
    "Summarize recent news sentiment for this company.",
    "What are the main risk factors mentioned?",
    "What financial figures were highlighted recently?",
    "What is the overall analyst sentiment?",
]


def get_suggested_questions(ticker: str) -> list[str]:
    return SUGGESTED_QUESTIONS.get(ticker, DEFAULT_QUESTIONS)


# ── Session state helpers ──────────────────────────────────────────────────────

def init_session_state(ticker: str) -> None:
    """
    Initialize Streamlit session state for the chatbot.

    Streamlit re-runs the entire script on every interaction.
    Session state persists values across re-runs within one session.
    We use it to:
        - Store the chatbot instance (avoid reloading models each re-run)
        - Store message history (display previous Q&A pairs)
        - Track which ticker the chatbot was initialized for
          (reload if user switches ticker)
    """
    # Initialize message history if not exists
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Initialize or reload chatbot if ticker changed
    needs_init = (
        "chatbot"        not in st.session_state or
        "chatbot_ticker" not in st.session_state or
        st.session_state.chatbot_ticker != ticker
    )

    if needs_init:
        with st.spinner("Loading AI models... (first load takes ~30 seconds)"):
            try:
                from src.rag.chatbot import FinancialChatbot
                st.session_state.chatbot        = FinancialChatbot()
                st.session_state.chatbot_ticker = ticker
                st.session_state.messages       = []   # clear history on ticker switch

                # Check if data exists for this ticker
                data_path = Path(PROCESSED_DATA_DIR) / ticker / "news_enriched.csv"
                st.session_state.has_data = data_path.exists()

            except Exception as e:
                st.error(f"Failed to load chatbot: {e}")
                st.session_state.chatbot = None


def add_message(role: str, content: str, sources: list = None) -> None:
    """Add a message to session state history."""
    st.session_state.messages.append({
        "role":    role,
        "content": content,
        "sources": sources or [],
    })


# ── Message rendering ──────────────────────────────────────────────────────────

def render_message(message: dict) -> None:
    """
    Render a single chat message with optional source citations.

    Uses Streamlit's native st.chat_message() for the speech bubble UI.
    Sources are shown in an expandable section below the answer.
    """
    role    = message["role"]
    content = message["content"]
    sources = message.get("sources", [])

    with st.chat_message(role):
        st.markdown(content)

        # Show source citations for assistant messages
        if role == "assistant" and sources:
            with st.expander(f"📎 {len(sources)} source(s) used"):
                for i, source in enumerate(sources[:5], 1):
                    ticker_  = source.get("ticker",       "")
                    date_    = str(source.get("published_at",
                                  source.get("date", "")))[:10]
                    src_name = source.get("source",        "Unknown")
                    sent_    = source.get("sentiment_label","")
                    url_     = source.get("url",           "")
                    src_type = source.get("source_type",   "")

                    # Format source line
                    parts = [f"**{i}.** {src_name}"]
                    if ticker_:  parts.append(f"`{ticker_}`")
                    if date_:    parts.append(date_)
                    if src_type: parts.append(f"*{src_type}*")
                    if sent_:    parts.append(f"sentiment: {sent_}")

                    source_line = " · ".join(parts)

                    if url_:
                        st.markdown(f"{source_line} · [Read article]({url_})")
                    else:
                        st.markdown(source_line)


def render_chat_history() -> None:
    """Render all messages in session state."""
    for message in st.session_state.messages:
        render_message(message)


# ── Chat input handling ────────────────────────────────────────────────────────

def handle_question(question: str, ticker: str) -> None:
    """
    Process a user question through the RAG pipeline and display the answer.

    Args:
        question: user's natural language question
        ticker:   active ticker for document filtering
    """
    if not question or not question.strip():
        return

    # Add user message to history and display it
    add_message("user", question)

    with st.chat_message("user"):
        st.markdown(question)

    # Generate and display assistant response
    with st.chat_message("assistant"):
        with st.spinner("Searching documents and generating answer..."):
            try:
                chatbot = st.session_state.chatbot
                result  = chatbot.ask(
                    question = question,
                    ticker   = ticker,
                    top_k    = 5,
                )

                answer  = result["answer"]
                sources = result["sources"]
                n_chunks = result["retrieved_chunks"]

                # Display answer
                st.markdown(answer)

                # Display retrieval stats
                st.caption(
                    f"Retrieved {n_chunks} document chunks | "
                    f"Context: {len(result.get('context_used', ''))} chars"
                )

                # Display sources in expander
                if sources:
                    with st.expander(f"📎 {len(sources)} source(s) used"):
                        for i, source in enumerate(sources[:5], 1):
                            ticker_  = source.get("ticker", "")
                            date_    = str(source.get("published_at",
                                          source.get("date", "")))[:10]
                            src_name = source.get("source", "Unknown")
                            sent_    = source.get("sentiment_label", "")
                            url_     = source.get("url", "")

                            parts = [f"**{i}.** {src_name}"]
                            if ticker_:  parts.append(f"`{ticker_}`")
                            if date_:    parts.append(date_)
                            if sent_:    parts.append(f"sentiment: {sent_}")

                            if url_:
                                st.markdown(
                                    " · ".join(parts) +
                                    f" · [Read]({url_})"
                                )
                            else:
                                st.markdown(" · ".join(parts))

                # Save to session history
                add_message("assistant", answer, sources)

            except Exception as e:
                error_msg = (
                    f"Sorry, I encountered an error: {str(e)}\n\n"
                    f"Please check your OpenAI API key in the .env file."
                )
                st.error(error_msg)
                add_message("assistant", error_msg)


# ── Sidebar controls ───────────────────────────────────────────────────────────

def render_sidebar_controls(ticker: str) -> None:
    """Render chatbot controls in the sidebar."""
    st.sidebar.markdown("---")
    st.sidebar.subheader("Chatbot Controls")

    # Clear conversation button
    if st.sidebar.button("🗑️ Clear Conversation"):
        st.session_state.messages = []
        if "chatbot" in st.session_state and st.session_state.chatbot:
            st.session_state.chatbot.clear_history()
        st.rerun()

    # Vector store stats
    st.sidebar.markdown("---")
    st.sidebar.subheader("Knowledge Base")
    try:
        from src.rag.vector_store import FinancialVectorStore
        store = FinancialVectorStore()
        stats = store.get_stats()
        st.sidebar.metric("Total Chunks", stats["total_chunks"])
        st.sidebar.caption(f"Tickers: {', '.join(stats['tickers']) or 'None'}")
    except Exception:
        st.sidebar.caption("Vector store not initialized")


# ── Main render function ───────────────────────────────────────────────────────

def render(ticker: str) -> None:
    """
    Main entry point called by streamlit_app.py.
    Renders the full chatbot page for the selected ticker.
    """
    company = TICKER_COMPANY_MAP.get(ticker, ticker)

    st.title(f"🤖 FinSight AI Chatbot")
    st.caption(
        f"Ask questions about **{company} ({ticker})** — "
        f"grounded in SEC filings, earnings calls, and financial news."
    )

    # Initialize chatbot and session state
    init_session_state(ticker)

    # Sidebar controls
    render_sidebar_controls(ticker)

    # Data availability warning
    if not st.session_state.get("has_data", False):
        st.warning(
            f"⚠️ No processed data found for **{ticker}**. "
            f"The chatbot may have limited context.\n\n"
            f"Run the pipeline first:\n"
            f"```bash\npython scripts/run_pipeline.py --ticker {ticker}\n```"
        )

    if st.session_state.chatbot is None:
        st.error("Chatbot failed to initialize. Check your API keys.")
        return

    # ── Suggested questions ───────────────────────────────────────────────────
    if not st.session_state.messages:
        st.markdown("**Suggested questions to get started:**")
        questions = get_suggested_questions(ticker)

        cols = st.columns(2)
        for i, question in enumerate(questions):
            with cols[i % 2]:
                if st.button(question, key=f"suggested_{i}", use_container_width=True):
                    handle_question(question, ticker)
                    st.rerun()

        st.markdown("---")

    # ── Chat history ──────────────────────────────────────────────────────────
    render_chat_history()

    # ── Chat input ────────────────────────────────────────────────────────────
    # st.chat_input stays fixed at the bottom of the page
    if prompt := st.chat_input(
        f"Ask about {company}... e.g. 'What are the main risk factors?'"
    ):
        handle_question(prompt, ticker)
        st.rerun()