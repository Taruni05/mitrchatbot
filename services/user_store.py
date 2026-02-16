"""
User data service — saves and loads per-user preferences and chat history.
All data is stored in Supabase and tied to the authenticated user.

STORAGE STRATEGY: Store ALL preferences as a single JSONB object to avoid
type conversion issues and simplify operations.
"""
import streamlit as st
from typing import Dict, List, Optional
from datetime import datetime
import json
from services.auth import get_supabase, get_current_user_id
from services.logger import get_logger

logger = get_logger(__name__)


# ✅ ADD THIS NEW FUNCTION
def get_supabase_with_retry(max_retries: int = 2):
    """
    Get Supabase client with retry on JWT expiry.
    
    Args:
        max_retries: Number of times to retry getting a fresh client
    
    Returns:
        Supabase client or None
    """
    for attempt in range(max_retries):
        supabase = get_supabase()
        if supabase:
            try:
                # Quick validation test - try a simple query
                supabase.table("user_preferences").select("user_id").limit(1).execute()
                return supabase
            except Exception as e:
                if "JWT expired" in str(e) or "PGRST303" in str(e):
                    logger.warning(f"JWT expired on attempt {attempt + 1}, retrying...")
                    if attempt < max_retries - 1:
                        import time
                        time.sleep(0.5)  # Brief pause before retry
                        continue
                # If not a JWT error or final attempt, return the client anyway
                return supabase
        else:
            logger.error(f"get_supabase_with_retry() returned None on attempt {attempt + 1}")
            if attempt < max_retries - 1:
                import time
                time.sleep(0.5)
                continue
    
    return None

# ═══════════════════════════════════════════════════════════════════════════
# PREFERENCES MANAGEMENT (JSONB Storage)
# ═══════════════════════════════════════════════════════════════════════════

def load_preferences() -> Dict:
    """
    Load all preferences for the current user as a single JSON object.
    
    Returns:
        Dictionary of preferences, or empty dict if not found
    """
    # Check if database is enabled
    if not st.secrets.get("ENABLE_DATABASE", True):
        logger.debug("Database disabled - returning empty preferences")
        return {}
    
    user_id = get_current_user_id()
    if not user_id:
        logger.debug("Cannot load preferences: No user logged in")
        return {}
    
    supabase = get_supabase_with_retry()
    if not supabase:
        logger.error("Cannot load preferences: Supabase not configured")
        return {}
    
    try:
        res = (
            supabase.table("user_preferences")
            .select("preferences")
            .eq("user_id", user_id)
            .execute()
        )
        
        if res.data and len(res.data) > 0:
            prefs = res.data[0].get("preferences", {})
            logger.debug(f"✅ Loaded preferences for user {user_id[:8]}")
            return prefs if isinstance(prefs, dict) else {}
        
        logger.debug(f"No preferences found for user {user_id[:8]}")
        return {}
        
    except Exception as e:
        logger.error(f"Failed to load preferences: {e}", exc_info=True)
        return {}

def save_preference(key: str, value) -> bool:
    """
    Save a single preference key without overwriting others.
    
    Args:
        key: Preference key
        value: Value (will be JSON serialized)
    
    Returns:
        True if updated successfully
    """
    if not st.secrets.get("ENABLE_DATABASE", True):
        logger.debug("Database disabled - skipping save")
        return True
    
    prefs = load_preferences()
    prefs[key] = value
    return save_preferences(prefs)


def save_preferences(preferences: Dict) -> bool:
    """
    Save all preferences as a single JSON object.
    
    Args:
        preferences: Complete preferences dictionary
    
    Returns:
        True if saved successfully
    """
    # Check if database is enabled
    if not st.secrets.get("ENABLE_DATABASE", True):
        logger.debug("Database disabled - skipping save")
        return True
    
    user_id = get_current_user_id()
    if not user_id:
        logger.warning("Cannot save preferences: No user logged in")
        return False
    
    supabase = get_supabase_with_retry()
    if not supabase:
        logger.error("Cannot save preferences: Supabase not configured")
        return False
    
    if not preferences:
        return True
    
    try:
        # Upsert the entire preferences object
        supabase.table("user_preferences").upsert({
            "user_id": user_id,
            "preferences": preferences  # Store as JSONB
        }).execute()
        
        logger.info(f"✅ Saved preferences for user {user_id[:8]}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to save preferences: {e}", exc_info=True)
        return False


def update_preference(key: str, value) -> bool:
    """
    Update a single preference key without overwriting others.
    
    Args:
        key: Preference key
        value: Value (will be JSON serialized)
    
    Returns:
        True if updated successfully
    """
    prefs = load_preferences()
    prefs[key] = value
    return save_preferences(prefs)


def delete_all_preferences() -> bool:
    """Delete ALL preferences for the current user."""
    if not st.secrets.get("ENABLE_DATABASE", True):
        return True
    
    user_id = get_current_user_id()
    if not user_id:
        return False
    
    supabase = get_supabase_with_retry()
    if not supabase:
        return False
    
    try:
        supabase.table("user_preferences").delete().eq("user_id", user_id).execute()
        logger.info(f"✅ Deleted all preferences for user {user_id[:8]}")
        return True
    except Exception as e:
        logger.error(f"Failed to delete preferences: {e}", exc_info=True)
        return False


# ═══════════════════════════════════════════════════════════════════════════
# CHAT HISTORY MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════

def save_chat_message(user_message: str, bot_response: str, intent: str = "") -> bool:
    """Save a chat exchange to the user's history."""
    if not st.secrets.get("ENABLE_DATABASE", True):
        logger.debug("Database disabled - skipping chat save")
        return True
    
    user_id = get_current_user_id()
    if not user_id:
        logger.debug("Cannot save chat: No user logged in")
        return False
    
    supabase = get_supabase_with_retry()
    if not supabase:
        logger.error("Cannot save chat: Supabase not configured")
        return False
    
    try:
        supabase.table("chat_history").insert({
            "user_id": user_id,
            "user_message": user_message[:1000],
            "bot_response": bot_response[:5000],
            "intent": intent,
        }).execute()
        
        logger.debug(f"✅ Saved chat message for user {user_id[:8]}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to save chat message: {e}", exc_info=True)
        return False


def load_chat_history(limit: int = 50) -> List[Dict]:
    """Load the most recent chat messages."""
    if not st.secrets.get("ENABLE_DATABASE", True):
        logger.debug("Database disabled - returning empty history")
        return []
    
    user_id = get_current_user_id()
    if not user_id:
        return []
    
    supabase = get_supabase_with_retry()
    if not supabase:
        return []
    
    try:
        res = (
            supabase.table("chat_history")
            .select("user_message, bot_response, intent, created_at")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        
        messages = list(reversed(res.data or []))
        logger.debug(f"✅ Loaded {len(messages)} chat messages")
        return messages
        
    except Exception as e:
        logger.error(f"Failed to load chat history: {e}", exc_info=True)
        return []


def get_chat_history_count() -> int:
    """Get total number of chat messages."""
    if not st.secrets.get("ENABLE_DATABASE", True):
        return 0
    
    user_id = get_current_user_id()
    if not user_id:
        return 0
    
    supabase = get_supabase_with_retry()
    if not supabase:
        return 0
    
    try:
        res = (
            supabase.table("chat_history")
            .select("id", count="exact")
            .eq("user_id", user_id)
            .execute()
        )
        return res.count or 0
    except Exception as e:
        logger.error(f"Failed to get chat count: {e}", exc_info=True)
        return 0


def delete_chat_history() -> bool:
    """Delete ALL chat history."""
    if not st.secrets.get("ENABLE_DATABASE", True):
        return True
    
    user_id = get_current_user_id()
    if not user_id:
        return False
    
    supabase = get_supabase_with_retry()
    if not supabase:
        return False
    
    try:
        supabase.table("chat_history").delete().eq("user_id", user_id).execute()
        logger.info(f"✅ Deleted all chat history for user {user_id[:8]}")
        return True
    except Exception as e:
        logger.error(f"Failed to delete chat history: {e}", exc_info=True)
        return False


# ═══════════════════════════════════════════════════════════════════════════
# ANALYTICS & STATS
# ═══════════════════════════════════════════════════════════════════════════

def get_user_stats() -> Dict:
    """
    Get comprehensive user statistics.
    
    Returns:
        Dictionary with user stats
    """
    if not st.secrets.get("ENABLE_DATABASE", True):
        return {}
    
    user_id = get_current_user_id()
    if not user_id:
        return {}
    
    supabase = get_supabase_with_retry()
    if not supabase:
        return {}
    
    try:
        # Get total message count
        result = supabase.table("chat_history")\
            .select("*", count="exact")\
            .eq("user_id", user_id)\
            .execute()
        
        total_messages = result.count if hasattr(result, 'count') else len(result.data)
        
        # Get unique days active
        messages = result.data
        if messages:
            dates = set()
            for msg in messages:
                created_at = msg.get("created_at", "")
                if created_at:
                    date = created_at.split("T")[0]
                    dates.add(date)
            
            days_active = len(dates)
        else:
            days_active = 0
        
        # Get preferences count
        prefs = load_preferences()
        total_preferences = len(prefs)
        
        return {
            "total_messages": total_messages,
            "days_active": days_active,
            "total_preferences": total_preferences
        }
        
    except Exception as e:
        logger.error(f"Failed to get user stats: {e}", exc_info=True)
        return {}


def export_user_data() -> Dict:
    """
    Export all user data for download.
    
    Returns:
        Dictionary with all user data
    """
    user_id = get_current_user_id()
    
    return {
        "user_id": user_id,
        "exported_at": datetime.now().isoformat(),
        "preferences": load_preferences(),
        "chat_history": load_chat_history(limit=1000),
        "stats": get_user_stats()
    }


# ═══════════════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════


def delete_all_user_data() -> bool:
    """Delete EVERYTHING for the current user."""
    prefs_deleted = delete_all_preferences()
    history_deleted = delete_chat_history()
    return prefs_deleted and history_deleted