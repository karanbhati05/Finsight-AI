"""
backend/api/dependencies.py
Shared model instances — safely loaded at startup, reused across all requests.

Heavy models (FinBERT, ChromaDB, Gemini Chatbot) are stored as module-level
singletons to avoid reloading on every API call, with graceful fallbacks
so the server never crashes on startup if network or weights are unavailable.
"""

import os
from src.utils.logger import get_logger

logger = get_logger(__name__)

# ── Fallback Lightweight Sentiment Analyzer ──────────────────────────────────
class FallbackSentiment:
    """Fast rule-based sentiment fallback when PyTorch/FinBERT is offline."""
    def predict(self, text: str) -> dict:
        t = (text or "").lower()
        pos_words = ["gain", "surge", "beat", "profit", "up", "bull", "growth", "high", "positive", "record", "jump", "rally"]
        neg_words = ["fall", "drop", "miss", "loss", "down", "bear", "decline", "low", "negative", "warn", "crash", "slump"]
        pos_count = sum(1 for w in pos_words if w in t)
        neg_count = sum(1 for w in neg_words if w in t)

        if pos_count > neg_count:
            score = min(0.9, 0.4 + pos_count * 0.15)
            label = "positive"
        elif neg_count > pos_count:
            score = max(-0.9, -0.4 - neg_count * 0.15)
            label = "negative"
        else:
            score = 0.0
            label = "neutral"

        return {
            "label":         label,
            "score":         round(score, 4),
            "confidence":    round(abs(score) if score != 0 else 0.5, 4),
            "prob_positive": round(max(0.0, score), 4),
            "prob_negative": round(max(0.0, -score), 4),
            "prob_neutral":  round(1.0 - abs(score), 4),
        }

    def predict_batch(self, texts: list[str]) -> list[dict]:
        return [self.predict(t) for t in texts]


# ── Global singleton instances ───────────────────────────────────────────────
_sentiment_model = None
_chatbot         = None
_vector_store    = None


async def startup_models():
    """
    Safely load AI models at application startup.
    Catches network/file errors gracefully so the backend boots in <1 second.
    """
    global _sentiment_model, _chatbot, _vector_store
    logger.info("Initializing FinSight AI model layer...")

    # 1. Vector Store
    try:
        from src.rag.vector_store import FinancialVectorStore
        _vector_store = FinancialVectorStore()
        logger.info("FinancialVectorStore ready")
    except Exception as e:
        logger.warning(f"Vector store deferred/fallback: {e}")

    # 2. FinBERT Sentiment
    try:
        from src.nlp.sentiment import FinBERTSentiment
        _sentiment_model = FinBERTSentiment()
        logger.info("FinBERT sentiment model ready")
    except Exception as e:
        logger.warning(f"FinBERT offline/loading error: {e}. Activating FallbackSentiment.")
        _sentiment_model = FallbackSentiment()

    # 3. Gemini / RAG Chatbot
    try:
        from src.rag.chatbot import FinancialChatbot
        _chatbot = FinancialChatbot(vector_store=_vector_store)
        logger.info("FinancialChatbot ready")
    except Exception as e:
        logger.warning(f"FinancialChatbot error: {e}")

    logger.info("AI Model layer initialization complete")


async def shutdown_models():
    """Cleanup on application shutdown."""
    logger.info("Shutting down model singletons...")


def get_sentiment_model():
    """Dependency injector for FinBERT sentiment model."""
    global _sentiment_model
    if _sentiment_model is None:
        _sentiment_model = FallbackSentiment()
    return _sentiment_model


def get_chatbot():
    """Dependency injector for RAG chatbot."""
    return _chatbot


def get_vector_store():
    """Dependency injector for ChromaDB vector store."""
    return _vector_store
