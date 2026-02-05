import json
from pathlib import Path

def load_crowd_data():
    """Load knowledge base with crowd information."""
    kb_path = Path(__file__).resolve().parent.parent / "knowledge_base.json"
    
    with open(kb_path, "r", encoding="utf-8") as f:
        kb = json.load(f)
    
    profile = kb.get("hyderabad_comprehensive_profile", {})
    tourism = profile.get("tourism_and_landmarks", {})
    
    return tourism


def get_all_locations_with_crowds():
    """
    Extract all locations that have crowd_level data.
    Returns a list of dicts with name, type, and crowd_level.
    """
    tourism = load_crowd_data()
    locations = []
    
    # Monuments
    for item in tourism.get("historical_monuments", []):
        if "crowd_level" in item:
            locations.append({
                "name": item["name"],
                "type": "Monument",
                "location": item.get("location", "Hyderabad"),
                "crowd_level": item["crowd_level"],
                "description": item.get("description", "")
            })
    
    # Parks
    for item in tourism.get("parks_and_nature", []):
        if "crowd_level" in item:
            locations.append({
                "name": item["name"],
                "type": "Park",
                "location": item.get("location", "Hyderabad"),
                "crowd_level": item["crowd_level"],
                "description": item.get("description", "")
            })
    
    # Modern Attractions
    for item in tourism.get("modern_attractions", []):
        if "crowd_level" in item:
            locations.append({
                "name": item["name"],
                "type": "Attraction",
                "location": item.get("location", "Hyderabad"),
                "crowd_level": item["crowd_level"],
                "description": item.get("description", "")
            })
    
    # Malls
    shopping = tourism.get("shopping_hubs", {})
    for item in shopping.get("premium_malls", []):
        if "crowd_level" in item:
            locations.append({
                "name": item["name"],
                "type": "Mall",
                "location": item.get("location", "Hyderabad"),
                "crowd_level": item["crowd_level"],
                "best_for": item.get("best_for", "")
            })
    
    return locations


def find_crowd_info(query: str):
    """
    Find crowd information for a specific location.
    
    Args:
        query: User's search query (e.g., "charminar", "hussain sagar")
    
    Returns:
        Dict with location details and crowd info, or None if not found
    """
    locations = get_all_locations_with_crowds()
    query_lower = query.lower()
    
    # Try exact or partial match
    for loc in locations:
        name_lower = loc["name"].lower()
        if query_lower in name_lower or name_lower in query_lower:
            return loc
    
    return None


def format_single_crowd_info(location: dict):
    """Format crowd information for a single location."""
    crowd = location["crowd_level"]
    
    response = f"👥 **Crowd Info: {location['name']}**\n\n"
    response += f"📍 **Location:** {location['location']}\n"
    response += f"🏛️ **Type:** {location['type']}\n\n"
    
    response += "📊 **Crowd Levels:**\n"
    response += f"   • Weekdays: {crowd['weekday']}\n"
    response += f"   • Weekends: {crowd['weekend']}\n\n"
    
    response += f"✅ **Best Time to Visit:** {crowd['best_time']}\n"
    
    if 'avoid' in crowd:
        response += f"⚠️ **Avoid:** {crowd['avoid']}\n"
    
    if 'notes' in crowd:
        response += f"\n💡 **Tips:** {crowd['notes']}"
    
    return response


def format_all_crowds_summary():
    """Format a summary of crowd patterns across all locations."""
    locations = get_all_locations_with_crowds()
    
    response = "👥 **CROWD GUIDE - BEST TIME TO VISIT**\n\n"
    
    # Group by type
    by_type = {}
    for loc in locations:
        loc_type = loc["type"]
        if loc_type not in by_type:
            by_type[loc_type] = []
        by_type[loc_type].append(loc)
    
    # Show each category
    for loc_type in ["Monument", "Park", "Attraction", "Mall"]:
        if loc_type not in by_type:
            continue
        
        items = by_type[loc_type]
        if loc_type == "Monument":
            emoji = "🏛️"
        elif loc_type == "Park":
            emoji = "🌳"
        elif loc_type == "Attraction":
            emoji = "🎬"
        else:
            emoji = "🛍️"
        
        response += f"**{emoji} {loc_type}s:**\n"
        for item in items:
            crowd = item["crowd_level"]
            response += f"• **{item['name']}**\n"
            response += f"  ✅ Best: {crowd['best_time']}\n"
            response += f"  📊 Weekend: {crowd['weekend']}\n"
        response += "\n"
    
    response += "💡 **General Tips:**\n"
    response += "• Weekday mornings = Least crowds everywhere\n"
    response += "• Weekend afternoons = Avoid monuments & parks\n"
    response += "• National holidays = Expect high crowds at all tourist spots\n"
    response += "• Early birds get the best experience (6-9 AM)\n\n"
    
    response += "❓ **Ask me:** \"crowd at Charminar\" or \"best time to visit Ramoji Film City\""
    
    return response


def format_quick_crowd_comparison():
    """Format a quick comparison of least crowded places."""
    locations = get_all_locations_with_crowds()
    
    # Find places with "Low" weekday crowds
    quiet_places = []
    for loc in locations:
        weekday = loc["crowd_level"]["weekday"].lower()
        if "low" in weekday:
            quiet_places.append(loc)
    
    if not quiet_places:
        return ""
    
    response = "🤫 **QUIET SPOTS (Low Crowds on Weekdays):**\n\n"
    for place in quiet_places:
        response += f"• **{place['name']}** ({place['type']})\n"
        response += f"  Best: {place['crowd_level']['best_time']}\n\n"
    
    return response


def get_crowd_info(query: str):
    """
    Main function to get crowd information based on query.
    
    Args:
        query: User's question about crowds
    
    Returns:
        Formatted string with crowd information
    """
    query_lower = query.lower()
    
    # Check for general queries
    if any(word in query_lower for word in ["all", "summary", "guide", "list", "overall"]):
        return format_all_crowds_summary()
    
    if any(word in query_lower for word in ["quiet", "peaceful", "less crowd", "least crowd", "empty"]):
        return format_quick_crowd_comparison()
    
    # Try to find specific location
    location = find_crowd_info(query)
    if location:
        return format_single_crowd_info(location)
    
    # Default: show all
    return format_all_crowds_summary()