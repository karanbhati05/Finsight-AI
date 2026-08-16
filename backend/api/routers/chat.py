"""
backend/api/routers/chat.py
RAG Chat endpoint — accepts questions, retrieves relevant financial
documents from ChromaDB, and generates grounded answers via Gemini.

Maintains per-session chatbot instances for multi-turn conversation history.
"""

from fastapi import APIRouter, Depends, HTTPException
from backend.api.dependencies import get_chatbot
from backend.models.schemas import ChatRequest, ChatResponse
from src.rag.chatbot import FinancialChatbot
from src.utils.logger import get_logger
import uuid

logger = get_logger(__name__)
router = APIRouter()

# ── Per-session chatbot instances ────────────────────────────────────────────
# Each session_id gets its own FinancialChatbot so conversation history
# is isolated between users/tabs. In production, use Redis-backed sessions.
_sessions: dict = {}

# ── Suggested questions per ticker ───────────────────────────────────────────
SUGGESTED_QUESTIONS = {
    "AAPL": [
        "What are the main risk factors Apple mentioned in their 10-K?",
        "How has Apple's revenue trended recently?",
        "What did analysts say about iPhone sales?",
        "What is Apple's outlook for next quarter?",
    ],
    "MSFT": [
        "What is Microsoft's Azure cloud growth strategy?",
        "How is Microsoft performing in the AI space?",
        "What are Microsoft's main risk factors?",
        "What did Microsoft say about Copilot adoption?",
    ],
    "GOOGL": [
        "How is Google's advertising revenue performing?",
        "What are Alphabet's main AI investments?",
        "What regulatory risks does Google face?",
        "How is Google Cloud competing with AWS and Azure?",
    ],
    "TSLA": [
        "What are Tesla's production and delivery numbers?",
        "How is Tesla's energy storage business growing?",
        "What are the main risks Tesla faces?",
        "What is Tesla's outlook for autonomous driving?",
    ],
    "DEFAULT": [
        "Summarize recent news sentiment for this company.",
        "What are the main risk factors mentioned?",
        "What financial figures were highlighted recently?",
        "What is the overall analyst sentiment?",
    ]
}


@router.post("", response_model=ChatResponse)
async def chat(
    request:    ChatRequest,
    chatbot_:   FinancialChatbot = Depends(get_chatbot),
):
    """
    Send a question to the RAG chatbot and get a grounded answer.

    The chatbot retrieves relevant document chunks from ChromaDB,
    builds a context window, and generates an answer via Gemini LLM.

    Session-based: each session_id maintains its own conversation
    history for multi-turn dialogue.
    """
    session_id = request.session_id or str(uuid.uuid4())

    # Get or create a session-specific chatbot instance
    if session_id not in _sessions:
        _sessions[session_id] = FinancialChatbot()

    session_bot = _sessions[session_id]

    try:
        result = session_bot.ask(
            question = request.question,
            ticker   = request.ticker,
            top_k    = request.top_k,
        )
        return ChatResponse(
            answer           = result["answer"],
            sources          = result["sources"],
            retrieved_chunks = result["retrieved_chunks"],
            session_id       = session_id,
        )
    except Exception as e:
        logger.error(f"Chat failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{session_id}")
async def clear_session(session_id: str):
    """Clear a chat session's conversation history."""
    if session_id in _sessions:
        _sessions[session_id].clear_history()
        del _sessions[session_id]
    return {"cleared": True}


@router.get("/suggestions/{ticker}")
async def get_suggestions(ticker: str):
    """
    Get suggested questions for a ticker.
    Returns ticker-specific questions if available, else defaults.
    """
    questions = SUGGESTED_QUESTIONS.get(
        ticker.upper(),
        SUGGESTED_QUESTIONS["DEFAULT"]
    )
    return {"ticker": ticker, "suggestions": questions}
