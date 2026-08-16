"""
backend/api/dependencies.py
Shared model instances — loaded ONCE at startup, reused across all requests.

Heavy models (FinBERT, XGBoost, ChromaDB) take 10-30 seconds to load.
Storing them here as module-level singletons avoids reloading on every API call.

Routers import getter functions (get_sentiment_model, get_chatbot, etc.)
and use FastAPI's Depends() to inject them into endpoint handlers.
"""

from src.nlp.sentiment    import FinBERTSentiment
from src.rag.chatbot      import FinancialChatbot
from src.rag.vector_store import FinancialVectorStore
from src.utils.logger     import get_logger

logger = get_logger(__name__)

# ── Global singleton instances ───────────────────────────────────────────────
_sentiment_model: FinBERTSentiment     = None
_chatbot:         FinancialChatbot     = None
_vector_store:    FinancialVectorStore = None


async def startup_models():
    """
    Load all AI models at application startup.

    Called from main.py lifespan context manager.
    Order matters: vector_store must be ready before chatbot
    because FinancialChatbot depends on it for RAG retrieval.
    """
    global _sentiment_model, _chatbot, _vector_store
    logger.info("Loading AI models at startup...")

    _vector_store    = FinancialVectorStore()
    _sentiment_model = FinBERTSentiment()
    _chatbot         = FinancialChatbot(vector_store=_vector_store)

    logger.info("All models loaded and ready")


async def shutdown_models():
    """Cleanup on application shutdown."""
    logger.info("Shutting down models...")


def get_sentiment_model() -> FinBERTSentiment:
    """Dependency injector for FinBERT sentiment model."""
    return _sentiment_model


def get_chatbot() -> FinancialChatbot:
    """Dependency injector for RAG chatbot."""
    return _chatbot


def get_vector_store() -> FinancialVectorStore:
    """Dependency injector for ChromaDB vector store."""
    return _vector_store
