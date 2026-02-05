import json
from pathlib import Path
import re

def load_metro_data():
    """Load Metro Rail data from knowledge base."""
    kb_path = Path(__file__).resolve().parent.parent / "knowledge_base.json"
    
    with open(kb_path, "r", encoding="utf-8") as f:
        kb = json.load(f)
    
    profile = kb.get("hyderabad_comprehensive_profile", {})
    transport = profile.get("infrastructure", {}).get("transport", [])
    
    # Find Metro Rail
    for t in transport:
        if t.get("mode") == "Metro Rail":
            return t
    
    return None


def get_metro_line_by_station(station_name):
    """
    Find which metro line(s) a station is on.
    
    Args:
        station_name: Name of the station
    
    Returns:
        List of line names, or empty list if not found
    """
    metro = load_metro_data()
    if not metro:
        return []
    
    station_lower = station_name.lower()
    lines_found = []
    
    for line in metro.get("lines", []):
        stations = line.get("stations", [])
        for station in stations:
            if station.lower() == station_lower or station_lower in station.lower():
                lines_found.append(line["line_name"])
                break
    
    return lines_found


def find_metro_route(from_station, to_station):
    """
    Find metro route between two stations.
    
    Args:
        from_station: Starting station name
        to_station: Destination station name
    
    Returns:
        Dict with route info, or None if no route found
    """
    metro = load_metro_data()
    if not metro:
        return None
    
    from_lower = from_station.lower()
    to_lower = to_station.lower()
    
    # Find which lines each station is on
    from_lines = []
    to_lines = []
    from_line_data = {}
    to_line_data = {}
    
    for line in metro.get("lines", []):
        stations = line.get("stations", [])
        stations_lower = [s.lower() for s in stations]
        
        from_idx = None
        to_idx = None
        
        # Find from station
        for i, station in enumerate(stations_lower):
            if from_lower in station or station in from_lower:
                from_idx = i
                from_lines.append(line["line_name"])
                from_line_data[line["line_name"]] = {
                    "line": line,
                    "index": i,
                    "exact_name": stations[i]
                }
        
        # Find to station
        for i, station in enumerate(stations_lower):
            if to_lower in station or station in to_lower:
                to_idx = i
                to_lines.append(line["line_name"])
                to_line_data[line["line_name"]] = {
                    "line": line,
                    "index": i,
                    "exact_name": stations[i]
                }
    
    if not from_lines:
        return {"error": f"Station '{from_station}' not found"}
    if not to_lines:
        return {"error": f"Station '{to_station}' not found"}
    
    # Check for direct route (both stations on same line)
    common_lines = set(from_lines) & set(to_lines)
    
    if common_lines:
        # Direct route
        line_name = list(common_lines)[0]
        line_info = from_line_data[line_name]["line"]
        from_idx = from_line_data[line_name]["index"]
        to_idx = to_line_data[line_name]["index"]
        
        stations = line_info["stations"]
        
        if from_idx < to_idx:
            route_stations = stations[from_idx:to_idx+1]
            direction = f"{line_info['route']['to']} direction"
        else:
            route_stations = list(reversed(stations[to_idx:from_idx+1]))
            direction = f"{line_info['route']['from']} direction"
        
        return {
            "type": "direct",
            "line": line_name,
            "color": line_info.get("color", ""),
            "from": from_line_data[line_name]["exact_name"],
            "to": to_line_data[line_name]["exact_name"],
            "stations": route_stations,
            "num_stops": len(route_stations) - 1,
            "direction": direction
        }
    
    # Check for interchange route
    # Find if any interchange connects the lines
    from_line_name = from_lines[0]
    to_line_name = to_lines[0]
    from_line = from_line_data[from_line_name]["line"]
    to_line = to_line_data[to_line_name]["line"]
    
    # Look for interchange stations
    interchange_station = None
    for interchange in from_line.get("interchanges", []):
        if to_line_name in interchange.get("connects_to", []):
            interchange_station = interchange["station"]
            break
    
    if interchange_station:
        # Two-leg journey with interchange
        # Leg 1: from → interchange
        from_idx = from_line_data[from_line_name]["index"]
        interchange_idx = from_line["stations"].index(interchange_station)
        
        if from_idx < interchange_idx:
            leg1_stations = from_line["stations"][from_idx:interchange_idx+1]
            leg1_direction = f"{from_line['route']['to']} direction"
        else:
            leg1_stations = list(reversed(from_line["stations"][interchange_idx:from_idx+1]))
            leg1_direction = f"{from_line['route']['from']} direction"
        
        # Leg 2: interchange → to
        to_idx = to_line_data[to_line_name]["index"]
        interchange_idx = to_line["stations"].index(interchange_station)
        
        if interchange_idx < to_idx:
            leg2_stations = to_line["stations"][interchange_idx:to_idx+1]
            leg2_direction = f"{to_line['route']['to']} direction"
        else:
            leg2_stations = list(reversed(to_line["stations"][to_idx:interchange_idx+1]))
            leg2_direction = f"{to_line['route']['from']} direction"
        
        return {
            "type": "interchange",
            "from": from_line_data[from_line_name]["exact_name"],
            "to": to_line_data[to_line_name]["exact_name"],
            "interchange": interchange_station,
            "leg1": {
                "line": from_line_name,
                "color": from_line.get("color", ""),
                "stations": leg1_stations,
                "num_stops": len(leg1_stations) - 1,
                "direction": leg1_direction
            },
            "leg2": {
                "line": to_line_name,
                "color": to_line.get("color", ""),
                "stations": leg2_stations,
                "num_stops": len(leg2_stations) - 1,
                "direction": leg2_direction
            }
        }
    
    return {"error": "No route found between these stations"}


def extract_stations_from_query(query):
    """
    Extract from and to stations from natural language query.
    
    Args:
        query: User query (e.g., "metro from ameerpet to hitech city")
    
    Returns:
        Tuple of (from_station, to_station) or (None, None)
    """
    query_lower = query.lower()
    
    # Pattern: "from X to Y"
    match = re.search(r'from\s+([a-z\s]+?)\s+to\s+([a-z\s]+)', query_lower)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    
    # Pattern: "X to Y"
    match = re.search(r'([a-z\s]+?)\s+to\s+([a-z\s]+)', query_lower)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    
    return None, None


def format_metro_route(route_info):
    """Format metro route information for display."""
    if not route_info:
        return "❌ Could not find metro route."
    
    if "error" in route_info:
        return f"❌ {route_info['error']}"
    
    if route_info["type"] == "direct":
        # Direct route on single line
        response = f"🚇 **Metro Route: {route_info['from']} → {route_info['to']}**\n\n"
        response += f"✅ **Direct Route** on **{route_info['line']}** {route_info.get('color', '')} Line\n"
        response += f"📍 **Direction:** {route_info['direction']}\n"
        response += f"🚉 **Stops:** {route_info['num_stops']} stop(s)\n\n"
        
        response += "**Stations:**\n"
        for i, station in enumerate(route_info['stations']):
            if i == 0:
                response += f"   🟢 {station} (start)\n"
            elif i == len(route_info['stations']) - 1:
                response += f"   🔴 {station} (destination)\n"
            else:
                response += f"   ⚪ {station}\n"
        
        response += f"\n💡 **Travel Time:** ~{route_info['num_stops'] * 2} minutes"
        
    else:
        # Interchange route
        response = f"🚇 **Metro Route: {route_info['from']} → {route_info['to']}**\n\n"
        response += f"🔄 **Route with Interchange** at **{route_info['interchange']}**\n\n"
        
        # Leg 1
        leg1 = route_info['leg1']
        response += f"**Leg 1:** {leg1['line']} {leg1.get('color', '')} Line\n"
        response += f"📍 Direction: {leg1['direction']}\n"
        response += f"🚉 Stops: {leg1['num_stops']}\n"
        for i, station in enumerate(leg1['stations']):
            if i == 0:
                response += f"   🟢 {station} (start)\n"
            elif i == len(leg1['stations']) - 1:
                response += f"   🔄 {station} (CHANGE HERE)\n"
            else:
                response += f"   ⚪ {station}\n"
        
        # Leg 2
        leg2 = route_info['leg2']
        response += f"\n**Leg 2:** {leg2['line']} {leg2.get('color', '')} Line\n"
        response += f"📍 Direction: {leg2['direction']}\n"
        response += f"🚉 Stops: {leg2['num_stops']}\n"
        for i, station in enumerate(leg2['stations']):
            if i == 0:
                response += f"   🔄 {station} (interchange)\n"
            elif i == len(leg2['stations']) - 1:
                response += f"   🔴 {station} (destination)\n"
            else:
                response += f"   ⚪ {station}\n"
        
        total_stops = leg1['num_stops'] + leg2['num_stops']
        response += f"\n💡 **Total Travel Time:** ~{total_stops * 2} minutes (+ 5 min for interchange)"
    
    response += "\n\n⏰ **Metro Timings:** 6:00 AM - 11:00 PM daily"
    response += "\n💳 **Fare:** ₹10-60 depending on distance"
    
    return response


def format_metro_station_list():
    """Format a complete list of all metro stations by line."""
    metro = load_metro_data()
    if not metro:
        return "Metro data unavailable."
    
    response = "🚇 **HYDERABAD METRO STATIONS**\n\n"
    
    for line in metro.get("lines", []):
        color_emoji = {"Red": "🔴", "Blue": "🔵", "Green": "🟢"}.get(line.get("color", ""), "⚪")
        response += f"{color_emoji} **{line['line_name']}** ({line['route']['from']} ↔ {line['route']['to']})\n"
        
        stations = line.get("stations", [])
        interchanges = {ic["station"] for ic in line.get("interchanges", [])}
        
        for i, station in enumerate(stations, 1):
            if station in interchanges:
                response += f"   {i:2d}. {station} 🔄\n"
            else:
                response += f"   {i:2d}. {station}\n"
        
        response += "\n"
    
    response += "🔄 = Interchange stations\n\n"
    response += "💡 **Try:** \"metro from ameerpet to hitech city\" or \"metro route to nagole\""
    
    return response


def get_general_metro_info():
    """Get general metro information."""
    metro = load_metro_data()
    if not metro:
        return "Metro data unavailable."
    
    response = "🚇 **HYDERABAD METRO RAIL**\n\n"
    response += f"**Operator:** {metro.get('operator', 'L&T Metro Rail Hyderabad Limited')}\n"
    response += f"**Operational Since:** {metro.get('operational_since', '2017')}\n\n"
    
    response += "**Lines:**\n"
    for line in metro.get("lines", []):
        color_emoji = {"Red": "🔴", "Blue": "🔵", "Green": "🟢"}.get(line.get("color", ""), "⚪")
        num_stations = len(line.get("stations", []))
        response += f"   {color_emoji} **{line['line_name']}:** {line['route']['from']} ↔ {line['route']['to']} ({num_stations} stations)\n"
    
    hours = metro.get("operating_hours", {})
    response += f"\n⏰ **Timings:** {hours.get('first_train', '6:00 AM')} - {hours.get('last_train', '11:00 PM')}\n"
    response += "💳 **Fare:** ₹10-60 (distance-based)\n"
    response += "🎫 **Payment:** Tokens, Metro cards, QR codes\n\n"
    
    response += "🔄 **Major Interchanges:**\n"
    response += "   • Ameerpet (Red ↔ Blue)\n"
    response += "   • MG Bus Station (Red ↔ Green)\n"
    response += "   • Parade Grounds (Blue ↔ Green)\n\n"
    
    response += "💡 **Ask me:**\n"
    response += '   • "metro stations list"\n'
    response += '   • "metro from ameerpet to hitech city"\n'
    response += '   • "how to reach raidurg by metro"'
    
    return response