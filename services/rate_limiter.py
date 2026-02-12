"""
Rate Limiting Service
Prevents abuse and protects against API cost overruns
"""

from datetime import datetime, timedelta
from typing import Dict, List
from collections import defaultdict
from services.logger import setup_logger
from services.config import config

logger = setup_logger('rate_limiter', 'rate_limiter.log')


class RateLimiter:
    """Simple in-memory rate limiter using sliding window algorithm"""
    
    def __init__(self, max_requests: int = None, window_seconds: int = None):
        self.max_requests = max_requests or config.app.RATE_LIMIT_REQUESTS
        self.window_seconds = window_seconds or config.app.RATE_LIMIT_WINDOW
        self._requests: Dict[str, List[datetime]] = defaultdict(list)
        
        logger.info(f"Rate limiter: {self.max_requests} requests per {self.window_seconds}s")
    
    def is_allowed(self, user_id: str) -> bool:
        """Check if request is allowed"""
        now = datetime.now()
        self._cleanup_old_requests(user_id, now)
        
        request_count = len(self._requests[user_id])
        
        if request_count >= self.max_requests:
            logger.warning(f"Rate limit exceeded: {user_id} ({request_count}/{self.max_requests})")
            return False
        
        self._requests[user_id].append(now)
        return True
    
    def get_retry_after(self, user_id: str) -> int:
        """Get seconds until user can retry"""
        if user_id not in self._requests or not self._requests[user_id]:
            return 0
        
        now = datetime.now()
        oldest = min(self._requests[user_id])
        retry_time = oldest + timedelta(seconds=self.window_seconds)
        return max(0, int((retry_time - now).total_seconds()))
    
    def get_remaining_requests(self, user_id: str) -> int:
        """Get remaining requests for user"""
        self._cleanup_old_requests(user_id, datetime.now())
        used = len(self._requests[user_id])
        return max(0, self.max_requests - used)
    
    def _cleanup_old_requests(self, user_id: str, now: datetime):
        """Remove old requests"""
        if user_id not in self._requests:
            return
        
        cutoff = now - timedelta(seconds=self.window_seconds)
        self._requests[user_id] = [r for r in self._requests[user_id] if r > cutoff]
        
        if not self._requests[user_id]:
            del self._requests[user_id]


# Global instance
_global_limiter = RateLimiter()

def is_rate_limited(user_id: str) -> bool:
    """Returns True if rate limited (should block)"""
    return not _global_limiter.is_allowed(user_id)

def get_rate_limit_info(user_id: str) -> Dict:
    """Get rate limit info"""
    return {
        "remaining": _global_limiter.get_remaining_requests(user_id),
        "retry_after": _global_limiter.get_retry_after(user_id),
        "max_requests": _global_limiter.max_requests,
        "window_seconds": _global_limiter.window_seconds,
    }