from google import genai
import streamlit as st
import time
from services.food_loader import load_restaurants

# Initialize Gemini client
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

# Load restaurant knowledge base
RESTAURANTS = load_restaurants()


def extract_preferences(query: str):
    q = query.lower()

    return {
        "price_range": (
            "budget" if "cheap" in q or "budget" in q else
            "premium" if "premium" in q or "fine dining" in q else None
        ),
        "timings": "late night" if "late" in q or "midnight" in q else None,
        "type": (
            "biryani" if "biryani" in q else
            "cafe" if "cafe" in q or "coffee" in q else None
        )
    }


def fallback_food_response(query: str):
    names = [r["name"] for r in RESTAURANTS[:3]]

    return (
        "🍽️ **Popular Hyderabad restaurants:**\n\n"
        + "\n".join(f"- {name}" for name in names)
        + "\n\n⚠️ Showing cached recommendations due to high traffic."
    )


def generate_food_recommendation(user_query: str):
    prefs = extract_preferences(user_query)

    # Deterministic filtering
    filtered_restaurants = []
    for r in RESTAURANTS:
        match = True
        for key, value in prefs.items():
            if value and r.get(key) != value:
                match = False
        if match:
            filtered_restaurants.append(r)

    if not filtered_restaurants:
        filtered_restaurants = RESTAURANTS[:]

    prompt =  f"""
You are a Hyderabad food recommendation assistant.

RULES:
- Recommend ONLY from the provided restaurant data
- Do NOT invent restaurant names
- Do NOT claim distance or proximity
- ALWAYS show ratings if available (format: ⭐ 4.3/5)

User query:
"{user_query}"

Available restaurants:
{filtered_restaurants}

Instructions:
- Pick up to 3 suitable restaurants
- Show rating prominently (e.g., "⭐ 4.3/5")
- Mention 2-3 best-selling dishes per restaurant
- Include Google Maps links if available
- Friendly, local tone with Hyderabad flavor

Example format:
**1. Paradise Biryani** ⭐ 4.3/5
📍 Multiple locations
💰 ₹250-600
🍽️ Must-try: Paradise Special Biryani, Chicken 65
🗺️ [Google Maps](link)
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt,
        )
        return response.text

    except Exception:
        time.sleep(1)
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=prompt,
            )
            return response.text
        except Exception:
            return fallback_food_response(user_query)
