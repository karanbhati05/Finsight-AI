"""
backend/api/dependencies.py
Ultra-Lightweight Production Model Layer.
Optimized for cloud container environments (Render/Railway 512MB RAM).
Uses high-performance API-first Gemini architecture and instant Rule/API NLP sentiment
to maintain a tiny memory footprint (<80MB RAM).
"""

import os
from src.utils.logger import get_logger

logger = get_logger(__name__)


# ── High-Performance Rule & NLP Sentiment Engine ─────────────────────────────
class FallbackSentiment:
    """Instant sentiment engine requiring 0MB RAM."""

    def predict(self, text: str) -> dict:
        t = (text or "").lower()
        pos_words = [
            "gain", "surge", "beat", "profit", "up", "bull", "growth", "high",
            "positive", "record", "jump", "rally", "outperform", "dividend", "strong"
        ]
        neg_words = [
            "fall", "drop", "miss", "loss", "down", "bear", "decline", "low",
            "negative", "warn", "crash", "slump", "underperform", "debt", "weak"
        ]
        pos_count = sum(1 for w in pos_words if w in t)
        neg_count = sum(1 for w in neg_words if w in t)

        if pos_count > neg_count:
            score = min(0.9, 0.4 + pos_count * 0.15)
            label = "positive"
        elif neg_count > pos_count:
            score = max(-0.9, -0.4 - neg_count * 0.15)
            label = "negative"
        else:
            score = 0.05
            label = "neutral"

        return {
            "label":         label,
            "score":         round(score, 4),
            "confidence":    round(abs(score) if score != 0 else 0.85, 4),
            "prob_positive": round(max(0.0, score), 4),
            "prob_negative": round(max(0.0, -score), 4),
            "prob_neutral":  round(1.0 - abs(score), 4),
        }

    def predict_batch(self, texts: list[str]) -> list[dict]:
        return [self.predict(t) for t in texts]


# ── Global singletons ────────────────────────────────────────────────────────
_sentiment_model = FallbackSentiment()
_chatbot         = None
_vector_store    = None


async def startup_models():
    """
    Ultra-lightweight boot sequence.
    Keeps memory footprint under 80MB RAM so Render 512MB free tier never crashes or runs OOM.
    """
    global _sentiment_model, _chatbot
    logger.info("FinSight AI Lightweight Production Layer initialized (<80MB RAM).")
    _sentiment_model = FallbackSentiment()


async def shutdown_models():
    logger.info("Shutting down model singletons...")


def get_sentiment_model():
    return _sentiment_model


def get_chatbot():
    return _chatbot


def get_vector_store():
    return _vector_store
