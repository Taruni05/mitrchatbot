"""
User data service — saves and loads per-user preferences and chat history.
All data is stored in Supabase and tied to the authenticated user.
"""
import streamlit as st
from typing import Dict, List, Optional
from datetime import datetime
from services.auth import get_supabase, get_current_user_id
from services.logger import get_logger

logger = get_logger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# PREFERENCES MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════

def save_preference(key: str, value: str) -> bool:
    """
    Save a single preference for the current user.
    Uses upsert to update if exists, insert if new.
    
    Args:
        key: Preference key (e.g., "language", "favorite_area")
        value: Preference value (will be converted to string)
    
    Returns:
        True if saved successfully, False otherwise
    
    Example:
        save_preference("language", "te")
        save_preference("food_preference", "biryani")
    """
    user_id = get_current_user_id()
    if not user_id:
        logger.warning("Cannot save preference: No user logged in")
        return False
    
    supabase = get_supabase()
    if not supabase:
        logger.error("Cannot save preference: Supabase not configured")
        return False
    
    try:
        supabase.table("user_preferences").upsert({
            "user_id": user_id,
            "preference_key": key,
            "preference_value": str(value),
        }).execute()
        
        logger.debug(f"✅ Saved preference for user {user_id[:8]}: {key} = {value}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to save preference {key}: {e}", exc_info=True)
        return False


def save_preferences(preferences: Dict[str, str]) -> bool:
    """
    Save multiple preferences at once.
    More efficient than calling save_preference() multiple times.
    
    Args:
        preferences: Dictionary of key-value pairs to save
    
    Returns:
        True if all saved successfully, False otherwise
    
    Example:
        save_preferences({
            "language": "te",
            "food_preference": "biryani",
            "home_area": "Gachibowli"
        })
    """
    user_id = get_current_user_id()
    if not user_id:
        logger.warning("Cannot save preferences: No user logged in")
        return False
    
    supabase = get_supabase()
    if not supabase:
        logger.error("Cannot save preferences: Supabase not configured")
        return False
    
    if not preferences:
        return True  # Nothing to save
    
    try:
        # Build list of records to upsert
        records = [
            {
                "user_id": user_id,
                "preference_key": key,
                "preference_value": str(value),
            }
            for key, value in preferences.items()
        ]
        
        supabase.table("user_preferences").upsert(records).execute()
        
        logger.info(f"✅ Saved {len(records)} preferences for user {user_id[:8]}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to save preferences: {e}", exc_info=True)
        return False


def load_preferences() -> Dict[str, str]:
    """
    Load all preferences for the current user.
    
    Returns:
        Dictionary of preference key-value pairs.
        Returns empty dict if not logged in or on error.
    
    Example:
        prefs = load_preferences()
        language = prefs.get("language", "en")
        food_pref = prefs.get("food_preference", "")
    """
    user_id = get_current_user_id()
    if not user_id:
        logger.debug("Cannot load preferences: No user logged in")
        return {}
    
    supabase = get_supabase()
    if not supabase:
        logger.error("Cannot load preferences: Supabase not configured")
        return {}
    
    try:
        res = (
            supabase.table("user_preferences")
            .select("preference_key, preference_value")
            .eq("user_id", user_id)
            .execute()
        )
        
        preferences = {
            row["preference_key"]: row["preference_value"]
            for row in (res.data or [])
        }
        
        logger.debug(f"✅ Loaded {len(preferences)} preferences for user {user_id[:8]}")
        return preferences
        
    except Exception as e:
        logger.error(f"Failed to load preferences: {e}", exc_info=True)
        return {}


def delete_preference(key: str) -> bool:
    """
    Delete a specific preference for the current user.
    
    Args:
        key: Preference key to delete
    
    Returns:
        True if deleted successfully, False otherwise
    """
    user_id = get_current_user_id()
    if not user_id:
        logger.warning("Cannot delete preference: No user logged in")
        return False
    
    supabase = get_supabase()
    if not supabase:
        logger.error("Cannot delete preference: Supabase not configured")
        return False
    
    try:
        supabase.table("user_preferences").delete().match({
            "user_id": user_id,
            "preference_key": key
        }).execute()
        
        logger.info(f"✅ Deleted preference for user {user_id[:8]}: {key}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to delete preference {key}: {e}", exc_info=True)
        return False


def delete_all_preferences() -> bool:
    """
    Delete ALL preferences for the current user.
    Use with caution!
    
    Returns:
        True if deleted successfully, False otherwise
    """
    user_id = get_current_user_id()
    if not user_id:
        logger.warning("Cannot delete preferences: No user logged in")
        return False
    
    supabase = get_supabase()
    if not supabase:
        logger.error("Cannot delete preferences: Supabase not configured")
        return False
    
    try:
        supabase.table("user_preferences").delete().eq("user_id", user_id).execute()
        
        logger.info(f"✅ Deleted all preferences for user {user_id[:8]}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to delete all preferences: {e}", exc_info=True)
        return False


# ═══════════════════════════════════════════════════════════════════════════
# CHAT HISTORY MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════

def save_chat_message(user_message: str, bot_response: str, intent: str = "") -> bool:
    """
    Save a chat exchange to the user's history.
    
    Args:
        user_message: What the user said/asked
        bot_response: What the bot replied
        intent: Detected intent (optional, for analytics)
    
    Returns:
        True if saved successfully, False otherwise
    """
    user_id = get_current_user_id()
    if not user_id:
        logger.debug("Cannot save chat: No user logged in")
        return False
    
    supabase = get_supabase()
    if not supabase:
        logger.error("Cannot save chat: Supabase not configured")
        return False
    
    try:
        supabase.table("chat_history").insert({
            "user_id": user_id,
            "user_message": user_message[:1000],  # Truncate to prevent huge messages
            "bot_response": bot_response[:5000],  # Truncate bot response too
            "intent": intent,
        }).execute()
        
        logger.debug(f"✅ Saved chat message for user {user_id[:8]}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to save chat message: {e}", exc_info=True)
        return False


def load_chat_history(limit: int = 50) -> List[Dict]:
    """
    Load the most recent chat messages for the current user.
    
    Args:
        limit: Maximum number of messages to retrieve (default: 50)
    
    Returns:
        List of chat message dicts, ordered oldest to newest.
        Each dict has: user_message, bot_response, intent, created_at
        
    Example:
        history = load_chat_history(limit=10)
        for msg in history:
            print(f"User: {msg['user_message']}")
            print(f"Bot: {msg['bot_response']}")
    """
    user_id = get_current_user_id()
    if not user_id:
        logger.debug("Cannot load chat history: No user logged in")
        return []
    
    supabase = get_supabase()
    if not supabase:
        logger.error("Cannot load chat history: Supabase not configured")
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
        
        # Reverse to get oldest-to-newest order (chat display order)
        messages = list(reversed(res.data or []))
        
        logger.debug(f"✅ Loaded {len(messages)} chat messages for user {user_id[:8]}")
        return messages
        
    except Exception as e:
        logger.error(f"Failed to load chat history: {e}", exc_info=True)
        return []


def get_chat_history_count() -> int:
    """
    Get total number of chat messages for the current user.
    
    Returns:
        Count of messages, or 0 if not logged in or on error
    """
    user_id = get_current_user_id()
    if not user_id:
        return 0
    
    supabase = get_supabase()
    if not supabase:
        return 0
    
    try:
        res = (
            supabase.table("chat_history")
            .select("id", count="exact")
            .eq("user_id", user_id)
            .execute()
        )
        
        count = res.count or 0
        logger.debug(f"Chat history count for user {user_id[:8]}: {count}")
        return count
        
    except Exception as e:
        logger.error(f"Failed to get chat history count: {e}", exc_info=True)
        return 0


def delete_chat_history() -> bool:
    """
    Delete ALL chat history for the current user.
    Use with caution!
    
    Returns:
        True if deleted successfully, False otherwise
    """
    user_id = get_current_user_id()
    if not user_id:
        logger.warning("Cannot delete chat history: No user logged in")
        return False
    
    supabase = get_supabase()
    if not supabase:
        logger.error("Cannot delete chat history: Supabase not configured")
        return False
    
    try:
        supabase.table("chat_history").delete().eq("user_id", user_id).execute()
        
        logger.info(f"✅ Deleted all chat history for user {user_id[:8]}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to delete chat history: {e}", exc_info=True)
        return False


def search_chat_history(query: str, limit: int = 20) -> List[Dict]:
    """
    Search through chat history for messages containing a query.
    
    Args:
        query: Search term
        limit: Maximum number of results
    
    Returns:
        List of matching chat messages
    """
    user_id = get_current_user_id()
    if not user_id:
        return []
    
    supabase = get_supabase()
    if not supabase:
        return []
    
    try:
        res = (
            supabase.table("chat_history")
            .select("user_message, bot_response, intent, created_at")
            .eq("user_id", user_id)
            .or_(f"user_message.ilike.%{query}%,bot_response.ilike.%{query}%")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        
        messages = res.data or []
        logger.debug(f"Found {len(messages)} chat messages matching '{query}'")
        return messages
        
    except Exception as e:
        logger.error(f"Failed to search chat history: {e}", exc_info=True)
        return []


# ═══════════════════════════════════════════════════════════════════════════
# ANALYTICS & STATS
# ═══════════════════════════════════════════════════════════════════════════

def get_user_stats() -> Dict:
    """
    Get usage statistics for the current user.
    
    Returns:
        Dictionary with stats like total_messages, favorite_intents, etc.
    """
    user_id = get_current_user_id()
    if not user_id:
        return {}
    
    supabase = get_supabase()
    if not supabase:
        return {}
    
    try:
        # Get total message count
        total_messages = get_chat_history_count()
        
        # Get preferences count
        prefs_res = (
            supabase.table("user_preferences")
            .select("id", count="exact")
            .eq("user_id", user_id)
            .execute()
        )
        total_preferences = prefs_res.count or 0
        
        # Get most common intents
        intents_res = (
            supabase.table("chat_history")
            .select("intent")
            .eq("user_id", user_id)
            .limit(100)
            .execute()
        )
        
        # Count intent frequencies
        from collections import Counter
        intents = [msg["intent"] for msg in (intents_res.data or []) if msg.get("intent")]
        intent_counts = Counter(intents)
        top_intents = intent_counts.most_common(5)
        
        return {
            "total_messages": total_messages,
            "total_preferences": total_preferences,
            "top_intents": top_intents,
            "user_id": user_id[:8]  # Truncated for privacy
        }
        
    except Exception as e:
        logger.error(f"Failed to get user stats: {e}", exc_info=True)
        return {}


# ═══════════════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def export_user_data() -> Dict:
    """
    Export all user data (preferences + chat history) for download/backup.
    
    Returns:
        Dictionary with all user data
    """
    return {
        "preferences": load_preferences(),
        "chat_history": load_chat_history(limit=1000),  # Get more for export
        "stats": get_user_stats(),
        "exported_at": datetime.now().isoformat()
    }


def delete_all_user_data() -> bool:
    """
    Delete EVERYTHING for the current user.
    This includes preferences and chat history.
    Use with extreme caution!
    
    Returns:
        True if all deleted successfully, False otherwise
    """
    prefs_deleted = delete_all_preferences()
    history_deleted = delete_chat_history()
    
    return prefs_deleted and history_deleted