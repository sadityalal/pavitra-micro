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
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        self.redis_client = None
        self._connect()
    
    def _connect(self):
        try:
            self.redis_client = redis.Redis(
                host=config.redis_host,
                port=config.redis_port,
                password=config.redis_password,
                db=config.redis_db,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            self.redis_client.ping()
            logger.info("Redis connection established successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None
    
    def _ensure_connection(self):
        if not self.redis_client:
            self._connect()
        try:
            self.redis_client.ping()
            return True
        except:
            self._connect()
            return bool(self.redis_client)
    
    def cache_product(self, product_id: int, product_data: dict, expire: int = 3600):
        if not self._ensure_connection():
            return False
        try:
            key = f"product:{product_id}"
            return self.redis_client.setex(key, expire, json.dumps(product_data))
        except Exception as e:
            logger.error(f"Failed to cache product {product_id}: {e}")
            return False
    
    def get_cached_product(self, product_id: int) -> Optional[dict]:
        if not self._ensure_connection():
            return None
        try:
            key = f"product:{product_id}"
            data = self.redis_client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Failed to get cached product {product_id}: {e}")
            return None
    
    def cache_user_session(self, user_id: int, session_data: dict, expire: int = 86400):
        if not self._ensure_connection():
            return False
        try:
            key = f"session:{user_id}"
            return self.redis_client.setex(key, expire, json.dumps(session_data))
        except Exception as e:
            logger.error(f"Failed to cache session for user {user_id}: {e}")
            return False
    
    def get_cached_session(self, user_id: int) -> Optional[dict]:
        if not self._ensure_connection():
            return None
        try:
            key = f"session:{user_id}"
            data = self.redis_client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Failed to get cached session for user {user_id}: {e}")
            return None
    
    def invalidate_product_cache(self, product_id: int):
        if not self._ensure_connection():
            return False
        try:
            key = f"product:{product_id}"
            return self.redis_client.delete(key)
        except Exception as e:
            logger.error(f"Failed to invalidate product cache {product_id}: {e}")
            return False
    
    def cache_categories(self, categories_data: list, expire: int = 1800):
        if not self._ensure_connection():
            return False
        try:
            key = "categories:all"
            return self.redis_client.setex(key, expire, json.dumps(categories_data))
        except Exception as e:
            logger.error(f"Failed to cache categories: {e}")
            return False
    
    def get_cached_categories(self) -> Optional[list]:
        if not self._ensure_connection():
            return None
        try:
            key = "categories:all"
            data = self.redis_client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Failed to get cached categories: {e}")
            return None
    
    def rate_limit_check(self, key: str, limit: int, window: int) -> bool:
        if not self._ensure_connection():
            return True  # Allow if Redis is down
        try:
            current = self.redis_client.incr(key)
            if current == 1:
                self.redis_client.expire(key, window)
            return current <= limit
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            return True

redis_client = RedisClient()
