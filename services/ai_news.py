from google import genai
import streamlit as st
import os

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def summarize_news(articles):
    text = ""
    for a in articles:
        text += f"{a['title']}. {a.get('description','')}\n"

    prompt = f"""
You are a Hyderabad city news assistant.

Summarize into:
1. 📰 Top Hyderabad Headlines (5)
2. ⚠️ City Alerts (traffic, rain, accidents, protests)
3. 🗓️ Events (if any)

Ignore national politics. Focus only on Hyderabad.

News:
{text}
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=prompt,
    )

    return response.text
