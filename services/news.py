import requests
import streamlit as st

NEWS_API_KEY = st.secrets["NEWS_API_KEY"]

def get_hyderabad_news():
    url = (
        "https://newsapi.org/v2/everything?"
        "q=Hyderabad OR Telangana OR GHMC OR Cyberabad OR Secunderabad&"
        "sortBy=publishedAt&"
        "language=en&"
        f"apiKey={NEWS_API_KEY}"
    )

    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        return data.get("articles", [])[:10]
    except:
        return []
