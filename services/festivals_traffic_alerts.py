"""
Festival-Rush Traffic & Crowd Alerts Service
Real-time traffic and crowd monitoring during festivals and events in Hyderabad
Integrates with TomTom Traffic API and event calendars
"""
import streamlit as st
from datetime import datetime, timedelta
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import requests
from collections import defaultdict


# ═══════════════════════════════════════════════════════════════════════════
# HYDERABAD FESTIVALS & EVENTS CALENDAR
# ═══════════════════════════════════════════════════════════════════════════

HYDERABAD_FESTIVALS = {
    # Major Hindu Festivals
    "ganesh_chaturthi": {
        "name": "Ganesh Chaturthi",
        "dates": ["2026-08-22", "2026-09-01"],  # 10-day festival
        "crowd_hotspots": ["Tank Bund", "Khairatabad", "Banjara Hills", "Moazzam Jahi Market"],
        "traffic_impact": "extreme",
        "peak_days": ["2026-08-22", "2026-09-01"],  # Installation & immersion
        "affected_routes": [
            "Tank Bund to Necklace Road",
            "Khairatabad Circle",
            "Basheerbagh to Secretariat"
        ],
        "advisory": "Avoid Tank Bund, Necklace Road, and Khairatabad on immersion day. Use Metro or alternate routes."
    },
    
    "dussehra": {
        "name": "Dussehra (Dasara)",
        "dates": ["2026-10-15", "2026-10-24"],
        "crowd_hotspots": ["HITEC City exhibitions", "Forum Mall", "Inorbit Mall"],
        "traffic_impact": "high",
        "peak_days": ["2026-10-23", "2026-10-24"],
        "affected_routes": ["HITEC City to Gachibowli", "Madhapur main road"],
        "advisory": "Shopping malls extremely crowded. Book parking in advance."
    },
    
    "diwali": {
        "name": "Diwali",
        "dates": ["2026-11-11", "2026-11-13"],
        "crowd_hotspots": ["Laad Bazaar", "Abids", "Koti", "Begum Bazaar"],
        "traffic_impact": "extreme",
        "peak_days": ["2026-11-11"],
        "affected_routes": ["Charminar area", "Abids shopping district"],
        "advisory": "Shopping areas heavily congested. Use public transport. Parking unavailable in Charminar area."
    },
    
    "bonalu": {
        "name": "Bonalu Festival",
        "dates": ["2026-07-12", "2026-07-26"],
        "crowd_hotspots": ["Golconda Fort", "Ujjaini Mahankali Temple", "Secunderabad"],
        "traffic_impact": "extreme",
        "peak_days": ["2026-07-19", "2026-07-26"],
        "affected_routes": ["Golconda Road", "Secunderabad main roads"],
        "advisory": "Major processions block roads. Expect 2-3 hour delays. Metro is best option."
    },
    
    # Islamic Festivals
    "ramadan": {
        "name": "Ramadan (Iftar Rush)",
        "dates": ["2026-02-18", "2026-03-19"],  # Example dates
        "crowd_hotspots": ["Charminar", "Madina Circle", "Tolichowki"],
        "traffic_impact": "high",
        "peak_hours": "18:00-21:00",  # Evening iftar time
        "affected_routes": ["Charminar to Madina", "Tolichowki Circle"],
        "advisory": "Evening traffic extremely heavy near mosques and eateries. Avoid 6-9 PM."
    },
    
    "eid": {
        "name": "Eid-ul-Fitr",
        "dates": ["2026-03-20", "2026-03-21"],
        "crowd_hotspots": ["Mecca Masjid", "Laad Bazaar", "Charminar"],
        "traffic_impact": "extreme",
        "peak_days": ["2026-03-20"],
        "affected_routes": ["Entire Old City area", "Charminar surroundings"],
        "advisory": "Old City completely gridlocked. Avoid the area entirely or use Metro to Charminar station."
    },
    
    "bakrid": {
        "name": "Bakrid (Eid-ul-Adha)",
        "dates": ["2026-06-17", "2026-06-19"],
        "crowd_hotspots": ["Mecca Masjid", "Old City markets"],
        "traffic_impact": "extreme",
        "peak_days": ["2026-06-17"],
        "affected_routes": ["Old City roads"],
        "advisory": "Animal markets cause additional congestion. Plan accordingly."
    },
    
    # Annual Events
    "numaish_exhibition": {
        "name": "Numaish Exhibition",
        "dates": ["2026-01-01", "2026-01-31"],  # Usually Jan-Feb
        "crowd_hotspots": ["Nampally Exhibition Grounds"],
        "traffic_impact": "extreme",
        "peak_days": "weekends",
        "affected_routes": ["Nampally area", "Abids to Nampally"],
        "advisory": "Weekends see 2-3 lakh visitors daily. Parking very limited. Use Metro (Nampally station)."
    },
    
    "deccan_festival": {
        "name": "Deccan Festival",
        "dates": ["2026-02-25", "2026-03-01"],
        "crowd_hotspots": ["Charminar", "Qutub Shahi Tombs", "Golconda Fort"],
        "traffic_impact": "medium",
        "peak_days": "all days",
        "affected_routes": ["Golconda Road", "Charminar area"],
        "advisory": "Cultural events attract tourists. Evening performances cause localized congestion."
    },
    
    # National Holidays
    "independence_day": {
        "name": "Independence Day",
        "dates": ["2026-08-15"],
        "crowd_hotspots": ["Parade Ground", "Tank Bund", "Public Gardens"],
        "traffic_impact": "high",
        "peak_hours": "08:00-12:00",
        "affected_routes": ["Parade Ground area", "Secunderabad"],
        "advisory": "Morning ceremonies cause road closures. Afternoon onwards normal."
    },
    
    "republic_day": {
        "name": "Republic Day",
        "dates": ["2026-01-26"],
        "crowd_hotspots": ["Parade Ground", "Tank Bund"],
        "traffic_impact": "high",
        "peak_hours": "08:00-12:00",
        "affected_routes": ["Parade Ground vicinity"],
        "advisory": "Security restrictions in place. Carry ID."
    }
}


# ═══════════════════════════════════════════════════════════════════════════
# TOMTOM TRAFFIC API INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════

def get_tomtom_key():
    """Get TomTom API key from secrets"""
    return st.secrets.get("TOMTOM_API_KEY", "")


def get_live_traffic_severity(lat: float, lon: float) -> Dict:
    """
    Get live traffic severity from TomTom Traffic Flow API
    
    Args:
        lat: Latitude
        lon: Longitude
    
    Returns:
        Dict with traffic severity data
    """
    api_key = get_tomtom_key()
    if not api_key:
        return {"severity": "unknown", "speed_ratio": 0}
    
    url = (
        f"https://api.tomtom.com/traffic/services/4/flowSegmentData/"
        f"absolute/10/json?point={lat},{lon}&key={api_key}"
    )
    
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        flow = data.get("flowSegmentData", {})
        current_speed = flow.get("currentSpeed", 0)
        free_flow = flow.get("freeFlowSpeed", 1)
        
        speed_ratio = current_speed / max(free_flow, 1)
        
        # Classify severity
        if speed_ratio >= 0.8:
            severity = "low"
        elif speed_ratio >= 0.5:
            severity = "medium"
        elif speed_ratio >= 0.3:
            severity = "high"
        else:
            severity = "extreme"
        
        return {
            "severity": severity,
            "speed_ratio": speed_ratio,
            "current_speed": current_speed,
            "free_flow_speed": free_flow,
            "delay_minutes": calculate_delay(speed_ratio, 10)  # 10 km reference
        }
        
    except Exception as e:
        print(f"[festival_alerts] TomTom API error: {e}")
        return {"severity": "unknown", "speed_ratio": 0}


def calculate_delay(speed_ratio: float, distance_km: float) -> int:
    """Calculate expected delay in minutes"""
    if speed_ratio >= 0.8:
        return 0
    
    # Normal time vs actual time difference
    normal_time = distance_km / 50 * 60  # 50 km/h average
    actual_time = distance_km / (50 * speed_ratio) * 60
    
    return int(actual_time - normal_time)


# ═══════════════════════════════════════════════════════════════════════════
# FESTIVAL DETECTION & ALERTING
# ═══════════════════════════════════════════════════════════════════════════

def get_active_festivals(date: datetime = None) -> List[Dict]:
    """
    Get list of active festivals on a given date
    
    Args:
        date: Date to check (default: today)
    
    Returns:
        List of active festival dicts
    """
    if date is None:
        date = datetime.now()
    
    date_str = date.strftime("%Y-%m-%d")
    active = []
    
    for festival_id, festival_data in HYDERABAD_FESTIVALS.items():
        dates = festival_data.get("dates", [])
        
        if isinstance(dates, list) and len(dates) == 2:
            # Date range
            start = datetime.strptime(dates[0], "%Y-%m-%d")
            end = datetime.strptime(dates[1], "%Y-%m-%d")
            
            if start <= date <= end:
                festival_data["id"] = festival_id
                festival_data["is_peak"] = date_str in festival_data.get("peak_days", [])
                active.append(festival_data)
        
        elif isinstance(dates, list) and date_str in dates:
            # Single date
            festival_data["id"] = festival_id
            festival_data["is_peak"] = True
            active.append(festival_data)
    
    return active


def get_upcoming_festivals(days_ahead: int = 7) -> List[Dict]:
    """Get festivals coming up in next N days"""
    today = datetime.now()
    upcoming = []
    
    for i in range(days_ahead):
        check_date = today + timedelta(days=i)
        festivals = get_active_festivals(check_date)
        
        for festival in festivals:
            # Avoid duplicates
            if not any(f["id"] == festival["id"] for f in upcoming):
                festival["starts_in_days"] = i
                upcoming.append(festival)
    
    return upcoming


def check_festival_impact_on_area(area_name: str, date: datetime = None) -> Dict:
    """
    Check if an area is affected by festival crowds/traffic
    
    Args:
        area_name: Area to check
        date: Date to check (default: today)
    
    Returns:
        Dict with impact assessment
    """
    active_festivals = get_active_festivals(date)
    
    result = {
        "affected": False,
        "festivals": [],
        "crowd_level": "normal",
        "traffic_level": "normal",
        "advisory": None
    }
    
    area_lower = area_name.lower()
    
    for festival in active_festivals:
        hotspots = [spot.lower() for spot in festival.get("crowd_hotspots", [])]
        routes = [route.lower() for route in festival.get("affected_routes", [])]
        
        # Check if area is in hotspots or affected routes
        if any(area_lower in spot or spot in area_lower for spot in hotspots):
            result["affected"] = True
            result["festivals"].append(festival)
            
            # Update severity
            impact = festival.get("traffic_impact", "medium")
            if impact == "extreme":
                result["crowd_level"] = "extreme"
                result["traffic_level"] = "extreme"
            elif impact == "high" and result["crowd_level"] != "extreme":
                result["crowd_level"] = "high"
                result["traffic_level"] = "high"
        
        elif any(area_lower in route or route in area_lower for route in routes):
            result["affected"] = True
            result["festivals"].append(festival)
            result["traffic_level"] = festival.get("traffic_impact", "medium")
    
    return result


# ═══════════════════════════════════════════════════════════════════════════
# CROWD PREDICTION (ML-based heuristics)
# ═══════════════════════════════════════════════════════════════════════════

def predict_crowd_level(location: str, hour: int, is_weekend: bool, festival_active: bool) -> str:
    """
    Predict crowd level based on location, time, and context
    
    Args:
        location: Location name
        hour: Hour of day (0-23)
        is_weekend: Is it weekend
        festival_active: Is there an active festival
    
    Returns:
        Crowd level: "low", "medium", "high", "extreme"
    """
    base_score = 0
    
    # Location factors
    busy_locations = ["charminar", "tank bund", "inorbit", "gvk", "forum mall", "hitech city"]
    if any(loc in location.lower() for loc in busy_locations):
        base_score += 2
    
    # Time factors
    if 18 <= hour <= 21:  # Evening peak
        base_score += 2
    elif 11 <= hour <= 14:  # Lunch time
        base_score += 1
    
    # Weekend factor
    if is_weekend:
        base_score += 2
    
    # Festival factor
    if festival_active:
        base_score += 3
    
    # Convert score to level
    if base_score >= 7:
        return "extreme"
    elif base_score >= 5:
        return "high"
    elif base_score >= 3:
        return "medium"
    else:
        return "low"


# ═══════════════════════════════════════════════════════════════════════════
# FORMATTING FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def format_festival_alert(festival: Dict) -> str:
    """Format a single festival alert"""
    name = festival.get("name", "Festival")
    dates = festival.get("dates", [])
    impact = festival.get("traffic_impact", "medium")
    is_peak = festival.get("is_peak", False)
    
    # Choose emoji based on impact
    impact_emoji = {
        "extreme": "🔴",
        "high": "🟠",
        "medium": "🟡",
        "low": "🟢"
    }.get(impact, "🟡")
    
    response = f"{impact_emoji} **{name}**\n"
    
    if is_peak:
        response += "⚠️ **PEAK DAY - Maximum crowds expected**\n"
    
    if isinstance(dates, list) and len(dates) == 2:
        start = datetime.strptime(dates[0], "%Y-%m-%d").strftime("%b %d")
        end = datetime.strptime(dates[1], "%Y-%m-%d").strftime("%b %d")
        response += f"📅 {start} - {end}\n"
    
    response += f"🚦 Traffic Impact: {impact.upper()}\n\n"
    
    # Crowd hotspots
    hotspots = festival.get("crowd_hotspots", [])
    if hotspots:
        response += "🏛️ **Crowd Hotspots:**\n"
        for spot in hotspots[:5]:
            response += f"   • {spot}\n"
    
    # Affected routes
    routes = festival.get("affected_routes", [])
    if routes:
        response += f"\n🚗 **Affected Routes:**\n"
        for route in routes[:3]:
            response += f"   • {route}\n"
    
    # Advisory
    advisory = festival.get("advisory")
    if advisory:
        response += f"\n💡 **Advisory:** {advisory}\n"
    
    return response


def format_area_festival_impact(area: str, impact: Dict) -> str:
    """Format festival impact for a specific area"""
    if not impact["affected"]:
        return f"✅ **{area}** - No major festival impact expected\n\n💡 Traffic and crowds should be normal."
    
    festivals = impact["festivals"]
    crowd = impact["crowd_level"]
    traffic = impact["traffic_level"]
    
    # Emoji based on severity
    crowd_emoji = {
        "extreme": "🔴🔴🔴",
        "high": "🟠🟠",
        "medium": "🟡",
        "normal": "🟢"
    }.get(crowd, "🟡")
    
    traffic_emoji = {
        "extreme": "🚨",
        "high": "⚠️",
        "medium": "🚦",
        "normal": "✅"
    }.get(traffic, "🚦")
    
    response = f"🎉 **FESTIVAL IMPACT: {area.upper()}**\n\n"
    response += f"{crowd_emoji} **Crowd Level:** {crowd.upper()}\n"
    response += f"{traffic_emoji} **Traffic Level:** {traffic.upper()}\n\n"
    
    response += f"**Active Festivals ({len(festivals)}):**\n"
    for festival in festivals:
        response += f"   🎊 {festival['name']}\n"
    
    response += "\n**Recommendations:**\n"
    if traffic == "extreme":
        response += "   • ❌ Avoid driving to this area\n"
        response += "   • 🚇 Use Metro if available\n"
        response += "   • ⏰ Expect 1-3 hour delays\n"
    elif traffic == "high":
        response += "   • ⚠️ Plan extra 30-60 min travel time\n"
        response += "   • 🚇 Public transport recommended\n"
    else:
        response += "   • ✅ Manageable with planning\n"
        response += "   • 🅿️ Book parking in advance\n"
    
    return response


def format_live_traffic_with_festival(area: str, lat: float, lon: float) -> str:
    """Combine live traffic data with festival alerts"""
    # Get festival impact
    impact = check_festival_impact_on_area(area)
    
    # Get live traffic
    traffic = get_live_traffic_severity(lat, lon)
    
    response = f"🚦 **LIVE TRAFFIC & CROWD ALERT: {area.upper()}**\n\n"
    
    # Live traffic status
    severity = traffic.get("severity", "unknown")
    if severity != "unknown":
        speed_ratio = traffic.get("speed_ratio", 0)
        current_speed = traffic.get("current_speed", 0)
        delay = traffic.get("delay_minutes", 0)
        
        severity_emoji = {
            "low": "🟢",
            "medium": "🟡",
            "high": "🟠",
            "extreme": "🔴"
        }.get(severity, "⚪")
        
        response += f"{severity_emoji} **Current Traffic:** {severity.upper()}\n"
        response += f"🚗 Current Speed: {current_speed:.0f} km/h\n"
        response += f"📊 Flow: {speed_ratio*100:.0f}% of normal\n"
        
        if delay > 0:
            response += f"⏱️ Expected Delay: {delay} minutes\n"
    
    response += "\n"
    
    # Festival impact
    if impact["affected"]:
        response += f"🎉 **Festival Impact:** YES\n"
        response += f"👥 Crowd Level: {impact['crowd_level'].upper()}\n"
        
        for festival in impact["festivals"]:
            response += f"\n🎊 **{festival['name']}**\n"
            advisory = festival.get("advisory", "")
            if advisory:
                response += f"💡 {advisory}\n"
    else:
        response += "🎉 **Festival Impact:** None\n"
    
    return response


def format_upcoming_festivals_calendar(days: int = 7) -> str:
    """Format upcoming festivals calendar"""
    upcoming = get_upcoming_festivals(days)
    
    if not upcoming:
        return f"📅 **No major festivals in next {days} days**\n\n✅ Normal traffic and crowd levels expected."
    
    response = f"📅 **UPCOMING FESTIVALS ({days} DAYS)**\n\n"
    
    for festival in upcoming:
        starts_in = festival.get("starts_in_days", 0)
        impact = festival.get("traffic_impact", "medium")
        
        impact_emoji = {
            "extreme": "🔴",
            "high": "🟠",
            "medium": "🟡",
            "low": "🟢"
        }.get(impact, "🟡")
        
        if starts_in == 0:
            timing = "**TODAY**"
        elif starts_in == 1:
            timing = "Tomorrow"
        else:
            timing = f"In {starts_in} days"
        
        response += f"{impact_emoji} **{festival['name']}** - {timing}\n"
        
        dates = festival.get("dates", [])
        if isinstance(dates, list) and len(dates) == 2:
            start = datetime.strptime(dates[0], "%Y-%m-%d").strftime("%b %d")
            end = datetime.strptime(dates[1], "%Y-%m-%d").strftime("%b %d")
            response += f"   📅 {start} - {end}\n"
        
        hotspots = festival.get("crowd_hotspots", [])
        if hotspots:
            response += f"   🏛️ Hotspots: {', '.join(hotspots[:3])}\n"
        
        response += "\n"
    
    response += "💡 **Tip:** Plan travel during off-peak hours to avoid festival crowds!"
    
    return response


# ═══════════════════════════════════════════════════════════════════════════
# MAIN QUERY HANDLER
# ═══════════════════════════════════════════════════════════════════════════

def handle_festival_traffic_query(query: str) -> str:
    """
    Main handler for festival traffic queries
    
    Args:
        query: User's query
    
    Returns:
        Formatted response string
    """
    query_lower = query.lower()
    
    # Check for upcoming festivals query
    if any(word in query_lower for word in ["upcoming", "next", "coming", "calendar", "schedule"]):
        return format_upcoming_festivals_calendar(7)
    
    # Check for specific area query
    from services.locations import HYDERABAD_AREA_COORDS
    
    for area, (lat, lon) in HYDERABAD_AREA_COORDS.items():
        if area.lower() in query_lower:
            # Check if asking for live traffic
            if any(word in query_lower for word in ["traffic", "live", "current", "now"]):
                return format_live_traffic_with_festival(area, lat, lon)
            else:
                # Just festival impact
                impact = check_festival_impact_on_area(area)
                return format_area_festival_impact(area, impact)
    
    # Check for specific festival query
    for festival_id, festival_data in HYDERABAD_FESTIVALS.items():
        if festival_data["name"].lower() in query_lower or festival_id in query_lower:
            return format_festival_alert(festival_data)
    
    # Check for today's festivals
    if "today" in query_lower or "right now" in query_lower:
        active = get_active_festivals()
        
        if not active:
            return "✅ **No major festivals today**\n\nTraffic and crowds should be normal across Hyderabad."
        
        response = "🎉 **ACTIVE FESTIVALS TODAY**\n\n"
        for festival in active:
            response += format_festival_alert(festival)
            response += "\n---\n\n"
        
        return response.rstrip("\n---\n\n")
    
    # Default: show upcoming festivals
    return format_upcoming_festivals_calendar(7)


# ═══════════════════════════════════════════════════════════════════════════
# PROACTIVE ALERTS
# ═══════════════════════════════════════════════════════════════════════════

def get_festival_alerts_for_saved_areas(saved_areas: List[str]) -> List[str]:
    """
    Get festival alerts for user's saved areas
    To be integrated with ai_preferences
    
    Args:
        saved_areas: List of area names
    
    Returns:
        List of alert messages
    """
    alerts = []
    
    upcoming = get_upcoming_festivals(3)  # Check next 3 days
    
    for area in saved_areas:
        impact = check_festival_impact_on_area(area)
        
        if impact["affected"]:
            for festival in impact["festivals"]:
                starts_in = festival.get("starts_in_days", 0)
                
                if starts_in <= 2:
                    msg = f"🎉 {festival['name']} affecting {area} "
                    msg += "today!" if starts_in == 0 else f"in {starts_in} days"
                    alerts.append(msg)
    
    return alerts