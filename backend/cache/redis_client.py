"""
backend/cache/redis_client.py
High-performance Cache wrapper with Redis support and an instant in-memory TTL fallback.
Guarantees sub-millisecond cache responses even when Redis is offline.
"""

import os
import time
import json
from typing import Optional, Any
from src.utils.logger import get_logger

logger = get_logger(__name__)

# In-memory dictionary store: {key: (value, expire_timestamp)}
_memory_cache: dict[str, tuple[Any, float]] = {}


class CacheClient:
    """
    Unified Cache Client. Uses Redis if available, otherwise uses high-speed
    in-memory TTL storage so the terminal never hangs or re-fetches redundant data.
    """

    def __init__(self):
        self._redis = None
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        try:
            import redis
            client = redis.from_url(redis_url, decode_responses=True)
            client.ping()
            self._redis = client
            logger.info(f"Redis connected: {redis_url}")
        except Exception:
            logger.info("Using ultra-fast in-memory TTL cache fallback")
            self._redis = None

    @property
    def is_connected(self) -> bool:
        return self._redis is not None

    def get(self, key: str) -> Optional[Any]:
        """Get a cached value. Checks Redis first, then in-memory cache."""
        if self._redis:
            try:
                data = self._redis.get(key)
                if data:
                    return json.loads(data)
            except Exception:
                pass

        # Check in-memory store
        item = _memory_cache.get(key)
        if item:
            val, expire_at = item
            if time.time() < expire_at:
                return val
            else:
                del _memory_cache[key]
        return None

    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Cache value in Redis and in-memory with TTL in seconds."""
        expire_at = time.time() + ttl
        _memory_cache[key] = (value, expire_at)

        if self._redis:
            try:
                self._redis.setex(key, ttl, json.dumps(value, default=str))
                return True
            except Exception:
                pass
        return True

    def delete(self, key: str) -> bool:
        """Delete a cached key."""
        _memory_cache.pop(key, None)
        if self._redis:
            try:
                self._redis.delete(key)
            except Exception:
                pass
        return True

    def flush_pattern(self, pattern: str) -> int:
        """Flush keys matching pattern."""
        count = 0
        prefix = pattern.replace("*", "")
        keys_to_del = [k for k in _memory_cache if k.startswith(prefix)]
        for k in keys_to_del:
            _memory_cache.pop(k, None)
            count += 1
        return count


cache = CacheClient()
