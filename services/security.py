"""
Phase 2: Security Module - Input Validation + Rate Limiting
services/security.py
"""

import re
from services.rate_limiter import RateLimiter
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

# RateLimiter moved to services/rate_limiter.py
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
    is_allowed = limiter.is_allowed(user_id)
    rate_msg = "" if is_allowed else f"Rate limit exceeded for {user_id}"
    if not is_allowed:
        return False, rate_msg
    
    # Record successful request
    # Request already recorded by is_allowed()
    
    return True, ""


def get_security_stats() -> Dict[str, int]:
    """Get security stats for admin display."""
    limiter = get_rate_limiter()
    user_id = get_user_id()
    return {
        "remaining": limiter.get_remaining_requests(user_id),
        "retry_after": limiter.get_retry_after(user_id)
    }