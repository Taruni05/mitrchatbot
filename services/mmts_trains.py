import json
import streamlit as st
from typing import List, Dict, Tuple, Optional
from pathlib import Path
from datetime import datetime, time
from services.kb_loader import get_mmts_data
from services.logger import get_logger
from services.config import config

# Initialize logger
logger = get_logger(__name__)




# Load knowledge base
@st.cache_data
def load_mmts_data():
    logger.debug("Loading MMTS train data from knowledge base")
    data = get_mmts_data()
    if data:
        logger.info(f"✅ Loaded MMTS data")
    return data


# Station name normalization
STATION_ALIASES = {
    # Common variations
    "hitech": "Hi-Tech City",
    "hi-tech": "Hi-Tech City",
    "hitec": "Hi-Tech City",
    "hitech city": "Hi-Tech City",
    "secbad": "Secunderabad",
    "sec bad": "Secunderabad",
    "npa": "NPA Shivram Pally",
    "shivram pally": "NPA Shivram Pally",
    "lakdi ka pul": "Lakdikapul",
    "lakdi-ka-pul": "Lakdikapul",
    "nature cure": "Nature Cure Hospital",
    "khairatabad": "Khairatabad",
    "khairatabadi": "Khairatabad",
    "fatehnagar": "Fatehnagar",
    "fateh nagar": "Fatehnagar",
}


def normalize_station(station: str) -> str:
    """Normalize station names to match knowledge base"""
    station_lower = station.lower().strip()

    # Check aliases first
    if station_lower in STATION_ALIASES:
        return STATION_ALIASES[station_lower]

    # Return title case for matching
    return station.title().strip()


def extract_stations_from_query(query: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract from/to stations from user query.
    
    Examples:
        "Train from Falaknuma to Lingampally" → ("Falaknuma", "Lingampally")
        "MMTS from Secunderabad to HITEC City" → ("Secunderabad", "Hi-Tech City")
        "How to reach Begumpet by train" → (None, "Begumpet")
        "Train to Lingampally" → (None, "Lingampally")
    """
    query_lower = query.lower()
    
    # Pattern 1: "from X to Y"
    if "from" in query_lower and "to" in query_lower:
        parts = query_lower.split("from")[1].split("to")
        if len(parts) == 2:
            from_station = normalize_station(parts[0].strip())
            to_station = normalize_station(parts[1].strip())
            return from_station, to_station
    
    # Pattern 2: "reach X" or "get to X" or "go to X"
    if any(phrase in query_lower for phrase in ["reach", "get to", "go to"]):
        # Extract station name after "reach"/"get to"/"go to"
        for phrase in ["reach", "get to", "go to"]:
            if phrase in query_lower:
                # Split by the phrase and take what comes after
                parts = query_lower.split(phrase)
                if len(parts) >= 2:
                    station_part = parts[1].strip()
                    
                    # Remove common words that might follow
                    for word in ["by train", "by mmts", "using train", "using mmts", "?", ".", "from"]:
                        station_part = station_part.replace(word, "").strip()
                    
                    # Take first significant word/phrase as station
                    # Split by common separators
                    for separator in [" by ", " using ", " via ", "?"]:
                        if separator in station_part:
                            station_part = station_part.split(separator)[0].strip()
                    
                    if station_part:
                        to_station = normalize_station(station_part)
                        return None, to_station
    
    # Pattern 3: "X to Y" (without "from")
    if "to" in query_lower and "from" not in query_lower:
        parts = query_lower.split("to")
        if len(parts) >= 2:
            # Try to extract station names
            potential_from = parts[0].strip()
            potential_to = parts[1].strip()
            
            # Remove common words from potential_from
            for word in ["train", "mmts", "reach", "go", "get", "how", "can", "i"]:
                potential_from = potential_from.replace(word, "").strip()
            
            # Remove common words from potential_to
            for word in ["by train", "by mmts", "using train", "?", "."]:
                potential_to = potential_to.replace(word, "").strip()
            
            # If we have content in potential_from, it might be a from station
            if potential_from and len(potential_from) > 2:
                from_station = normalize_station(potential_from)
                to_station = normalize_station(potential_to)
                return from_station, to_station
            else:
                # Only destination specified
                to_station = normalize_station(potential_to)
                return None, to_station
    
    # Pattern 4: "train to X" or "mmts to X"
    if any(phrase in query_lower for phrase in ["train to", "mmts to"]):
        for phrase in ["train to", "mmts to"]:
            if phrase in query_lower:
                parts = query_lower.split(phrase)
                if len(parts) >= 2:
                    station_part = parts[1].strip()
                    
                    # Clean up
                    for word in ["?", ".", "from", "by"]:
                        station_part = station_part.replace(word, "").strip()
                    
                    if station_part:
                        to_station = normalize_station(station_part)
                        return None, to_station
    
    return None, None

def find_mmts_route(from_station: str, to_station: str) -> Optional[Dict]:
    """
    Find MMTS route between two stations.

    Returns:
        {
            'line': str,
            'route_name': str,
            'stations': List[str],
            'duration': str,
            'interchange_required': bool,
            'interchange_at': str (if applicable)
        }
    """
    mmts_data = load_mmts_data()

    if not mmts_data:
        return None

    routes = mmts_data.get("routes", [])

    # Search for direct route
    for route in routes:
        stations = route.get("stations", [])

        # Check if both stations are on this line
        if from_station in stations and to_station in stations:
            from_idx = stations.index(from_station)
            to_idx = stations.index(to_station)

            # Calculate route direction
            if from_idx < to_idx:
                direction = "Forward"
                route_stations = stations[from_idx : to_idx + 1]
            else:
                direction = "Reverse"
                route_stations = stations[to_idx : from_idx + 1]
                route_stations.reverse()

            # Estimate duration (assume 3-4 mins per station)
            num_stations = len(route_stations)
            duration_mins = num_stations * 4

            return {
                "line": route.get("route_name"),
                "route_name": route.get("route_name"),
                "from": route.get("route", {}).get("from"),
                "to": route.get("route", {}).get("to"),
                "stations": route_stations,
                "total_stations": num_stations,
                "duration_mins": duration_mins,
                "interchange_required": False,
                "direction": direction,
            }

    # Check for interchange routes
    interchange_points = mmts_data.get("interchange_points", [])

    for interchange in interchange_points:
        station_name = interchange.get("station")
        connects_to = interchange.get("connects_to", [])

        # Find routes containing from_station
        from_routes = []
        for route in routes:
            if from_station in route.get("stations", []) and station_name in route.get(
                "stations", []
            ):
                from_routes.append(route)

        # Find routes containing to_station
        to_routes = []
        for route in routes:
            if to_station in route.get("stations", []) and station_name in route.get(
                "stations", []
            ):
                to_routes.append(route)

        if from_routes and to_routes:
            # Found interchange route
            from_route = from_routes[0]
            to_route = to_routes[0]

            # Build combined stations list
            from_stations = from_route.get("stations", [])
            to_stations = to_route.get("stations", [])

            from_idx = from_stations.index(from_station)
            interchange_idx_1 = from_stations.index(station_name)

            leg1_stations = (
                from_stations[from_idx : interchange_idx_1 + 1]
                if from_idx < interchange_idx_1
                else from_stations[interchange_idx_1 : from_idx + 1][::-1]
            )

            interchange_idx_2 = to_stations.index(station_name)
            to_idx = to_stations.index(to_station)

            leg2_stations = (
                to_stations[interchange_idx_2 : to_idx + 1]
                if interchange_idx_2 < to_idx
                else to_stations[to_idx : interchange_idx_2 + 1][::-1]
            )

            total_stations_count = (
                len(leg1_stations) + len(leg2_stations) - 1
            )  # -1 because interchange counted twice
            duration_mins = total_stations_count * 4 + 10  # +10 for interchange time

            return {
                "line": f"{from_route.get('route_name')} → {to_route.get('route_name')}",
                "route_name": "Interchange Route",
                "stations": leg1_stations
                + leg2_stations[1:],  # Avoid duplicate interchange station
                "leg1_stations": leg1_stations,
                "leg2_stations": leg2_stations,
                "total_stations": total_stations_count,
                "duration_mins": duration_mins,
                "interchange_required": True,
                "interchange_at": station_name,
                "leg1_line": from_route.get("route_name"),
                "leg2_line": to_route.get("route_name"),
            }

    return None


def generate_sample_timings(base_hour: int = 6) -> List[str]:
    """
    Generate sample train timings (since not in knowledge base).
    Trains run approximately every 20-30 minutes during peak hours.
    """
    timings = []

    # Morning peak (6 AM - 10 AM): Every 20-25 mins
    current_time = base_hour * 60  # Convert to minutes
    while current_time < 10 * 60:
        hour = current_time // 60
        minute = current_time % 60
        timings.append(f"{hour:02d}:{minute:02d}")
        current_time += 25  # 25 min frequency

    # Mid-day (10 AM - 5 PM): Every 30-40 mins
    while current_time < 17 * 60:
        hour = current_time // 60
        minute = current_time % 60
        timings.append(f"{hour:02d}:{minute:02d}")
        current_time += 35  # 35 min frequency

    # Evening peak (5 PM - 10 PM): Every 20-25 mins
    while current_time < 22 * 60:
        hour = current_time // 60
        minute = current_time % 60
        timings.append(f"{hour:02d}:{minute:02d}")
        current_time += 25  # 25 min frequency

    return timings


def format_mmts_route(route_info: Dict) -> str:
    """
    Format MMTS route information into readable response.
    """
    if not route_info:
        return ""

    mmts_data = load_mmts_data()
    operating_hours = mmts_data.get("operating_hours", {})

    response = f"🚆 **MMTS TRAIN ROUTE**\n\n"

    # Route info
    if route_info["interchange_required"]:
        response += f"📍 **Route:** {route_info['line']}\n"
        response += f"⚠️ **Interchange Required:** At {route_info['interchange_at']}\n\n"

        # Leg 1
        response += f"**Leg 1:** {route_info['leg1_line']}\n"
        response += f"🚉 Stations: {' → '.join(route_info['leg1_stations'])}\n\n"

        response += f"🔄 **Change trains at {route_info['interchange_at']}**\n\n"

        # Leg 2
        response += f"**Leg 2:** {route_info['leg2_line']}\n"
        response += f"🚉 Stations: {' → '.join(route_info['leg2_stations'])}\n\n"
    else:
        response += f"📍 **Line:** {route_info['line']}\n"
        response += f"🚉 **Stations:** {' → '.join(route_info['stations'])}\n\n"

    # Journey details
    response += f"📊 **Journey Details:**\n"
    response += f"⏱️ Duration: ~{route_info['duration_mins']} mins\n"
    response += f"🚉 Total Stations: {route_info['total_stations']}\n"
    response += f"🔄 Changes: {'1 interchange' if route_info['interchange_required'] else 'Direct route'}\n\n"

    # Sample timings
    response += f"⏰ **Operating Hours:**\n"
    response += f"🌅 First Train: {operating_hours.get('first_train', '05:30 AM')}\n"
    response += f"🌙 Last Train: {operating_hours.get('last_train', '10:30 PM')}\n"
    response += (
        f"⚡ Frequency: {operating_hours.get('frequency_minutes', '20-30 mins')}\n\n"
    )

    # Sample departures
    sample_timings = generate_sample_timings(6)
    response += f"🕐 **Sample Departure Times** (from {route_info['stations'][0]}):\n\n"

    # Morning trains
    morning = [t for t in sample_timings if t.startswith(("06", "07", "08", "09"))]
    response += f"🔹 **Morning:** {', '.join(morning[:5])}\n"

    # Afternoon trains
    afternoon = [
        t for t in sample_timings if t.startswith(("12", "13", "14", "15", "16"))
    ]
    response += f"🔹 **Afternoon:** {', '.join(afternoon[:4])}\n"

    # Evening trains
    evening = [
        t for t in sample_timings if t.startswith(("17", "18", "19", "20", "21"))
    ]
    response += f"🔹 **Evening:** {', '.join(evening[:5])}\n\n"

    # Fare and tips
    response += f"💰 **Fare:** ₹10-20 (varies by distance)\n\n"

    # Metro connections if available
    interchange_points = mmts_data.get("interchange_points", [])
    metro_connections = [
        ip for ip in interchange_points if "Metro" in str(ip.get("connects_to", []))
    ]

    if metro_connections:
        response += f"🚇 **Metro Connections Available At:**\n"
        for ip in metro_connections:
            connects = ", ".join(ip.get("connects_to", []))
            response += f"   • {ip.get('station')}: {connects}\n"
        response += "\n"

    response += f"💡 **Tips:**\n"
    response += f"• Trains are most frequent during 8-10 AM and 5-8 PM\n"
    response += f"• Purchase tickets before boarding\n"
    response += f"• Keep ₹10-20 change ready\n"

    return response


def get_general_mmts_info() -> str:
    """
    Return general MMTS information when no specific route requested.
    """
    mmts_data = load_mmts_data()

    if not mmts_data:
        return "MMTS information is currently unavailable."

    routes = mmts_data.get("routes", [])
    operating_hours = mmts_data.get("operating_hours", {})

    response = f"🚆 **MMTS (MULTI-MODAL TRANSPORT SYSTEM)**\n\n"
    response += f"**Operator:** {mmts_data.get('operator', 'South Central Railway')}\n"
    response += (
        f"**Operational Since:** {mmts_data.get('operational_since', '2003')}\n\n"
    )

    response += f"📍 **Available Routes:**\n\n"

    for route in routes:
        route_name = route.get("route_name")
        from_station = route.get("route", {}).get("from")
        to_station = route.get("route", {}).get("to")
        stations = route.get("stations", [])

        response += f"🔹 **{route_name}**\n"
        response += f"   Route: {from_station} ↔ {to_station}\n"
        response += f"   Stations: {len(stations)}\n"
        response += f"   Via: {', '.join(route.get('major_areas_served', []))}\n\n"

    response += f"⏰ **Operating Hours:**\n"
    response += f"🌅 First Train: {operating_hours.get('first_train', '05:30 AM')}\n"
    response += f"🌙 Last Train: {operating_hours.get('last_train', '10:30 PM')}\n"
    response += (
        f"⚡ Frequency: {operating_hours.get('frequency_minutes', '20-30 mins')}\n\n"
    )

    # Interchange points
    interchange_points = mmts_data.get("interchange_points", [])
    if interchange_points:
        response += f"🔄 **Interchange Stations:**\n"
        for ip in interchange_points:
            station = ip.get("station")
            connects = ", ".join(ip.get("connects_to", []))
            response += f"   • {station}: {connects}\n"
        response += "\n"

    response += f"💰 **Fare:** ₹10-20 (varies by distance)\n\n"

    response += f"❓ **Ask me:**\n"
    response += f'• "Train from Falaknuma to Lingampally"\n'
    response += f'• "MMTS from Secunderabad to HITEC City"\n'
    response += f'• "How to reach Begumpet by train?"\n'

    return response

def find_routes_to_station(station: str) -> List[Dict]:
    """
    Find all MMTS routes that serve a particular station.
    
    Returns:
        List of route info with station details
    """
    mmts_data = load_mmts_data()
    
    if not mmts_data:
        return []
    
    routes = mmts_data.get("routes", [])
    serving_routes = []
    
    for route in routes:
        stations = route.get("stations", [])
        
        if station in stations:
            station_idx = stations.index(station)
            
            serving_routes.append({
                'line': route.get('route_name'),
                'route_from': route.get('route', {}).get('from'),
                'route_to': route.get('route', {}).get('to'),
                'station': station,
                'station_position': f"{station_idx + 1}/{len(stations)}",
                'stations': stations,
                'previous_stations': stations[:station_idx] if station_idx > 0 else [],
                'next_stations': stations[station_idx+1:] if station_idx < len(stations)-1 else []
            })
    
    return serving_routes


def format_routes_to_station(station: str, routes: List[Dict]) -> str:
    if not routes:
        return f"""🚆 **Station not found:** {station}

Try stations like:
Falaknuma, Secunderabad, Begumpet, Hi-Tech City, Lingampally
"""

    response = f"## 🚆 MMTS Routes for {station}\n\n"
    response += f"📍 **{station} is served by {len(routes)} line(s)**\n\n"

    for idx, route in enumerate(routes, 1):
        response += "---\n\n"
        response += f"### 🟦 {route['line']}\n\n"
        response += f"**Full Route:** {route['route_from']} → {route['route_to']}\n\n"
        response += f"**Stop Position:** {station} ({route['station_position']})\n\n"

        if route["previous_stations"]:
            prev = route["previous_stations"][-2:]
            response += "⬅️ **Arriving via**\n"
            response += " → ".join(prev) + f" → **{station}**\n\n"

        if route["next_stations"]:
            nxt = route["next_stations"][:2]
            response += "➡️ **Continuing to**\n"
            response += f"**{station}** → " + " → ".join(nxt) + "\n\n"

    mmts_data = load_mmts_data()
    operating = mmts_data.get("operating_hours", {})

    response += "---\n\n"
    response += "### ⏰ Operating Hours\n\n"
    response += f"🌅 First Train: {operating.get('first_train', '05:30 AM')}\n\n"
    response += f"🌙 Last Train: {operating.get('last_train', '10:30 PM')}\n\n"
    response += f"⚡ Frequency: {operating.get('frequency_minutes', '20–30 mins')}\n\n"

    response += f"💡 **Tip:** Ask like\n"
    response += f"“Train from Secunderabad to {station}”\n"

    return response