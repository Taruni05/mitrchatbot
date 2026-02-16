"""
AI Preference Learning System
Learns and adapts to user preferences across sessions using local storage
"""
import streamlit as st
from datetime import datetime, timedelta
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from collections import defaultdict, Counter
import hashlib
from services.logger import get_logger
from services.config import config
from services.user_store import load_preferences, save_preference,save_preferences

logger = get_logger(__name__)

# ═══════════════════════════════════════════════════════════════════════════
# USER IDENTIFICATION & SESSION MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════

def get_user_id() -> str:
    """Get user ID from auth system"""
    from services.auth import get_current_user_id
    user_id = get_current_user_id()
    if not user_id:
        # Fallback for non-logged-in users (shouldn't happen with auth gate)
        import secrets
        return secrets.token_hex(16)
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
    "frequent_areas": [],  # Most queried areas
    "home_area": None,  # Detected home location
    "work_area": None,  # Detected work location
    
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
        "cuisines": [],  # ["biryani", "irani chai", etc.]
        "price_range": "medium",  # "budget", "medium", "premium"
        "dietary": []  # ["vegetarian", "halal", etc.]
    },
    
    "transport_preferences": {
        "modes": [],  # ["metro", "bus", "cab"]
        "frequent_routes": []  # [(from, to, mode), ...]
    },
    
    "tourism_preferences": {
        "types": [],  # ["monuments", "parks", "malls"]
        "crowd_tolerance": "medium"  # "low", "medium", "high"
    },
    
    # Language preference
    "language": "en",  # "en", "te", "hi", "ur"
    
    # Behavioral patterns
    "active_hours": {  # Hour of day -> count
        str(i): 0 for i in range(24)
    },
    "active_days": {  # Day of week -> count
        "monday": 0, "tuesday": 0, "wednesday": 0, "thursday": 0,
        "friday": 0, "saturday": 0, "sunday": 0
    },
    
    # Query history (last 50 queries)
    "query_history": [],
    
    # Personalization scores
    "personalization_enabled": True,
    "personalization_score": 0.0,  # 0-1, higher = more personalized
}


# ═══════════════════════════════════════════════════════════════════════════
# PREFERENCE STORAGE (Local JSON files)
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
    """Load user preferences from database"""
    from services.user_store import load_preferences as load_prefs_from_db
    
    prefs = load_prefs_from_db()
    
    if not prefs:
        # Return default preferences for new users
        return DEFAULT_PREFERENCES.copy()
    
    # Merge with defaults to ensure all keys exist
    merged = DEFAULT_PREFERENCES.copy()
    merged.update(prefs)
    return merged



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
        preferences: Current preferences dict (if None, loads from file)
    
    Returns:
        Updated preferences dict
    """
    if preferences is None:
        preferences = load_user_preferences()
    
    query_lower = query.lower()
    
    # Increment total interactions
    preferences["total_interactions"] += 1
    
    # Update active hours
    current_hour = datetime.now().hour
    preferences["active_hours"][str(current_hour)] += 1
    
    # Update active days
    day_name = datetime.now().strftime("%A").lower()
    if day_name in preferences["active_days"]:
        preferences["active_days"][day_name] += 1
    
    # Update interests based on intent
    if intent in preferences["interests"]:
        preferences["interests"][intent] += 1
    
    # Add to query history (keep last 50)
    preferences["query_history"].append({
        "query": query[:100],  # Truncate for privacy
        "intent": intent,
        "timestamp": datetime.now().isoformat()
    })
    preferences["query_history"] = preferences["query_history"][-50:]
    
    # Learn location preferences
    preferences = learn_location_preferences(query_lower, preferences)
    
    # Learn food preferences
    if intent == "food":
        preferences = learn_food_preferences(query_lower, preferences)
    
    # Learn transport preferences
    if intent == "transport":
        preferences = learn_transport_preferences(query_lower, preferences)
    
    # Learn tourism preferences
    if intent == "tourism":
        preferences = learn_tourism_preferences(query_lower, preferences)
    
    # Update personalization score
    preferences = update_personalization_score(preferences)
    
    # Save updated preferences
    save_user_preferences(preferences)
    
    return preferences


def learn_location_preferences(query: str, preferences: Dict) -> Dict:
    """Learn frequent areas from queries"""
    from services.locations import HYDERABAD_AREA_COORDS
    
    # Check for area mentions in query
    for area in HYDERABAD_AREA_COORDS.keys():
        if area.lower() in query:
            # Add to frequent areas
            if area not in preferences["frequent_areas"]:
                preferences["frequent_areas"].append(area)
            
            # Move to front (most recent)
            preferences["frequent_areas"].remove(area)
            preferences["frequent_areas"].insert(0, area)
            
            # Keep only top 10
            preferences["frequent_areas"] = preferences["frequent_areas"][:10]
            
            # Detect home/work areas based on query patterns
            # Home: mentioned during evening/night hours
            # Work: mentioned during morning/afternoon hours
            hour = datetime.now().hour
            if 18 <= hour or hour < 6:  # Evening/night
                if not preferences["home_area"]:
                    preferences["home_area"] = area
            elif 9 <= hour < 18:  # Work hours
                if not preferences["work_area"] or preferences["work_area"] != preferences["home_area"]:
                    preferences["work_area"] = area
    
    return preferences


def learn_food_preferences(query: str, preferences: Dict) -> Dict:
    """Learn food preferences from queries"""
    food_prefs = preferences["food_preferences"]
    
    # Detect cuisines
    cuisines = ["biryani", "haleem", "irani chai", "dosa", "idli", "north indian", 
                "chinese", "pizza", "burger", "kebab", "tandoori"]
    
    for cuisine in cuisines:
        if cuisine in query:
            if cuisine not in food_prefs["cuisines"]:
                food_prefs["cuisines"].append(cuisine)
    
    # Detect price preferences
    if any(word in query for word in ["cheap", "budget", "affordable"]):
        food_prefs["price_range"] = "budget"
    elif any(word in query for word in ["expensive", "premium", "luxury", "fine dining"]):
        food_prefs["price_range"] = "premium"
    
    # Detect dietary preferences
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
    transport_prefs = preferences["transport_preferences"]
    
    # Detect preferred modes
    modes = {
        "metro": ["metro", "train"],
        "bus": ["bus", "rtc"],
        "cab": ["ola", "uber", "cab", "taxi"],
        "auto": ["auto", "rickshaw"]
    }
    
    for mode, keywords in modes.items():
        if any(kw in query for kw in keywords):
            if mode not in transport_prefs["modes"]:
                transport_prefs["modes"].append(mode)
    
    # Detect frequent routes (from X to Y pattern)
    import re
    route_pattern = r'from\s+([a-z\s]+?)\s+to\s+([a-z\s]+)'
    match = re.search(route_pattern, query)
    if match:
        from_place = match.group(1).strip()
        to_place = match.group(2).strip()
        
        # Add to frequent routes
        route = (from_place, to_place, transport_prefs["modes"][0] if transport_prefs["modes"] else "metro")
        if route not in transport_prefs["frequent_routes"]:
            transport_prefs["frequent_routes"].append(route)
        
        # Keep only last 5 routes
        transport_prefs["frequent_routes"] = transport_prefs["frequent_routes"][-5:]
    
    preferences["transport_preferences"] = transport_prefs
    return preferences


def learn_tourism_preferences(query: str, preferences: Dict) -> Dict:
    """Learn tourism preferences from queries"""
    tourism_prefs = preferences["tourism_preferences"]
    
    # Detect tourism types
    types = {
        "monuments": ["charminar", "golconda", "qutub shahi", "monument", "fort"],
        "parks": ["park", "garden", "lake", "hussain sagar"],
        "malls": ["mall", "shopping", "inorbit", "gvk"],
        "museums": ["museum", "gallery", "salar jung"],
        "temples": ["temple", "birla mandir"]
    }
    
    for tourism_type, keywords in types.items():
        if any(kw in query for kw in keywords):
            if tourism_type not in tourism_prefs["types"]:
                tourism_prefs["types"].append(tourism_type)
    
    # Detect crowd tolerance
    if any(word in query for word in ["quiet", "peaceful", "less crowd", "empty"]):
        tourism_prefs["crowd_tolerance"] = "low"
    elif any(word in query for word in ["popular", "famous", "crowded"]):
        tourism_prefs["crowd_tolerance"] = "high"
    
    preferences["tourism_preferences"] = tourism_prefs
    return preferences


def update_personalization_score(preferences: Dict) -> Dict:
    """
    Calculate personalization score based on data collected.
    Higher score = more personalized recommendations possible.
    
    Score factors:
    - Number of interactions
    - Variety of interests
    - Frequency of specific areas
    - Consistency of patterns
    """
    score = 0.0
    
    # Interaction count (max 0.3)
    interactions = preferences["total_interactions"]
    score += min(interactions / 100, 0.3)
    
    # Interest diversity (max 0.2)
    active_interests = sum(1 for v in preferences["interests"].values() if v > 0)
    score += (active_interests / len(preferences["interests"])) * 0.2
    
    # Location data (max 0.2)
    if preferences["frequent_areas"]:
        score += 0.1
    if preferences["home_area"] or preferences["work_area"]:
        score += 0.1
    
    # Category-specific preferences (max 0.3)
    if preferences["food_preferences"]["cuisines"]:
        score += 0.1
    if preferences["transport_preferences"]["modes"]:
        score += 0.1
    if preferences["tourism_preferences"]["types"]:
        score += 0.1
    
    preferences["personalization_score"] = min(score, 1.0)
    return preferences


# ═══════════════════════════════════════════════════════════════════════════
# PERSONALIZED RECOMMENDATIONS
# ═══════════════════════════════════════════════════════════════════════════

def get_personalized_suggestions(preferences: Dict = None) -> List[str]:
    """
    Generate personalized suggestions based on user preferences.
    
    Args:
        preferences: User preferences dict (if None, loads from file)
    
    Returns:
        List of personalized suggestion strings
    """
    if preferences is None:
        preferences = load_user_preferences()
    
    suggestions = []
    
    # If personalization score is low, return generic suggestions
    if preferences["personalization_score"] < 0.2:
        return [
            "🍛 Explore famous biryani places",
            "🚇 Check metro routes",
            "🏛️ Visit Charminar",
            "🌦️ Today's weather",
            "📰 Latest Hyderabad news"
        ]
    
    # Personalized based on interests
    top_interests = sorted(
        preferences["interests"].items(),
        key=lambda x: x[1],
        reverse=True
    )[:3]
    
    for interest, count in top_interests:
        if count > 0:
            if interest == "food":
                if preferences["food_preferences"]["cuisines"]:
                    cuisine = preferences["food_preferences"]["cuisines"][0]
                    suggestions.append(f"🍛 New {cuisine} restaurants nearby")
                else:
                    suggestions.append("🍽️ Food recommendations for you")
            
            elif interest == "transport":
                if preferences["transport_preferences"]["frequent_routes"]:
                    from_place, to_place, _ = preferences["transport_preferences"]["frequent_routes"][0]
                    suggestions.append(f"🚇 Quick route: {from_place} to {to_place}")
                else:
                    suggestions.append("🚌 Check bus/metro routes")
            
            elif interest == "tourism":
                if preferences["tourism_preferences"]["types"]:
                    place_type = preferences["tourism_preferences"]["types"][0]
                    suggestions.append(f"🏛️ Explore {place_type}")
                else:
                    suggestions.append("🎡 Tourist attractions nearby")
            
            elif interest == "news":
                suggestions.append("📰 Latest Hyderabad updates")
            
            elif interest == "weather":
                suggestions.append("🌦️ Weather forecast")
    
    # Add location-specific suggestions
    if preferences["frequent_areas"]:
        top_area = preferences["frequent_areas"][0]
        suggestions.append(f"📍 What's happening in {top_area}")
    
    return suggestions[:5]  # Return max 5 suggestions


def get_personalized_greeting(preferences: Dict = None) -> str:
    """Generate a personalized greeting message"""
    if preferences is None:
        preferences = load_user_preferences()
    
    hour = datetime.now().hour
    interactions = preferences["total_interactions"]
    
    # Time-based greeting
    if hour < 12:
        time_greeting = "Good morning"
    elif hour < 18:
        time_greeting = "Good afternoon"
    else:
        time_greeting = "Good evening"
    
    # Personalization level
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
    Enhance a response with personalized touches.
    
    Args:
        response: Original response text
        preferences: User preferences
    
    Returns:
        Enhanced response with personalization
    """
    if preferences is None:
        preferences = load_user_preferences()
    
    # If personalization is disabled or score is too low, return as-is
    if not preferences.get("personalization_enabled") or preferences["personalization_score"] < 0.3:
        return response
    
    # Add personalized footer based on context
    enhancements = []
    
    # Add area-specific tip if relevant
    if preferences["frequent_areas"]:
        top_area = preferences["frequent_areas"][0]
        if top_area.lower() not in response.lower():
            enhancements.append(f"\n\n💡 *Psst! I noticed you're often in {top_area}. Want recommendations for that area?*")
    
    # Add preference-based tip
    top_interest = max(preferences["interests"].items(), key=lambda x: x[1])[0]
    if top_interest not in response.lower():
        interest_tips = {
            "food": "Try asking me for food recommendations!",
            "transport": "Need help with routes? Just ask!",
            "tourism": "Want to explore new places? I can suggest!",
            "shopping": "Looking for malls or markets? I know them all!"
        }
        if top_interest in interest_tips:
            enhancements.append(f"\n💫 *{interest_tips[top_interest]}*")
    
    # Add one enhancement max to avoid clutter
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
    """Update preferences in session state and save to file"""
    st.session_state["user_preferences"] = preferences
    save_user_preferences(preferences)


# ═══════════════════════════════════════════════════════════════════════════
# PRIVACY & DATA MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════

def clear_user_data(user_id: str = None):
    """
    Clear all stored data for a user.
    
    Args:
        user_id: User ID (if None, uses current session user)
    """
    if not user_id:
        user_id = get_user_id()
    
    prefs_file = get_user_preferences_file(user_id)
    
    if prefs_file.exists():
        prefs_file.unlink()
        print(f"[ai_preferences] Cleared data for user {user_id}")
    
    # Clear from session state
    if "user_preferences" in st.session_state:
        del st.session_state["user_preferences"]


def export_user_data(user_id: str = None) -> Dict:
    """
    Export all user data for download/backup.
    
    Args:
        user_id: User ID (if None, uses current session user)
    
    Returns:
        Complete user preferences dict
    """
    if not user_id:
        user_id = get_user_id()
    
    return load_user_preferences(user_id)


def get_privacy_summary(preferences: Dict = None) -> str:
    """Get a summary of what data is being collected"""
    if preferences is None:
        preferences = load_user_preferences()
    
    summary = "🔒 **Your Privacy & Data**\n\n"
    summary += "We collect the following to personalize your experience:\n\n"
    summary += f"✅ **Interactions:** {preferences['total_interactions']} queries processed\n"
    summary += f"✅ **Interests:** {sum(1 for v in preferences['interests'].values() if v > 0)} categories identified\n"
    summary += f"✅ **Locations:** {len(preferences['frequent_areas'])} areas you've asked about\n"
    summary += f"✅ **Personalization Level:** {int(preferences['personalization_score'] * 100)}%\n\n"
    
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