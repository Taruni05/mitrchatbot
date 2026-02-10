"""
Power-Cut & Water-Supply Alerts Service
Provides real-time utility outage information for Hyderabad areas
"""
import streamlit as st
from datetime import datetime, timedelta
import json
from pathlib import Path
from typing import Dict, List, Optional
import requests


# ═══════════════════════════════════════════════════════════════════════════
# FALLBACK DATA (Manual updates or cached from last successful fetch)
# ═══════════════════════════════════════════════════════════════════════════

FALLBACK_POWER_CUTS = {
    "timestamp": datetime.now().isoformat(),
    "areas": [
        {
            "area": "Gachibowli",
            "zone": "Cyberabad",
            "type": "planned",
            "start_time": "10:00 AM",
            "end_time": "2:00 PM",
            "date": "today",
            "reason": "Maintenance work",
            "affected_localities": ["Gachibowli Circle", "DLF Cyber City", "Wipro Circle"]
        },
        {
            "area": "HITEC City",
            "zone": "Cyberabad", 
            "type": "planned",
            "start_time": "11:00 AM",
            "end_time": "3:00 PM",
            "date": "today",
            "reason": "Transformer upgrade",
            "affected_localities": ["HITEC City Main Road", "Cyber Towers"]
        },
        {
            "area": "Kukatpally",
            "zone": "North",
            "type": "unplanned",
            "start_time": "8:00 AM",
            "end_time": "Unknown",
            "date": "today",
            "reason": "Technical fault",
            "affected_localities": ["KPHB Colony", "Kukatpally Housing Board"]
        }
    ]
}

FALLBACK_WATER_SUPPLY = {
    "timestamp": datetime.now().isoformat(),
    "areas": [
        {
            "area": "Dilsukhnagar",
            "zone": "South",
            "type": "reduced_supply",
            "schedule": "6:00 AM - 9:00 AM only",
            "date": "today",
            "reason": "Pipeline repair work",
            "affected_localities": ["Dilsukhnagar Main Road", "Moosarambagh"]
        },
        {
            "area": "Uppal",
            "zone": "East",
            "type": "no_supply",
            "schedule": "All day",
            "date": "today",
            "reason": "Pump breakdown",
            "affected_localities": ["Uppal Depot", "Ramanthapur"]
        },
        {
            "area": "Secunderabad",
            "zone": "North",
            "type": "reduced_supply",
            "schedule": "Morning hours only",
            "date": "today",
            "reason": "Reservoir maintenance",
            "affected_localities": ["Tarnaka", "Mettuguda"]
        }
    ]
}


# ═══════════════════════════════════════════════════════════════════════════
# DATA FETCHING (Web scraping or API integration)
# ═══════════════════════════════════════════════════════════════════════════

def fetch_live_power_cuts() -> Dict:
    """
    Fetch live power-cut data from TSSPDCL or other sources.
    
    INTEGRATION OPTIONS:
    1. Web scraping TSSPDCL website (https://www.tssouthernpower.com/)
    2. Twitter/X API for @TSSPDCL_CMD announcements
    3. Custom RSS feed parser
    4. Manual updates to knowledge_base.json
    
    Returns:
        Dict with power-cut data or fallback data
    """
    # TODO: Implement actual data source integration
    # For now, return fallback data
    
    try:
        # Example: Check if we have cached data in session state
        if "power_cuts_cache" in st.session_state:
            cache_time = st.session_state.get("power_cuts_cache_time")
            if cache_time and (datetime.now() - cache_time).total_seconds() < 3600:  # 1 hour cache
                return st.session_state["power_cuts_cache"]
        
        # TODO: Add actual API call here
        # response = requests.get("https://api.example.com/power-cuts", timeout=5)
        # data = response.json()
        
        # For now, return fallback
        return FALLBACK_POWER_CUTS
        
    except Exception as e:
        print(f"[utilities_alerts] Error fetching power cuts: {e}")
        return FALLBACK_POWER_CUTS


def fetch_live_water_supply() -> Dict:
    """
    Fetch live water supply data from HMWSSB or other sources.
    
    INTEGRATION OPTIONS:
    1. Web scraping HMWSSB website (https://www.hyderabadwater.gov.in/)
    2. Twitter/X API for @HMWSSBOnline announcements
    3. Custom RSS feed parser
    4. Manual updates to knowledge_base.json
    
    Returns:
        Dict with water supply data or fallback data
    """
    try:
        # Check cache
        if "water_supply_cache" in st.session_state:
            cache_time = st.session_state.get("water_supply_cache_time")
            if cache_time and (datetime.now() - cache_time).total_seconds() < 3600:
                return st.session_state["water_supply_cache"]
        
        # TODO: Add actual API call here
        # response = requests.get("https://api.example.com/water-supply", timeout=5)
        # data = response.json()
        
        # For now, return fallback
        return FALLBACK_WATER_SUPPLY
        
    except Exception as e:
        print(f"[utilities_alerts] Error fetching water supply: {e}")
        return FALLBACK_WATER_SUPPLY


# ═══════════════════════════════════════════════════════════════════════════
# CACHE MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_power_cuts() -> Dict:
    """Get power-cut data with caching"""
    return fetch_live_power_cuts()


@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_water_supply() -> Dict:
    """Get water supply data with caching"""
    return fetch_live_water_supply()


# ═══════════════════════════════════════════════════════════════════════════
# SEARCH & FILTER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def find_alerts_for_area(query: str, alert_type: str = "both") -> Dict:
    """
    Find utility alerts for a specific area.
    
    Args:
        query: User's area query (e.g., "Gachibowli", "Kukatpally")
        alert_type: "power", "water", or "both"
    
    Returns:
        Dict with matching alerts
    """
    query_lower = query.lower()
    results = {
        "power_cuts": [],
        "water_issues": [],
        "area_matched": False
    }
    
    # Search power cuts
    if alert_type in ["power", "both"]:
        power_data = get_power_cuts()
        for alert in power_data.get("areas", []):
            area_name = alert.get("area", "").lower()
            localities = [loc.lower() for loc in alert.get("affected_localities", [])]
            
            if query_lower in area_name or any(query_lower in loc for loc in localities):
                results["power_cuts"].append(alert)
                results["area_matched"] = True
    
    # Search water supply issues
    if alert_type in ["water", "both"]:
        water_data = get_water_supply()
        for alert in water_data.get("areas", []):
            area_name = alert.get("area", "").lower()
            localities = [loc.lower() for loc in alert.get("affected_localities", [])]
            
            if query_lower in area_name or any(query_lower in loc for loc in localities):
                results["water_issues"].append(alert)
                results["area_matched"] = True
    
    return results


def get_all_active_alerts() -> Dict:
    """Get all active utility alerts across Hyderabad"""
    power_data = get_power_cuts()
    water_data = get_water_supply()
    
    return {
        "power_cuts": power_data.get("areas", []),
        "water_issues": water_data.get("areas", []),
        "last_updated": power_data.get("timestamp", datetime.now().isoformat())
    }


def get_alerts_by_zone(zone: str) -> Dict:
    """
    Get alerts filtered by zone (Cyberabad, North, South, East, Central)
    
    Args:
        zone: Zone name (Cyberabad/North/South/East/Central)
    
    Returns:
        Dict with zone-specific alerts
    """
    zone_lower = zone.lower()
    all_alerts = get_all_active_alerts()
    
    filtered = {
        "power_cuts": [a for a in all_alerts["power_cuts"] if a.get("zone", "").lower() == zone_lower],
        "water_issues": [a for a in all_alerts["water_issues"] if a.get("zone", "").lower() == zone_lower]
    }
    
    return filtered


# ═══════════════════════════════════════════════════════════════════════════
# FORMATTING FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def format_power_cut_alert(alert: Dict) -> str:
    """Format a single power-cut alert"""
    area = alert.get("area", "Unknown")
    alert_type = alert.get("type", "unknown")
    start = alert.get("start_time", "Unknown")
    end = alert.get("end_time", "Unknown")
    reason = alert.get("reason", "No reason provided")
    localities = alert.get("affected_localities", [])
    
    # Emoji based on type
    type_emoji = "⚠️" if alert_type == "unplanned" else "🔧"
    status_text = "**UNPLANNED OUTAGE**" if alert_type == "unplanned" else "**Planned Maintenance**"
    
    response = f"{type_emoji} {status_text}\n\n"
    response += f"📍 **Area:** {area}\n"
    response += f"🕐 **Time:** {start} - {end}\n"
    response += f"📋 **Reason:** {reason}\n\n"
    
    if localities:
        response += f"**Affected Localities:**\n"
        for loc in localities:
            response += f"   • {loc}\n"
    
    return response


def format_water_alert(alert: Dict) -> str:
    """Format a single water supply alert"""
    area = alert.get("area", "Unknown")
    alert_type = alert.get("type", "unknown")
    schedule = alert.get("schedule", "Unknown")
    reason = alert.get("reason", "No reason provided")
    localities = alert.get("affected_localities", [])
    
    # Emoji based on severity
    type_emoji = "🚱" if alert_type == "no_supply" else "💧"
    
    if alert_type == "no_supply":
        status_text = "**NO WATER SUPPLY**"
    elif alert_type == "reduced_supply":
        status_text = "**REDUCED WATER SUPPLY**"
    else:
        status_text = "**WATER SUPPLY ISSUE**"
    
    response = f"{type_emoji} {status_text}\n\n"
    response += f"📍 **Area:** {area}\n"
    response += f"🕐 **Schedule:** {schedule}\n"
    response += f"📋 **Reason:** {reason}\n\n"
    
    if localities:
        response += f"**Affected Localities:**\n"
        for loc in localities:
            response += f"   • {loc}\n"
    
    return response


def format_area_alerts(area_name: str, alerts: Dict) -> str:
    """Format all alerts for a specific area"""
    power_cuts = alerts.get("power_cuts", [])
    water_issues = alerts.get("water_issues", [])
    
    if not power_cuts and not water_issues:
        return f"✅ **No active utility alerts for {area_name}**\n\n💡 Everything seems to be running smoothly in your area!"
    
    response = f"⚡ **UTILITY ALERTS FOR {area_name.upper()}**\n\n"
    
    # Power cuts
    if power_cuts:
        response += "🔌 **POWER SUPPLY:**\n\n"
        for i, alert in enumerate(power_cuts, 1):
            response += format_power_cut_alert(alert)
            if i < len(power_cuts):
                response += "\n---\n\n"
    
    # Water issues
    if water_issues:
        if power_cuts:
            response += "\n---\n\n"
        response += "💧 **WATER SUPPLY:**\n\n"
        for i, alert in enumerate(water_issues, 1):
            response += format_water_alert(alert)
            if i < len(water_issues):
                response += "\n---\n\n"
    
    response += "\n\n📞 **Helplines:**\n"
    response += "   • Power: TSSPDCL 1912\n"
    response += "   • Water: HMWSSB 155313\n"
    
    return response


def format_all_alerts_summary() -> str:
    """Format a city-wide summary of all active alerts"""
    all_alerts = get_all_active_alerts()
    power_cuts = all_alerts.get("power_cuts", [])
    water_issues = all_alerts.get("water_issues", [])
    last_updated = all_alerts.get("last_updated", "Unknown")
    
    if not power_cuts and not water_issues:
        return "✅ **No active utility alerts in Hyderabad**\n\nAll areas are receiving normal power and water supply."
    
    response = "⚡💧 **HYDERABAD UTILITY ALERTS**\n"
    response += f"📅 Last Updated: {format_timestamp(last_updated)}\n\n"
    
    # Power cuts summary
    if power_cuts:
        planned = [a for a in power_cuts if a.get("type") == "planned"]
        unplanned = [a for a in power_cuts if a.get("type") == "unplanned"]
        
        response += f"🔌 **POWER CUTS:** {len(power_cuts)} area(s) affected\n"
        if planned:
            response += f"   • Planned: {len(planned)}\n"
        if unplanned:
            response += f"   • Unplanned: {len(unplanned)}\n"
        response += "\n"
        
        for alert in power_cuts[:5]:  # Show max 5
            area = alert.get("area")
            time = f"{alert.get('start_time')} - {alert.get('end_time')}"
            response += f"   ⚠️ **{area}** ({time})\n"
    
    # Water issues summary
    if water_issues:
        response += f"\n💧 **WATER SUPPLY ISSUES:** {len(water_issues)} area(s) affected\n\n"
        for alert in water_issues[:5]:  # Show max 5
            area = alert.get("area")
            schedule = alert.get("schedule")
            response += f"   🚱 **{area}** ({schedule})\n"
    
    response += "\n\n💡 **Check your area:** Type 'power cut in [area name]' or 'water supply in [area name]'"
    response += "\n📞 **Helplines:** TSSPDCL 1912 | HMWSSB 155313"
    
    return response


def format_timestamp(iso_timestamp: str) -> str:
    """Convert ISO timestamp to readable format"""
    try:
        dt = datetime.fromisoformat(iso_timestamp.replace("Z", "+00:00"))
        return dt.strftime("%b %d, %I:%M %p")
    except:
        return "Recently"


# ═══════════════════════════════════════════════════════════════════════════
# NOTIFICATION SYSTEM (For future integration with Streamlit notifications)
# ═══════════════════════════════════════════════════════════════════════════

def check_alerts_for_saved_areas() -> List[str]:
    """
    Check for new alerts in user's saved areas.
    Returns list of notification messages.
    
    To be integrated with user preferences (see ai_preferences.py)
    """
    notifications = []
    
    # Get user's saved areas from preferences
    saved_areas = st.session_state.get("user_preferences", {}).get("frequent_areas", [])
    
    for area in saved_areas:
        alerts = find_alerts_for_area(area, "both")
        
        if alerts.get("power_cuts"):
            for alert in alerts["power_cuts"]:
                msg = f"⚡ Power cut alert in {area}: {alert.get('start_time')} - {alert.get('end_time')}"
                notifications.append(msg)
        
        if alerts.get("water_issues"):
            for alert in alerts["water_issues"]:
                msg = f"💧 Water supply issue in {area}: {alert.get('schedule')}"
                notifications.append(msg)
    
    return notifications


# ═══════════════════════════════════════════════════════════════════════════
# MAIN QUERY HANDLER
# ═══════════════════════════════════════════════════════════════════════════

def handle_utilities_query(query: str) -> str:
    """
    Main handler for utility-related queries.
    
    Args:
        query: User's query about power/water
    
    Returns:
        Formatted response string
    """
    query_lower = query.lower()
    
    # Detect query type
    is_power = any(word in query_lower for word in ["power", "electricity", "power cut", "load shed", "outage"])
    is_water = any(word in query_lower for word in ["water", "supply", "tap water"])
    
    # Extract area name from query if present
    area_keywords = ["in", "at", "near", "around"]
    area_name = None
    for keyword in area_keywords:
        if keyword in query_lower:
            parts = query_lower.split(keyword)
            if len(parts) > 1:
                area_name = parts[1].strip().split()[0].title()
                break
    
    # If no specific area, check for area names directly in query
    if not area_name:
        from services.locations import HYDERABAD_AREA_COORDS
        for area in HYDERABAD_AREA_COORDS.keys():
            if area.lower() in query_lower:
                area_name = area.title()
                break
    
    # Handle specific area query
    if area_name:
        alert_type = "power" if is_power and not is_water else "water" if is_water and not is_power else "both"
        alerts = find_alerts_for_area(area_name, alert_type)
        return format_area_alerts(area_name, alerts)
    
    # Handle general queries
    if "all" in query_lower or "list" in query_lower or "summary" in query_lower:
        return format_all_alerts_summary()
    
    # Default: show all alerts
    return format_all_alerts_summary()


# ═══════════════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def clear_alerts_cache():
    """Force refresh of alerts data"""
    get_power_cuts.clear()
    get_water_supply.clear()
    if "power_cuts_cache" in st.session_state:
        del st.session_state["power_cuts_cache"]
    if "water_supply_cache" in st.session_state:
        del st.session_state["water_supply_cache"]
    print("[utilities_alerts] Cache cleared")