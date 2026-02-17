import requests
import streamlit as st

# Import logger and config
from services.logger import setup_logger
from services.config import config

# Set up logger
logger = setup_logger('traffic', 'traffic.log')


# ══════════════════════════════════════════════════════════════════════════════
# ALTERNATE ROUTES MAP
# Hardcoded map of area → alternate routes to check when traffic is heavy
# ══════════════════════════════════════════════════════════════════════════════

ALTERNATE_ROUTES = {
    "gachibowli": ["kondapur", "madhapur", "tellapur"],
    "hitec city": ["gachibowli", "madhapur", "kondapur"],
    "madhapur": ["hitec city", "kondapur", "jubilee hills"],
    "kondapur": ["madhapur", "kukatpally", "miyapur"],
    "ameerpet": ["sr nagar", "kukatpally", "begumpet"],
    "secunderabad": ["alwal", "trimulgherry", "bowenpally"],
    "dilsukhnagar": ["lb nagar", "kothapet", "malakpet"],
    "kukatpally": ["miyapur", "bachupally", "kompally"],
    "begumpet": ["ameerpet", "somajiguda", "banjara hills"],
    "jubilee hills": ["banjara hills", "madhapur", "gachibowli"],
    "banjara hills": ["jubilee hills", "somajiguda", "lakdikapul"],
    "uppal": ["nagole", "habsiguda", "tarnaka"],
    "lb nagar": ["dilsukhnagar", "vanasthalipuram", "nagole"],
    "miyapur": ["kukatpally", "bachupally", "kondapur"],
    "mehdipatnam": ["tolichowki", "attapur", "lakdikapul"],
}


def get_traffic_flow(lat, lon):
    """
    Fetch traffic flow data from TomTom API.
    
    Args:
        lat: Latitude
        lon: Longitude
    
    Returns:
        Traffic flow data dict or None on error
    """
    api_key = config.api.get_tomtom_api_key()
    
    if not api_key:
        logger.error("TOMTOM_API_KEY not configured")
        return None
    
    logger.debug(f"Fetching traffic for coordinates ({lat:.4f}, {lon:.4f})")
    
    url = (
        "https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json"
        f"?point={lat},{lon}&key={api_key}"
    )

    try:
        response = requests.get(url, timeout=config.api.TRAFFIC_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        
        # Log traffic status
        if "flowSegmentData" in data:
            flow = data["flowSegmentData"]
            current_speed = flow.get("currentSpeed", 0)
            free_speed = flow.get("freeFlowSpeed", 1)
            ratio = current_speed / max(free_speed, 1)
            
            status = "smooth" if ratio >= 0.8 else "moderate" if ratio >= 0.5 else "heavy"
            logger.info(f"Traffic status: {status} (current: {current_speed} km/h, free flow: {free_speed} km/h)")
        
        return data
        
    except requests.exceptions.Timeout:
        logger.warning(f"Traffic API timeout for ({lat:.4f}, {lon:.4f})")
        return None
    except requests.exceptions.HTTPError as e:
        logger.error(f"Traffic API HTTP error: {e.response.status_code}")
        return None
    except Exception as e:
        logger.error(f"Traffic fetch failed: {e}", exc_info=True)
        return None


def format_traffic(data, area_name=None):
    """
    Format traffic data with optional alternate route suggestions.
    
    Args:
        data: Traffic flow data from TomTom
        area_name: Name of the area (optional, for alternate route suggestions)
    """
    if not data or "flowSegmentData" not in data:
        return "🚦 Traffic data unavailable."

    flow = data["flowSegmentData"]

    current_speed = flow.get("currentSpeed", 0)
    free_speed = flow.get("freeFlowSpeed", 1)

    ratio = current_speed / max(free_speed, 1)

    if ratio >= 0.8:
        status = "🟢 Smooth traffic — no delays"
        advice = "Safe to travel."
        show_alternates = False
    elif ratio >= 0.5:
        status = "🟡 Moderate traffic — minor delays"
        advice = "Plan buffer time."
        show_alternates = False
    else:
        status = "🔴 Heavy traffic — expect delays"
        advice = "Consider alternate routes or wait for off-peak hours."
        show_alternates = True

    response = (
        f"{status}\n"
        f"🚗 Current Speed: {current_speed} km/h\n"
        f"🛣️ Free Flow Speed: {free_speed} km/h\n\n"
        f"💡 Advice: {advice}"
    )
    
    # Add alternate route suggestions if traffic is heavy
    if show_alternates and area_name:
        alternates = get_alternate_routes_for_area(area_name)
        if alternates:
            response += "\n\n🔀 **Alternate Routes to Check:**\n"
            for alt in alternates:
                response += f"   • {alt.title()}\n"
            response += "\n💡 These nearby areas might have lighter traffic."
    
    return response


def get_alternate_routes_for_area(area_name):
    """
    Get list of alternate routes for a given area.
    
    Args:
        area_name: Name of the area (e.g., "gachibowli", "hitec city")
    
    Returns:
        List of alternate area names, or empty list if none defined
    """
    if not area_name:
        return []
    
    # Normalize area name
    area_lower = area_name.lower().strip()
    
    # Direct lookup
    if area_lower in ALTERNATE_ROUTES:
        return ALTERNATE_ROUTES[area_lower]
    
    # Try partial matches
    for key in ALTERNATE_ROUTES:
        if key in area_lower or area_lower in key:
            return ALTERNATE_ROUTES[key]
    
    return []


def suggest_alternate_route(from_area, to_area):
    """
    Suggest alternate routes for a journey.
    
    This is a simple heuristic-based suggestion. For production,
    you'd call TomTom's routing API with alternatives=true.
    
    Args:
        from_area: Starting area name
        to_area: Destination area name
    
    Returns:
        String with route suggestions or empty string
    """
    # Check if either area has defined alternates
    from_alts = get_alternate_routes_for_area(from_area)
    to_alts = get_alternate_routes_for_area(to_area)
    
    if not from_alts and not to_alts:
        return ""
    
    response = "\n\n🔀 **Alternate Route Ideas:**\n"
    
    if from_alts:
        response += f"**From {from_area.title()}:**\n"
        response += f"   Instead of the direct route, try going via:\n"
        for alt in from_alts[:2]:  # Show max 2 alternates
            response += f"   • {alt.title()}\n"
    
    if to_alts:
        response += f"\n**To reach {to_area.title()}:**\n"
        response += f"   Consider approaching from:\n"
        for alt in to_alts[:2]:
            response += f"   • {alt.title()}\n"
    
    response += "\n💡 Use Google Maps or Waze for live traffic-aware routing."
    
    return response