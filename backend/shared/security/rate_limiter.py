import time
from typing import Dict, Tuple
import logging
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

class RateLimiter:
    def __init__(self, max_requests: int = 100, window_seconds: int = 900):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, list] = {}
    
    def is_rate_limited(self, identifier: str) -> Tuple[bool, Dict[str, int]]:
        """Check if request is rate limited"""
        now = time.time()
        
        if identifier not in self.requests:
            self.requests[identifier] = []
        
        # Remove old requests outside the window
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier] 
            if now - req_time < self.window_seconds
        ]
        
        # Check if rate limited
        if len(self.requests[identifier]) >= self.max_requests:
            retry_after = int(self.window_seconds - (now - self.requests[identifier][0]))
            logger.warning(f"Rate limit exceeded for {identifier}")
            return True, {
                "retry_after": retry_after,
                "limit": self.max_requests,
                "remaining": 0
            }
        
        # Add current request
        self.requests[identifier].append(now)
        
        remaining = self.max_requests - len(self.requests[identifier])
        return False, {
            "retry_after": 0,
            "limit": self.max_requests,
            "remaining": remaining
        }
    
    def check_rate_limit(self, identifier: str):
        """Decorator for rate limiting"""
        is_limited, details = self.is_rate_limited(identifier)
        if is_limited:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Rate limit exceeded",
                    "retry_after": details["retry_after"],
                    "limit": details["limit"]
                }
            )
        return details
