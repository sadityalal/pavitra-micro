# backend/shared/redis_client.py

import redis
import logging
import json
from typing import Any, Optional, Union
from .config import config

logger = logging.getLogger(__name__)


class RedisClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RedisClient, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self.redis_client = None
            self._initialized = True
            self._connect()

    def _connect(self):
        try:
            self.redis_client = redis.Redis(
                host=config.redis_host,
                port=config.redis_port,
                password=config.redis_password if config.redis_password else None,
                db=config.redis_db,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            self.redis_client.ping()
            logger.info("✅ Redis connection established successfully")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            self.redis_client = None

    def _ensure_connection(self):
        if not self.redis_client:
            self._connect()
            return self.redis_client is not None

        try:
            self.redis_client.ping()
            return True
        except (redis.ConnectionError, redis.TimeoutError):
            logger.warning("Redis connection lost, reconnecting...")
            self._connect()
            return self.redis_client is not None
        except Exception as e:
            logger.error(f"Redis connection error: {e}")
            return False

    def incr(self, key: str, amount: int = 1) -> int:
        """Increment key by amount, return new value"""
        if not self._ensure_connection():
            logger.warning(f"Redis not available for incr on key: {key}")
            return amount  # Fallback

        try:
            return self.redis_client.incr(key, amount)
        except Exception as e:
            logger.error(f"Redis incr failed for {key}: {e}")
            return amount  # Fallback

    def setex(self, key: str, expire: int, value: str) -> bool:
        """Set key with expiration"""
        if not self._ensure_connection():
            logger.warning(f"Redis not available for setex on key: {key}")
            return False

        try:
            result = self.redis_client.setex(key, expire, value)
            return result is True
        except Exception as e:
            logger.error(f"Redis setex failed for {key}: {e}")
            return False

    def get(self, key: str) -> Optional[str]:
        if not self._ensure_connection():
            return None

        try:
            return self.redis_client.get(key)
        except Exception as e:
            logger.error(f"Redis get failed for {key}: {e}")
            return None

    def delete(self, *keys) -> bool:
        if not self._ensure_connection():
            return False

        try:
            return bool(self.redis_client.delete(*keys))
        except Exception as e:
            logger.error(f"Redis delete failed for {keys}: {e}")
            return False

    def exists(self, key: str) -> bool:
        if not self._ensure_connection():
            return False

        try:
            return self.redis_client.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis exists failed for {key}: {e}")
            return False

    def expire(self, key: str, expire: int) -> bool:
        if not self._ensure_connection():
            return False

        try:
            return self.redis_client.expire(key, expire)
        except Exception as e:
            logger.error(f"Redis expire failed for {key}: {e}")
            return False

    def keys(self, pattern: str):
        if not self._ensure_connection():
            return []

        try:
            return self.redis_client.keys(pattern)
        except Exception as e:
            logger.error(f"Redis keys failed for pattern {pattern}: {e}")
            return []

    def ping(self) -> bool:
        if not self._ensure_connection():
            return False
        try:
            return self.redis_client.ping()
        except Exception:
            return False

    # Additional methods for session service
    def pipeline(self):
        """Return pipeline for batch operations"""
        if not self._ensure_connection():
            # Return a dummy pipeline that does nothing
            class DummyPipeline:
                def execute(self):
                    return []

                def __getattr__(self, name):
                    return lambda *args, **kwargs: self

            return DummyPipeline()

        try:
            return self.redis_client.pipeline()
        except Exception as e:
            logger.error(f"Redis pipeline failed: {e}")

            class DummyPipeline:
                def execute(self):
                    return []

                def __getattr__(self, name):
                    return lambda *args, **kwargs: self

            return DummyPipeline()

    # Cache methods
    def cache_product(self, product_id: int, product_data: dict, expire: int = 3600):
        if not self._ensure_connection():
            return False
        try:
            key = f"product:{product_id}"
            return self.setex(key, expire, json.dumps(product_data))
        except Exception as e:
            logger.error(f"Failed to cache product {product_id}: {e}")
            return False

    def get_cached_product(self, product_id: int) -> Optional[dict]:
        if not self._ensure_connection():
            return None
        try:
            key = f"product:{product_id}"
            data = self.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Failed to get cached product {product_id}: {e}")
            return None

    def cache_user_session(self, user_id: int, session_data: dict, expire: int = 86400):
        if not self._ensure_connection():
            return False
        try:
            key = f"session:{user_id}"
            return self.setex(key, expire, json.dumps(session_data))
        except Exception as e:
            logger.error(f"Failed to cache session for user {user_id}: {e}")
            return False

    def get_cached_session(self, session_key: str) -> Optional[dict]:
        if not self._ensure_connection():
            return None
        try:
            data = self.get(session_key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Failed to get cached session {session_key}: {e}")
            return None

    def invalidate_product_cache(self, product_id: int):
        if not self._ensure_connection():
            return False
        try:
            key = f"product:{product_id}"
            return self.delete(key)
        except Exception as e:
            logger.error(f"Failed to invalidate product cache {product_id}: {e}")
            return False

    def cache_categories(self, categories_data: list, expire: int = 1800):
        if not self._ensure_connection():
            return False
        try:
            key = "categories:all"
            return self.setex(key, expire, json.dumps(categories_data))
        except Exception as e:
            logger.error(f"Failed to cache categories: {e}")
            return False

    def get_cached_categories(self) -> Optional[list]:
        if not self._ensure_connection():
            return None
        try:
            key = "categories:all"
            data = self.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Failed to get cached categories: {e}")
            return None

    def rate_limit_check(self, key: str, limit: int, window: int) -> bool:
        """Check rate limit with fallback"""
        if not self._ensure_connection():
            return True  # Allow if Redis is down

        try:
            current = self.incr(key)
            if current == 1:
                self.expire(key, window)
            return current <= limit
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            return True  # Allow if check fails

    def delete_pattern(self, pattern: str) -> bool:
        if not self._ensure_connection():
            return False
        try:
            keys = self.keys(pattern)
            if keys:
                return self.delete(*keys)
            return True
        except Exception as e:
            logger.error(f"Failed to delete pattern {pattern}: {e}")
            return False


# Global instance
redis_client = RedisClient()