from fastapi import HTTPException, Request
from fastapi.security import HTTPBearer
from typing import Optional
import time
from .redis_client import redis_client
from .config import config
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    def __init__(self):
        self.requests_limit = config.rate_limit_requests
        self.window_seconds = config.rate_limit_window
    
    async def check_rate_limit(self, request: Request, identifier: Optional[str] = None):
        if config.debug_mode:
            return True
            
        if not identifier:
            identifier = request.client.host
        
        key = f"rate_limit:{identifier}:{int(time.time() // self.window_seconds)}"
        
        try:
            current = redis_client.incr(key)
            if current == 1:
                redis_client.expire(key, self.window_seconds)
            
            if current > self.requests_limit:
                logger.warning(f"Rate limit exceeded for {identifier}")
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded. Try again in {self.window_seconds} seconds."
                )
            return True
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            # Fail open in case of Redis issues
            return True

rate_limiter = RateLimiter()

class RateLimitBearer(HTTPBearer):
    async def __call__(self, request: Request):
        await rate_limiter.check_rate_limit(request)
        return await super().__call__(request)
