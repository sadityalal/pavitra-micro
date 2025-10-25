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
        try:
            self.redis_client = redis.Redis(
                host=config.redis_host,
                port=config.redis_port,
                password=config.redis_password,
                db=config.redis_db,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            # Test connection
            self.redis_client.ping()
            logger.info("Redis connection established successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            # Fallback to in-memory cache or continue without Redis
            self.redis_client = None
    
    def cache_product(self, product_id: int, product_data: dict, expire: int = 3600):
        """Cache product data"""
        if not self.redis_client:
            return False
        try:
            key = f"product:{product_id}"
            return self.redis_client.setex(key, expire, json.dumps(product_data))
        except Exception as e:
            logger.error(f"Failed to cache product {product_id}: {e}")
            return False
    
    def get_cached_product(self, product_id: int) -> Optional[dict]:
        """Get cached product data"""
        if not self.redis_client:
            return None
        try:
            key = f"product:{product_id}"
            data = self.redis_client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Failed to get cached product {product_id}: {e}")
            return None
    
    def cache_user_session(self, user_id: int, session_data: dict, expire: int = 86400):
        """Cache user session data"""
        if not self.redis_client:
            return False
        try:
            key = f"session:{user_id}"
            return self.redis_client.setex(key, expire, json.dumps(session_data))
        except Exception as e:
            logger.error(f"Failed to cache session for user {user_id}: {e}")
            return False

# Global redis instance
redis_client = RedisClient()
