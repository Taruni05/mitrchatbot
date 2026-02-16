"""
Proactive Assistant Service
Provides intelligent, contextual suggestions based on time, weather, location, and user preferences.
"""

import streamlit as st
from datetime import datetime, time
from typing import List, Dict, Optional
from services.logger import get_logger

# Initialize logger
logger = get_logger(__name__)


class ProactiveAssistant:
    """Provides contextual suggestions without being asked"""
    
    @staticmethod
    def get_time_based_suggestions() -> List[Dict[str, str]]:
        """
        Suggest things based on time of day.
        
        Returns:
            List of suggestion dicts with 'text' and 'query' keys
        """
        current_hour = datetime.now().hour
        suggestions = []
        
        # Early Morning (5 AM - 8 AM)
        if 5 <= current_hour < 8:
            suggestions.extend([
                {
                    "text": "🌅 Good morning! Best breakfast spots open now",
                    "query": "best breakfast places in hyderabad"
                },
                {
                    "text": "☕ Irani chai cafes - perfect morning start",
                    "query": "best irani chai cafes hyderabad"
                },
                {
                    "text": "🏃 Morning jogging spots - beat the heat",
                    "query": "morning jogging parks in hyderabad"
                }
            ])
        
        # Morning Rush (8 AM - 10 AM)
        elif 8 <= current_hour < 10:
            suggestions.extend([
                {
                    "text": "🚇 Metro rush starting - check timings",
                    "query": "metro timings hyderabad"
                },
                {
                    "text": "🚦 Traffic updates - plan your route",
                    "query": "traffic conditions hyderabad"
                },
                {
                    "text": "☕ Quick breakfast spots near you",
                    "query": "fast breakfast places near me"
                }
            ])
        
        # Late Morning (10 AM - 12 PM)
        elif 10 <= current_hour < 12:
            suggestions.extend([
                {
                    "text": "🏛️ Museums & monuments - less crowded now",
                    "query": "museums in hyderabad"
                },
                {
                    "text": "☕ Best cafes for work/study",
                    "query": "work friendly cafes hyderabad"
                }
            ])
        
        # Lunch Time (12 PM - 2 PM)
        elif 12 <= current_hour < 14:
            suggestions.extend([
                {
                    "text": "🍛 Lunch time! Best biryani spots",
                    "query": "best biryani restaurants hyderabad"
                },
                {
                    "text": "🥘 Quick lunch thalis nearby",
                    "query": "best thali restaurants hyderabad"
                },
                {
                    "text": "🍕 Fast food options - beat the rush",
                    "query": "fast food restaurants near me"
                }
            ])
        
        # Afternoon (2 PM - 5 PM)
        elif 14 <= current_hour < 17:
            suggestions.extend([
                {
                    "text": "🏬 Shopping malls - less crowded now",
                    "query": "shopping malls in hyderabad"
                },
                {
                    "text": "☕ Coffee spots with AC - escape the heat",
                    "query": "best cafes in hyderabad"
                },
                {
                    "text": "🎬 Afternoon movie shows - check times",
                    "query": "movie theatres hyderabad"
                }
            ])
        
        # Evening (5 PM - 8 PM)
        elif 17 <= current_hour < 20:
            suggestions.extend([
                {
                    "text": "🌆 Sunset at Hussain Sagar - perfect timing!",
                    "query": "hussain sagar lake timings"
                },
                {
                    "text": "🚦 Evening traffic alert - check routes",
                    "query": "traffic conditions gachibowli hitech city"
                },
                {
                    "text": "🍿 Evening food street - explore local bites",
                    "query": "street food places hyderabad"
                }
            ])
        
        # Night (8 PM - 11 PM)
        elif 20 <= current_hour < 23:
            suggestions.extend([
                {
                    "text": "🌙 Late-night cafes still open",
                    "query": "late night cafes hyderabad"
                },
                {
                    "text": "🍽️ Dinner recommendations nearby",
                    "query": "best restaurants for dinner hyderabad"
                },
                {
                    "text": "🎭 Cultural events happening tonight",
                    "query": "events in hyderabad today"
                }
            ])
        
        # Late Night (11 PM - 5 AM)
        else:
            suggestions.extend([
                {
                    "text": "🌙 24-hour eateries open now",
                    "query": "24 hour restaurants hyderabad"
                },
                {
                    "text": "🏥 Emergency services & pharmacies",
                    "query": "24 hour pharmacies hyderabad"
                }
            ])
        
        return suggestions
    
    @staticmethod
    def get_weather_based_suggestions(weather_data: Optional[Dict] = None) -> List[Dict[str, str]]:
        """
        Suggest things based on current weather.
        
        Args:
            weather_data: Weather data from API (temp, condition, etc.)
        
        Returns:
            List of weather-based suggestions
        """
        suggestions = []
        
        if not weather_data:
            return suggestions
        
        try:
            temp = weather_data.get("main", {}).get("temp", 0)
            condition = weather_data.get("weather", [{}])[0].get("main", "")
            humidity = weather_data.get("main", {}).get("humidity", 0)
            
            # Hot weather (> 35°C)
            if temp > 35:
                suggestions.extend([
                    {
                        "text": "🔥 Very hot! Indoor attractions recommended",
                        "query": "indoor activities hyderabad"
                    },
                    {
                        "text": "☕ Cool down at Irani chai cafes",
                        "query": "best irani cafes with AC"
                    },
                    {
                        "text": "🏊 Swimming pools & water parks",
                        "query": "swimming pools in hyderabad"
                    }
                ])
            
            # Pleasant weather (20°C - 30°C)
            elif 20 <= temp <= 30:
                suggestions.extend([
                    {
                        "text": "🌤️ Perfect weather for outdoor sightseeing!",
                        "query": "monuments to visit in hyderabad"
                    },
                    {
                        "text": "🚶 Great for walking tours",
                        "query": "walking tours hyderabad"
                    }
                ])
            
            # Cool weather (< 20°C)
            elif temp < 20:
                suggestions.extend([
                    {
                        "text": "🧥 Cool weather - perfect for Golconda Fort!",
                        "query": "golconda fort timings"
                    },
                    {
                        "text": "☕ Hot chai & pakodas - best spots",
                        "query": "best chai and pakoda places"
                    }
                ])
            
            # Rainy weather
            if condition in ["Rain", "Drizzle", "Thunderstorm"]:
                suggestions.extend([
                    {
                        "text": "☔ Raining! Indoor museums & malls",
                        "query": "indoor activities hyderabad rainy day"
                    },
                    {
                        "text": "🍵 Cozy cafes for rainy day vibes",
                        "query": "best cafes for rainy day hyderabad"
                    }
                ])
            
            # High humidity
            if humidity > 70:
                suggestions.extend([
                    {
                        "text": "💨 High humidity - AC malls recommended",
                        "query": "shopping malls in hyderabad"
                    }
                ])
        
        except Exception as e:
            logger.error(f"Error processing weather suggestions: {e}")
        
        return suggestions
    
    @staticmethod
    def get_location_based_suggestions(user_area: str) -> List[Dict[str, str]]:
        """
        Suggest nearby things based on user's current area.
        
        Args:
            user_area: User's area/neighborhood
        
        Returns:
            List of location-specific suggestions
        """
        suggestions = []
        area_lower = user_area.lower()
        
        # Gachibowli / HITEC City
        if any(x in area_lower for x in ["gachibowli", "hitech", "madhapur"]):
            suggestions.extend([
                {
                    "text": "🍕 Nearby: Olive Bistro, Forum Sujana Mall",
                    "query": "restaurants in gachibowli"
                },
                {
                    "text": "☕ Work cafes: Starbucks, Third Wave Coffee",
                    "query": "work friendly cafes gachibowli"
                },
                {
                    "text": "🎬 AMB Cinemas - check latest movies",
                    "query": "amb cinemas gachibowli showtimes"
                }
            ])
        
        # Banjara Hills / Jubilee Hills
        elif any(x in area_lower for x in ["banjara", "jubilee"]):
            suggestions.extend([
                {
                    "text": "🍽️ Fine dining: Collage, Over The Moon",
                    "query": "fine dining restaurants banjara hills"
                },
                {
                    "text": "🏬 Nearby: Road No. 10 shopping",
                    "query": "shopping in banjara hills"
                },
                {
                    "text": "☕ Trendy cafes: Roastery, Autumn Leaf",
                    "query": "best cafes banjara hills"
                }
            ])
        
        # Secunderabad
        elif "secunderabad" in area_lower:
            suggestions.extend([
                {
                    "text": "🏛️ Qutb Shahi Tombs - 20 min away",
                    "query": "qutb shahi tombs timings"
                },
                {
                    "text": "🍰 Karachi Bakery - iconic Hyderabad",
                    "query": "karachi bakery secunderabad"
                },
                {
                    "text": "🚇 Metro connectivity - check routes",
                    "query": "metro routes from secunderabad"
                }
            ])
        
        # Old City / Charminar
        elif any(x in area_lower for x in ["charminar", "old city", "laad bazaar"]):
            suggestions.extend([
                {
                    "text": "🕌 Charminar & Laad Bazaar - explore",
                    "query": "things to do near charminar"
                },
                {
                    "text": "☕ Nimrah Cafe - legendary Irani chai",
                    "query": "nimrah cafe near charminar"
                },
                {
                    "text": "🍛 Shah Ghouse - famous biryani nearby",
                    "query": "shah ghouse biryani old city"
                }
            ])
        
        # Kukatpally / KPHB
        elif any(x in area_lower for x in ["kukatpally", "kphb"]):
            suggestions.extend([
                {
                    "text": "🏬 Manjeera Mall - shopping & movies",
                    "query": "manjeera mall kukatpally"
                },
                {
                    "text": "🍕 Food courts & restaurants nearby",
                    "query": "restaurants in kukatpally"
                }
            ])
        
        # Begumpet / Somajiguda
        elif any(x in area_lower for x in ["begumpet", "somajiguda", "panjagutta"]):
            suggestions.extend([
                {
                    "text": "🏛️ Birla Mandir - peaceful temple visit",
                    "query": "birla mandir hyderabad timings"
                },
                {
                    "text": "🍽️ Paradise Biryani - original branch",
                    "query": "paradise biryani secunderabad"
                }
            ])
        
        return suggestions
    
    @staticmethod
    def get_preference_based_suggestions(preferences: Dict) -> List[Dict[str, str]]:
        """
        Suggest things based on user's saved preferences and interests.
        
        Args:
            preferences: User preferences from database
        
        Returns:
            List of personalized suggestions
        """
        suggestions = []
        
        # Check favorite cuisines
        fav_cuisines = preferences.get("favorite_cuisines", [])
        if "biryani" in fav_cuisines:
            suggestions.append({
                "text": "🍛 Your favorite: Top biryani spots",
                "query": "best biryani restaurants hyderabad"
            })
        
        if "chinese" in fav_cuisines:
            suggestions.append({
                "text": "🥡 Chinese food recommendations for you",
                "query": "best chinese restaurants hyderabad"
            })
        
        # Check interests
        interests = preferences.get("interests", [])
        if "history" in interests:
            suggestions.append({
                "text": "🏛️ Historical sites you might love",
                "query": "historical monuments hyderabad"
            })
        
        if "shopping" in interests:
            suggestions.append({
                "text": "🛍️ Shopping destinations for you",
                "query": "best shopping places hyderabad"
            })
        
        # Check if user visits frequently
        total_interactions = preferences.get("total_interactions", 0)
        if total_interactions > 10:
            suggestions.append({
                "text": "✨ Discover hidden gems - off the beaten path",
                "query": "hidden places to visit in hyderabad"
            })
        
        return suggestions
    
    @staticmethod
    def get_event_based_suggestions() -> List[Dict[str, str]]:
        """
        Suggest things based on current events, festivals, etc.
        
        Returns:
            List of event-based suggestions
        """
        suggestions = []
        current_date = datetime.now()
        current_month = current_date.month
        
        # Festival-based suggestions
        # Ramadan (varies, but typically March-April)
        if current_month in [3, 4]:
            suggestions.append({
                "text": "🌙 Ramadan special: Haleem hotspots",
                "query": "best haleem in hyderabad"
            })
        
        # Diwali (October-November)
        if current_month in [10, 11]:
            suggestions.extend([
                {
                    "text": "🪔 Diwali shopping - Laad Bazaar, Begum Bazaar",
                    "query": "diwali shopping places hyderabad"
                },
                {
                    "text": "🎆 Diwali sweets - best shops",
                    "query": "best sweet shops hyderabad"
                }
            ])
        
        # Bonalu Festival (July-August)
        if current_month in [7, 8]:
            suggestions.append({
                "text": "🎊 Bonalu festival celebrations in the city",
                "query": "bonalu festival celebrations hyderabad"
            })
        
        # Weekend suggestions (Friday-Sunday)
        if current_date.weekday() >= 4:  # Friday = 4
            suggestions.extend([
                {
                    "text": "🎉 Weekend plans: Best events happening",
                    "query": "weekend events in hyderabad"
                },
                {
                    "text": "🎬 New movie releases this weekend",
                    "query": "movies playing in hyderabad this weekend"
                }
            ])
        
        return suggestions
    
    @staticmethod
    def get_smart_suggestions(max_suggestions: int = 3) -> List[Dict[str, str]]:
        """
        Combine all suggestion sources intelligently.
        
        Args:
            max_suggestions: Maximum number of suggestions to return
        
        Returns:
            List of smart, contextual suggestions
        """
        all_suggestions = []
        
        # 1. Time-based (always relevant)
        time_suggestions = ProactiveAssistant.get_time_based_suggestions()
        all_suggestions.extend(time_suggestions[:2])  # Take top 2
        
        # 2. Weather-based (if available)
        try:
            from services.weatherapi import get_weather_by_coords
            from services.locations import HYDERABAD_AREA_COORDS
            
            # Get weather for user's area or default to Hyderabad center
            area = st.session_state.get("selected_area", "hitech city")
            coords = HYDERABAD_AREA_COORDS.get(area.lower(), (17.4065, 78.4772))
            
            weather_data = get_weather_by_coords(*coords)
            if weather_data:
                weather_suggestions = ProactiveAssistant.get_weather_based_suggestions(weather_data)
                all_suggestions.extend(weather_suggestions[:1])  # Take top 1
        except Exception as e:
            logger.warning(f"Could not get weather suggestions: {e}")
        
        # 3. Location-based (from selected area)
        current_area = st.session_state.get("selected_area", "")
        if current_area:
            location_suggestions = ProactiveAssistant.get_location_based_suggestions(current_area)
            all_suggestions.extend(location_suggestions[:2])  # Take top 2
        
        # 4. Preference-based (if user is logged in)
        try:
            from services.auth import is_logged_in
            from services.user_store import load_preferences
            
            if is_logged_in():
                preferences = load_preferences()
                if preferences:
                    pref_suggestions = ProactiveAssistant.get_preference_based_suggestions(preferences)
                    all_suggestions.extend(pref_suggestions[:1])  # Take top 1
        except Exception as e:
            logger.debug(f"Could not get preference suggestions: {e}")
        
        # 5. Event-based (festivals, weekends)
        event_suggestions = ProactiveAssistant.get_event_based_suggestions()
        all_suggestions.extend(event_suggestions[:1])  # Take top 1
        
        # Remove duplicates while preserving order
        seen = set()
        unique_suggestions = []
        for suggestion in all_suggestions:
            key = suggestion["text"]
            if key not in seen:
                seen.add(key)
                unique_suggestions.append(suggestion)
        
        # Return top N suggestions
        return unique_suggestions[:max_suggestions]


# Helper function for easy access
def get_proactive_suggestions(max_suggestions: int = 3) -> List[Dict[str, str]]:
    """
    Get smart proactive suggestions for the user.
    
    Args:
        max_suggestions: Maximum number of suggestions
    
    Returns:
        List of suggestion dicts with 'text' and 'query'
    """
    return ProactiveAssistant.get_smart_suggestions(max_suggestions)