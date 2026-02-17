"""
Phase 2: Security Module - Input Validation + Rate Limiting
services/security.py
"""

import re
import time
from datetime import datetime, timedelta
from typing import Tuple, Dict, List
import streamlit as st
from services.logger import get_logger

logger = get_logger(__name__)


# ============================================================================
# INPUT VALIDATION
# ============================================================================

def validate_input(text: str, max_length: int = 500) -> Tuple[bool, str]:
    """
    Validate user input for security and quality.
    
    Args:
        text: User input text
        max_length: Maximum allowed length
    
    Returns:
        (is_valid, error_message)
    """
    
    # Check if empty
    if not text or not text.strip():
        return False, "Input cannot be empty"
    
    # Check length
    if len(text) > max_length:
        return False, f"Input too long. Maximum {max_length} characters allowed"
    
    # Check for suspicious patterns
    suspicious_patterns = [
        # SQL injection
        r"(\bUNION\b|\bSELECT\b|\bDROP\b|\bINSERT\b|\bDELETE\b|\bUPDATE\b)",
        # Script tags
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        # Command injection
        r"[;&|`$]",
        # Path traversal
        r"\.\./",
    ]
    
    text_upper = text.upper()
    for pattern in suspicious_patterns:
        if re.search(pattern, text_upper, re.IGNORECASE):
            logger.warning(f"Suspicious input detected: {pattern}")
            return False, "Invalid input detected. Please use normal language"
    
    # Check for excessive special characters (spam detection)
    special_char_count = len(re.findall(r"[^a-zA-Z0-9\s\u0900-\u097F\u0C00-\u0C7F]", text))
    if special_char_count > len(text) * 0.3:  # More than 30% special chars
        return False, "Too many special characters. Please use normal text"
    
    # Check for repeated characters (spam)
    if re.search(r"(.)\1{10,}", text):  # Same character 10+ times
        return False, "Please avoid excessive character repetition"
    
    return True, ""


# ============================================================================
# RATE LIMITING
# ============================================================================

class RateLimiter:
    """
    Rate limiter to prevent abuse.
    Tracks requests per session and enforces limits.
    """
    
    def __init__(self):
        # Initialize session state for tracking
        if 'rate_limit_data' not in st.session_state:
            st.session_state.rate_limit_data = {}
        
        # Limits
        self.REQUESTS_PER_MINUTE = 10
        self.REQUESTS_PER_HOUR = 50
        self.REQUESTS_PER_DAY = 200
    
    def _get_session_id(self) -> str:
        """Get or create session ID."""
        if 'session_id' not in st.session_state:
            st.session_state.session_id = f"session_{int(time.time())}"
        return st.session_state.session_id
    
    def _clean_old_requests(self, session_id: str):
        """Remove requests older than 24 hours."""
        if session_id not in st.session_state.rate_limit_data:
            st.session_state.rate_limit_data[session_id] = []
        
        now = datetime.now()
        cutoff = now - timedelta(days=1)
        
        st.session_state.rate_limit_data[session_id] = [
            ts for ts in st.session_state.rate_limit_data[session_id]
            if ts > cutoff
        ]
    
    def check_rate_limit(self) -> Tuple[bool, str]:
        """
        Check if request is within rate limits.
        
        Returns:
            (is_allowed, message)
        """
        session_id = self._get_session_id()
        self._clean_old_requests(session_id)
        
        now = datetime.now()
        requests = st.session_state.rate_limit_data.get(session_id, [])
        
        # Check per-minute limit
        one_min_ago = now - timedelta(minutes=1)
        recent_requests_1min = len([ts for ts in requests if ts > one_min_ago])
        
        if recent_requests_1min >= self.REQUESTS_PER_MINUTE:
            logger.warning(f"Rate limit exceeded (1 min): {session_id}")
            return False, f"⚠️ Too many requests. Please wait a minute. ({recent_requests_1min}/{self.REQUESTS_PER_MINUTE})"
        
        # Check per-hour limit
        one_hour_ago = now - timedelta(hours=1)
        recent_requests_1hour = len([ts for ts in requests if ts > one_hour_ago])
        
        if recent_requests_1hour >= self.REQUESTS_PER_HOUR:
            logger.warning(f"Rate limit exceeded (1 hour): {session_id}")
            return False, f"⚠️ Hourly limit reached. Please try again later. ({recent_requests_1hour}/{self.REQUESTS_PER_HOUR})"
        
        # Check per-day limit
        if len(requests) >= self.REQUESTS_PER_DAY:
            logger.warning(f"Rate limit exceeded (24 hours): {session_id}")
            return False, f"⚠️ Daily limit reached. Come back tomorrow! ({len(requests)}/{self.REQUESTS_PER_DAY})"
        
        return True, ""
    
    def record_request(self):
        """Record a successful request."""
        session_id = self._get_session_id()
        
        if session_id not in st.session_state.rate_limit_data:
            st.session_state.rate_limit_data[session_id] = []
        
        st.session_state.rate_limit_data[session_id].append(datetime.now())
        logger.debug(f"Request recorded for {session_id}")
    
    def get_stats(self) -> Dict[str, int]:
        """Get current rate limit stats for display."""
        session_id = self._get_session_id()
        self._clean_old_requests(session_id)
        
        requests = st.session_state.rate_limit_data.get(session_id, [])
        now = datetime.now()
        
        one_min_ago = now - timedelta(minutes=1)
        one_hour_ago = now - timedelta(hours=1)
        
        return {
            "last_minute": len([ts for ts in requests if ts > one_min_ago]),
            "last_hour": len([ts for ts in requests if ts > one_hour_ago]),
            "last_day": len(requests),
            "remaining_minute": self.REQUESTS_PER_MINUTE - len([ts for ts in requests if ts > one_min_ago]),
            "remaining_hour": self.REQUESTS_PER_HOUR - len([ts for ts in requests if ts > one_hour_ago]),
            "remaining_day": self.REQUESTS_PER_DAY - len(requests),
        }


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

# Global rate limiter instance
_rate_limiter = None

def get_rate_limiter() -> RateLimiter:
    """Get or create the global rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


def validate_and_rate_limit(text: str, max_length: int = 500) -> Tuple[bool, str]:
    """
    Convenience function to validate input AND check rate limit.
    
    Args:
        text: User input
        max_length: Max allowed length
    
    Returns:
        (is_allowed, error_message)
    """
    # First validate input
    is_valid, error_msg = validate_input(text, max_length)
    if not is_valid:
        return False, error_msg
    
    # Then check rate limit
    limiter = get_rate_limiter()
    is_allowed, rate_msg = limiter.check_rate_limit()
    if not is_allowed:
        return False, rate_msg
    
    # Record successful request
    limiter.record_request()
    
    return True, ""


def get_security_stats() -> Dict[str, int]:
    """Get security stats for admin display."""
    limiter = get_rate_limiter()
    return limiter.get_stats()