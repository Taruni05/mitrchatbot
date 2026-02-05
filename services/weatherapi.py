import requests
import streamlit as st
from datetime import datetime

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

@st.cache_data(ttl=1800)  # Cache for 30 min (forecasts change less frequently)
def get_forecast_by_coords(lat: float, lon: float):
    """
    Fetch 5-day/3-hour forecast from OpenWeather.
    Returns forecast data or None on error.
    """
    api_key = st.secrets["OPENWEATHER_API_KEY"]
    
    url = (
        "https://api.openweathermap.org/data/2.5/forecast"
        f"?lat={lat}&lon={lon}&appid={api_key}&units=metric"
    )
    
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"[weatherapi] Forecast fetch failed: {e}")
        return None


def format_forecast_3day(forecast_data):
    """
    Format 3-day forecast into a readable card.
    
    OpenWeather /forecast returns 40 data points (5 days × 8 times/day).
    We aggregate by day and show:
      - Max/Min temp
      - Dominant weather condition
      - Rain probability (if > 50%)
    """
    if not forecast_data or "list" not in forecast_data:
        return ""
    
    items = forecast_data["list"]
    if not items:
        return ""
    
    # Group by date
    from collections import defaultdict
    daily = defaultdict(list)
    
    for item in items[:24]:  # First 3 days (24 data points = 3 days × 8)
        dt = datetime.fromtimestamp(item["dt"])
        date_str = dt.strftime("%Y-%m-%d")
        daily[date_str].append(item)
    
    if len(daily) < 3:
        return ""  # Not enough data
    
    response = "\n\n📅 **3-Day Forecast:**\n\n"
    
    for date_str in sorted(daily.keys())[:3]:
        day_items = daily[date_str]
        
        # Calculate aggregates
        temps = [d["main"]["temp"] for d in day_items]
        max_temp = max(temps)
        min_temp = min(temps)
        
        # Find dominant weather condition (most frequent)
        conditions = [d["weather"][0]["main"] for d in day_items]
        dominant_condition = max(set(conditions), key=conditions.count)
        
        # Check for rain probability (if rain data exists)
        rain_probs = [d.get("pop", 0) * 100 for d in day_items]
        max_rain_prob = max(rain_probs) if rain_probs else 0
        
        # Format date nicely
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        day_name = dt.strftime("%A")  # Monday, Tuesday, etc.
        date_display = dt.strftime("%b %d")  # Jan 15
        
        # Build the line
        response += f"**{day_name}, {date_display}**\n"
        response += f"   🌡️ {min_temp:.0f}°C - {max_temp:.0f}°C"
        response += f"   •   {get_weather_emoji(dominant_condition)} {dominant_condition}\n"
        
        if max_rain_prob > 50:
            response += f"   ☔ Rain likely ({max_rain_prob:.0f}% chance)\n"
        
        response += "\n"
    
    return response


def get_weather_emoji(condition):
    """Map weather condition to emoji."""
    emoji_map = {
        "Clear": "☀️",
        "Clouds": "☁️",
        "Rain": "🌧️",
        "Drizzle": "🌦️",
        "Thunderstorm": "⛈️",
        "Snow": "❄️",
        "Mist": "🌫️",
        "Fog": "🌫️",
        "Haze": "🌫️",
    }
    return emoji_map.get(condition, "🌤️")


def get_rain_alert(forecast_data):
    """
    Check if heavy rain is expected in the next 24 hours.
    Returns an alert banner string or empty string.
    """
    if not forecast_data or "list" not in forecast_data:
        return ""
    
    items = forecast_data["list"][:8]  # Next 24 hours (8 × 3-hour blocks)
    
    # Check for high rain probability or "Rain" condition
    for item in items:
        rain_prob = item.get("pop", 0) * 100
        condition = item["weather"][0]["main"]
        
        if rain_prob > 70 or condition == "Rain":
            dt = datetime.fromtimestamp(item["dt"])
            time_str = dt.strftime("%I:%M %p")
            
            return (
                f"⚠️ **Rain Alert:** Heavy rain expected around {time_str} "
                f"({rain_prob:.0f}% probability). Carry an umbrella!\n"
            )
    
    return ""

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
