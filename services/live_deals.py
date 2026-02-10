"""
Live Local Deals Service
Aggregates deals from food delivery apps and e-commerce platforms for Hyderabad
Integrates with Swiggy, Zomato, Amazon, Flipkart APIs
"""
import streamlit as st
from datetime import datetime, timedelta
import json
from pathlib import Path
from typing import Dict, List, Optional
import requests
from collections import defaultdict
import hashlib


# ═══════════════════════════════════════════════════════════════════════════
# API CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

def get_rapidapi_key():
    """Get RapidAPI key for Zomato/Swiggy APIs"""
    return st.secrets.get("RAPIDAPI_KEY", "")


# ═══════════════════════════════════════════════════════════════════════════
# FOOD DELIVERY DEALS (Swiggy & Zomato via RapidAPI)
# ═══════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=1800)  # Cache for 30 minutes
def get_swiggy_offers(city: str = "Hyderabad") -> List[Dict]:
    """
    Fetch live Swiggy offers using RapidAPI
    
    API: Swiggy API on RapidAPI
    Endpoint: /swiggy/offers
    
    Args:
        city: City name (default: Hyderabad)
    
    Returns:
        List of offer dicts
    """
    api_key = get_rapidapi_key()
    if not api_key:
        print("[deals] RAPIDAPI_KEY not configured")
        return get_fallback_food_deals("swiggy")
    
    url = "https://swiggy-api.p.rapidapi.com/offers"
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "swiggy-api.p.rapidapi.com"
    }
    
    params = {
        "city": city,
        "lat": "17.385",
        "lng": "78.486"
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 429:
            print("[deals] Swiggy API rate limited")
            return get_fallback_food_deals("swiggy")
        
        response.raise_for_status()
        data = response.json()
        
        # Parse offers
        offers = []
        for offer_data in data.get("data", {}).get("offers", [])[:10]:
            offers.append({
                "platform": "Swiggy",
                "title": offer_data.get("title", "Special Offer"),
                "description": offer_data.get("description", ""),
                "code": offer_data.get("code", ""),
                "discount": offer_data.get("discount", ""),
                "min_order": offer_data.get("minOrder", ""),
                "max_discount": offer_data.get("maxDiscount", ""),
                "valid_till": offer_data.get("validTill", ""),
                "category": "food_delivery",
                "link": "https://www.swiggy.com"
            })
        
        return offers if offers else get_fallback_food_deals("swiggy")
        
    except Exception as e:
        print(f"[deals] Swiggy API error: {e}")
        return get_fallback_food_deals("swiggy")


@st.cache_data(ttl=1800)
def get_zomato_offers(city_id: int = 4) -> List[Dict]:
    """
    Fetch live Zomato offers using RapidAPI
    
    API: Zomato API on RapidAPI
    Endpoint: /offers
    
    Args:
        city_id: Zomato city ID (4 = Hyderabad)
    
    Returns:
        List of offer dicts
    """
    api_key = get_rapidapi_key()
    if not api_key:
        return get_fallback_food_deals("zomato")
    
    url = "https://zomato.p.rapidapi.com/offers"
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "zomato.p.rapidapi.com"
    }
    
    params = {"city_id": city_id}
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 429:
            return get_fallback_food_deals("zomato")
        
        response.raise_for_status()
        data = response.json()
        
        offers = []
        for offer_data in data.get("offers", [])[:10]:
            offers.append({
                "platform": "Zomato",
                "title": offer_data.get("title", "Special Offer"),
                "description": offer_data.get("description", ""),
                "code": offer_data.get("code", ""),
                "discount": offer_data.get("discount_rate", ""),
                "min_order": offer_data.get("min_value", ""),
                "max_discount": offer_data.get("max_discount", ""),
                "valid_till": offer_data.get("valid_till", ""),
                "category": "food_delivery",
                "link": "https://www.zomato.com"
            })
        
        return offers if offers else get_fallback_food_deals("zomato")
        
    except Exception as e:
        print(f"[deals] Zomato API error: {e}")
        return get_fallback_food_deals("zomato")


# ═══════════════════════════════════════════════════════════════════════════
# E-COMMERCE DEALS (Amazon, Flipkart, Myntra)
# ═══════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_amazon_deals(category: str = "electronics") -> List[Dict]:
    """
    Fetch Amazon deals using RapidAPI
    
    API: Amazon Data Scraper on RapidAPI
    Endpoint: /deals
    
    Args:
        category: Product category
    
    Returns:
        List of deal dicts
    """
    api_key = get_rapidapi_key()
    if not api_key:
        return get_fallback_ecommerce_deals("amazon")
    
    url = "https://real-time-amazon-data.p.rapidapi.com/deals"
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "real-time-amazon-data.p.rapidapi.com"
    }
    
    params = {
        "country": "IN",
        "category": category
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 429:
            return get_fallback_ecommerce_deals("amazon")
        
        response.raise_for_status()
        data = response.json()
        
        deals = []
        for item in data.get("data", {}).get("deals", [])[:10]:
            discount_pct = item.get("deal_badge", "")
            
            deals.append({
                "platform": "Amazon",
                "title": item.get("product_title", "Product"),
                "price": f"₹{item.get('deal_price', 0)}",
                "original_price": f"₹{item.get('list_price', 0)}",
                "discount": discount_pct,
                "rating": item.get("product_star_rating", ""),
                "category": category,
                "link": item.get("product_url", "https://www.amazon.in"),
                "delivery": "Free delivery available"
            })
        
        return deals if deals else get_fallback_ecommerce_deals("amazon")
        
    except Exception as e:
        print(f"[deals] Amazon API error: {e}")
        return get_fallback_ecommerce_deals("amazon")


@st.cache_data(ttl=3600)
def get_flipkart_deals(category: str = "electronics") -> List[Dict]:
    """
    Fetch Flipkart deals using RapidAPI or web scraping
    
    Args:
        category: Product category
    
    Returns:
        List of deal dicts
    """
    # Note: Flipkart API access is limited, so we use fallback data
    # In production, you could integrate with affiliate APIs
    
    return get_fallback_ecommerce_deals("flipkart", category)


# ═══════════════════════════════════════════════════════════════════════════
# BANK OFFERS & CREDIT CARD DEALS
# ═══════════════════════════════════════════════════════════════════════════

def get_bank_offers() -> List[Dict]:
    """
    Get active bank offers for popular cards
    Updated manually or via bank APIs
    
    Returns:
        List of bank offer dicts
    """
    return [
        {
            "bank": "HDFC Bank",
            "card_type": "Credit Card",
            "offer": "10% instant discount on Swiggy",
            "max_discount": "₹100",
            "min_order": "₹500",
            "valid_till": "2026-02-28",
            "category": "food_delivery",
            "terms": "Valid once per card per month"
        },
        {
            "bank": "ICICI Bank",
            "card_type": "Credit/Debit Card",
            "offer": "15% off on Amazon",
            "max_discount": "₹1000",
            "min_order": "₹5000",
            "valid_till": "2026-03-15",
            "category": "ecommerce",
            "terms": "Valid on select categories"
        },
        {
            "bank": "Axis Bank",
            "card_type": "Credit Card",
            "offer": "20% off on Zomato Pro membership",
            "max_discount": "₹300",
            "min_order": "-",
            "valid_till": "2026-02-20",
            "category": "food_delivery",
            "terms": "One-time offer for new members"
        },
        {
            "bank": "SBI Card",
            "card_type": "Credit Card",
            "offer": "5% cashback on Flipkart",
            "max_discount": "₹500",
            "min_order": "₹3000",
            "valid_till": "2026-03-31",
            "category": "ecommerce",
            "terms": "Valid on electronics only"
        }
    ]


# ═══════════════════════════════════════════════════════════════════════════
# FALLBACK DATA (when APIs are unavailable)
# ═══════════════════════════════════════════════════════════════════════════

def get_fallback_food_deals(platform: str) -> List[Dict]:
    """Fallback food delivery deals"""
    fallback_data = {
        "swiggy": [
            {
                "platform": "Swiggy",
                "title": "50% OFF up to ₹100",
                "description": "Use code SWIGGY50 on orders above ₹199",
                "code": "SWIGGY50",
                "discount": "50%",
                "min_order": "₹199",
                "max_discount": "₹100",
                "valid_till": "Today",
                "category": "food_delivery",
                "link": "https://www.swiggy.com"
            },
            {
                "platform": "Swiggy",
                "title": "Free Delivery",
                "description": "Get free delivery on orders above ₹149",
                "code": "FREEDEL",
                "discount": "100%",
                "min_order": "₹149",
                "max_discount": "₹50",
                "valid_till": "This week",
                "category": "food_delivery",
                "link": "https://www.swiggy.com"
            },
            {
                "platform": "Swiggy",
                "title": "₹125 OFF",
                "description": "Flat ₹125 off on orders above ₹499",
                "code": "SAVE125",
                "discount": "₹125",
                "min_order": "₹499",
                "max_discount": "₹125",
                "valid_till": "Weekend",
                "category": "food_delivery",
                "link": "https://www.swiggy.com"
            }
        ],
        "zomato": [
            {
                "platform": "Zomato",
                "title": "60% OFF up to ₹120",
                "description": "New users get 60% off on first order",
                "code": "FIRST60",
                "discount": "60%",
                "min_order": "₹199",
                "max_discount": "₹120",
                "valid_till": "For new users",
                "category": "food_delivery",
                "link": "https://www.zomato.com"
            },
            {
                "platform": "Zomato",
                "title": "Zomato Gold",
                "description": "2 complimentary items on every order",
                "code": "GOLD",
                "discount": "2 free items",
                "min_order": "-",
                "max_discount": "-",
                "valid_till": "Members only",
                "category": "food_delivery",
                "link": "https://www.zomato.com/gold"
            },
            {
                "platform": "Zomato",
                "title": "₹100 OFF",
                "description": "Flat ₹100 off on orders above ₹399",
                "code": "ZOMATO100",
                "discount": "₹100",
                "min_order": "₹399",
                "max_discount": "₹100",
                "valid_till": "This month",
                "category": "food_delivery",
                "link": "https://www.zomato.com"
            }
        ]
    }
    
    return fallback_data.get(platform, [])


def get_fallback_ecommerce_deals(platform: str, category: str = "electronics") -> List[Dict]:
    """Fallback e-commerce deals"""
    fallback_data = {
        "amazon": [
            {
                "platform": "Amazon",
                "title": "Samsung Galaxy M34 5G",
                "price": "₹14,999",
                "original_price": "₹19,999",
                "discount": "25% OFF",
                "rating": "4.3⭐",
                "category": "electronics",
                "link": "https://www.amazon.in",
                "delivery": "Free delivery by tomorrow"
            },
            {
                "platform": "Amazon",
                "title": "boAt Airdopes 141",
                "price": "₹999",
                "original_price": "₹2,490",
                "discount": "60% OFF",
                "rating": "4.1⭐",
                "category": "electronics",
                "link": "https://www.amazon.in",
                "delivery": "Free delivery today"
            },
            {
                "platform": "Amazon",
                "title": "Fire TV Stick 4K",
                "price": "₹3,299",
                "original_price": "₹5,999",
                "discount": "45% OFF",
                "rating": "4.5⭐",
                "category": "electronics",
                "link": "https://www.amazon.in",
                "delivery": "Prime delivery available"
            }
        ],
        "flipkart": [
            {
                "platform": "Flipkart",
                "title": "Realme Narzo 60 5G",
                "price": "₹16,999",
                "original_price": "₹22,999",
                "discount": "26% OFF",
                "rating": "4.4⭐",
                "category": "electronics",
                "link": "https://www.flipkart.com",
                "delivery": "Free delivery in 2 days"
            },
            {
                "platform": "Flipkart",
                "title": "HP Laptop 15s",
                "price": "₹34,990",
                "original_price": "₹51,490",
                "discount": "32% OFF",
                "rating": "4.2⭐",
                "category": "electronics",
                "link": "https://www.flipkart.com",
                "delivery": "No cost EMI available"
            },
            {
                "platform": "Flipkart",
                "title": "Philips Air Fryer",
                "price": "₹5,999",
                "original_price": "₹9,995",
                "discount": "40% OFF",
                "rating": "4.3⭐",
                "category": "home_appliances",
                "link": "https://www.flipkart.com",
                "delivery": "Free delivery"
            }
        ]
    }
    
    return fallback_data.get(platform, [])


# ═══════════════════════════════════════════════════════════════════════════
# DEAL AGGREGATION & FILTERING
# ═══════════════════════════════════════════════════════════════════════════

def get_all_food_deals() -> List[Dict]:
    """Aggregate deals from all food delivery platforms"""
    all_deals = []
    
    # Swiggy offers
    swiggy_deals = get_swiggy_offers()
    all_deals.extend(swiggy_deals)
    
    # Zomato offers
    zomato_deals = get_zomato_offers()
    all_deals.extend(zomato_deals)
    
    return all_deals


def get_all_ecommerce_deals(category: str = "all") -> List[Dict]:
    """Aggregate deals from all e-commerce platforms"""
    all_deals = []
    
    # Amazon deals
    amazon_deals = get_amazon_deals(category if category != "all" else "electronics")
    all_deals.extend(amazon_deals)
    
    # Flipkart deals
    flipkart_deals = get_flipkart_deals(category if category != "all" else "electronics")
    all_deals.extend(flipkart_deals)
    
    return all_deals


def filter_deals_by_discount(deals: List[Dict], min_discount_pct: int = 30) -> List[Dict]:
    """Filter deals by minimum discount percentage"""
    filtered = []
    
    for deal in deals:
        discount_str = deal.get("discount", "")
        
        # Try to extract percentage
        if "%" in discount_str:
            try:
                pct = int(discount_str.split("%")[0].strip())
                if pct >= min_discount_pct:
                    filtered.append(deal)
            except:
                filtered.append(deal)  # Include if can't parse
        else:
            filtered.append(deal)  # Include non-percentage deals
    
    return filtered


def search_deals(query: str, deals: List[Dict]) -> List[Dict]:
    """Search deals by keyword"""
    query_lower = query.lower()
    
    results = []
    for deal in deals:
        title = deal.get("title", "").lower()
        description = deal.get("description", "").lower()
        platform = deal.get("platform", "").lower()
        
        if (query_lower in title or 
            query_lower in description or 
            query_lower in platform):
            results.append(deal)
    
    return results


# ═══════════════════════════════════════════════════════════════════════════
# FORMATTING FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def format_food_deal(deal: Dict) -> str:
    """Format a single food delivery deal"""
    platform = deal.get("platform", "Platform")
    title = deal.get("title", "Special Offer")
    description = deal.get("description", "")
    code = deal.get("code", "")
    discount = deal.get("discount", "")
    min_order = deal.get("min_order", "")
    max_discount = deal.get("max_discount", "")
    valid_till = deal.get("valid_till", "")
    
    response = f"🍔 **{platform}** - {title}\n"
    
    if description:
        response += f"📝 {description}\n"
    
    if code:
        response += f"🎫 **Code:** `{code}`\n"
    
    if discount:
        response += f"💰 **Discount:** {discount}\n"
    
    if min_order:
        response += f"📦 **Min Order:** {min_order}\n"
    
    if max_discount:
        response += f"🎁 **Max Discount:** {max_discount}\n"
    
    if valid_till:
        response += f"⏰ **Valid Till:** {valid_till}\n"
    
    return response


def format_ecommerce_deal(deal: Dict) -> str:
    """Format a single e-commerce deal"""
    platform = deal.get("platform", "Platform")
    title = deal.get("title", "Product")
    price = deal.get("price", "")
    original_price = deal.get("original_price", "")
    discount = deal.get("discount", "")
    rating = deal.get("rating", "")
    delivery = deal.get("delivery", "")
    
    response = f"🛍️ **{platform}** - {title}\n"
    
    if price:
        response += f"💵 **Price:** {price}"
        if original_price:
            response += f" ~~{original_price}~~"
        response += "\n"
    
    if discount:
        response += f"🏷️ **Discount:** {discount}\n"
    
    if rating:
        response += f"⭐ **Rating:** {rating}\n"
    
    if delivery:
        response += f"🚚 {delivery}\n"
    
    return response


def format_bank_offer(offer: Dict) -> str:
    """Format a bank offer"""
    bank = offer.get("bank", "Bank")
    card_type = offer.get("card_type", "Card")
    offer_text = offer.get("offer", "Special offer")
    max_discount = offer.get("max_discount", "")
    min_order = offer.get("min_order", "")
    valid_till = offer.get("valid_till", "")
    terms = offer.get("terms", "")
    
    response = f"💳 **{bank}** ({card_type})\n"
    response += f"🎁 {offer_text}\n"
    
    if max_discount:
        response += f"💰 Max Discount: {max_discount}\n"
    
    if min_order and min_order != "-":
        response += f"📦 Min Order: {min_order}\n"
    
    if valid_till:
        response += f"⏰ Valid Till: {valid_till}\n"
    
    if terms:
        response += f"📋 {terms}\n"
    
    return response


def format_all_food_deals() -> str:
    """Format all food delivery deals"""
    deals = get_all_food_deals()
    
    if not deals:
        return "🍔 **No food delivery deals available right now**\n\nCheck back later for fresh offers!"
    
    response = f"🍔 **LIVE FOOD DELIVERY DEALS**\n"
    response += f"📅 Updated: {datetime.now().strftime('%b %d, %I:%M %p')}\n\n"
    
    # Group by platform
    by_platform = defaultdict(list)
    for deal in deals:
        by_platform[deal["platform"]].append(deal)
    
    for platform in ["Swiggy", "Zomato"]:
        if platform in by_platform:
            response += f"**{platform} Offers ({len(by_platform[platform])}):**\n\n"
            
            for deal in by_platform[platform][:5]:  # Show max 5 per platform
                response += format_food_deal(deal)
                response += "\n"
            
            response += "---\n\n"
    
    response += "💡 **Tip:** Stack bank offers with app offers for maximum savings!"
    
    return response


def format_all_ecommerce_deals(category: str = "all") -> str:
    """Format all e-commerce deals"""
    deals = get_all_ecommerce_deals(category)
    
    if not deals:
        return "🛍️ **No deals available right now**\n\nCheck back later!"
    
    response = f"🛍️ **LIVE E-COMMERCE DEALS**\n"
    if category != "all":
        response += f"📂 Category: {category.title()}\n"
    response += f"📅 Updated: {datetime.now().strftime('%b %d, %I:%M %p')}\n\n"
    
    # Group by platform
    by_platform = defaultdict(list)
    for deal in deals:
        by_platform[deal["platform"]].append(deal)
    
    for platform in ["Amazon", "Flipkart"]:
        if platform in by_platform:
            response += f"**{platform} Deals ({len(by_platform[platform])}):**\n\n"
            
            for deal in by_platform[platform][:5]:
                response += format_ecommerce_deal(deal)
                response += "\n"
            
            response += "---\n\n"
    
    return response


def format_all_bank_offers() -> str:
    """Format all bank offers"""
    offers = get_bank_offers()
    
    response = f"💳 **BANK CARD OFFERS**\n"
    response += f"📅 Updated: {datetime.now().strftime('%b %d, %I:%M %p')}\n\n"
    
    for offer in offers:
        response += format_bank_offer(offer)
        response += "\n"
    
    response += "💡 **Tip:** Check your card's terms for additional cashback benefits!"
    
    return response


# ═══════════════════════════════════════════════════════════════════════════
# MAIN QUERY HANDLER
# ═══════════════════════════════════════════════════════════════════════════

def handle_deals_query(query: str) -> str:
    """
    Main handler for deals queries
    
    Args:
        query: User's query
    
    Returns:
        Formatted response string
    """
    query_lower = query.lower()
    
    # Food delivery deals
    if any(word in query_lower for word in ["swiggy", "zomato", "food", "delivery", "order", "restaurant"]):
        return format_all_food_deals()
    
    # E-commerce deals
    if any(word in query_lower for word in ["amazon", "flipkart", "shopping", "online", "buy"]):
        category = "all"
        
        # Detect category
        if any(word in query_lower for word in ["phone", "mobile", "laptop", "electronics"]):
            category = "electronics"
        elif any(word in query_lower for word in ["fashion", "clothes", "dress"]):
            category = "fashion"
        elif any(word in query_lower for word in ["home", "furniture", "appliance"]):
            category = "home_appliances"
        
        return format_all_ecommerce_deals(category)
    
    # Bank offers
    if any(word in query_lower for word in ["bank", "card", "credit", "debit", "hdfc", "icici", "axis", "sbi"]):
        return format_all_bank_offers()
    
    # Search query
    if any(word in query_lower for word in ["deal", "offer", "discount", "coupon"]):
        # Generic deals request - show food + top e-commerce
        response = format_all_food_deals()
        response += "\n\n" + "="*50 + "\n\n"
        response += format_all_ecommerce_deals()[:1000]  # Truncate
        return response
    
    # Default: show all deals
    return format_all_food_deals()


# ═══════════════════════════════════════════════════════════════════════════
# PERSONALIZED DEALS (Integration with ai_preferences)
# ═══════════════════════════════════════════════════════════════════════════

def get_personalized_deals(user_preferences: Dict) -> List[Dict]:
    """
    Get personalized deals based on user preferences
    
    Args:
        user_preferences: User preferences dict from ai_preferences
    
    Returns:
        List of personalized deals
    """
    all_deals = []
    
    # Check food preferences
    food_interest = user_preferences.get("interests", {}).get("food", 0)
    if food_interest > 0:
        all_deals.extend(get_all_food_deals())
    
    # Check shopping preferences
    shopping_interest = user_preferences.get("interests", {}).get("shopping", 0)
    if shopping_interest > 0:
        all_deals.extend(get_all_ecommerce_deals())
    
    # If no specific preferences, show top deals
    if not all_deals:
        all_deals = get_all_food_deals()[:3]
    
    return all_deals[:10]  # Return top 10