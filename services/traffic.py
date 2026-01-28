import requests
import streamlit as st

TOMTOM_API_KEY = st.secrets["TOMTOM_API_KEY"]

def get_traffic_flow(lat, lon):
    url = (
        "https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json"
        f"?point={lat},{lon}&key={TOMTOM_API_KEY}"
    )

    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return None


def format_traffic(data):
    if not data or "flowSegmentData" not in data:
        return "🚦 Traffic data unavailable."

    flow = data["flowSegmentData"]

    current_speed = flow.get("currentSpeed", 0)
    free_speed = flow.get("freeFlowSpeed", 1)

    ratio = current_speed / max(free_speed, 1)

    if ratio >= 0.8:
        status = "🟢 Smooth traffic — no delays"
        advice = "Safe to travel."
    elif ratio >= 0.5:
        status = "🟡 Moderate traffic — minor delays"
        advice = "Plan buffer time."
    else:
        status = "🔴 Heavy traffic — expect delays"
        advice = "Avoid peak hours or reroute."

    return (
        f"{status}\n"
        f"🚗 Current Speed: {current_speed} km/h\n"
        f"🛣️ Free Flow Speed: {free_speed} km/h\n\n"
        f"💡 Advice: {advice}"
    )

