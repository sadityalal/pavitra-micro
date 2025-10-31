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
            identifier = request.client.host if request.client else "unknown"

        # FIX: Use a more specific key to avoid conflicts
        current_time = int(time.time())
        window_start = current_time // self.window_seconds
        key = f"rate_limit:{identifier}:{window_start}"

        try:
            # FIX: Use the enhanced Redis client methods
            current = redis_client.incr(key)
            if current == 1:
                redis_client.expire(key, self.window_seconds)

            if current > self.requests_limit:
                logger.warning(f"Rate limit exceeded for {identifier} - {current}/{self.requests_limit}")
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded. Try again in {self.window_seconds} seconds."
                )

            return True
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            # FIX: Fail open instead of blocking users during Redis issues
            return True


# FIX: Add global rate limiter instance
rate_limiter = RateLimiter()


class RateLimitBearer(HTTPBearer):
    async def __call__(self, request: Request):
        await rate_limiter.check_rate_limit(request)
        return await super().__call__(request)


# FIX: Add additional rate limiting utilities
class AdvancedRateLimiter:
    def __init__(self):
        self.limiters = {}

    def get_limiter(self, name: str, max_requests: int, window: int):
        """Get or create a named rate limiter"""
        if name not in self.limiters:
            self.limiters[name] = {
                'max_requests': max_requests,
                'window': window
            }
        return self.limiters[name]

    async def check_named_limit(self, request: Request, limiter_name: str, identifier: Optional[str] = None):
        """Check rate limit for a specific named limiter"""
        if config.debug_mode:
            return True

        if not identifier:
            identifier = request.client.host if request.client else "unknown"

        limiter = self.get_limiter(limiter_name, 100, 900)  # Default values

        current_time = int(time.time())
        window_start = current_time // limiter['window']
        key = f"rate_limit:{limiter_name}:{identifier}:{window_start}"

        try:
            current = redis_client.incr(key)
            if current == 1:
                redis_client.expire(key, limiter['window'])

            if current > limiter['max_requests']:
                logger.warning(f"Rate limit exceeded for {limiter_name}:{identifier}")
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded for {limiter_name}. Try again later."
                )

            return True
        except Exception as e:
            logger.error(f"Named rate limit check failed for {limiter_name}: {e}")
            return True


# FIX: Create global instance
advanced_rate_limiter = AdvancedRateLimiter()