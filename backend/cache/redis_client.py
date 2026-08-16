"""
backend/cache/redis_client.py
Redis cache wrapper — provides a simple get/set interface with TTL.

Falls back gracefully to no-caching if Redis is unavailable,
so the app works in development without a running Redis instance.
"""

import os
import json
from typing import Optional, Any
from src.utils.logger import get_logger

logger = get_logger(__name__)

# ── Attempt Redis import — optional dependency ───────────────────────────────
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("redis package not installed — caching disabled")


class CacheClient:
    """
    Simple Redis cache wrapper with JSON serialization.

    Usage:
        cache = CacheClient()
        cache.set("market:indices:india", data, ttl=300)  # 5 min
        cached = cache.get("market:indices:india")
    """

    def __init__(self):
        self._client = None

        if not REDIS_AVAILABLE:
            logger.info("Cache disabled — redis not installed")
            return

        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        try:
            self._client = redis.from_url(redis_url, decode_responses=True)
            self._client.ping()
            logger.info(f"Redis connected: {redis_url}")
        except Exception as e:
            logger.warning(f"Redis unavailable ({e}) — caching disabled")
            self._client = None

    @property
    def is_connected(self) -> bool:
        return self._client is not None

    def get(self, key: str) -> Optional[Any]:
        """Get a cached value by key. Returns None if miss or Redis down."""
        if not self._client:
            return None
        try:
            data = self._client.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            logger.warning(f"Cache get failed for '{key}': {e}")
        return None

    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """
        Cache a value with TTL (default 5 minutes).

        Args:
            key:   cache key string
            value: any JSON-serializable Python object
            ttl:   time-to-live in seconds
        """
        if not self._client:
            return False
        try:
            self._client.setex(key, ttl, json.dumps(value, default=str))
            return True
        except Exception as e:
            logger.warning(f"Cache set failed for '{key}': {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete a cached key."""
        if not self._client:
            return False
        try:
            self._client.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Cache delete failed for '{key}': {e}")
            return False

    def flush_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching a pattern (e.g. 'market:*').
        Useful for invalidating all market data cache at once.
        """
        if not self._client:
            return 0
        try:
            keys = self._client.keys(pattern)
            if keys:
                return self._client.delete(*keys)
        except Exception as e:
            logger.warning(f"Cache flush failed for '{pattern}': {e}")
        return 0


# ── Module-level singleton ───────────────────────────────────────────────────
cache = CacheClient()
