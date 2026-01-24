import requests
from bs4 import BeautifulSoup
import streamlit as st
from datetime import datetime

@st.cache_data(ttl=86400)  # Cache for 24 hours (daily update)
def get_fuel_prices_hyderabad():
    """
    Fetch current fuel prices for Hyderabad.
    
    Returns:
        dict: {
            "petrol": float,
            "diesel": float,
            "cng": float,
            "date": str,
            "source": str
        }
    """
    
    # Fallback prices (updated manually when you deploy)
    FALLBACK_PRICES = {
        "petrol": 102.63,
        "diesel": 88.84,
        "cng": 75.50,
        "date": "2026-01-19",
        "source": "cached"
    }
    
    try:
        # Method 1: Try scraping from MyPetrolPrice.com
        url = "https://www.mypetrolprice.com/7/Petrol-price-in-Hyderabad"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find price elements (adjust selectors based on actual HTML)
        petrol_element = soup.find('div', class_='petrol-price')
        diesel_element = soup.find('div', class_='diesel-price')
        
        if petrol_element and diesel_element:
            petrol_price = float(petrol_element.text.strip().replace('₹', '').replace('/L', ''))
            diesel_price = float(diesel_element.text.strip().replace('₹', '').replace('/L', ''))
            
            return {
                "petrol": petrol_price,
                "diesel": diesel_price,
                "cng": 75.50,  # CNG not always available on this site
                "date": datetime.now().strftime("%Y-%m-%d"),
                "source": "live"
            }
        
    except Exception as e:
        # Log error but don't crash
        print(f"Fuel price fetch failed: {e}")
    
    # Return fallback if scraping fails
    return FALLBACK_PRICES


def format_fuel_prices(prices_data):
    """
    Format fuel prices - Clean Version with Better Spacing
    """
    if not prices_data:
        return "⛽ Fuel price information is currently unavailable."
    
    petrol = prices_data.get("petrol", 0)
    diesel = prices_data.get("diesel", 0)
    cng = prices_data.get("cng", 0)
    date = prices_data.get("date", "Unknown")
    source = prices_data.get("source", "cached")
    
    source_text = "🔴 Live" if source == "live" else "📦 Cached"
    diff = abs(petrol - diesel)
    comparison_text = "📈 Petrol is higher than diesel" if petrol > diesel else "📉 Diesel is higher than petrol"
    
    return f"""⛽ **FUEL PRICES IN HYDERABAD**  
({source_text} | Updated: {date})

🔴 **Petrol:** ₹{petrol:.2f}/L  
🟢 **Diesel:** ₹{diesel:.2f}/L  
🔵 **CNG:** ₹{cng:.2f}/kg

📊 **Price Comparison:**  
{comparison_text}  
Difference: ₹{diff:.2f}/L

💡 **Tip:** Prices are revised daily at 6:00 AM by oil companies."""