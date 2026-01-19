import requests
import streamlit as st

@st.cache_data(ttl=600)
def get_weather_by_coords(lat: float, lon: float):
    """
    Fetch weather using latitude & longitude.
    """
    api_key = st.secrets["OPENWEATHER_API_KEY"]

    url = (
        "https://api.openweathermap.org/data/2.5/weather"
        f"?lat={lat}&lon={lon}&appid={api_key}&units=metric"
    )

    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception:
        return None

    
def format_weather(data):
    """
    Convert raw weather JSON into readable text.
    """
    if not data:
        return "Weather information is currently unavailable."

    temp = data["main"]["temp"]
    humidity = data["main"]["humidity"]
    condition = data["weather"][0]["description"].title()

    return (
        f"It is currently {temp}°C with {condition}. "
        f"Humidity is around {humidity}%."
    )
@st.cache_data(ttl=600)
def get_aqi_by_coords(lat: float, lon: float):
    """
    Fetch Air Quality Index (AQI) using latitude & longitude.
    """
    api_key = st.secrets["OPENWEATHER_API_KEY"]

    url = (
        "https://api.openweathermap.org/data/2.5/air_pollution"
        f"?lat={lat}&lon={lon}&appid={api_key}"
    )

    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception:
        return None

def format_aqi(aqi_data):
    """
    Convert AQI number into readable text.
    """
    if not aqi_data:
        return "AQI data unavailable"

    aqi = aqi_data["list"][0]["main"]["aqi"]

    mapping = {
        1: "Good 🟢",
        2: "Fair 🟡",
        3: "Moderate 🟠",
        4: "Poor 🔴",
        5: "Very Poor 🟣",
    }

    return mapping.get(aqi, "Unknown")

def get_aqi_advice(aqi_data):
    if not aqi_data:
        return ""

    aqi = aqi_data["list"][0]["main"]["aqi"]

    advice_map = {
        1: "🟢 Air quality is good. Enjoy outdoor activities.",
        2: "🟡 Air quality is fair. Sensitive individuals should take care.",
        3: "🟠 Air quality is moderate. Limit prolonged outdoor exposure.",
        4: "🔴 Air quality is poor. Avoid outdoor activities if possible.",
        5: "🟣 Air quality is very poor. Stay indoors and wear a mask.",
    }

    return advice_map.get(aqi, "")
