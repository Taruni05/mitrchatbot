import json
from pathlib import Path

def load_itinerary_data():
    try:
        with open("knowledge_base.json", "r", encoding="utf-8") as f:
            kb = json.load(f)

        profile = kb.get("hyderabad_comprehensive_profile", {})
        tourism = profile.get("tourism_and_landmarks", {})
        itineraries = tourism.get("Itinearies", {})

        return itineraries

    except Exception:
        return {}

# Replace ITINERARIES = {...} with:


def generate_itinerary(query: str):
    global ITINERARIES
    ITINERARIES = load_itinerary_data()

    
    query_lower = query.lower()
    
    # Detect intent
    if any(word in query_lower for word in ["one day", "single day", "tourist", "first time", "visitor"]):
        return format_itinerary(ITINERARIES["one_day_tourist"])
    
    elif any(word in query_lower for word in ["food", "biryani", "eat", "culinary", "foodie"]):
        return format_itinerary(ITINERARIES["food_trail"])
    
    elif any(word in query_lower for word in ["weekend", "saturday", "sunday", "it hub", "professional"]):
        return format_itinerary(ITINERARIES["it_hub_weekend"])
    
    elif any(word in query_lower for word in ["family", "kids", "children", "zoo"]):
        return format_itinerary(ITINERARIES["family_fun"])
    
    else:
        # Show all options
        return show_all_itineraries()


def format_itinerary(itinerary: dict):
    """Format a single itinerary"""
    response = f"🗓️ **{itinerary['name']}**\n\n"
    response += f"👥 **Best For:** {itinerary['best_for']}\n"
    response += f"⏰ **Duration:** {itinerary['duration']}\n"
    response += f"💰 **Budget:** {itinerary['budget']}\n\n"
    
    response += "📋 **SCHEDULE:**\n\n"
    
    for i, item in enumerate(itinerary['schedule'], 1):
        response += f"**{item['time']} - {item['activity']}**\n"
        response += f"📍 {item['location']}\n"
        response += f"⏱️ {item['duration']} | 💵 {item['cost']}\n"
        
        if 'must_try' in item:
            response += f"🍽️ Must Try: {item['must_try']}\n"
        
        if 'why' in item:
            response += f"✨ {item['why']}\n"
        
        response += f"💡 Tip: {item['tip']}\n\n"
    
    response += f"🚗 **Transportation:** {itinerary['transportation']}\n"
    response += f"💰 **Total Cost:** {itinerary['total_cost_estimate']}\n\n"
    
    if 'calories_warning' in itinerary:
        response += f"⚠️ {itinerary['calories_warning']}\n\n"
    
    response += "📱 **Pro Tips:**\n"
    response += "• Book restaurants in advance on weekends\n"
    response += "• Download Ola/Uber for easy transport\n"
    response += "• Carry cash for street food\n"
    response += "• Start early to avoid traffic\n"
    
    return response


def show_all_itineraries():
    """Show all available itinerary options"""
    response = "🗓️ **PERSONALIZED HYDERABAD ITINERARIES**\n\n"
    response += "I can create custom day plans for you! Choose one:\n\n"
    
    for key, itin in ITINERARIES.items():
        response += f"**{itin['name']}**\n"
        response += f"👥 {itin['best_for']}\n"
        response += f"⏰ {itin['duration']} | 💰 {itin['budget']}\n\n"
    
    response += "❓ **Ask me:**\n"
    response += '• "Plan my one-day Hyderabad tour"\n'
    response += '• "Create a food trail for me"\n'
    response += '• "Weekend itinerary for professionals"\n'
    response += '• "Family day out with kids"\n'
    
    return response


def get_custom_itinerary(preferences: dict):
    """
    Generate custom itinerary based on specific preferences
    Future: Can integrate with AI for more personalization
    """
    # This is a placeholder for future AI-powered customization
    budget = preferences.get('budget', 'medium')
    duration = preferences.get('duration', 'full_day')
    interests = preferences.get('interests', [])
    
    # For now, return closest match
    if 'food' in interests:
        return format_itinerary(ITINERARIES["food_trail"])
    elif 'history' in interests:
        return format_itinerary(ITINERARIES["one_day_tourist"])
    elif 'family' in interests:
        return format_itinerary(ITINERARIES["family_fun"])
    else:
        return format_itinerary(ITINERARIES["it_hub_weekend"])




