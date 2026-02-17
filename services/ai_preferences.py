"""
AI Preference Learning System
Learns and adapts to user preferences across sessions using local storage
"""
import streamlit as st
from datetime import datetime, timedelta
import copy
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from collections import defaultdict, Counter
from services.logger import get_logger
from services.config import config
from services.user_store import load_preferences, save_preference, save_preferences

logger = get_logger(__name__)

# ═══════════════════════════════════════════════════════════════════════════
# USER IDENTIFICATION & SESSION MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════

def get_user_id() -> str:
    """Get user ID from auth system"""
    from services.auth import get_current_user_id
    user_id = get_current_user_id()
    if not user_id:
        # FIX: store generated anon ID in session_state so the same session
        # always gets the same ID (original code returned a fresh token each call)
        if "anon_user_id" not in st.session_state:
            import secrets
            st.session_state.anon_user_id = secrets.token_hex(16)
        return st.session_state.anon_user_id
    return user_id


# ═══════════════════════════════════════════════════════════════════════════
# PREFERENCE DATA STRUCTURE
# ═══════════════════════════════════════════════════════════════════════════

DEFAULT_PREFERENCES = {
    "user_id": None,
    "created_at": None,
    "last_active": None,
    "total_interactions": 0,

    # Location preferences
    "frequent_areas": [],
    "home_area": None,
    "work_area": None,

    # Interest categories (scored by frequency)
    "interests": {
        "food": 0,
        "transport": 0,
        "tourism": 0,
        "shopping": 0,
        "entertainment": 0,
        "news": 0,
        "weather": 0,
        "utilities": 0,
        "sports": 0,
        "healthcare": 0
    },

    # Specific preferences within categories
    "food_preferences": {
        "cuisines": [],
        "price_range": "medium",
        "dietary": []
    },

    "transport_preferences": {
        "modes": [],
        "frequent_routes": []
    },

    "tourism_preferences": {
        "types": [],
        "crowd_tolerance": "medium"
    },

    # Language preference
    "language": "en",

    # Behavioral patterns
    "active_hours": {str(i): 0 for i in range(24)},
    "active_days": {
        "monday": 0, "tuesday": 0, "wednesday": 0, "thursday": 0,
        "friday": 0, "saturday": 0, "sunday": 0
    },

    # Query history (last 50 queries)
    "query_history": [],

    # Personalization scores
    "personalization_enabled": True,
    "personalization_score": 0.0,   # 0–1, higher = more personalised
}


# ═══════════════════════════════════════════════════════════════════════════
# DEEP MERGE HELPER
# ═══════════════════════════════════════════════════════════════════════════

def _deep_merge(base: Dict, override: Dict) -> Dict:
    """
    Recursively merge *override* into a deep copy of *base*.

    - Dict values are merged key-by-key so nested keys added to DEFAULT_PREFERENCES
      in newer versions are never silently dropped.
    - Non-dict values from *override* win outright.
    """
    result = copy.deepcopy(base)
    for key, val in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(val, dict):
            result[key] = _deep_merge(result[key], val)
        else:
            result[key] = val
    return result


# ═══════════════════════════════════════════════════════════════════════════
# PREFERENCE STORAGE
# ═══════════════════════════════════════════════════════════════════════════

def get_preferences_dir() -> Path:
    """Get or create preferences storage directory"""
    prefs_dir = Path(config.app.USER_PREFS_DIR)
    prefs_dir.mkdir(exist_ok=True)
    return prefs_dir


def get_user_preferences_file(user_id: str) -> Path:
    """Get path to user's preferences file"""
    prefs_dir = get_preferences_dir()
    return prefs_dir / f"{user_id}.json"


def load_user_preferences(user_id: str = None) -> Dict:
    """
    Load user preferences from the database.

    FIX (shallow-merge bug): use _deep_merge so nested dicts (interests,
    food_preferences, …) always contain every key defined in DEFAULT_PREFERENCES,
    even after the defaults have been extended in a newer version of the code.
    """
    from services.user_store import load_preferences as load_prefs_from_db

    prefs = load_prefs_from_db()

    if not prefs:
        return copy.deepcopy(DEFAULT_PREFERENCES)

    # Deep merge: defaults supply missing keys, user data wins on conflicts
    return _deep_merge(DEFAULT_PREFERENCES, prefs)


def save_user_preferences(preferences: Dict, user_id: str = None):
    """Save user preferences to database"""
    from services.user_store import save_preferences as save_prefs_to_db
    save_prefs_to_db(preferences)


# ═══════════════════════════════════════════════════════════════════════════
# PREFERENCE LEARNING FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def learn_from_query(query: str, intent: str, preferences: Dict = None) -> Dict:
    """
    Update preferences based on user query and detected intent.

    Args:
        query: User's query text
        intent: Detected intent (food/transport/tourism/etc.)
        preferences: Current preferences dict (loads from DB if None)

    Returns:
        Updated preferences dict
    """
    if preferences is None:
        preferences = load_user_preferences()

    query_lower = query.lower()

    # Increment total interactions
    preferences["total_interactions"] = preferences.get("total_interactions", 0) + 1

    # --- active_hours -------------------------------------------------------
    # FIX: was preferences.get("active_hours", False)[str(hour)] += 1
    # .get(key, False) returns False when missing; False is not subscriptable.
    # Use direct access — _deep_merge guarantees the key exists.
    current_hour = datetime.now().hour
    preferences["active_hours"][str(current_hour)] = (
        preferences["active_hours"].get(str(current_hour), 0) + 1
    )

    # --- active_days --------------------------------------------------------
    # FIX: was preferences.get("active_days", False)[day_name] += 1
    day_name = datetime.now().strftime("%A").lower()
    if day_name in preferences["active_days"]:
        preferences["active_days"][day_name] = (
            preferences["active_days"].get(day_name, 0) + 1
        )

    # --- interests ----------------------------------------------------------
    # FIX: was preferences.get("interests", None)[intent] += 1
    # None is not subscriptable.  Use direct access with a safe default.
    if intent in preferences["interests"]:
        preferences["interests"][intent] = preferences["interests"].get(intent, 0) + 1

    # --- query_history ------------------------------------------------------
    # FIX: was preferences.get("query_history", []).append(…) — the temporary
    # [] was discarded without being written back.  Access the key directly.
    preferences["query_history"].append({
        "query": query[:100],
        "intent": intent,
        "timestamp": datetime.now().isoformat()
    })
    preferences["query_history"] = preferences["query_history"][-50:]

    # Learn derived preferences
    preferences = learn_location_preferences(query_lower, preferences)

    if intent == "food":
        preferences = learn_food_preferences(query_lower, preferences)

    if intent == "transport":
        preferences = learn_transport_preferences(query_lower, preferences)

    if intent == "tourism":
        preferences = learn_tourism_preferences(query_lower, preferences)

    preferences = update_personalization_score(preferences)
    save_user_preferences(preferences)

    return preferences


def learn_location_preferences(query: str, preferences: Dict) -> Dict:
    """Learn frequent areas from queries"""
    from services.locations import HYDERABAD_AREA_COORDS

    for area in HYDERABAD_AREA_COORDS.keys():
        if area.lower() in query:
            # FIX: was preferences.get("frequent_areas", None).append(area)
            # Direct access is safe; _deep_merge guarantees the list exists.
            frequent_areas: List = preferences["frequent_areas"]

            if area in frequent_areas:
                frequent_areas.remove(area)
            frequent_areas.insert(0, area)          # move-to-front (most recent)
            preferences["frequent_areas"] = frequent_areas[:10]

            hour = datetime.now().hour
            if 18 <= hour or hour < 6:
                if not preferences.get("home_area"):
                    preferences["home_area"] = area
            elif 9 <= hour < 18:
                if (not preferences.get("work_area")
                        or preferences["work_area"] != preferences.get("home_area")):
                    preferences["work_area"] = area

    return preferences


def learn_food_preferences(query: str, preferences: Dict) -> Dict:
    """Learn food preferences from queries"""
    # FIX: was preferences.get("food_preferences", None)
    # None has no .get() method → AttributeError.  Direct access is safe.
    food_prefs: Dict = preferences["food_preferences"]

    cuisines = [
        "biryani", "haleem", "irani chai", "dosa", "idli",
        "north indian", "chinese", "pizza", "burger", "kebab", "tandoori"
    ]

    for cuisine in cuisines:
        if cuisine in query:
            # FIX: was food_prefs.get("cuisines", None).append(cuisine)
            if cuisine not in food_prefs["cuisines"]:
                food_prefs["cuisines"].append(cuisine)

    if any(word in query for word in ["cheap", "budget", "affordable"]):
        food_prefs["price_range"] = "budget"
    elif any(word in query for word in ["expensive", "premium", "luxury", "fine dining"]):
        food_prefs["price_range"] = "premium"

    # FIX: was food_prefs.get("dietary", None).append(...)
    if "vegetarian" in query or "veg" in query:
        if "vegetarian" not in food_prefs["dietary"]:
            food_prefs["dietary"].append("vegetarian")

    if "halal" in query:
        if "halal" not in food_prefs["dietary"]:
            food_prefs["dietary"].append("halal")

    preferences["food_preferences"] = food_prefs
    return preferences


def learn_transport_preferences(query: str, preferences: Dict) -> Dict:
    """Learn transport preferences from queries"""
    # FIX: was preferences.get("transport_preferences", None)
    transport_prefs: Dict = preferences["transport_preferences"]

    modes_map = {
        "metro": ["metro", "train"],
        "bus":   ["bus", "rtc"],
        "cab":   ["ola", "uber", "cab", "taxi"],
        "auto":  ["auto", "rickshaw"]
    }

    for mode, keywords in modes_map.items():
        if any(kw in query for kw in keywords):
            # FIX: was transport_prefs.get("modes", None).append(mode)
            if mode not in transport_prefs["modes"]:
                transport_prefs["modes"].append(mode)

    import re
    route_pattern = r'from\s+([a-z\s]+?)\s+to\s+([a-z\s]+)'
    match = re.search(route_pattern, query)
    if match:
        from_place = match.group(1).strip()
        to_place   = match.group(2).strip()

        # FIX: was transport_prefs.get("modes", None)[0]
        # Safe fallback if modes list is empty
        default_mode = transport_prefs["modes"][0] if transport_prefs["modes"] else "metro"
        route = (from_place, to_place, default_mode)

        # FIX: was transport_prefs.get("frequent_routes", None).append(route)
        if route not in transport_prefs["frequent_routes"]:
            transport_prefs["frequent_routes"].append(route)
        transport_prefs["frequent_routes"] = transport_prefs["frequent_routes"][-5:]

    preferences["transport_preferences"] = transport_prefs
    return preferences


def learn_tourism_preferences(query: str, preferences: Dict) -> Dict:
    """Learn tourism preferences from queries"""
    # FIX: was preferences.get("tourism_preferences", None)
    tourism_prefs: Dict = preferences["tourism_preferences"]

    types_map = {
        "monuments": ["charminar", "golconda", "qutub shahi", "monument", "fort"],
        "parks":     ["park", "garden", "lake", "hussain sagar"],
        "malls":     ["mall", "shopping", "inorbit", "gvk"],
        "museums":   ["museum", "gallery", "salar jung"],
        "temples":   ["temple", "birla mandir"]
    }

    for tourism_type, keywords in types_map.items():
        if any(kw in query for kw in keywords):
            # FIX: was tourism_prefs.get("types", None).append(tourism_type)
            if tourism_type not in tourism_prefs["types"]:
                tourism_prefs["types"].append(tourism_type)

    if any(word in query for word in ["quiet", "peaceful", "less crowd", "empty"]):
        tourism_prefs["crowd_tolerance"] = "low"
    elif any(word in query for word in ["popular", "famous", "crowded"]):
        tourism_prefs["crowd_tolerance"] = "high"

    preferences["tourism_preferences"] = tourism_prefs
    return preferences


def update_personalization_score(preferences: Dict) -> Dict:
    """
    Calculate personalisation score (0–1) based on collected data.

    FIX: multiple .get(key, None).values() / .items() / len() calls replaced
    with direct key access (safe because _deep_merge guarantees all keys).
    """
    score = 0.0

    # Interaction count (max 0.3)
    interactions = preferences.get("total_interactions", 0)
    score += min(interactions / 100, 0.3)

    # Interest diversity (max 0.2)
    interests: Dict = preferences["interests"]
    active_interests = sum(1 for v in interests.values() if v > 0)
    if interests:
        score += (active_interests / len(interests)) * 0.2

    # Location data (max 0.2)
    if preferences["frequent_areas"]:
        score += 0.1
    if preferences.get("home_area") or preferences.get("work_area"):
        score += 0.1

    # Category-specific preferences (max 0.3)
    # FIX: was preferences.get("food_preferences", None)["cuisines"]
    if preferences["food_preferences"]["cuisines"]:
        score += 0.1
    if preferences["transport_preferences"]["modes"]:
        score += 0.1
    if preferences["tourism_preferences"]["types"]:
        score += 0.1

    preferences["personalization_score"] = round(min(score, 1.0), 4)
    return preferences


# ═══════════════════════════════════════════════════════════════════════════
# PERSONALIZED RECOMMENDATIONS
# ═══════════════════════════════════════════════════════════════════════════

def get_personalized_suggestions(preferences: Dict = None) -> List[str]:
    """
    Generate personalised suggestions based on user preferences.

    FIX (the reported crash): .get("personalization_score", None) returns None
    for a freshly-loaded user whose DB row has no score yet.  None < 0.2 raises
    TypeError.  Use a numeric default of 0.0 instead.
    """
    if preferences is None:
        preferences = load_user_preferences()

    # FIX: was preferences.get("personalization_score", None) < 0.2
    score: float = preferences.get("personalization_score") or 0.0

    if score < 0.2:
        return [
            "🍛 Explore famous biryani places",
            "🚇 Check metro routes",
            "🏛️ Visit Charminar",
            "🌦️ Today's weather",
            "📰 Latest Hyderabad news"
        ]

    suggestions: List[str] = []

    # FIX: was preferences.get("interests", None).items()
    top_interests = sorted(
        preferences["interests"].items(),
        key=lambda x: x[1],
        reverse=True
    )[:3]

    for interest, count in top_interests:
        if count <= 0:
            continue

        if interest == "food":
            # FIX: was preferences.get("food_preferences", None)["cuisines"]
            cuisines = preferences["food_preferences"]["cuisines"]
            if cuisines:
                suggestions.append(f"🍛 New {cuisines[0]} restaurants nearby")
            else:
                suggestions.append("🍽️ Food recommendations for you")

        elif interest == "transport":
            routes = preferences["transport_preferences"]["frequent_routes"]
            if routes:
                from_place, to_place, _ = routes[0]
                suggestions.append(f"🚇 Quick route: {from_place} to {to_place}")
            else:
                suggestions.append("🚌 Check bus/metro routes")

        elif interest == "tourism":
            types = preferences["tourism_preferences"]["types"]
            if types:
                suggestions.append(f"🏛️ Explore {types[0]}")
            else:
                suggestions.append("🎡 Tourist attractions nearby")

        elif interest == "news":
            suggestions.append("📰 Latest Hyderabad updates")

        elif interest == "weather":
            suggestions.append("🌦️ Weather forecast")

    # Add location-specific suggestion
    # FIX: was preferences.get("frequent_areas", None)[0]
    if preferences["frequent_areas"]:
        top_area = preferences["frequent_areas"][0]
        suggestions.append(f"📍 What's happening in {top_area}")

    return suggestions[:5]


def get_personalized_greeting(preferences: Dict = None) -> str:
    """Generate a personalized greeting message"""
    if preferences is None:
        preferences = load_user_preferences()

    hour = datetime.now().hour
    interactions = preferences.get("total_interactions", 0)

    if hour < 12:
        time_greeting = "Good morning"
    elif hour < 18:
        time_greeting = "Good afternoon"
    else:
        time_greeting = "Good evening"

    if interactions == 0:
        return f"{time_greeting}! Welcome to Hyderabad City Guide! 👋"
    elif interactions < 5:
        return f"{time_greeting}! Great to see you again! 😊"
    elif interactions < 20:
        return f"{time_greeting}! I'm learning your preferences to help you better! 🎯"
    else:
        return f"{time_greeting}! I've got some personalized suggestions for you today! ✨"


def apply_personalization_to_response(response: str, preferences: Dict = None) -> str:
    """
    Enhance a response with personalised touches.

    FIX: was preferences.get("personalization_score", None) < 0.3 — same
    None-comparison crash as in get_personalized_suggestions.
    """
    if preferences is None:
        preferences = load_user_preferences()

    # FIX: use numeric default 0.0 so the comparison is always valid
    score: float = preferences.get("personalization_score") or 0.0

    if not preferences.get("personalization_enabled") or score < 0.3:
        return response

    enhancements: List[str] = []

    # FIX: was preferences.get("frequent_areas", None)
    if preferences["frequent_areas"]:
        top_area = preferences["frequent_areas"][0]
        if top_area.lower() not in response.lower():
            enhancements.append(
                f"\n\n💡 *Psst! I noticed you're often in {top_area}. "
                f"Want recommendations for that area?*"
            )

    # FIX: was max(preferences["interests"].items(), ...) — safe now via direct access
    interests: Dict = preferences["interests"]
    if interests:
        top_interest = max(interests.items(), key=lambda x: x[1])[0]
        if top_interest not in response.lower():
            interest_tips = {
                "food":      "Try asking me for food recommendations!",
                "transport": "Need help with routes? Just ask!",
                "tourism":   "Want to explore new places? I can suggest!",
                "shopping":  "Looking for malls or markets? I know them all!"
            }
            if top_interest in interest_tips:
                enhancements.append(f"\n💫 *{interest_tips[top_interest]}*")

    if enhancements:
        return response + enhancements[0]

    return response


# ═══════════════════════════════════════════════════════════════════════════
# SESSION STATE MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════

def initialize_preferences():
    """Initialize preferences in session state"""
    if "user_preferences" not in st.session_state:
        st.session_state["user_preferences"] = load_user_preferences()


def get_current_preferences() -> Dict:
    """Get current session preferences"""
    initialize_preferences()
    return st.session_state["user_preferences"]


def update_session_preferences(preferences: Dict):
    """Update preferences in session state and persist to DB"""
    st.session_state["user_preferences"] = preferences
    save_user_preferences(preferences)


# ═══════════════════════════════════════════════════════════════════════════
# PRIVACY & DATA MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════

def clear_user_data(user_id: str = None):
    """Clear all stored data for a user."""
    if not user_id:
        user_id = get_user_id()

    prefs_file = get_user_preferences_file(user_id)
    if prefs_file.exists():
        prefs_file.unlink()
        logger.info(f"[ai_preferences] Cleared data for user {user_id}")

    if "user_preferences" in st.session_state:
        del st.session_state["user_preferences"]


def export_user_data(user_id: str = None) -> Dict:
    """Export all user data for download/backup."""
    if not user_id:
        user_id = get_user_id()
    return load_user_preferences(user_id)


def get_privacy_summary(preferences: Dict = None) -> str:
    """Get a human-readable summary of what data is being collected."""
    if preferences is None:
        preferences = load_user_preferences()

    # FIX: was preferences['personalization_score'] * 100 — could be None
    score: float = preferences.get("personalization_score") or 0.0

    summary  = "🔒 **Your Privacy & Data**\n\n"
    summary += "We collect the following to personalize your experience:\n\n"
    summary += f"✅ **Interactions:** {preferences.get('total_interactions', 0)} queries processed\n"
    summary += (
        f"✅ **Interests:** "
        f"{sum(1 for v in preferences['interests'].values() if v > 0)} "
        f"categories identified\n"
    )
    summary += f"✅ **Locations:** {len(preferences['frequent_areas'])} areas you've asked about\n"
    summary += f"✅ **Personalization Level:** {int(score * 100)}%\n\n"

    summary += "**What we DON'T collect:**\n"
    summary += "❌ Personal information (name, phone, email)\n"
    summary += "❌ Exact locations or GPS data\n"
    summary += "❌ Private messages or sensitive data\n\n"

    summary += "**Your Control:**\n"
    summary += "• Turn off personalization anytime\n"
    summary += "• Export your data\n"
    summary += "• Clear all stored preferences\n\n"

    summary += "All data is stored locally and never shared with third parties."
    return summary