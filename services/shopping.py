import json,streamlit as st
from pathlib import Path

@st.cache_data
def load_shopping_data():
    """Load shopping data from knowledge base"""
    kb_path = Path(__file__).resolve().parent.parent / "knowledge_base.json"
    with open(kb_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("shopping_malls", {})

# Replace MALLS_DATA = {...} with:
MALLS_DATA = None  # Will be loaded dynamically

def get_mall_info(query: str = None):
    global MALLS_DATA
    if MALLS_DATA is None:
        MALLS_DATA = load_shopping_data()
    
    query_lower = query.lower() if query else ""
    
    # Check for specific mall
    if "inorbit" in query_lower:
        return format_single_mall(MALLS_DATA["premium_malls"][0])
    elif "gvk" in query_lower:
        return format_single_mall(MALLS_DATA["premium_malls"][1])
    elif "forum" in query_lower or "kukatpally" in query_lower:
        return format_single_mall(MALLS_DATA["premium_malls"][2])
    elif "ikea" in query_lower:
        return format_single_mall(MALLS_DATA["premium_malls"][3])
    elif "amb" in query_lower:
        return format_single_mall(MALLS_DATA["premium_malls"][4])
    
    # Check for market queries
    elif any(word in query_lower for word in ["laad", "bangle", "charminar market"]):
        return format_single_market(MALLS_DATA["traditional_markets"][0])
    elif "begum bazaar" in query_lower or "wholesale" in query_lower:
        return format_single_market(MALLS_DATA["traditional_markets"][1])
    elif "abids" in query_lower or "book" in query_lower:
        return format_single_market(MALLS_DATA["traditional_markets"][2])
    
    # Check for sale info
    elif "sale" in query_lower or "discount" in query_lower or "offer" in query_lower:
        return format_sales_info()
    
    # Check for crowd info
    elif "crowd" in query_lower or "busy" in query_lower or "best time" in query_lower:
        return format_crowd_info()
    
    # General shopping guide
    else:
        return format_general_shopping()


def format_single_mall(mall: dict):
    """Format single mall information"""
    response = f"🛍️ **{mall['name']}**\n\n"
    response += f"📍 **Location:** {mall['location']}\n"
    response += f"⏰ **Timings:** {mall['timings']}\n"
    response += f"💰 **Avg Spending:** {mall['avg_spending']}\n\n"
    
    response += f"✨ **Attractions:**\n"
    for attr in mall['attractions']:
        response += f"   • {attr}\n"
    
    response += f"\n🏪 **Popular Stores:**\n"
    for store in mall['popular_stores'][:5]:
        response += f"   • {store}\n"
    
    response += f"\n🍽️ **Food Options:**\n"
    for food in mall['food_options']:
        response += f"   • {food}\n"
    
    response += f"\n🚗 **Parking:** {mall['parking']}\n"
    response += f"👥 **Best For:** {mall['best_for']}\n\n"
    
    response += f"📊 **Crowd Levels:**\n"
    crowd = mall['crowd_level']
    response += f"   • Weekdays: {crowd['weekday']}\n"
    response += f"   • Weekends: {crowd['weekend']}\n"
    response += f"   • **Best Time:** {crowd['best_time']}\n\n"
    
    response += f"💡 **Tip:** Visit during weekday afternoons to avoid crowds!"
    
    return response


def format_single_market(market: dict):
    """Format traditional market information"""
    response = f"🏪 **{market['name']}**\n\n"
    response += f"📍 **Location:** {market['location']}\n"
    response += f"⏰ **Timings:** {market['timings']}\n"
    response += f"🎯 **Specialty:** {market['specialty']}\n"
    response += f"💰 **Avg Spending:** {market['avg_spending']}\n\n"
    
    if 'attractions' in market:
        response += f"✨ **Highlights:**\n"
        for attr in market['attractions']:
            response += f"   • {attr}\n"
        response += "\n"
    
    response += f"👥 **Best For:** {market['best_for']}\n\n"
    
    if 'tips' in market:
        response += f"💡 **Tips:**\n{market['tips']}\n\n"
    
    if 'crowd_level' in market:
        response += f"📊 **Crowd:**\n"
        for time, level in market['crowd_level'].items():
            response += f"   • {time.title()}: {level}\n"
    
    return response


def format_sales_info():
    """Format ongoing sales information"""
    response = "🎉 **CURRENT SALES & OFFERS IN HYDERABAD**\n\n"
    
    for sale in MALLS_DATA["ongoing_sales"]:
        response += f"**{sale['event']}**\n"
        response += f"📅 Period: {sale['period']}\n"
        response += f"💰 Discount: {sale['discount']}\n"
        response += f"📍 Where: {sale['where']}\n"
        response += f"🎯 Best Deals: {sale['best_deals']}\n\n"
    
    response += "💡 **Pro Tips:**\n"
    response += "• Download mall apps for exclusive deals\n"
    response += "• Check credit card offers (extra 10-20% off)\n"
    response += "• Visit on weekdays for better service\n"
    
    return response


def format_crowd_info():
    """Format crowd prediction for all malls"""
    response = "👥 **BEST TIME TO VISIT MALLS**\n\n"
    
    for mall in MALLS_DATA["premium_malls"][:5]:
        crowd = mall['crowd_level']
        response += f"**{mall['name']}**\n"
        response += f"   ✅ Best: {crowd['best_time']}\n"
        response += f"   ⚠️ Avoid: Weekend afternoons\n\n"
    
    response += "🕐 **General Pattern:**\n"
    response += "• **Least Crowded:** Weekdays 11 AM - 2 PM\n"
    response += "• **Moderately Crowded:** Weekday evenings\n"
    response += "• **Most Crowded:** Weekends 3 PM - 9 PM\n\n"
    
    response += "💡 **Tip:** IKEA is crazy on weekends - go on weekday mornings!"
    
    return response


def format_general_shopping():
    """Format general shopping guide"""
    response = "🛍️ **SHOPPING GUIDE - HYDERABAD**\n\n"
    
    response += "**🏢 Premium Malls:**\n"
    for mall in MALLS_DATA["premium_malls"][:3]:
        response += f"• **{mall['name']}** ({mall['location']})\n"
        response += f"  Best for: {mall['best_for']}\n"
    
    response += "\n**🏪 Traditional Markets:**\n"
    for market in MALLS_DATA["traditional_markets"][:3]:
        response += f"• **{market['name']}** - {market['specialty']}\n"
    
    response += "\n**💰 Budget Shopping:**\n"
    response += "• Abids - Books & electronics\n"
    response += "• Koti - Women's wear\n"
    response += "• Begum Bazaar - Wholesale groceries\n\n"
    
    response += "**💎 Luxury Shopping:**\n"
    response += "• GVK One - International brands\n"
    response += "• Banjara Hills boutiques\n\n"
    
    response += "❓ **Ask me:**\n"
    response += '• "Tell me about Inorbit mall"\n'
    response += '• "Best time to visit IKEA"\n'
    response += '• "Current sales and offers"\n'
    response += '• "Where to buy bangles in Hyderabad"'
    
    return response