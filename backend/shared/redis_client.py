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
            raise
    
    @property
    def client(self):
        return self.redis_client
    
    def get(self, key: str) -> Optional[Any]:
        try:
            value = self.redis_client.get(key)
            if value:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            return None
        except Exception as e:
            logger.error(f"Redis get error for key {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            return self.redis_client.set(key, value, ex=ex)
        except Exception as e:
            logger.error(f"Redis set error for key {key}: {e}")
            return False
    
    def delete(self, *keys) -> int:
        try:
            return self.redis_client.delete(*keys)
        except Exception as e:
            logger.error(f"Redis delete error for keys {keys}: {e}")
            return 0
    
    def exists(self, key: str) -> bool:
        try:
            return self.redis_client.exists(key) == 1
        except Exception as e:
            logger.error(f"Redis exists error for key {key}: {e}")
            return False
    
    def incr(self, key: str, amount: int = 1) -> Optional[int]:
        try:
            return self.redis_client.incr(key, amount)
        except Exception as e:
            logger.error(f"Redis incr error for key {key}: {e}")
            return None
    
    def expire(self, key: str, time: int) -> bool:
        try:
            return self.redis_client.expire(key, time)
        except Exception as e:
            logger.error(f"Redis expire error for key {key}: {e}")
            return False

# Global redis instance
redis_client = RedisClient()
