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
    get_forecast_by_coords,
    format_forecast_3day,
    get_rain_alert,
)
from services.ai_food import generate_food_recommendation
from services.fuel_prices import get_fuel_prices_hyderabad, format_fuel_prices

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

from services.news import get_hyderabad_news, get_news_by_category
from services.ai_news import summarize_news

from services.shopping import get_mall_info
from services.movies import get_movie_info
from services.itineary import generate_itinerary
from services.traffic import get_traffic_flow, format_traffic
from services.translator import translate_response, get_language_name
from services.metro_rail import(extract_stations_from_query,find_metro_route,format_metro_route,get_general_metro_info,format_metro_station_list)
from services.voice_service import render_audio_input, render_audio_output
from services.crowd import get_crowd_info
from services.utilities import handle_utilities_query,get_all_active_alerts,check_alerts_for_saved_areas,clear_alerts_cache
from services.ai_preferences import (
    initialize_preferences,
    learn_from_query,
    get_personalized_greeting,
    get_personalized_suggestions,
    apply_personalization_to_response
)
from services.festivals_traffic_alerts import handle_festival_traffic_query,get_active_festivals,get_festival_alerts_for_saved_areas
from services.live_deals import handle_deals_query,get_all_food_deals,get_all_ecommerce_deals,get_personalized_deals

import base64
from datetime import datetime

import os
os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]


# ========================================
# PAGE CONFIG - Must be first Streamlit command
# ========================================
st.set_page_config(
    page_title="Mitr - Hyderabad City Guide",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded",
)
initialize_preferences()
# Header
st.title(" Mitr - Your Personal Assistant for Exploring Hyderabad")
st.markdown("---")



# ========================================
# PERSONALIZED GREETING & SUGGESTIONS
# ========================================
from services.ai_preferences import get_current_preferences

# Show personalized greeting
prefs = get_current_preferences()
greeting = get_personalized_greeting(prefs)
st.markdown(f"### {greeting}")

# Show personalized suggestions as quick action buttons
suggestions = get_personalized_suggestions(prefs)
if suggestions:
    st.markdown("**🎯 Suggested for you:**")
    cols = st.columns(min(len(suggestions), 5))
    for i, suggestion in enumerate(suggestions[:5]):
        with cols[i]:
            # Extract the main text after emoji
            button_text = suggestion.split(" ", 1)[1] if " " in suggestion else suggestion
            if st.button(button_text, key=f"suggestion_{i}", use_container_width=True):
                st.session_state.last_query = button_text
                st.rerun()
    st.markdown("---")
# ========================================
# PROACTIVE ALERTS FOR SAVED AREAS
# ========================================
saved_areas = prefs.get("frequent_areas", [])

if saved_areas:
    # Store in session state for utilities_alerts to access
    if "user_preferences" not in st.session_state:
        st.session_state["user_preferences"] = prefs
    
    # Call without arguments (reads from session state internally)
    utility_alerts = check_alerts_for_saved_areas()
    
    if utility_alerts:
        st.warning("⚡💧 **Utility Alerts in Your Areas**")
        for alert in utility_alerts:
            st.markdown(f"• {alert}")
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
    background: rgba(0, 0, 0, 0) !important;
    backdrop-filter: blur(14px);
    border-right: 1px solid rgba(255,255,255,0.08);
}}

/* ================================
CHAT MESSAGES
=============================== */
[data-testid="stChatMessage"] {{
    background: rgba(0, 0, 0, 0) !important;
    border-radius: 14px;
    padding: 12px;
    backdrop-filter: blur(10px);
    border: 1px solid rgba(0,0,0,0);
}}

/* ================================
TEXT READABILITY
=============================== */
h1, h2, h3, h4, p, span,
[data-testid="stMarkdownContainer"] {{
    color: #ffffff !important;
    text-shadow: 0 1px 3px rgba(0,0,0,0);
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
st.markdown("""
<div id="chat-anchor"></div>

<style>
.floating-chat-btn {
    position: fixed;
    bottom: 24px;
    right: 24px;
    width: 60px;
    height: 60px;
    border-radius: 50%;
    background: linear-gradient(135deg, #6366F1, #4F46E5);
    color: white;
    font-size: 26px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    z-index: 9999;
    box-shadow: 0 8px 24px rgba(0,0,0,0.35);
}
.floating-chat-btn:hover {
    transform: scale(1.05);
}
</style>
            
<style>/* =====================================
FINAL CHAT LAYOUT FIX (USE ONLY THIS)
===================================== */

[data-testid="stChatMessage"] {
    display: grid !important;
    grid-template-columns: auto 1fr !important;
    column-gap: 0.5rem !important;
    padding-left: 0.75rem !important;
    margin-bottom: 10px;
}

[data-testid="stChatMessageAvatar"] img {
    width: 36px !important;
    height: 36px !important;
    border-radius: 50%;
    flex-shrink: 0;
}

[data-testid="stChatMessageContent"] {
    margin-left: 0 !important;
    padding-left: 0 !important;
}
</style>

<div class="floating-chat-btn"
     onclick="document.getElementById('chat-anchor').scrollIntoView({behavior: 'smooth'});">
💬
</div>
""", unsafe_allow_html=True)



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

# ═══════════════════════════════════════════════════════════════════════════
# EVENTS & GOVT SERVICES DATA (manually curated — refresh periodically)
# ═══════════════════════════════════════════════════════════════════════════
EVENTS_DATA = [
    {"name":"HITEX Technology Expo 2026","dates":"March 10–14, 2026","location":"HITEX Exhibition Centre, Madhapur","cost":"Free (business days) / ₹200 (public weekend)","description":"India's largest technology exhibition. Covers AI, IoT, robotics, cloud computing, and startup innovations. Over 300 exhibitors expected.","type":"Technology Expo"},
    {"name":"Hyderabad Comic Con 2026","dates":"April 5–7, 2026","location":"HITEX Exhibition Centre","cost":"₹500 (1-day) / ₹800 (weekend pass)","description":"South India's biggest pop culture convention. Cosplay competitions, artist alleys, celebrity panels, exclusive merch, and gaming zones.","type":"Pop Culture Convention"},
    {"name":"All India Industrial Exhibition (Numaish)","dates":"January 1 – February 15, 2026","location":"Nampally Exhibition Grounds","cost":"₹50 entry","description":"One of India's oldest and largest trade fairs. Over 2,500 stalls selling crafts, textiles, electronics, food, and more. A Hyderabad tradition since 1938.","type":"Trade Fair"},
    {"name":"Deccan Heritage & Arts Festival","dates":"March 22–24, 2026","location":"Qutb Shahi Tombs, Golconda","cost":"₹300 (day pass) / ₹500 (3-day pass)","description":"Celebrating Deccan art, architecture, and culture. Live performances, heritage walks, craft bazaar, poetry readings, and classical music.","type":"Cultural Festival"},
    {"name":"Hyderabad Book Fair 2026","dates":"February 20–28, 2026","location":"NTR Stadium, Indira Park","cost":"₹50 entry","description":"Annual book fair with over 400 publishers. Meet authors, attend workshops, and explore books in Telugu, English, Urdu, and Hindi.","type":"Book Fair"},
    {"name":"Bonalu Festival","dates":"July 2026 (dates vary by temple)","location":"Temples across Hyderabad (Ujjaini Mahankali, Akkanna Madanna, etc.)","cost":"Free","description":"Telangana's state festival dedicated to Goddess Mahakali. Grand processions (ghatams), traditional dances, and offerings. Major celebrations at Secunderabad and Old City temples.","type":"Religious Festival"},
]

GOVT_SERVICES = [
    {"name":"MeeSeva (e-Seva)","description":"Telangana government's integrated citizen service portal. Apply for certificates (birth, caste, income), ration cards, land records, and more.","type":"Citizen Services Portal","location":"Online + MeeSeva centers across Hyderabad","url":"https://meeseva.telangana.gov.in","services":["Birth Certificate","Caste Certificate","Income Certificate","Ration Card","Land Records","Pensions"],"hours":"Online: 24/7 | Centers: 9 AM – 5 PM (Mon–Sat)","contact":"155214"},
    {"name":"RTA Hyderabad (Transport Office)","description":"Regional Transport Authority for vehicle registration, driving licenses, permits, and road tax payments.","type":"Transport Services","location":"Khairatabad (main office) + 17 other RTOs across Hyderabad","url":"https://transport.telangana.gov.in","services":["Driving License","Vehicle Registration","Road Tax","Learner's License","RC Transfer","Fitness Certificate"],"hours":"9:30 AM – 5 PM (Mon–Sat, closed Sundays & public holidays)","contact":"040-23401000"},
    {"name":"Passport Seva Kendra (PSK)","description":"Passport application and renewal services. Book appointments online via the Passport Seva portal.","type":"Passport Services","location":"3 PSKs: Secunderabad, Gachibowli, LB Nagar | 8 Post Office Passport Seva Kendras","url":"https://portal2.passportindia.gov.in","services":["New Passport","Passport Renewal","Lost Passport","Police Clearance Certificate (PCC)","Minor Passport"],"hours":"9 AM – 5 PM (all days except national holidays)","contact":"1800-258-1800 (toll-free)"},
    {"name":"Aadhaar Enrollment & Update Centers","description":"UIDAI authorized centers for Aadhaar card enrollment, demographic updates, and biometric updates.","type":"Identity Services","location":"300+ centers across Hyderabad (MeeSeva, post offices, banks)","url":"https://uidai.gov.in","services":["Aadhaar Enrollment","Update Name/Address/Mobile","Biometric Update","Aadhaar PVC Card","e-Aadhaar Download"],"hours":"Varies by center (most: 9 AM – 5 PM)","contact":"1947 (Aadhaar helpline)"},
    {"name":"GHMC (Greater Hyderabad Municipal Corporation)","description":"Birth/death certificates, property tax, building permits, trade licenses, and civic complaint resolution.","type":"Municipal Services","location":"GHMC Head Office (Nampally) + 30 Circle Offices","url":"https://ghmc.gov.in","services":["Birth/Death Certificate","Property Tax","Building Permit","Trade License","Water Connection","Garbage Complaints"],"hours":"9 AM – 5 PM (Mon–Sat)","contact":"040-21111111 / 155304"},
    {"name":"T-Seva (Telangana State Portal)","description":"Unified portal for 850+ government services. Pay bills, apply for subsidies, check application status, and more.","type":"Integrated Services Portal","location":"Online","url":"https://www.tganywhere.telangana.gov.in","services":["Electricity Bills","Water Bills","Subsidies","Pensions","Scholarships","Grievance Redressal"],"hours":"24/7","contact":"155321"},
    {"name":"Employment Exchange (Labour Department)","description":"Job seeker registration, unemployment benefits, and skill development programs.","type":"Employment Services","location":"Abids (main office) + 16 district exchanges","url":"https://telangana.ncs.gov.in","services":["Job Seeker Registration","Unemployment Allowance","Skill Training","Employment Fair Updates"],"hours":"10 AM – 5 PM (Mon–Sat)","contact":"040-24600370"},
    {"name":"Consumer Court / Online Consumer Disputes","description":"File consumer complaints online for defective goods, deficient services, unfair trade practices.","type":"Consumer Protection","location":"Online + District Consumer Forums in Hyderabad","url":"https://edaakhil.nic.in","services":["File Complaints","Track Case Status","Consumer Awareness"],"hours":"Online: 24/7 | Physical courts: 10:30 AM – 5 PM","contact":"1800-11-4000 (National Consumer Helpline)"},
]


# ========================================
# BOT STATE
# ========================================
class BotState(TypedDict):
    user_input: str
    intent: str
    response: str


# ========================================
# SHARED TOURISM HELPERS
# ========================================
# Every tourism category in the KB uses the same four-field shape:
#   { "name", "type", "location", (optional) "description" }
# These two functions handle ALL of them — monuments, temples, palaces,
# museums, parks, and attractions — so each handler is just 8 lines.

def _match_item(query: str, items: list) -> dict | None:
    """
    Find the best-matching item from a list by name.

    Pass 1 — word-sequence: tries every contiguous sub-sequence of the item's
      name words against the query.  Picks the longest hit.
    Pass 2 — substring fallback: if pass 1 found nothing, checks whether any
      query word (>2 chars) appears anywhere inside the lowered name.
      Catches "nizam" inside "nizam's", "zoo" inside "zoological", etc.
    """
    if not query or not items:
        return None

    q           = query.lower()
    best_match  = None
    best_length = 0

    # pass 1 — word-sequence
    for item in items:
        name = item.get("name", "")
        if not name:
            continue
        words = name.lower().split()
        for start in range(len(words)):
            for end in range(len(words), start, -1):
                candidate = " ".join(words[start:end])
                if candidate in q and len(candidate) > best_length:
                    best_match  = item
                    best_length = len(candidate)

    if best_match:
        return best_match

    # pass 2 — single-word substring fallback
    query_words = [w for w in q.split() if len(w) > 2]
    for item in items:
        name_lower = item.get("name", "").lower()
        if not name_lower:
            continue
        for qw in query_words:
            if qw in name_lower and len(qw) > best_length:
                best_match  = item
                best_length = len(qw)

    return best_match


def _format_detail(item: dict, emoji: str = "🏛️") -> str:
    """Full-detail card for a single tourism KB item."""
    name        = item.get("name", "Unknown")
    item_type   = item.get("type")
    location    = item.get("location")
    description = item.get("description", "")

    lines = [f"{emoji} **{name}**\n"]
    if item_type:
        lines.append(f"🏷️  **Type:** {item_type}")
    if location:
        lines.append(f"📍 **Location:** {location}")
    if description:
        lines.append(f"\n📖 **About:**\n{description}")
    lines.append("\n💡 **Tip:** Visit early in the morning to avoid crowds and get the best photos!")
    return "\n".join(lines)


def _format_list(items: list, title: str, emoji: str = "🏛️") -> str:
    """Browsable list with first-sentence teasers."""
    lines = [f"{emoji} **{title}**\n", "Ask me about any of these for full details:\n"]
    for i, item in enumerate(items, 1):
        name = item.get("name", "Unknown")
        loc  = item.get("location", "Hyderabad")
        desc = item.get("description", "")
        first_sentence = desc.split(".")[0] if desc else ""

        lines.append(f"**{i}. {name}**")
        lines.append(f"   📍 {loc}")
        if first_sentence:
            lines.append(f"   {first_sentence}.")
        lines.append("")
    return "\n".join(lines)


# ========================================
# BOT LOGIC
# ========================================

def is_food_query(message: str) -> bool:
    """Enhanced food intent detection"""
    
    FOOD_KEYWORDS = [
        # Basics
        "food", "eat", "eating", "meal", "meals", "dining", "dine",
        "breakfast", "lunch", "brunch", "dinner", "supper", "snack", "snacks",
        
        # Establishments
        "restaurant", "restaurants", "cafe", "cafes", "coffee", "eatery",
        "dhaba", "hotel", "hotels", "canteen", "bakery", "bakeries",
        "bar", "bars", "pub", "pubs", "lounge", "bistro", "joint",
        
        # Cuisines
        "biryani", "hyderabadi", "mughlai", "north indian", "south indian",
        "chinese", "italian", "continental", "mexican", "thai", "japanese",
        "fast food", "street food", "seafood", "vegetarian", "vegan", "non-veg",
        
        # Famous Hyderabad dishes
        "haleem", "nihari", "paya", "keema", "korma", "kebab", "kebabs",
        "shawarma", "tikka", "tandoori", "curry", "dal", "paneer",
        "dosa", "idli", "vada", "upma", "chai", "tea", "irani chai",
        
        # Actions
        "hungry", "craving", "taste", "order", "delivery", "takeaway",
        
        # Descriptors
        "delicious", "tasty", "yummy", "spicy", "sweet", "savory",
        "famous", "popular", "best", "good", "recommended",
        "cheap", "expensive", "budget", "premium", "fine dining",
        "late night", "24 hours", "midnight", "romantic", "family", "buffet",
        "nightlife", "night out", "party",
    ]
    
    FOOD_PATTERNS = [
        "where to eat", "where can i eat", "what to eat", "what should i eat",
        "looking for food", "suggest food", "recommend food", "place to eat",
        "places to eat", "good food", "best food", "famous food", "want to eat",
        "something to eat", "grab food", "get food", "must try",
    ]
    
    message_lower = message.lower()
    
    # Check keywords
    if any(keyword in message_lower for keyword in FOOD_KEYWORDS):
        return True
    
    # Check patterns
    if any(pattern in message_lower for pattern in FOOD_PATTERNS):
        return True
    
    return False


def classify_intent(state: BotState):
    """Classify user intent"""
    message = state["user_input"].lower()

    if any(
        message.strip().startswith(word) for word in ["hello", "hi", "hey", "namaste"]
    ):
        state["intent"] = "greeting"

    elif any(word in message for word in ["emergency", "police", "ambulance", "fire"]):
        state["intent"] = "emergency"
    
    elif any(word in message for word in [
        "event", "events", "exhibition", "expo", "hitex", "comic con",
        "numaish", "book fair", "happening", "what's on",
    ]):
        state["intent"] = "events"

    # ── government services ─────────────────────────────────────────────
    elif any(word in message for word in [
        "meeseva", "rta", "passport", "aadhaar", "aadhar", "ghmc",
        "driving license", "birth certificate", "government service",
        "govt service", "tseva", "consumer court",
    ]):
        state["intent"] = "govt"
    

    elif any(word in message for word in ["mmts", "train", "suburban rail"]) or (
        "from" in message and "to" in message and any(w in message for w in ["train", "rail"])
    ):
        state["intent"] = "mmts"
    elif any(word in message.lower() for word in 
           ["power", "power cut", "electricity", "outage", "load shed",
            "water", "water supply", "tap water"]):
        state["intent"] = "utilities"
        return state
    
    elif any(word in message for word in ["crowd","crowded", "busy", "best time", "avoid crowd",
        "peaceful", "quiet", "less people", "when to visit",]):
        state["intent"] = "crowd"
    elif any(word in message for word in ["metro", "transport", "airport"]):
        state["intent"] = "transport"

    elif any(word in message for word in ["bus", "rtc", "tsrtc"]):
        state["intent"] = "bus"

    elif any(word in message for word in ["weather", "temperature", "rain", "climate", "forecast"]):
        state["intent"] = "weather"

    elif any(word in message for word in ["mall", "shopping", "shop", "market", "ikea", "inorbit", "gvk", "sale", "discount"]):
        state["intent"] = "shopping"

    elif any(word in message for word in ["plan", "itinerary", "tour", "trip", "day out", "visit", "sightseeing", "trail"]):
        state["intent"] = "itinerary"

    elif any(word in message for word in ["news", "headline", "latest news", "today news", "city news", "updates"]):
        state["intent"] = "news"
    

    elif any(word in message for word in ["traffic", "congestion", "road", "jam", "slow", "block"]):
        state["intent"] = "traffic"

    elif any(word in message for word in ["movie", "cinema", "theater", "pvr", "inox", "imax", "film", "show"]):
        state["intent"] = "movies"

    # ── palaces ─────────────────────────────────────────────────────────
    elif any(word in message for word in [
        "palace", "chowmahalla", "falaknuma", "purani haveli", "king koti",
    ]):
        state["intent"] = "palace"

    # ── museums ─────────────────────────────────────────────────────────
    elif any(word in message for word in [
        "museum", "gallery", "salar jung", "nizam museum", "archaeology",
        "birla science", "state art",
    ]):
        state["intent"] = "museum"

    # ── parks & nature ──────────────────────────────────────────────────
    elif any(word in message for word in [
        "park", "hussain sagar", "zoo", "zoological", "kbr", "botanical",
        "sanjeevaiah", "lake front", "nature",
    ]):
        state["intent"] = "park"

    # ── modern attractions ──────────────────────────────────────────────
    elif any(word in message for word in [
        "ramoji", "shilparamam", "cable bridge", "durgam", "necklace road",
        "film city", "attraction",
    ]):
        state["intent"] = "attraction"

    # ── monuments ───────────────────────────────────────────────────────
    elif any(word in message for word in [
        "charminar", "golconda", "monument", "fort", "qutb shahi",
        "makkah masjid", "historical",
    ]):
        state["intent"] = "monument"

    # ── temples / religious sites ───────────────────────────────────────
    elif any(word in message for word in [
        "temple", "birla", "chilkur", "mandir", "mosque", "masjid",
        "church", "cathedral", "basilica", "iskcon", "peddamma",
        "hanuman", "yellamma", "religious",
    ]):
        state["intent"] = "temple"


    elif any(word in message for word in ["fuel", "petrol", "diesel", "cng", "gas price"]):
        state["intent"] = "fuel"

    elif is_food_query(message):
        state["intent"] = "food"
    elif any(word in message for word in [
        "hospital", "hospitals", "doctor", "medical", "healthcare", "health",
        "clinic", "apollo", "yashoda", "care", "continental", "emergency room",
        "pharmacy", "medicine", "treatment", "surgery",
    ]):
        state["intent"] = "healthcare"
    elif any(word in message for word in [
        "sport", "sports", "stadium", "cricket", "gym", "fitness",
        "uppal stadium", "sports complex", "badminton", "tennis",
        "lal bahadur stadium", "gachibowli stadium", "arena",
    ]):
        state["intent"] = "sports"

    elif any(word in message for word in [
        "school", "college", "university", "education", "institute",
        "iit", "nit", "bits", "iiit", "osmania", "jntu",
        "study", "courses", "admission", "campus",
    ]):
        state["intent"] = "education"
    elif any(word in message for word in [
        "history", "trivia", "fact", "facts", "did you know",
        "tell me about hyderabad", "about hyderabad", "founded",
        "nizam", "nizams", "pearl city", "city of pearls",
        "hyderabadi", "heritage", "legacy",
    ]):
        state["intent"] = "trivia"
    elif any(word in message for word in [
    "festival", "ganesh", "diwali", "bonalu", "eid", "ramadan",
    "numaish", "rush", "crowd today", "procession", "immersion"
    ]):
        state["intent"] = "festival_traffic"

    elif any(word in message for word in [
        "festival", "festivals", "bonalu", "bathukamma", "dussehra", "ganesh",
        "ramadan", "eid", "diwali", "holi", "sankranti", "ugadi",
        "culture", "cultural", "tradition", "celebration",
    ]):
        state["intent"] = "festival"
    # ── events & exhibitions ───────────────────────────────────────────
    elif any(word in message for word in [
    "deal", "deals", "offer", "offers", "discount", "discounts",
    "swiggy", "zomato", "amazon", "flipkart", "coupon", "sale",
    "cheap", "save money", "cashback", "promo"
    ]):
        state["intent"] = "deals"

    else:
        state["intent"] = "general"

    return state


# ── greeting & emergency ────────────────────────────────────────────────────

def handle_greeting(state: BotState):
    state["response"] = """👋 **Hello! I am Mitr**
Your personal Hyderabad city guide.
I can help you with:
🏛️ **Monuments** - Charminar, Golconda Fort
👑 **Palaces** - Chowmahalla, Falaknuma Palace
🏛️ **Museums** - Salar Jung, Nizam's Museum
🌳 **Parks** - Hussain Sagar, KBR National Park
🎬 **Attractions** - Ramoji Film City, Shilparamam
🛕 **Temples** - Birla Mandir, Chilkur Balaji
🍛 **Food** - Best Biryani places
🚇 **Transport** - Metro, Airport info
🚆 **MMTS Trains** - Suburban rail schedules
🚌 **Bus Routes** - RTC bus timings & routes
⛽ **Fuel Prices** - Daily petrol, diesel, CNG rates
📰 **City News** - Hyderabad headlines & alerts
🛍️ **Shopping** - Malls, markets, sales
👥 **Crowd Info** - Best time to visit any place   
🗓️ **Itineraries** - Personalized day plans
🎬 **Movies** - Theaters, showtimes, bookings
🌦️ **Weather** - Live updates & air quality
🎉 **Festivals** - Bonalu, Bathukamma, cultural events
⚽ **Sports** - Stadiums, sports complexes
🏥 **Healthcare** - Hospitals, emergency services
🎓 **Education** - Universities, colleges, schools
📜 **History** - Trivia, facts about Hyderabad
🎪 **Events** - HITEX, Comic Con, Numaish & more
🏛️ **Govt Services** - MeeSeva, RTA, Passport, Aadhaar
🎉 **Festival Traffic** - Live crowd & traffic alerts
💰 **Live Deals** - Swiggy, Zomato, Amazon offers
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


# ── tourism handlers (monuments, temples, palaces, museums, parks, attractions) ──

def handle_monument(state: BotState):
    items = PROFILE.get("tourism_and_landmarks", {}).get("historical_monuments", [])
    if not items:
        state["response"] = "🏛️ Sorry, monument information is currently unavailable."
        return state

    matched = _match_item(state["user_input"], items)
    state["response"] = (
        _format_detail(matched, emoji="🏛️")
        if matched
        else _format_list(items, "Famous Monuments & Landmarks in Hyderabad", emoji="🏛️")
    )
    return state


def handle_temple(state: BotState):
    """Temples & religious sites — collects ALL religions into one list."""
    religious = PROFILE.get("tourism_and_landmarks", {}).get("religious_sites", {})
    if not religious:
        state["response"] = "🛕 Sorry, temple information is currently unavailable."
        return state

    # flatten all religions into one searchable list
    all_sites = []
    for religion, sites in religious.items():
        for site in sites:
            site_copy = dict(site)
            site_copy["_religion"] = religion   # tag for display
            all_sites.append(site_copy)

    if not all_sites:
        state["response"] = "🛕 Sorry, no religious sites found."
        return state

    matched = _match_item(state["user_input"], all_sites)
    if matched:
        # show full detail + which religion it belongs to
        detail = _format_detail(matched, emoji="🛕")
        religion_label = matched.get("_religion", "").title()
        if religion_label:
            detail = detail.replace(
                f"🛕 **{matched['name']}**",
                f"🛕 **{matched['name']}**  ·  {religion_label}",
            )
        state["response"] = detail
    else:
        state["response"] = _format_list(all_sites, "Temples & Religious Sites in Hyderabad", emoji="🛕")

    return state

def handle_utilities(state: BotState) -> BotState:
    """Handle power-cut and water-supply queries"""
    try:
        response = handle_utilities_query(state["user_input"])
        state["response"] = response
    except Exception as e:
        state["response"] = "Sorry, utility alerts are currently unavailable."
    return state

def handle_palace(state: BotState):
    items = PROFILE.get("tourism_and_landmarks", {}).get("palaces", [])
    if not items:
        state["response"] = "👑 Sorry, palace information is currently unavailable."
        return state

    matched = _match_item(state["user_input"], items)
    state["response"] = (
        _format_detail(matched, emoji="👑")
        if matched
        else _format_list(items, "Royal Palaces of Hyderabad", emoji="👑")
    )
    return state


def handle_museum(state: BotState):
    items = PROFILE.get("tourism_and_landmarks", {}).get("museums_and_galleries", [])
    if not items:
        state["response"] = "🏛️ Sorry, museum information is currently unavailable."
        return state

    matched = _match_item(state["user_input"], items)
    state["response"] = (
        _format_detail(matched, emoji="🏛️")
        if matched
        else _format_list(items, "Museums & Galleries in Hyderabad", emoji="🏛️")
    )
    return state


def handle_park(state: BotState):
    items = PROFILE.get("tourism_and_landmarks", {}).get("parks_and_nature", [])
    if not items:
        state["response"] = "🌳 Sorry, parks information is currently unavailable."
        return state

    matched = _match_item(state["user_input"], items)
    state["response"] = (
        _format_detail(matched, emoji="🌳")
        if matched
        else _format_list(items, "Parks & Nature Spots in Hyderabad", emoji="🌳")
    )
    return state


def handle_attraction(state: BotState):
    items = PROFILE.get("tourism_and_landmarks", {}).get("modern_attractions", [])
    if not items:
        state["response"] = "🎬 Sorry, attractions information is currently unavailable."
        return state

    matched = _match_item(state["user_input"], items)
    state["response"] = (
        _format_detail(matched, emoji="🎬")
        if matched
        else _format_list(items, "Modern Attractions in Hyderabad", emoji="🎬")
    )
    return state


# ── food ────────────────────────────────────────────────────────────────────

def handle_food(state: BotState):
    state["response"] = generate_food_recommendation(state["user_input"])
    return state


# ── transport ───────────────────────────────────────────────────────────────

def handle_transport(state: BotState):
    """Handle metro, airport, and general transport queries."""
    query = state["user_input"].lower()
    
    # ── Check for metro station list request ──
    if any(word in query for word in ["station list", "all stations", "metro stations", "list of stations"]):
        state["response"] = format_metro_station_list()
        return state
    
    # ── Check for metro routing request (from X to Y) ──
    if "metro" in query and any(word in query for word in ["from", "to"]):
        from_station, to_station = extract_stations_from_query(query)
        if from_station and to_station:
            route = find_metro_route(from_station, to_station)
            state["response"] = format_metro_route(route)
            return state
    
    # ── Check for general metro info ──
    if "metro" in query:
        state["response"] = get_general_metro_info()
        return state
    
    # ── Check for airport info ──
    if "airport" in query:
        transport = PROFILE.get("infrastructure", {}).get("transport", [])
        airport = next((t for t in transport if t.get("mode") == "Airport"), None)
        if airport:
            response = "✈️ **Rajiv Gandhi International Airport (RGIA)**\n\n"
            response += f"📍 **Location:** {airport.get('location', 'Shamshabad')}\n"
            response += f"🛫 **IATA Code:** {airport.get('iata_code', 'HYD')}\n\n"
            response += f"🇮🇳 **Domestic Routes:** {', '.join(airport.get('domestic_routes', [])[:6])}\n"
            response += f"🌏 **International Routes:** {', '.join(airport.get('international_routes', [])[:4])}\n"
            response += f"✈️ **Airlines:** {', '.join(airport.get('major_airlines', [])[:5])}\n\n"
            notes = airport.get('connectivity_notes', '')
            if notes:
                response += f"💡 {notes}\n"
            state["response"] = response
        else:
            state["response"] = "✈️ Airport information is currently unavailable."
        return state
    
    # ── Default: general transport info ──
    state["response"] = get_general_metro_info()
    return state

# ── weather ─────────────────────────────────────────────────────────────────

def resolve_hyderabad_area(query: str):
    """Resolve Hyderabad area from user query → (area_name, lat, lon)."""
    query_lower = query.lower()

    for area, (lat, lon) in HYDERABAD_AREA_COORDS.items():
        if area in query_lower:
            return area.title(), lat, lon

    if "hyderabad" in query_lower:
        return "Hyderabad (Central)", 17.3850, 78.4867

    weather_keywords = ["weather", "temperature", "rain", "hot", "cold", "climate"]
    if any(word in query_lower for word in weather_keywords):
        return "Hyderabad (Central)", 17.3850, 78.4867

    return None, None, None


def handle_weather(state: BotState):
    area, lat, lon = resolve_hyderabad_area(state["user_input"])

    if area is None:
        state["response"] = (
            "🌦️ I currently provide weather updates only for Hyderabad areas.\n\n"
            "Try places like Hitech City, Gachibowli, Madhapur, Jubilee Hills, etc."
        )
        return state

    weather_data = get_weather_by_coords(lat, lon)

    if weather_data:
        st.session_state.selected_area  = area
        st.session_state.selected_coords = (lat, lon)

        # Current weather
        weather_text = format_weather(weather_data)
        aqi_data     = get_aqi_by_coords(lat, lon)
        aqi_text     = format_aqi(aqi_data)
        aqi_advice   = get_aqi_advice(aqi_data)

        response = f"🌦️ **Weather in {area}**\n\n"
        
        # Check for rain alerts
        forecast_data = get_forecast_by_coords(lat, lon)
        rain_alert = get_rain_alert(forecast_data)
        if rain_alert:
            response += rain_alert + "\n"
        
        response += f"{weather_text}\n{aqi_text}\n\n{aqi_advice}"
        
        # Add 3-day forecast
        forecast_text = format_forecast_3day(forecast_data)
        if forecast_text:
            response += forecast_text
        
        state["response"] = response
    else:
        state["response"] = "Sorry, I'm unable to fetch weather data right now."
    return state


# ── fuel ────────────────────────────────────────────────────────────────────

def handle_fuel(state: BotState):
    try:
        prices = get_fuel_prices_hyderabad()
        state["response"] = format_fuel_prices(prices)
    except Exception:
        state["response"] = (
            "⛽ Sorry, I couldn't fetch current fuel prices.\n\n"
            "You can check:\n"
            "• Indian Oil: https://iocl.com/\n"
            "• MyPetrolPrice: https://www.mypetrolprice.com/"
        )
    return state


# ── bus ─────────────────────────────────────────────────────────────────────

def handle_bus(state: BotState):
    from_area, to_area = extract_locations_from_query(state["user_input"])

    if from_area and to_area:
        direct_routes = get_bus_routes(from_area, to_area)

        if not direct_routes.empty:
            state["response"] = format_bus_routes(from_area, to_area, direct_routes)
        else:
            connections = get_connecting_routes(from_area, to_area)
            if connections:
                response  = f"🚌 **BUS ROUTES:** {from_area.title()} → {to_area.title()}\n\n"
                response += "⚠️ **No direct routes available**\n"
                response += format_connecting_routes(from_area, to_area, connections)
                response += "\n💡 **Alternative Options:**  \n"
                response += "• Take Metro if available (faster & no changes)  \n"
                response += "• Use taxi/auto for direct journey  \n"
                response += "• Download TSRTC App for real-time tracking\n"
                state["response"] = response
            else:
                state["response"] = (
                    f"🚌 **No bus routes found** from **{from_area.title()}** to **{to_area.title()}**.\n\n"
                    "💡 **Suggestions:**\n"
                    "- Take Metro if available\n"
                    "- Use Google Maps for multi-hop routes\n"
                    "- Consider auto/cab for this journey\n\n"
                    "📱 Download **TSRTC App** for comprehensive route planning."
                )
    else:
        state["response"] = get_general_bus_info()

    return state


# ── mmts ────────────────────────────────────────────────────────────────────

def handle_mmts(state: BotState):
    from_station, to_station = extract_stations_from_query(state["user_input"])

    if from_station and to_station:
        route_info = find_mmts_route(from_station, to_station)
        if route_info:
            state["response"] = format_mmts_route(route_info)
        else:
            state["response"] = (
                f"🚆 **No MMTS route found** from **{from_station}** to **{to_station}**.\n\n"
                "💡 Check station names (e.g. use \"Hi-Tech City\" not \"HITEC\"), "
                "or try Metro / RTC buses for this route.\n\n"
                "🚇 Ask: \"MMTS routes\" to see all available lines."
            )
    elif to_station:
        routes = find_routes_to_station(to_station)
        state["response"] = format_routes_to_station(to_station, routes)
    else:
        state["response"] = get_general_mmts_info()

    return state


# ── news ────────────────────────────────────────────────────────────────────

def handle_news(state: BotState):
    query = state["user_input"]

    # Route to category-specific news if keywords match
    if any(word in query.lower() for word in ["traffic", "road", "jam"]):
        articles = get_news_by_category("traffic")
        header = "🚦 **Traffic & Transportation News**"
    elif any(word in query.lower() for word in ["weather", "rain", "temperature"]):
        articles = get_news_by_category("weather")
        header = "🌦️ **Weather Updates**"
    elif any(word in query.lower() for word in ["tech", "IT", "startup"]):
        articles = get_news_by_category("tech")
        header = "💻 **Tech & IT Sector News**"
    elif any(word in query.lower() for word in ["event", "festival", "concert"]):
        articles = get_news_by_category("events")
        header = "🎉 **Events & Happenings**"
    else:
        articles = get_hyderabad_news()
        header = "📰 **Hyderabad Today**"

    if not articles:
        state["response"] = "📰 News unavailable at the moment. Try again in a few minutes."
        return state

    # Pass the user query for context-aware summarization
    state["response"] = f"{header}\n\n{summarize_news(articles, query)}"
    return state


# ── shopping ────────────────────────────────────────────────────────────────

def handle_shopping(state: BotState):
    state["response"] = get_mall_info(state["user_input"])
    return state
# ── crowd prediction ─────────────────────────────────────────────────────────

def handle_crowd(state: BotState):
    """Handle queries about crowd levels and best times to visit."""
    state["response"] = get_crowd_info(state["user_input"])
    return state


# ── itinerary ───────────────────────────────────────────────────────────────

def handle_itinerary(state: BotState):
    state["response"] = generate_itinerary(state["user_input"])
    return state


# ── movies ──────────────────────────────────────────────────────────────────

def handle_movies(state: BotState):
    state["response"] = get_movie_info(state["user_input"])
    return state


# ── traffic ─────────────────────────────────────────────────────────────────

def handle_traffic(state: BotState):
    area, lat, lon = resolve_hyderabad_area(state["user_input"])

    if area is None:
        state["response"] = (
            "🚦 I provide traffic updates only for Hyderabad areas.\n\n"
            "Try: Gachibowli, Begumpet, Hitech City, Madhapur."
        )
        return state

    traffic_data = get_traffic_flow(lat, lon)
    # Pass area name to format_traffic for alternate route suggestions
    state["response"] = f"🚦 **Traffic in {area}**\n\n{format_traffic(traffic_data, area_name=area)}"
    return state

# ── HEALTHCARE HANDLER ──────────────────────────────────────────────────────

def handle_healthcare(state: BotState):
    """Handle queries about hospitals and healthcare facilities."""
    healthcare_data = PROFILE.get("healthcare", {})
    
    if not healthcare_data:
        state["response"] = """🏥 **Healthcare in Hyderabad**

**Major Hospitals:**
• Apollo Hospitals - Multiple locations
• Yashoda Hospitals - Comprehensive care
• CARE Hospitals - Multi-specialty
• Continental Hospitals - Advanced treatment
• Gandhi Hospital - Government facility

🚨 **Emergency:** Call 108 for ambulance

💡 Ask me about specific hospitals for details!"""
        return state
    
    query = state["user_input"].lower()
    
    hospitals = healthcare_data.get("major_hospitals", [])
    specialty = healthcare_data.get("specialty_hospitals", [])
    
    all_healthcare = hospitals + specialty
    
    matched = _match_item(query, all_healthcare)
    
    if matched:
        state["response"] = _format_detail(matched, emoji="🏥")
    else:
        response = "🏥 **Healthcare Facilities in Hyderabad**\n\n"
        
        if hospitals:
            response += "**Major Hospitals:**\n"
            for hosp in hospitals[:5]:
                name = hosp.get("name", "Unknown")
                loc = hosp.get("location", "Hyderabad")
                response += f"• {name} - {loc}\n"
            response += "\n"
        
        response += "🚨 **Emergency:** Call 108 for ambulance\n\n"
        response += "💡 Ask me about any specific hospital!"
        state["response"] = response
    
    return state


# ── SPORTS HANDLER ──────────────────────────────────────────────────────────

def handle_sports(state: BotState):
    """Handle queries about sports facilities and stadiums."""
    sports_data = PROFILE.get("sports_and_recreation", {})
    
    if not sports_data:
        state["response"] = """⚽ **Sports & Recreation in Hyderabad**

**Major Stadiums:**
• Rajiv Gandhi International Cricket Stadium (Uppal)
• GMC Balayogi Stadium (Gachibowli)
• Lal Bahadur Shastri Stadium
• Gymkhana Ground

**Sports Facilities:**
• Hyderabad Sports Complex
• Saroornagar Sports Stadium
• Various gyms and fitness centers

💡 Ask me about specific stadiums for details!"""
        return state
    
    query = state["user_input"].lower()
    
    stadiums = sports_data.get("stadiums", [])
    complexes = sports_data.get("sports_complexes", [])
    
    all_sports = stadiums + complexes
    
    matched = _match_item(query, all_sports)
    
    if matched:
        state["response"] = _format_detail(matched, emoji="⚽")
    else:
        response = "⚽ **Sports & Recreation in Hyderabad**\n\n"
        
        if stadiums:
            response += "**Major Stadiums:**\n"
            for stadium in stadiums[:4]:
                name = stadium.get("name", "Unknown")
                loc = stadium.get("location", "Hyderabad")
                response += f"• {name} - {loc}\n"
            response += "\n"
        
        response += "💡 Ask me about any specific stadium!"
        state["response"] = response
    
    return state


# ── EDUCATION HANDLER ───────────────────────────────────────────────────────

def handle_education(state: BotState):
    """Handle queries about educational institutions."""
    infrastructure = PROFILE.get("infrastructure", {})
    education_list = infrastructure.get("premier_education_institutes", [])
    
    state["response"] = """🎓 **Education in Hyderabad**

**Major Universities:**
- IIT Hyderabad - Premier technology institute
- IIIT Hyderabad - Information technology specialization  
- Osmania University - Historic public university (founded 1918)
- JNTU Hyderabad - Technical university
- University of Hyderabad - Central university

**Engineering Colleges:**
- BITS Pilani Hyderabad Campus
- CBIT (Chaitanya Bharathi Institute of Technology)
- Vasavi College of Engineering
- CVR College of Engineering
- MVSR Engineering College

**Management Institutes:**
- ISB (Indian School of Business) - Top MBA program
- ICFAI Business School

💡 Ask me about specific institutions for more details!"""
    
    return state
    query = state["user_input"].lower()
    matched = _match_item(query, education_list)

    if matched:
        # Show detailed info about matched institution
        name = matched.get("name", "Unknown")
        location = matched.get("location", "Hyderabad")
        established = matched.get("established", "N/A")
        fact = matched.get("notable_fact", "")
        
        response = f"🎓 **{name}**\n\n"
        response += f"📍 **Location:** {location}\n"
        response += f"📅 **Established:** {established}\n\n"
        
        if fact:
            response += f"ℹ️ **About:**\n{fact}\n\n"
        
        response += "💡 Ask me about other institutions in Hyderabad!"
        
        state["response"] = response
        return state
    
    # Show list of all institutions
    response = "🎓 **Premier Educational Institutions in Hyderabad**\n\n"
    
    for i, inst in enumerate(education_list, 1):
        name = inst.get("name", "Unknown")
        location = inst.get("location", "")
        established = inst.get("established", "")
        
        response += f"**{i}. {name}**\n"
        response += f"   📍 {location}"
        if established:
            response += f" • Est. {established}"
        response += "\n\n"
    
    response += "💡 Ask me about any specific institution for more details!"
    state["response"] = response
    
    return state



# ── TRIVIA / HISTORY HANDLER ────────────────────────────────────────────────

def handle_trivia(state: BotState):
    """Handle queries about Hyderabad's history and trivia."""
    
    # Rich fallback content (always available)
    basic_history = """📜 **Hyderabad - History & Trivia**

🏛️ **Foundation (1591):**
Hyderabad was founded by Muhammad Quli Qutb Shah, the fifth ruler of the Qutb Shahi dynasty. Legend says the city was named after Bhagmati, a local nautch girl who later became his wife Hyder Mahal.

👑 **The Nizams Era (1724-1948):**
The Asaf Jahi dynasty ruled Hyderabad for over 200 years. The last Nizam, Mir Osman Ali Khan, was once the richest man in the world, appearing on Time magazine's cover in 1937.

💎 **City of Pearls:**
Hyderabad earned this nickname due to its historic pearl and diamond trading center. The city was a major hub on the pearl trade route from the Persian Gulf.

🏗️ **Iconic Charminar (1591):**
Built by Muhammad Quli Qutb Shah to commemorate the end of a deadly plague. Its four minarets represent the first four caliphs of Islam.

🍛 **Culinary Heritage:**
Hyderabadi Biryani was born in the royal kitchens of the Nizams, blending Mughlai and Telugu cuisines. The unique "Dum" cooking method was perfected here.

🎬 **Modern Cyberabad:**
Today, Hyderabad is India's second-largest IT hub after Bengaluru, hosting Microsoft, Google, Amazon, and over 1,500 IT companies.

💡 **Fun Facts:**
• The word "Hyderabad" means "Lion City"
• Golconda Fort was famous for its acoustics and diamond mines
• The state of Hyderabad was larger than many European countries

💡 Ask me about Charminar, Golconda Fort, or specific monuments for more details!"""
    
    # CORRECT PATH: Get history section from PROFILE
    history_section = PROFILE.get("history", {})
    
    # If history section is empty or not a dict, show basic history
    if not history_section or not isinstance(history_section, dict):
        state["response"] = basic_history
        return state
    
    query = state["user_input"].lower()
    
    # The KB structure has nested periods under history
    # We'll extract facts from these periods
    historical_facts = []
    
    # Check for historical periods and extract info
    for period_name, period_data in history_section.items():
        if isinstance(period_data, dict):
            period_label = period_data.get("period", period_name)
            
            # Extract key points from this period
            for key, value in period_data.items():
                if key != "period" and isinstance(value, str):
                    historical_facts.append({
                        "title": f"{period_label} - {key.replace('_', ' ').title()}",
                        "description": value
                    })
    
    # Build response
    if historical_facts:
        response = "📜 **Hyderabad - History & Trivia**\n\n"
        response += "**Historical Facts:**\n"
        
        for i, fact in enumerate(historical_facts[:5], 1):
            title = fact.get("title", "")
            desc = fact.get("description", "")
            response += f"{i}. **{title}**\n   {desc}\n\n"
        
        response += "💡 Ask about Charminar, Golconda, or the Nizams for more!"
        state["response"] = response
    else:
        # No historical facts found, use basic history
        state["response"] = basic_history
    
    return state

# ── FESTIVAL / CULTURE HANDLER ──────────────────────────────────────────────

def handle_festival(state: BotState):
    """Handle queries about festivals and cultural events."""
    festivals_data = PROFILE.get("festivals_and_culture", {})
    
    if not festivals_data:
        state["response"] = """🎉 **Festivals & Culture in Hyderabad**

**Major Festivals:**
• Bonalu (July-August) - Telangana's iconic festival
• Bathukamma (September-October) - Floral festival
• Ganesh Chaturthi (August-September) - Grand celebrations
• Diwali (October-November) - Festival of lights
• Ramadan & Eid (varies) - Islamic celebrations

**Cultural Highlights:**
• Hyderabadi culture is a unique blend of Telugu and Urdu traditions
• Famous for Qawwali music and Deccani art
• Rich heritage of handicrafts and pearls

💡 Ask me about specific festivals for more details!"""
        return state
    
    query = state["user_input"].lower()
    
    major = festivals_data.get("major_festivals", [])
    religious = festivals_data.get("religious_celebrations", [])
    cultural = festivals_data.get("cultural_events", [])
    
    all_festivals = major + religious + cultural
    
    matched = _match_item(query, all_festivals)
    
    if matched:
        state["response"] = _format_detail(matched, emoji="🎉")
    else:
        response = "🎉 **Festivals & Cultural Events in Hyderabad**\n\n"
        
        if major:
            response += "**Major Festivals:**\n"
            for fest in major[:5]:
                name = fest.get("name", "Unknown")
                desc = fest.get("description", "")
                first_line = desc.split(".")[0] if desc else ""
                response += f"• **{name}**"
                if first_line:
                    response += f" - {first_line}"
                response += "\n"
            response += "\n"
        
        if religious:
            response += "**Religious Celebrations:**\n"
            for fest in religious[:5]:
                name = fest.get("name", "Unknown")
                response += f"• {name}\n"
            response += "\n"
        
        response += "💡 Ask about any specific festival for details!"
        state["response"] = response
    
    return state

# ── events & exhibitions ────────────────────────────────────────────────────

def handle_events(state: BotState):
    if not EVENTS_DATA:
        state["response"] = "🎪 Sorry, no upcoming events information is currently available."
        return state

    query = state["user_input"]
    matched = _match_item(query, EVENTS_DATA)

    if matched:
        lines = [f"🎪 **{matched['name']}**\n"]
        lines.append(f"📅 **Dates:** {matched['dates']}")
        lines.append(f"📍 **Location:** {matched['location']}")
        lines.append(f"💰 **Cost:** {matched['cost']}")
        if matched.get("type"):
            lines.append(f"🏷️  **Type:** {matched['type']}")
        lines.append(f"\n📖 **About:**\n{matched['description']}")
        state["response"] = "\n".join(lines)
    else:
        lines = ["🎪 **Upcoming Events & Exhibitions in Hyderabad**\n"]
        lines.append("Ask me about any event for full details:\n")
        for i, evt in enumerate(EVENTS_DATA, 1):
            lines.append(f"**{i}. {evt['name']}**")
            lines.append(f"   📅 {evt['dates']}")
            lines.append(f"   📍 {evt['location']}")
            lines.append(f"   💰 {evt['cost']}")
            lines.append("")
        lines.append("💡 **Pro Tip:** This list is manually updated. For real-time events, check Insider.in or BookMyShow.")
        state["response"] = "\n".join(lines)
    return state


# ── government services ─────────────────────────────────────────────────────
def handle_govt(state: BotState):
    if not GOVT_SERVICES:
        state["response"] = "🏛️ Sorry, government services information is currently unavailable."
        return state

    query = state["user_input"]
    matched = _match_item(query, GOVT_SERVICES)

    if matched:
        lines = [f"🏛️ **{matched['name']}**\n"]
        if matched.get("type"):
            lines.append(f"🏷️  **Type:** {matched['type']}")
        lines.append(f"📍 **Location:** {matched['location']}")
        if matched.get("url"):
            lines.append(f"🌐 **Website:** {matched['url']}")
        services = matched.get("services", [])
        if services:
            lines.append(f"\n📋 **Services Offered:**")
            for s in services:
                lines.append(f"   • {s}")
        if matched.get("hours"):
            lines.append(f"\n⏰ **Hours:** {matched['hours']}")
        if matched.get("contact"):
            lines.append(f"📞 **Contact:** {matched['contact']}")
        lines.append(f"\n📖 **About:**\n{matched['description']}")
        state["response"] = "\n".join(lines)
    else:
        lines = ["🏛️ **Government Services in Hyderabad**\n"]
        lines.append("Ask me about any service for full details:\n")
        for i, svc in enumerate(GOVT_SERVICES, 1):
            lines.append(f"**{i}. {svc['name']}**")
            lines.append(f"   🏷️  {svc.get('type','Service')}")
            lines.append(f"   🌐 {svc.get('url','')}")
            top_services = svc.get("services", [])[:3]
            if top_services:
                lines.append(f"   📋 Key: {', '.join(top_services)}")
            lines.append("")
        lines.append("💡 **Quick Links:**")
        lines.append("   • MeeSeva (all certificates): https://meeseva.telangana.gov.in")
        lines.append("   • T-Seva (bills & subsidies): https://www.tganywhere.telangana.gov.in")
        lines.append("   • Passport: https://portal2.passportindia.gov.in")
        lines.append("   • RTA: https://transport.telangana.gov.in")
        state["response"] = "\n".join(lines)
    return state

# ── festival traffic handler ────────────────────────────────────────────────

def handle_festival_traffic(state: BotState):
    """Handle queries about festival traffic and crowds."""
    try:
        response = handle_festival_traffic_query(state["user_input"])
        state["response"] = response
    except Exception as e:
        state["response"] = """🎉 **Festival Traffic Information**

I can help you check:
- Active festivals today
- Upcoming festivals calendar
- Traffic impact in specific areas
- Crowd predictions

Try asking:
- "What festivals are happening today?"
- "Traffic at Charminar during Ganesh Chaturthi"
- "Upcoming festivals next week"
- "Is Tank Bund crowded right now?"

⚠️ Note: Live traffic data requires TomTom API key configuration."""
    
    return state


# ── deals handler ───────────────────────────────────────────────────────────

def handle_deals(state: BotState):
    """Handle queries about food delivery and e-commerce deals."""
    try:
        response = handle_deals_query(state["user_input"])
        state["response"] = response
    except Exception as e:
        state["response"] = """💰 **Live Deals & Offers**

I can show you deals from:
🍔 **Food Delivery:** Swiggy, Zomato
🛍️ **E-commerce:** Amazon, Flipkart
💳 **Bank Offers:** HDFC, ICICI, Axis, SBI

Try asking:
- "Show me Swiggy offers"
- "Amazon deals on electronics"
- "Best food delivery discounts today"
- "Bank card offers"
- "Shopping deals"

💡 Note: Live deals require RapidAPI key configuration."""
    
    return state

# ── general fallback ────────────────────────────────────────────────────────

def handle_general(state: BotState):
    state["response"] = """It look like i can't help with that but I can help you with any of these topics related to Hyderabad:

🏛️ **Monuments** - Charminar, Golconda Fort
👑 **Palaces** - Chowmahalla, Falaknuma Palace
🏛️ **Museums** - Salar Jung, Nizam's Museum
🌳 **Parks** - Hussain Sagar, KBR National Park
🎬 **Attractions** - Ramoji Film City, Shilparamam
🛕 **Temples** - Birla Mandir, Chilkur Balaji
🍛 **Food** - Best Biryani places
🚇 **Transport** - Metro, Airport info
🚆 **MMTS Trains** - Suburban rail schedules
🚌 **Bus Routes** - RTC bus timings & routes
⛽ **Fuel Prices** - Daily petrol, diesel, CNG rates
🌦️ **Weather** - Live updates & air quality
📰 **City News** - Hyderabad headlines & alerts
🛍️ **Shopping** - Malls, markets, sales
👥 **Crowd Info** - Best time to visit any place    
🗓️ **Itineraries** - Personalized day plans
🎬 **Movies** - Theaters, showtimes, bookings
🎉 **Festivals** - Bonalu, Bathukamma, cultural events
⚽ **Sports** - Stadiums, sports complexes
🏥 **Healthcare** - Hospitals, emergency services
🎓 **Education** - Universities, colleges, schools
📜 **History** - Trivia, facts about Hyderabad
🎪 **Events** - HITEX, Comic Con, Numaish & more
🏛️ **Govt Services** - MeeSeva, RTA, Passport, Aadhaar
🎉 **Festival Traffic** - Live crowd & traffic alerts
💰 **Live Deals** - Swiggy, Zomato, Amazon offers
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

    # ── nodes ───────────────────────────────────────────────────────────
    workflow.add_node("classifier",  classify_intent)
    workflow.add_node("greeting",    handle_greeting)
    workflow.add_node("emergency",   handle_emergency)
    workflow.add_node("monument",    handle_monument)
    workflow.add_node("temple",      handle_temple)
    workflow.add_node("palace",      handle_palace)
    workflow.add_node("museum",      handle_museum)
    workflow.add_node("park",        handle_park)
    workflow.add_node("attraction",  handle_attraction)
    workflow.add_node("food",        handle_food)
    workflow.add_node("transport",   handle_transport)
    workflow.add_node("weather",     handle_weather)
    workflow.add_node("fuel",        handle_fuel)
    workflow.add_node("bus",         handle_bus)
    workflow.add_node("mmts",        handle_mmts)
    workflow.add_node("news",        handle_news)
    workflow.add_node("shopping",    handle_shopping)
    workflow.add_node("itinerary",   handle_itinerary)
    workflow.add_node("movies",      handle_movies)
    workflow.add_node("traffic",     handle_traffic)
    workflow.add_node("healthcare",  handle_healthcare)
    workflow.add_node("sports",      handle_sports)
    workflow.add_node("education",   handle_education)
    workflow.add_node("trivia",      handle_trivia)
    workflow.add_node("festival",    handle_festival)
    workflow.add_node("crowd",       handle_crowd) 
    workflow.add_node("events",      handle_events)
    workflow.add_node("govt",        handle_govt)
    workflow.add_node("utilities",    handle_utilities)
    workflow.add_node("festival_traffic", handle_festival_traffic)
    workflow.add_node("deals", handle_deals)
    workflow.add_node("general",     handle_general)

    workflow.set_entry_point("classifier")

    # ── routing map ─────────────────────────────────────────────────────
    INTENT_MAP = {
        "greeting":   "greeting",
        "emergency":  "emergency",
        "monument":   "monument",
        "temple":     "temple",
        "palace":     "palace",
        "museum":     "museum",
        "park":       "park",
        "attraction": "attraction",
        "food":       "food",
        "transport":  "transport",
        "weather":    "weather",
        "fuel":       "fuel",
        "bus":        "bus",
        "mmts":       "mmts",
        "news":       "news",
        "shopping":   "shopping",
        "itinerary":  "itinerary",
        "movies":     "movies",
        "traffic":    "traffic",
        "healthcare": "healthcare",
        "sports":     "sports",
        "education":  "education",
        "trivia":     "trivia",
        "festival":   "festival",
        "crowd":      "crowd",
        "events":     "events",
        "govt":       "govt",  
        "utilities":   "utilities",
        "festival_traffic": "festival_traffic",
        "deals": "deals",
        "general":    "general",
    }

    workflow.add_conditional_edges("classifier", lambda s: s["intent"], INTENT_MAP)

    # every handler → END
    for node in INTENT_MAP.values():
        workflow.add_edge(node, END)

    return workflow.compile()


with st.spinner("Starting assistant…"):
    app = create_workflow()


# ========================================
# SIDEBAR
# ========================================
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

    # ── AI Preferences Dashboard ────────────────────────────────────────
    st.sidebar.subheader("🎯 Your Preferences")
    
    with st.sidebar.expander("📊 View My Data", expanded=False):
        prefs = get_current_preferences()
        
        # Show stats
        st.metric("Total Interactions", prefs["total_interactions"])
        st.metric("Personalization Level", f"{int(prefs['personalization_score']*100)}%")
        
        # Show top interests
        if prefs["total_interactions"] > 0:
            st.markdown("**Your Top Interests:**")
            top_interests = sorted(
                prefs["interests"].items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            for interest, count in top_interests:
                if count > 0:
                    st.progress(min(count/20, 1.0), text=f"{interest.title()}: {count}")
        
        # Show frequent areas
        if prefs.get("frequent_areas"):
            st.markdown("**Your Frequent Areas:**")
            for area in prefs["frequent_areas"][:5]:
                st.markdown(f"• {area}")
        
        # Privacy controls
        st.markdown("---")
        st.markdown("**🔒 Privacy Controls**")
        
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("📄 View Privacy", key="view_privacy"):
                from services.ai_preferences import get_privacy_summary
                st.info(get_privacy_summary(prefs))
        
        with col_b:
            if st.button("🗑️ Clear Data", key="clear_data"):
                from services.ai_preferences import clear_user_data
                clear_user_data()
                st.success("✅ All data cleared!")
                st.rerun()

    # ── voice settings ──────────────────────────────────────────────────
    st.sidebar.subheader("🎙️ Voice Settings")
    voice_enabled = st.sidebar.toggle("Enable voice input",  key="voice_enabled",  value=False)
    auto_speak    = st.sidebar.toggle("Auto-play responses", key="auto_speak",     value=False)

    # ── quick links ─────────────────────────────────────────────────────
    st.sidebar.header("🎯 Quick Links")
    st.sidebar.info("**Popular Queries:**")

    if st.sidebar.button("🏛️ Famous Monuments"):
        st.session_state.last_query = "tell me about famous monuments"
    if st.sidebar.button("👑 Royal Palaces"):
        st.session_state.last_query = "royal palaces in hyderabad"
    if st.sidebar.button("🏛️ Museums"):
        st.session_state.last_query = "museums in hyderabad"
    if st.sidebar.button("🌳 Parks & Nature"):
        st.session_state.last_query = "parks and nature in hyderabad"
    if st.sidebar.button("🎬 Attractions"):
        st.session_state.last_query = "modern attractions in hyderabad"
    if st.sidebar.button("🍛 Best Biryani Places"):
        st.session_state.last_query = "best biryani places"
    if st.sidebar.button("🛕 Temples"):
        st.session_state.last_query = "famous temples"
    if st.sidebar.button("🚇 Metro Info"):
        st.session_state.last_query = "metro timings"
    if st.sidebar.button("🚌 Bus Routes"):
        st.session_state.last_query = "bus routes in hyderabad"
    if st.sidebar.button("🚆 MMTS Train Info"):
        st.session_state.last_query = "mmts train info"
    if st.sidebar.button("⛽ Fuel Prices"):
        st.session_state.last_query = "fuel prices today"
    if st.sidebar.button("📰 City News"):
        st.session_state.last_query = "hyderabad news"
    if st.sidebar.button("🛍️ Shopping Malls"):
        st.session_state.last_query = "shopping malls in hyderabad"
    if st.sidebar.button("👥 Crowd Guide"):
        st.session_state.last_query = "best time to visit places"
    if st.sidebar.button("🗓️ Plan My Day"):
        st.session_state.last_query = "plan my one day hyderabad tour"
    if st.sidebar.button("🎬 Movie Theaters"):
        st.session_state.last_query = "movie theaters in hyderabad"
    if st.sidebar.button("🌦️ Weather Update"):
        st.session_state.last_query = "weather in hyderabad"
    if st.sidebar.button("🚦 Traffic Update"):
        st.session_state.last_query = "traffic in hyderabad"
    if st.sidebar.button("🎉 Festivals & Culture"):
        st.session_state.last_query = "festivals in hyderabad"
    if st.sidebar.button("⚽ Sports & Stadiums"):
        st.session_state.last_query = "sports stadiums"
    if st.sidebar.button("🏥 Hospitals & Healthcare"):
        st.session_state.last_query = "major hospitals"
    if st.sidebar.button("🎓 Education & Universities"):
        st.session_state.last_query = "university in hyderabad"
    if st.sidebar.button("📜 Hyderabad History"):
        st.session_state.last_query = "tell me about hyderabad history"
    if st.sidebar.button("🎪 Events"):
        st.session_state.last_query = "upcoming events in hyderabad"
    if st.sidebar.button("🏛️ Government Services"):
        st.session_state.last_query = "government services in hyderabad"
    if st.sidebar.button("🎉 Festival Traffic"):
        st.session_state.last_query = "what festivals are happening today"
    if st.sidebar.button("💰 Live Deals & Offers"):
        st.session_state.last_query = "show me food delivery offers"
    if st.sidebar.button("🚨 Emergency Contacts"):
        st.session_state.last_query = "emergency numbers"

    st.markdown("---")
    st.markdown("**💡 Tip:** Type your question in the chat below!")


# ========================================
# CHAT
# ========================================
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append(
        {"role": "assistant", "content": "👋 Welcome to Mitr! I am your personal assistant for exploring Hyderabad. How can I help you today?"}
    )

for message in st.session_state.messages:
    if message["role"] == "assistant":
        with st.chat_message(
            "assistant",
            avatar="https://raw.githubusercontent.com/Taruni05/mitrchatbot/master/mitr_avatar.png"
        ):
            st.markdown(message["content"])
    else:
        with st.chat_message("user"):
            st.markdown(message["content"])


# ── voice input (browser mic) ───────────────────────────────────────────────
language = st.session_state.get("language", "en")
voice_text = ""

if st.session_state.get("voice_enabled", False):
    voice_text = render_audio_input(language=language)

# ── text input (always shown) ───────────────────────────────────────────────
PLACEHOLDERS = {
    "en": "Ask me anything about Hyderabad…",
    "te": "హైదరాబాద్ గురించి ఏదైనా అడగండి…",
    "ur": "حیدرآباد کے بارے میں کچھ بھی پوچھیں…",
    "hi": "हैदराबाद के बारे में कुछ भी पूछें…",
}
typed_input = st.chat_input(PLACEHOLDERS.get(language, PLACEHOLDERS["en"]))

# voice wins if both arrive in the same rerun
user_input = voice_text or typed_input

# ── sidebar button clicks ───────────────────────────────────────────────────
if "last_query" in st.session_state:
    user_input = st.session_state.last_query
    del st.session_state.last_query


# ── process ─────────────────────────────────────────────────────────────────
if user_input:
    # 1️⃣ Save + render USER message
    st.session_state.messages.append(
        {"role": "user", "content": user_input}
    )

    with st.chat_message("user"):
        st.markdown(user_input)

    # 2️⃣ Show spinner OUTSIDE chat messages
    with st.spinner("Thinking..."):
        try:
            # translate input to English if needed
            normalized_input = (
                translate_response(user_input, "en")
                if language != "en"
                else user_input
            )

            # Run LangGraph
            result   = app.invoke({
                "user_input": normalized_input,
                "intent": "",
                "response": ""
            })

            intent   = result["intent"]
            response = result["response"]

            # Learn + personalize
            learn_from_query(normalized_input, intent)
            response = apply_personalization_to_response(response)

            # translate output back if needed
            if language != "en":
                response = translate_response(response, language)

        except Exception as e:
            response = f"❌ Error: {str(e)}"

    # 3️⃣ Render ASSISTANT message (NO spinner here)
    with st.chat_message(
        "assistant",
        avatar="https://raw.githubusercontent.com/Taruni05/mitrchatbot/master/mitr_avatar.png"
    ):
        st.markdown(response)

        # 🔊 voice output
        if st.session_state.get("voice_enabled", False):
            render_audio_output(
                text=response,
                language=language,
                auto_play=st.session_state.get("auto_speak", False),
            )

    # 4️⃣ Save assistant message
    st.session_state.messages.append(
        {"role": "assistant", "content": response}
    )

# ========================================
# LIVE SNAPSHOT DASHBOARD
# ========================================
st.subheader("🌏  Hyderabad Live Snapshot")

area       = st.session_state.selected_area
lat, lon   = st.session_state.selected_coords

weather_data = get_weather_by_coords(lat, lon)
aqi_data     = get_aqi_by_coords(lat, lon)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("🌡️ Temperature", f"{weather_data['main']['temp']} °C" if weather_data else "—")
with col2:
    st.metric("💧 Humidity",    f"{weather_data['main']['humidity']} %" if weather_data else "—")
with col3:
    st.metric("🌫️ Air Quality", format_aqi(aqi_data) if aqi_data else "—")

traffic_data = get_traffic_flow(lat, lon)
traffic_text = format_traffic(traffic_data)

with col4:
    st.metric(
        "🚦 Traffic",
        "Heavy"    if "Heavy"    in traffic_text else
        "Moderate" if "Moderate" in traffic_text else "Smooth"
    )


# ========================================
# FOOTER
# ========================================
st.markdown("---")
st.markdown(
    "<div style='text-align: center'>"
    "<p>Made with ❤️ for Hyderabad | Thank You for Visiting!</p>"
    "</div>",
    unsafe_allow_html=True,
)