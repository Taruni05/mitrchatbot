"""
Enhanced Phase 3: Smart Response Caching Module
services/cache_manager.py

Features:
- Intent-based TTL (different cache times for different content types)
- Smart invalidation (auto-refresh time-sensitive content)
- Metadata tracking (date, location, intent for intelligent cache decisions)
- Cache warming (pre-populate common queries)
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
# SMART TTL RULES
# ============================================================================

class SmartTTL:
    """
    Intelligent TTL (Time To Live) rules based on content type.
    Different types of content need different cache durations.
    """
    
    # TTL rules in seconds
    RULES = {
        # === STATIC CONTENT (cache for 24 hours) ===
        "monuments": 86400,          # Monument info doesn't change
        "temples": 86400,            # Temple info static
        "museums": 86400,            # Museum details static
        "history": 86400,            # Historical facts static
        "landmarks": 86400,          # Landmark info static
        
        # === SEMI-STATIC CONTENT (cache for 6 hours) ===
        "food": 21600,               # Restaurants change menus
        "shopping": 21600,           # Shopping centers update
        "movies": 21600,             # Movie schedules update
        "itinerary": 21600,          # Itineraries can change
        
        # === DYNAMIC CONTENT (cache for 1 hour) ===
        "news": 3600,                # News updates hourly
        "events": 3600,              # Events can be added/cancelled
        "crowd": 3600,               # Crowd levels change
        
        # === REAL-TIME CONTENT (cache for 10-30 minutes) ===
        "weather": 600,              # Weather changes quickly
        "traffic": 600,              # Traffic is real-time
        "fuel": 1800,                # Fuel prices update daily but check every 30 min
        "metro": 1800,               # Live timings, but routes are static
        "bus": 1800,                 # Live timings
        
        # === NEVER CACHE (0 seconds) ===
        "utilities": 0,              # Power cuts, water supply (real-time)
        "deals": 0,                  # Deals expire quickly
        "live_deals": 0,             # Live deals must be fresh
        
        # === DEFAULT ===
        "chat": 300,                 # General queries - 5 minutes
        "default": 600               # Unknown queries - 10 minutes
    }
    
    @classmethod
    def get_ttl(cls, intent: str) -> int:
        """
        Get appropriate TTL for an intent.
        
        Args:
            intent: Detected intent from LangGraph
        
        Returns:
            TTL in seconds
        """
        intent_lower = intent.lower() if intent else "default"
        return cls.RULES.get(intent_lower, cls.RULES["default"])
    
    @classmethod
    def should_cache(cls, intent: str) -> bool:
        """
        Check if content should be cached at all.
        
        Args:
            intent: Detected intent
        
        Returns:
            True if should cache
        """
        ttl = cls.get_ttl(intent)
        return ttl > 0


# ============================================================================
# SMART CACHE INVALIDATION
# ============================================================================

class CacheInvalidator:
    """
    Smart cache invalidation rules.
    Automatically invalidate cache based on conditions.
    """
    
    @staticmethod
    def should_invalidate(cache_key: str, metadata: Dict) -> bool:
        """
        Check if cache should be invalidated based on metadata.
        
        Args:
            cache_key: Cache key
            metadata: Cache entry metadata
        
        Returns:
            True if cache should be invalidated
        """
        intent = metadata.get("intent", "")
        cached_date = metadata.get("date", "")
        cached_area = metadata.get("area", "")
        
        current_date = datetime.now().strftime("%Y-%m-%d")
        current_area = st.session_state.get("selected_area", "")
        
        # === RULE 1: Time-sensitive content invalidation ===
        if intent in ["events", "deals", "news"]:
            # Invalidate if date changed (midnight passed)
            if cached_date != current_date:
                logger.debug(f"Invalidating {intent} cache: date changed")
                return True
        
        # === RULE 2: Location-dependent content ===
        if intent in ["weather", "traffic", "food", "shopping"]:
            # Invalidate if user's area changed
            if current_area and cached_area != current_area:
                logger.debug(f"Invalidating {intent} cache: location changed")
                return True
        
        # === RULE 3: Weather invalidation (special rules) ===
        if intent == "weather":
            # Check if weather conditions likely changed
            hours_old = metadata.get("hours_old", 0)
            if hours_old > 0.5:  # More than 30 minutes old
                logger.debug(f"Invalidating weather cache: {hours_old:.1f}h old")
                return True
        
        # === RULE 4: Peak hour invalidation ===
        if intent == "traffic":
            # Invalidate traffic during peak hours (more volatile)
            current_hour = datetime.now().hour
            if 8 <= current_hour <= 10 or 17 <= current_hour <= 20:
                minutes_old = metadata.get("minutes_old", 0)
                if minutes_old > 5:  # Invalidate after 5 min during peak
                    logger.debug(f"Invalidating traffic cache: peak hour")
                    return True
        
        return False


# ============================================================================
# ENHANCED CACHE STORAGE
# ============================================================================

class ResponseCache:
    """
    Enhanced in-memory response cache with smart TTL and invalidation.
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
                'invalidations': 0,
                'total_queries': 0
            }
    
    def _calculate_age_metadata(self, timestamp: float) -> Dict:
        """Calculate age-related metadata for a cache entry."""
        age_seconds = time.time() - timestamp
        return {
            "age_seconds": int(age_seconds),
            "minutes_old": age_seconds / 60,
            "hours_old": age_seconds / 3600,
        }
    
    def get(self, cache_key: str, query: str = "", intent: str = "") -> Optional[str]:
        """
        Retrieve cached response if available and not expired.
        
        Args:
            cache_key: Cache key
            query: Original query (for logging)
            intent: Intent for TTL determination
        
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
        metadata = entry.get('metadata', {})
        
        # Add age metadata
        metadata.update(self._calculate_age_metadata(timestamp))
        
        # Check smart invalidation rules
        if CacheInvalidator.should_invalidate(cache_key, metadata):
            del cache[cache_key]
            st.session_state.cache_stats['invalidations'] += 1
            st.session_state.cache_stats['misses'] += 1
            logger.debug(f"Cache invalidated: {cache_key[:8]}")
            return None
        
        # Get TTL based on intent
        ttl = SmartTTL.get_ttl(intent or metadata.get("intent", ""))
        
        # Check if expired
        if metadata["age_seconds"] > ttl:
            del cache[cache_key]
            st.session_state.cache_stats['misses'] += 1
            logger.debug(f"Cache expired: {cache_key[:8]} (age: {metadata['age_seconds']}s, ttl: {ttl}s)")
            return None
        
        # Cache hit!
        st.session_state.cache_stats['hits'] += 1
        logger.debug(f"✅ Cache hit: {cache_key[:8]} (age: {metadata['age_seconds']}s)")
        return entry['response']
    
    def set(self, cache_key: str, response: str, query: str = "", 
            intent: str = "", ttl: Optional[int] = None, metadata: Optional[Dict] = None):
        """
        Store response in cache with metadata.
        
        Args:
            cache_key: Cache key
            response: Response to cache
            query: Original query (for debugging)
            intent: Intent type (for TTL)
            ttl: Optional custom TTL (overrides intent-based TTL)
            metadata: Additional metadata
        """
        # Check if this intent should be cached
        if not SmartTTL.should_cache(intent):
            logger.debug(f"Skipping cache (TTL=0): intent={intent}")
            return
        
        # Build metadata
        cache_metadata = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "area": st.session_state.get("selected_area", ""),
            "intent": intent,
            "query": query[:100],  # Truncated for debugging
            "ttl": ttl or SmartTTL.get_ttl(intent)
        }
        
        # Merge with any additional metadata
        if metadata:
            cache_metadata.update(metadata)
        
        st.session_state.response_cache[cache_key] = {
            'response': response,
            'timestamp': time.time(),
            'metadata': cache_metadata
        }
        
        logger.debug(f"Cache set: {cache_key[:8]} (intent={intent}, ttl={cache_metadata['ttl']}s)")
        
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
    
    def clear_by_intent(self, intent: str):
        """
        Clear cache entries for a specific intent.
        
        Args:
            intent: Intent to clear
        """
        cache = st.session_state.response_cache
        keys_to_remove = [
            key for key, entry in cache.items()
            if entry.get('metadata', {}).get('intent', '') == intent
        ]
        
        for key in keys_to_remove:
            del cache[key]
        
        logger.info(f"Cleared {len(keys_to_remove)} entries for intent: {intent}")
    
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
        
        # Calculate average TTL
        cache = st.session_state.response_cache
        if cache:
            ttls = [entry['metadata'].get('ttl', 0) for entry in cache.values()]
            stats['avg_ttl'] = sum(ttls) / len(ttls) if ttls else 0
        else:
            stats['avg_ttl'] = 0
        
        return stats
    
    def display_stats(self):
        """Display cache stats in Streamlit UI (for debugging)."""
        stats = self.get_stats()
        
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 📊 Cache Stats")
        
        col1, col2 = st.sidebar.columns(2)
        col1.metric("Hit Rate", f"{stats['hit_rate']:.1f}%")
        col2.metric("Size", stats['cache_size'])
        
        col3, col4 = st.sidebar.columns(2)
        col3.metric("Hits", stats['hits'])
        col4.metric("Misses", stats['misses'])
        
        if stats['invalidations'] > 0:
            st.sidebar.caption(f"🔄 {stats['invalidations']} smart invalidations")


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


def cached_response(query: str, language: str = "en", location: str = "", 
                   intent: str = "") -> Optional[str]:
    """
    Check if response is cached.
    
    Args:
        query: User query
        language: Language code
        location: User location
        intent: Intent for TTL determination
    
    Returns:
        Cached response or None
    """
    cache = get_cache()
    cache_key = generate_cache_key(query, language, location)
    return cache.get(cache_key, query, intent)


def cache_response(query: str, response: str, language: str = "en", 
                  location: str = "", intent: str = ""):
    """
    Cache a response with smart TTL.
    
    Args:
        query: User query
        response: Response to cache
        language: Language code
        location: User location
        intent: Intent type (determines TTL)
    """
    cache = get_cache()
    cache_key = generate_cache_key(query, language, location)
    cache.set(cache_key, response, query, intent)


def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics."""
    cache = get_cache()
    return cache.get_stats()


def clear_cache():
    """Clear all cached responses."""
    cache = get_cache()
    cache.clear()


def clear_cache_by_intent(intent: str):
    """Clear cache for specific intent."""
    cache = get_cache()
    cache.clear_by_intent(intent)


# ============================================================================
# SMART CACHE DECORATOR
# ============================================================================

def smart_cache(ttl: Optional[int] = None, intent: str = ""):
    """
    Decorator for caching function responses with smart TTL.
    
    Usage:
        @smart_cache(intent="weather")
        def get_weather_data(query):
            # ... expensive API call
            return result
    """
    def decorator(func):
        def wrapper(query: str, *args, **kwargs):
            # Generate cache key from function name and query
            cache_key = generate_cache_key(f"{func.__name__}:{query}")
            cache = get_cache()
            
            # Try to get from cache
            cached = cache.get(cache_key, query, intent)
            if cached is not None:
                return cached
            
            # Call function
            result = func(query, *args, **kwargs)
            
            # Cache result
            cache.set(cache_key, result, query, intent, ttl)
            
            return result
        
        return wrapper
    return decorator