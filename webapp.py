# web_app.py - Beautiful Web Interface for Hyderabad Chatbot
import streamlit as st
import json
from langgraph.graph import StateGraph, END
from typing import TypedDict
from services.locations import HYDERABAD_AREA_COORDS
from services.weatherapi import (
    get_weather_by_coords,
    get_aqi_by_coords,
    format_weather,
    format_aqi,
    get_aqi_advice,
)
from services.ai_food import generate_food_recommendation
from services.fuel_prices import get_fuel_prices_hyderabad, format_fuel_prices
# At top of webapp.py (around line 10), add:
from services.rtc_bus import (
    extract_locations_from_query,
    get_bus_routes,
    format_bus_routes,
    get_general_bus_info,
    get_connecting_routes,       
    format_connecting_routes,  
)

from services.mmts_trains import (
    extract_stations_from_query,
    find_mmts_route,
    format_mmts_route,
    get_general_mmts_info,
    find_routes_to_station,      
    format_routes_to_station
)

from services.news import get_hyderabad_news
from services.ai_news import summarize_news

from services.shopping import get_mall_info
from services.movies import get_movie_info
from services.itineary import generate_itinerary
from services.traffic import get_traffic_flow, format_traffic
from services.translator import translate_response, get_language_name

from services.voice_service import (
    create_voice_input_button,
    create_voice_output_player,
    create_voice_settings_ui
)



import base64
from datetime import datetime

import os
os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]


# ========================================
# PAGE CONFIG - Must be first Streamlit command
# ========================================
st.set_page_config(
    page_title="Hyderabad City Guide",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded",
)
# Header
st.title("🏙️ Hyderabad City Guide")
st.markdown("### Your Personal Assistant for Exploring Hyderabad")
st.markdown("---")

st.empty()

# Default dashboard location
if "selected_area" not in st.session_state:
    st.session_state.selected_area = "Hyderabad (Central)"
    st.session_state.selected_coords = (17.3850, 78.4867)

if st.session_state.get("trigger_dashboard_update"):
    st.session_state.trigger_dashboard_update = False
    st.rerun()


def load_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


with st.spinner("Loading theme…"):
    hour = datetime.now().hour

    if 6 <= hour < 18:
        bg_image = load_base64("hyderabad_day.jpg")
    else:
        bg_image = load_base64("hyderabad_night.jpg")


mode = st.sidebar.radio("Theme", ["Auto", "Day", "Night"])

if mode == "Day":
    bg_image = load_base64("hyderabad_day.jpg")
elif mode == "Night":
    bg_image = load_base64("hyderabad_night.jpg")

st.markdown(
    f"""
<style>

/* ================================
GLOBAL BACKGROUND
=============================== */
html, body, .stApp, [data-testid="stAppViewContainer"] {{
    height: 100%;
    margin: 0;
    background:
        linear-gradient(
            rgba(0, 0, 0, 0.6),
            rgba(0, 0, 0, 0.6)
        ),
        url("data:image/jpeg;base64,{bg_image}");
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
}}

/* ================================
REMOVE STREAMLIT DEFAULT LAYERS
=============================== */
[data-testid="stHeader"],
[data-testid="stAppHeader"],
[data-testid="stToolbar"] {{
    background: transparent !important;
}}

/* ================================
SIDEBAR
=============================== */
[data-testid="stSidebar"] {{
    background: rgba(0, 0, 0, 0.78) !important;
    backdrop-filter: blur(14px);
    border-right: 1px solid rgba(255,255,255,0.08);
}}

/* ================================
CHAT MESSAGES
=============================== */
[data-testid="stChatMessage"] {{
    background: rgba(255, 255, 255, 0.12) !important;
    border-radius: 14px;
    padding: 12px;
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255,255,255,0.08);
}}

/* ================================
TEXT READABILITY
=============================== */
h1, h2, h3, h4, p, span,
[data-testid="stMarkdownContainer"] {{
    color: #ffffff !important;
    text-shadow: 0 1px 3px rgba(0,0,0,0.85);
}}

/* ================================
MOBILE OPTIMIZATION
=============================== */
@media (max-width: 768px) {{
    html, body, .stApp {{
        background-attachment: scroll;
    }}
}}

</style>
""",
    unsafe_allow_html=True,
)


# ========================================
# LOAD KNOWLEDGE BASE
# ========================================
@st.cache_resource
def load_knowledge_base():
    """Load knowledge base (cached for performance)"""
    try:
        with open("knowledge_base.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"❌ Error loading knowledge base: {e}")
        return None


with st.spinner("Loading city knowledge base…"):
    KB = load_knowledge_base()

if KB is None:
    st.stop()


PROFILE = KB.get("hyderabad_comprehensive_profile", {})
EMERGENCY = KB.get("emergency contacts", {})


# ========================================
# BOT STATE
# ========================================
class BotState(TypedDict):
    user_input: str
    intent: str
    response: str


# ========================================
# BOT LOGIC (Same as your chatbot)
# ========================================


def get_biryani_restaurants():
    """Get biryani restaurants"""
    restaurants_data = KB.get("restaurants", {})
    heritage = restaurants_data.get("Heritage_Regional", [])

    response = "🍛 **BEST BIRYANI PLACES IN HYDERABAD:**\n\n"

    for i, rest in enumerate(heritage[:7]):
        name = rest.get("name", "Unknown")
        price = rest.get("price_range", {})
        location = rest.get("main_branch", {}).get("location", "Hyderabad")
        hours = rest.get("opening_hours", {}).get("Monday", "11:00 AM - 11:00 PM")

        response += f"**{i + 1}. {name}**\n"
        response += f"📍 {location}\n"
        response += f"💰 ₹{price.get('min', 150)} - ₹{price.get('max', 600)}\n"
        response += f"⏰ {hours}\n\n"

    response += "💡 **Pro Tip:** Try the mutton biryani for the authentic Hyderabadi experience!"
    return response


def classify_intent(state: BotState):
    """Classify user intent"""
    message = state["user_input"].lower()

    if any(
        message.strip().startswith(word) for word in ["hello", "hi", "hey", "namaste"]
    ):
        state["intent"] = "greeting"
    elif any(word in message for word in ["emergency", "police", "ambulance", "fire"]):
        state["intent"] = "emergency"
    elif any(word in message for word in ["mmts", "train", "suburban rail"]) or ("from" in message and "to" in message and any(w in message for w in ["train", "rail"])):
        state["intent"] = "mmts"
    elif any(word in message for word in ["bus", "rtc", "tsrtc"]):
        state["intent"] = "bus"
    elif any(
        word in message
        for word in ["weather", "temperature", "rain", "climate", "forecast"]
    ):
        state["intent"] = "weather"
    elif any(word in message for word in ["mall", "shopping", "shop", "market", "ikea", "inorbit", "gvk", "sale", "discount"]):
        state["intent"] = "shopping"
    
    elif any(word in message for word in ["plan", "itinerary", "tour", "trip", "day out", "visit", "sightseeing","trail"]):
        state["intent"] = "itinerary"
    elif any(word in message for word in ["news", "headlines", "updates", "breaking"]):
        state["intent"] = "news"
    elif any(word in message for word in ["traffic", "congestion", "road", "jam", "slow", "block"]):
        state["intent"] = "traffic"

    elif any(word in message for word in ["movie", "cinema", "theater", "pvr", "inox", "imax", "film", "show"]):
        state["intent"] = "movies"
    elif any(word in message for word in ["charminar", "golconda", "monument", "fort"]):
        state["intent"] = "monument"
    elif any(word in message for word in ["temple", "birla", "chilkur"]):
        state["intent"] = "temple"
    elif any(
        word in message
        for word in [
            "biryani",
            "food",
            "restaurant",
            "restaurants",
            "cafe",
            "coffee",
            "cafes",
            "pubs",
            "dining",
            "hotels",
            "eat",
        ]
    ):
        state["intent"] = "food"
    elif any(word in message for word in ["metro", "transport", "airport"]):
        state["intent"] = "transport"
    elif any(word in message for word in ["fuel", "petrol", "diesel", "cng", "gas price"]):
        state["intent"] = "fuel"
       
    else:
        state["intent"] = "general"

    return state


def handle_greeting(state: BotState):
    state["response"] = """👋 **Welcome to Hyderabad City Guide!**

I can help you with:
🏛️ **Monuments** - Charminar, Golconda Fort
🛕 **Temples** - Birla Mandir, Chilkur Balaji
🍛 **Food** - Best Biryani places
🚇 **Transport** - Metro, Airport info
🚆 **MMTS Trains** - Suburban rail schedules
🚌 **Bus Routes** - RTC bus timings & routes  
⛽ **Fuel Prices** - Daily petrol, diesel, CNG rates
📰 **City News** - Hyderabad headlines & alerts
🛍️ **Shopping** - Malls, markets, sales          
🗓️ **Itineraries** - Personalized day plans       
🎬 **Movies** - Theaters, showtimes, bookings
🌦️ **Weather** - Live updates & air quality

🚨 **Emergency** - Important contacts

What would you like to know?"""
    return state

def handle_emergency(state: BotState):
    state["response"] = f"""🚨 **EMERGENCY CONTACTS - HYDERABAD**

**Immediate Help:**
• 🚓 Police: {EMERGENCY.get("police", "100")}
• 🚑 Ambulance: {EMERGENCY.get("ambulance", "108")}
• 🔥 Fire: {EMERGENCY.get("fire", "101")}
• 👩 Women Helpline: {EMERGENCY.get("women_helpline", "181")}

⚠️ **For emergencies, call 108 immediately!**"""
    return state


def resolve_hyderabad_area(query: str):
    """
    Resolve Hyderabad area from user query.

    Returns:
        (area_name, lat, lon)
        or (None, None, None) if unsupported
    """
    query_lower = query.lower()

    for area, (lat, lon) in HYDERABAD_AREA_COORDS.items():
        if area in query_lower:
            return area.title(), lat, lon

    # If user explicitly says Hyderabad
    if "hyderabad" in query_lower:
        return "Hyderabad (Central)", 17.3850, 78.4867

    # 👉 NEW RULE:
    # If user asks about weather but doesn't say a place,
    # assume Hyderabad by default
    weather_keywords = ["weather", "temperature", "rain", "hot", "cold", "climate"]

    if any(word in query_lower for word in weather_keywords):
        return "Hyderabad (Central)", 17.3850, 78.4867

    # Otherwise, reject (non-Hyderabad city)
    return None, None, None


def handle_monument(state: BotState):
    monuments = PROFILE.get("tourism_and_landmarks", {}).get("historical_monuments", [])
    response = "🏛️ **Famous Monuments:**\n\n"
    for i, mon in enumerate(monuments[:5], 1):
        response += f"**{i}. {mon['name']}**\n"
        response += f"📍 {mon['location']}\n"
        response += f"{mon['description'][:100]}...\n\n"
    state["response"] = response
    return state


def handle_temple(state: BotState):
    temples = (
        PROFILE.get("tourism_and_landmarks", {})
        .get("religious_sites", {})
        .get("hinduism", [])
    )
    response = "🛕 **Major Temples:**\n\n"
    for i, temple in enumerate(temples[:10], 1):
        response += f"**{i}. {temple['name']}**\n"
        response += f"📍 {temple.get('location', 'Hyderabad')}\n\n"
    state["response"] = response
    return state


def handle_food(state: BotState):
    user_query = state["user_input"]
    state["response"] = generate_food_recommendation(user_query)
    return state


def handle_transport(state: BotState):
    transport = PROFILE.get("infrastructure", {}).get("transport", [])
    metro = next((t for t in transport if t.get("mode") == "Metro Rail"), None)

    if metro:
        response = "🚇 **Hyderabad Metro:**\n\n"
        for line in metro.get("lines", [])[:3]:
            response += f"**{line['line_name']}:** {line['route']['from']} → {line['route']['to']}\n"
        response += "\n⏰ Timings: 6:00 AM - 11:00 PM"
        state["response"] = response
    else:
        state["response"] = "Metro information not available."
    return state


def handle_weather(state: BotState):
    user_query = state["user_input"]

    area, lat, lon = resolve_hyderabad_area(user_query)

    if area is None:
        state["response"] = (
            "🌦️ I currently provide weather updates only for Hyderabad areas.\n\n"
            "Try places like Hitech City, Gachibowli, Madhapur, Jubilee Hills, etc."
        )
        return state

    weather_data = get_weather_by_coords(lat, lon)

    if weather_data:
        st.session_state.selected_area = area
        st.session_state.selected_coords = (lat, lon)

        weather_text = format_weather(weather_data)
        aqi_data = get_aqi_by_coords(lat, lon)
        aqi_text = format_aqi(aqi_data)
        aqi_advice = get_aqi_advice(aqi_data)

        state["response"] = (
            f"🌦️ **Weather in {area}**\n\n{weather_text}\n{aqi_text}\n\n{aqi_advice}"
        )
    else:
        state["response"] = "Sorry, I'm unable to fetch weather data right now."
    return state


def handle_fuel(state: BotState):
    """Handle fuel price queries"""
    try:
        prices = get_fuel_prices_hyderabad()
        state["response"] = format_fuel_prices(prices)
    except Exception as e:
        state["response"] = (
            "⛽ Sorry, I couldn't fetch current fuel prices.\n\n"
            "You can check:\n"
            "• Indian Oil: https://iocl.com/\n"
            "• MyPetrolPrice: https://www.mypetrolprice.com/"
        )
    
    return state

def handle_bus(state: BotState):
    """Handle RTC bus route queries with connecting routes support"""
    user_query = state["user_input"]
    
    # Try to extract from/to locations
    from_area, to_area = extract_locations_from_query(user_query)
    
    if from_area and to_area:
        # Search for direct routes
        direct_routes = get_bus_routes(from_area, to_area)
        
        if not direct_routes.empty:
            # Direct routes found
            state["response"] = format_bus_routes(from_area, to_area, direct_routes)
        else:
            # No direct routes - search for connections
            connections = get_connecting_routes(from_area, to_area)
            
            if connections:
                # Format response with no direct routes + connections
                response = f"🚌 **BUS ROUTES:** {from_area.title()} → {to_area.title()}\n\n"
                response += "⚠️ **No direct routes available**\n"
                response += format_connecting_routes(from_area, to_area, connections)
                
                # Add alternative suggestions
                response += "\n💡 **Alternative Options:**  \n"
                response += "• Take Metro if available (faster & no changes)  \n"
                response += "• Use taxi/auto for direct journey  \n"
                response += "• Download TSRTC App for real-time tracking\n"
                
                state["response"] = response
            else:
                # No direct OR connecting routes found
                state["response"] = f"""🚌 **No bus routes found** from **{from_area.title()}** to **{to_area.title()}**.

💡 **Suggestions:**
- These areas may not have good bus connectivity
- Take Metro if available (check metro routes)
- Use Google Maps for detailed multi-hop routes
- Consider auto/cab for this journey

📱 Download **TSRTC App** for comprehensive route planning."""
    else:
        # General bus info
        state["response"] = get_general_bus_info()
    
    return state

def handle_mmts(state: BotState):
    """Handle MMTS train route queries"""
    user_query = state["user_input"]
    
    # Try to extract from/to stations
    from_station, to_station = extract_stations_from_query(user_query)
    
    if from_station and to_station:
        # Both stations specified - find specific route
        route_info = find_mmts_route(from_station, to_station)
        
        if route_info:
            state["response"] = format_mmts_route(route_info)
        else:
            state["response"] = f"""🚆 **No MMTS route found** from **{from_station}** to **{to_station}**.

💡 **Suggestions:**
- Check station names (e.g., use "Hi-Tech City" not "HITEC")
- These stations may not be connected by MMTS
- Try Metro or RTC buses for this route
- Ask: "MMTS routes" to see all available lines

🚇 **Alternative:** Use Metro for faster connectivity in this area."""
    
    elif to_station:
        # Only destination specified - show all routes serving that station
        routes = find_routes_to_station(to_station)
        state["response"] = format_routes_to_station(to_station, routes)
    
    else:
        # General MMTS info
        state["response"] = get_general_mmts_info()
    
    return state

def handle_news(state: BotState):
    articles = get_hyderabad_news()

    if not articles:
        state["response"] = "📰 Sorry, I couldn't fetch Hyderabad news right now."
        return state

    summary = summarize_news(articles)
    state["response"] = "📰 **Hyderabad Today**\n\n" + summary
    return state

def handle_shopping(state: BotState):
    """Handle shopping and mall queries"""
    user_query = state["user_input"]
    state["response"] = get_mall_info(user_query)
    return state


def handle_itinerary(state: BotState):
    """Handle itinerary planning queries"""
    user_query = state["user_input"]
    state["response"] = generate_itinerary(user_query)
    return state


def handle_movies(state: BotState):
    """Handle movie and theater queries"""
    user_query = state["user_input"]
    state["response"] = get_movie_info(user_query)
    return state

def handle_traffic(state: BotState):
    user_query = state["user_input"]

    area, lat, lon = resolve_hyderabad_area(user_query)

    if area is None:
        state["response"] = (
            "🚦 I provide traffic updates only for Hyderabad areas.\n\n"
            "Try: Gachibowli, Begumpet, Hitech City, Madhapur."
        )
        return state

    traffic_data = get_traffic_flow(lat, lon)
    traffic_text = format_traffic(traffic_data)

    state["response"] = f"🚦 **Traffic in {area}**\n\n{traffic_text}"
    return state



def handle_general(state: BotState):
    state["response"] = """I can help you with:

🏛️ **Monuments** - Charminar, Golconda Fort
🛕 **Temples** - Birla Mandir, Chilkur Balaji
🍛 **Food** - Best Biryani places
🚇 **Transport** - Metro, Airport info
🚆 **MMTS Trains** - Suburban rail schedules
🚌 **Bus Routes** - RTC bus timings & routes  
⛽ **Fuel Prices** - Daily petrol, diesel, CNG rates
🌦️ **Weather** - Live updates & air quality
📰 **City News** - Hyderabad headlines & alerts
🛍️ **Shopping** - Malls, markets, sales          
🗓️ **Itineraries** - Personalized day plans       
🎬 **Movies** - Theaters, showtimes, bookings
🚨 **Emergency** - Important contacts

Please ask me about any of these!"""
    return state


# ========================================
# BUILD WORKFLOW
# ========================================
@st.cache_resource
def create_workflow():
    """Create the chatbot workflow (cached)"""
    workflow = StateGraph(BotState)

    workflow.add_node("classifier", classify_intent)
    workflow.add_node("greeting", handle_greeting)
    workflow.add_node("emergency", handle_emergency)
    workflow.add_node("monument", handle_monument)
    workflow.add_node("temple", handle_temple)
    workflow.add_node("food", handle_food)
    workflow.add_node("transport", handle_transport)
    workflow.add_node("weather", handle_weather)
    workflow.add_node("fuel", handle_fuel)
    workflow.add_node("bus", handle_bus)
    workflow.add_node("mmts", handle_mmts)
    workflow.add_node("news", handle_news)
    workflow.add_node("shopping", handle_shopping)
    workflow.add_node("itinerary", handle_itinerary)
    workflow.add_node("movies", handle_movies)
    workflow.add_node("traffic", handle_traffic)
    workflow.add_node("general", handle_general)

    workflow.set_entry_point("classifier")

    def route(state: BotState):
        return state["intent"]

    workflow.add_conditional_edges(
        "classifier",
        route,
        {
            "greeting": "greeting",
            "emergency": "emergency",
            "monument": "monument",
            "temple": "temple",
            "food": "food",
            "transport": "transport",
            "weather": "weather",
            "fuel": "fuel",
            "bus": "bus",
            "mmts": "mmts",
            "news": "news",
            "shopping": "shopping", 
            "itinerary": "itinerary",
            "movies": "movies",
            "traffic": "traffic",
            "general": "general",
        },
    )

    for node in [
        "greeting",
        "emergency",
        "monument",
        "temple",
        "food",
        "transport",
        "weather",
        "fuel",
        "bus",
        "mmts",
        "news",
        "shopping",
        "itinerary",
        "movies",
        "traffic",
        "general",
    ]:
        workflow.add_edge(node, END)

    return workflow.compile()


with st.spinner("Starting assistant…"):
    app = create_workflow()


# Sidebar
with st.sidebar:
    st.subheader("🌐 Language / భాష / زبان / भाषा")
    
    languages = {
        "English 🇬🇧": "en",
        "తెలుగు 🇮🇳": "te",
        "اردو 🇵🇰": "ur",
        "हिंदी 🇮🇳": "hi"
    }
    
    selected_language = st.selectbox(
        "Select Language:",
        options=list(languages.keys()),
        index=0
    )
    
    language_code = languages[selected_language]
    
    if 'language' not in st.session_state:
        st.session_state.language = "en"
    
    if st.session_state.language != language_code:
        st.session_state.language = language_code
        st.rerun()
    
    if language_code != "en":
        lang_name = selected_language.split()[0]
        st.success(f"✓ Responses in {lang_name}")
    
    st.sidebar.markdown("---")
    voice_enabled, duration, auto_speak = create_voice_settings_ui()

    st.header("🎯 Quick Links")
    st.info("**Popular Queries:**")

    if st.button("🏛️ Famous Monuments"):
        st.session_state.last_query = "tell me about famous monuments"

    if st.button("🍛 Best Biryani Places"):
        st.session_state.last_query = "best biryani places"

    if st.button("🛕 Temples"):
        st.session_state.last_query = "famous temples"

    if st.button("🚇 Metro Info"):
        st.session_state.last_query = "metro timings"
    if st.button("🚌 Bus Routes"):
        st.session_state.last_query = "bus routes in hyderabad"
    if st.button("🚆 MMTS Train Info"):
        st.session_state.last_query = "mmts train info"
    if st.button("⛽ Fuel Prices"):
        st.session_state.last_query = "fuel prices today"
    if st.button("📰 City News"):
        st.session_state.last_query = "hyderabad news"
    if st.button("🛍️ Shopping Malls"):
        st.session_state.last_query = "shopping malls in hyderabad"
    
    if st.button("🗓️ Plan My Day"):
        st.session_state.last_query = "plan my one day hyderabad tour"
    
    if st.button("🎬 Movie Theaters"):
        st.session_state.last_query = "movie theaters in hyderabad"
    if st.button("🌦️ Weather Update"):
        st.session_state.last_query = "weather in hyderabad"
    if st.button("🚦 Traffic Update"):
        st.session_state.last_query = "traffic in hyderabad"
    if st.button("🚨 Emergency Contacts"):
        st.session_state.last_query = "emergency numbers"

    st.markdown("---")
    st.markdown("**💡 Tip:** Type your question in the chat below!")


# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []
    # Add welcome message
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": "👋 **Welcome to Hyderabad City Guide!** How can I help you today?",
        }
    )


# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# Chat input
language = st.session_state.get('language', 'en')
placeholders = {
    "en": "Ask me anything about Hyderabad...",
    "te": "హైదరాబాద్ గురించి ఏదైనా అడగండి...",
    "ur": "حیدرآباد کے بارے میں کچھ بھی پوچھیں...",
    "hi": "हैदराबाद के बारे में कुछ भी पूछें..."
}

# Voice input
voice_text = ""
if voice_enabled:
    voice_text = create_voice_input_button(
        language=language,
        duration=duration
    )

# Text input

# Prefer voice if available
if voice_text:
    user_input = voice_text
else:
    user_input = st.chat_input(placeholders.get(language, placeholders["en"]))


# Handle sidebar button clicks
if "last_query" in st.session_state:
    user_input = st.session_state.last_query
    del st.session_state.last_query

# Process user input
if user_input:
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    # Get bot response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                original_language = language  # from voice settings

                if language != "en":
                    normalized_input = translate_response(user_input, "en")
                else:
                    normalized_input = user_input

                result = app.invoke(
                    {"user_input": normalized_input, "intent": "", "response": ""}
                )
                response = result["response"]

                # OUTPUT TRANSLATION
                if language != "en":
                    response = translate_response(response, language)

                # DISPLAY TRANSLATED RESPONSE
                st.markdown(response)

# 🔊 AUTO VOICE OUTPUT
                if auto_speak:
                    create_voice_output_player(
                        text=response,
                        language=language
                    )

                # 🔊 MANUAL VOICE OUTPUT BUTTON
                if voice_enabled and not auto_speak:
                    create_voice_output_player(
                        text=response,
                        language=language
                    )

                # Add assistant response to chat history
                st.session_state.messages.append(
                    {"role": "assistant", "content": response}
                )

            except Exception as e:
                error_msg = f"❌ Error: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append(
                    {"role": "assistant", "content": error_msg}
                )

st.subheader("🌍 Hyderabad Live Snapshot")

area = st.session_state.selected_area
lat, lon = st.session_state.selected_coords

weather_data = get_weather_by_coords(lat, lon)
aqi_data = get_aqi_by_coords(lat, lon)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "🌡️ Temperature", f"{weather_data['main']['temp']} °C" if weather_data else "—"
    )
with col2:
    st.metric(
        "💧 Humidity", f"{weather_data['main']['humidity']} %" if weather_data else "—"
    )
with col3:
    st.metric("🌫️ Air Quality", format_aqi(aqi_data) if aqi_data else "—")
    st.divider()

traffic_data = get_traffic_flow(lat, lon)
traffic_text = format_traffic(traffic_data)

with col4:
    st.metric(
        "🚦 Traffic",
        "Heavy" if "Heavy" in traffic_text else
        "Moderate" if "Moderate" in traffic_text else
        "Smooth"
    )



# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center'>
        <p>Made with ❤️ for Hyderabad | Data last updated: October 2025</p>
    </div>
""",
    unsafe_allow_html=True,
)
