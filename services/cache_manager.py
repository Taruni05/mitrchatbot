"""
Phase 3: Response Caching Module
services/cache_manager.py
"""

import hashlib
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
import streamlit as st
from services.logger import get_logger

logger = get_logger(__name__)


# ============================================================================
# CACHE KEY GENERATION
# ============================================================================

def generate_cache_key(query: str, language: str = "en", location: str = "") -> str:
    """
    Generate a unique cache key for a query.
    
    Args:
        query: User query text
        language: Language code
        location: User location (optional)
    
    Returns:
        MD5 hash as cache key
    """
    # Normalize query (lowercase, strip whitespace)
    normalized = query.lower().strip()
    
    # Create composite key
    composite = f"{normalized}|{language}|{location}"
    
    # Generate hash
    key = hashlib.md5(composite.encode('utf-8')).hexdigest()
    
    return key


# ============================================================================
# CACHE STORAGE & RETRIEVAL
# ============================================================================

class ResponseCache:
    """
    In-memory response cache with TTL support.
    Stores responses to avoid redundant API calls.
    """
    
    def __init__(self):
        # Initialize cache in session state
        if 'response_cache' not in st.session_state:
            st.session_state.response_cache = {}
        
        # Cache statistics
        if 'cache_stats' not in st.session_state:
            st.session_state.cache_stats = {
                'hits': 0,
                'misses': 0,
                'total_queries': 0
            }
        
        # TTL settings (in seconds)
        self.TTL = {
            'weather': 600,      # 10 minutes
            'metro': 3600,       # 1 hour (routes don't change)
            'bus': 1800,         # 30 minutes
            'crowd': 86400,      # 24 hours
            'chat': 300,         # 5 minutes (general queries)
            'default': 600       # 10 minutes
        }
    
    def _determine_query_type(self, query: str) -> str:
        """
        Determine query type based on keywords.
        
        Args:
            query: User query
        
        Returns:
            Query type (weather, metro, bus, etc.)
        """
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['weather', 'temperature', 'rain', 'forecast']):
            return 'weather'
        
        if any(word in query_lower for word in ['metro', 'train', 'railway']):
            return 'metro'
        
        if any(word in query_lower for word in ['bus', 'rtc']):
            return 'bus'
        
        if any(word in query_lower for word in ['crowd', 'busy', 'crowded']):
            return 'crowd'
        
        return 'chat'
    
    def _is_expired(self, timestamp: float, ttl: int) -> bool:
        """Check if cache entry is expired."""
        age = time.time() - timestamp
        return age > ttl
    
    def get(self, cache_key: str, query: str = "") -> Optional[str]:
        """
        Retrieve cached response if available and not expired.
        
        Args:
            cache_key: Cache key
            query: Original query (to determine TTL)
        
        Returns:
            Cached response or None
        """
        cache = st.session_state.response_cache
        
        if cache_key not in cache:
            st.session_state.cache_stats['misses'] += 1
            logger.debug(f"Cache miss: {cache_key[:8]}")
            return None
        
        entry = cache[cache_key]
        timestamp = entry['timestamp']
        
        # Determine TTL based on query type
        query_type = self._determine_query_type(query) if query else 'default'
        ttl = self.TTL.get(query_type, self.TTL['default'])
        
        # Check if expired
        if self._is_expired(timestamp, ttl):
            # Remove expired entry
            del cache[cache_key]
            st.session_state.cache_stats['misses'] += 1
            logger.debug(f"Cache expired: {cache_key[:8]}")
            return None
        
        # Cache hit!
        st.session_state.cache_stats['hits'] += 1
        logger.debug(f"Cache hit: {cache_key[:8]} (age: {int(time.time() - timestamp)}s)")
        return entry['response']
    
    def set(self, cache_key: str, response: str, query: str = ""):
        """
        Store response in cache.
        
        Args:
            cache_key: Cache key
            response: Response to cache
            query: Original query (for logging)
        """
        st.session_state.response_cache[cache_key] = {
            'response': response,
            'timestamp': time.time(),
            'query': query[:100]  # Store truncated query for debugging
        }
        
        logger.debug(f"Cache set: {cache_key[:8]}")
        
        # Cleanup old entries if cache is too large
        self._cleanup_if_needed()
    
    def _cleanup_if_needed(self, max_entries: int = 100):
        """
        Remove oldest entries if cache exceeds max size.
        
        Args:
            max_entries: Maximum number of cache entries
        """
        cache = st.session_state.response_cache
        
        if len(cache) <= max_entries:
            return
        
        # Sort by timestamp and keep only newest entries
        sorted_entries = sorted(
            cache.items(),
            key=lambda x: x[1]['timestamp'],
            reverse=True
        )
        
        st.session_state.response_cache = dict(sorted_entries[:max_entries])
        logger.info(f"Cache cleanup: kept {max_entries} newest entries")
    
    def clear(self):
        """Clear all cache entries."""
        st.session_state.response_cache = {}
        logger.info("Cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        stats = st.session_state.cache_stats.copy()
        stats['total_queries'] = stats['hits'] + stats['misses']
        stats['hit_rate'] = (
            stats['hits'] / stats['total_queries'] * 100
            if stats['total_queries'] > 0
            else 0
        )
        stats['cache_size'] = len(st.session_state.response_cache)
        
        return stats
    
    def display_stats(self):
        """Display cache stats in Streamlit UI (for debugging)."""
        stats = self.get_stats()
        
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 📊 Cache Stats")
        st.sidebar.metric("Hit Rate", f"{stats['hit_rate']:.1f}%")
        st.sidebar.metric("Cache Size", stats['cache_size'])
        st.sidebar.metric("Hits", stats['hits'])
        st.sidebar.metric("Misses", stats['misses'])


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

# Global cache instance
_cache = None

def get_cache() -> ResponseCache:
    """Get or create the global cache instance."""
    global _cache
    if _cache is None:
        _cache = ResponseCache()
    return _cache


def cached_response(query: str, language: str = "en", location: str = "") -> Optional[str]:
    """
    Check if response is cached.
    
    Args:
        query: User query
        language: Language code
        location: User location
    
    Returns:
        Cached response or None
    """
    cache = get_cache()
    cache_key = generate_cache_key(query, language, location)
    return cache.get(cache_key, query)


def cache_response(query: str, response: str, language: str = "en", location: str = ""):
    """
    Cache a response.
    
    Args:
        query: User query
        response: Response to cache
        language: Language code
        location: User location
    """
    cache = get_cache()
    cache_key = generate_cache_key(query, language, location)
    cache.set(cache_key, response, query)


def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics."""
    cache = get_cache()
    return cache.get_stats()


def clear_cache():
    """Clear all cached responses."""
    cache = get_cache()
    cache.clear()


# ============================================================================
# SMART CACHE DECORATOR
# ============================================================================

def smart_cache(ttl: Optional[int] = None):
    """
    Decorator for caching function responses.
    
    Usage:
        @smart_cache(ttl=600)
        def expensive_function(query):
            # ... do expensive work
            return result
    """
    def decorator(func):
        def wrapper(query: str, *args, **kwargs):
            # Generate cache key from function name and query
            cache_key = generate_cache_key(f"{func.__name__}:{query}")
            cache = get_cache()
            
            # Try to get from cache
            cached = cache.get(cache_key, query)
            if cached is not None:
                return cached
            
            # Call function
            result = func(query, *args, **kwargs)
            
            # Cache result
            cache.set(cache_key, result, query)
            
            return result
        
        return wrapper
    return decorator