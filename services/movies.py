import json
from pathlib import Path
from services.kb_loader import get_theaters


def load_theater_data():
    return get_theaters()

THEATERS      = None
BOOKING_TIPS  = None


def get_movie_info(query: str = None):
    global THEATERS, BOOKING_TIPS

    if THEATERS is None:
        theater_data = load_theater_data()
        THEATERS = {
            "pvr":     theater_data.get("pvr",     []),
            "inox":    theater_data.get("inox",    []),
            "special": theater_data.get("special", []),
            "budget":  theater_data.get("budget",  []),
        }
        BOOKING_TIPS = theater_data.get("booking_tips", {})

    if not query:
        return show_general_theater_info()

    query_lower = query.lower()

    # ── specific theater queries ──────────────────────────────────────
    if "pvr" in query_lower:
        if "inorbit" in query_lower:
            return format_single_theater(THEATERS["pvr"][0]) if THEATERS["pvr"] else show_general_theater_info()
        else:
            return format_theater_chain("pvr")

    elif "inox" in query_lower:
        if "gvk" in query_lower:
            return format_single_theater(THEATERS["inox"][0]) if THEATERS["inox"] else show_general_theater_info()
        else:
            return format_theater_chain("inox")

    elif "amb" in query_lower:
        return format_single_theater(THEATERS["special"][0]) if THEATERS["special"] else show_general_theater_info()

    elif "prasad" in query_lower or "imax" in query_lower:
        # Prasads is special[1] if it exists, otherwise fall back to special[0]
        idx = 1 if len(THEATERS["special"]) > 1 else 0
        return format_single_theater(THEATERS["special"][idx]) if THEATERS["special"] else show_general_theater_info()

    # ── booking / tips ────────────────────────────────────────────────
    elif "book" in query_lower or "ticket" in query_lower or "how to" in query_lower:
        return format_booking_tips()

    # ── budget ────────────────────────────────────────────────────────
    elif "cheap" in query_lower or "budget" in query_lower or "affordable" in query_lower:
        return format_budget_theaters()

    # ── premium formats ───────────────────────────────────────────────
    elif "4dx" in query_lower or "imax" in query_lower or "premium" in query_lower:
        return format_premium_formats()

    else:
        return show_general_theater_info()


# ── formatters (unchanged logic, just use the globals populated above) ──────

def format_single_theater(theater: dict):
    response  = f"🎬 **{theater['name']}**\n\n"
    response += f"📍 **Location:** {theater['location']}\n"
    response += f"🎞️ **Screens:** {theater.get('screens', 'N/A')}\n"
    response += f"💰 **Avg Ticket:** {theater.get('avg_ticket', 'Check website')}\n\n"

    response += "**Formats Available:**\n"
    for fmt in theater.get('formats', []):
        response += f"   • {fmt}\n"

    if 'amenities' in theater:
        response += "\n**Amenities:**\n"
        for amenity in theater['amenities']:
            response += f"   • {amenity}\n"

    if 'special_feature' in theater:
        response += f"\n✨ **Special:** {theater['special_feature']}\n"

    response += f"\n🔗 **Book:** {theater.get('booking_link', 'BookMyShow')}\n"
    response += f"📞 **Phone:** {theater.get('phone', 'Check website')}\n\n"

    response += "💡 **Tips:**\n"
    response += "• Book online to avoid queues\n"
    response += "• Weekday shows are cheaper\n"
    response += "• F&B is expensive - eat outside if possible\n"

    return response


def format_theater_chain(chain: str):
    theaters = THEATERS.get(chain, [])
    if not theaters:
        return show_general_theater_info()

    response = f"🎬 **{chain.upper()} THEATERS IN HYDERABAD**\n\n"

    for theater in theaters:
        response += f"**{theater['name']}**\n"
        response += f"📍 {theater['location']} | 🎞️ {theater.get('screens', '?')} screens\n"
        response += f"💰 {theater.get('avg_ticket', 'Check website')}\n"
        response += f"Formats: {', '.join(theater.get('formats', []))}\n\n"

    response += f"🔗 **Book Online:** {theaters[0].get('booking_link', 'BookMyShow')}\n\n"

    response += "💡 **Which one to choose?**\n"
    if chain == "pvr":
        response += "• **Inorbit** - Best for IMAX/4DX\n"
        response += "• **Irrum Manzil** - Central location, Gold Class\n"
        response += "• **Next Galleria** - Good screens, convenient parking\n"
    elif chain == "inox":
        response += "• **GVK One** - Premium experience, IMAX available\n"
        response += "• **Maheshwari** - Budget-friendly, good sound\n"

    return response


def format_booking_tips():
    response = "🎟️ **HOW TO BOOK MOVIE TICKETS**\n\n"

    if BOOKING_TIPS:
        response += "**📱 Online Booking Platforms:**\n"
        for platform in BOOKING_TIPS.get("online", []):
            response += f"   • {platform}\n"

        response += "\n**💰 Best Deals & Offers:**\n"
        for deal in BOOKING_TIPS.get("best_deals", []):
            response += f"   • {deal}\n"

        response += "\n**💡 Pro Tips:**\n"
        for tip in BOOKING_TIPS.get("pro_tips", []):
            response += f"   • {tip}\n"
    else:
        response += "**📱 Online Booking Platforms:**\n"
        response += "   • BookMyShow\n   • PayTM\n   • Theater websites\n"

    response += "\n**🎫 Ticket Prices:**\n"
    response += "• Weekday matinee: ₹100-150\n"
    response += "• Weekday evening: ₹150-250\n"
    response += "• Weekend: ₹200-350\n"
    response += "• IMAX/4DX: ₹350-600\n"
    response += "• Gold/Premium: ₹400-800\n\n"

    response += "⚡ **Book Now:** https://www.bookmyshow.com\n"
    return response


def format_budget_theaters():
    response = "💰 **BUDGET-FRIENDLY THEATERS**\n\n"

    for theater in THEATERS.get("budget", []):
        response += f"**{theater['name']}**\n"
        response += f"📍 {theater['location']}\n"
        response += f"💵 {theater.get('avg_ticket', 'Check website')}\n"
        response += f"✨ {theater.get('special_feature', 'Classic experience')}\n\n"

    response += "**Why Choose Single Screens?**\n"
    response += "• **Cheapest tickets** in the city\n"
    response += "• **Massive crowd energy** - Bollywood blockbusters are fun here!\n"
    response += "• **Nostalgia** - Classic cinema experience\n"
    response += "• **Central location** - Easy to reach\n\n"
    response += "⚠️ **Note:** Single screens can get very crowded. Go with friends!\n"

    return response


def format_premium_formats():
    response = "✨ **PREMIUM MOVIE EXPERIENCES**\n\n"

    response += "**🎬 IMAX:**\n"
    response += "• **Prasads IMAX** - One of world's largest IMAX screens\n"
    response += "• **PVR Inorbit IMAX** - Modern facility\n"
    response += "• **INOX GVK One IMAX** - Premium seating\n"
    response += "💰 ₹350-600 per ticket\n\n"

    response += "**🌀 4DX (Motion Seats + Effects):**\n"
    response += "• **PVR Inorbit 4DX** - Only 4DX in Hyderabad\n"
    response += "• Wind, water, scent, motion effects\n"
    response += "💰 ₹400-600 per ticket\n"
    response += "⚠️ Not for everyone - can cause motion sickness\n\n"

    response += "**🥂 Gold/Insignia (Luxury):**\n"
    response += "• **INOX Insignia (GVK One)** - Recliner seats, butler service\n"
    response += "• **PVR Gold Class** - Gourmet food, premium seats\n"
    response += "💰 ₹600-800 per ticket\n\n"

    response += "💡 **Recommendation:**\n"
    response += "• Action/Sci-fi → IMAX\n"
    response += "• Action with effects → 4DX\n"
    response += "• Romance/Drama → Gold Class\n"

    return response


def show_general_theater_info():
    response = "🎬 **HYDERABAD MOVIE THEATERS GUIDE**\n\n"

    response += "**🌟 Premium Experiences:**\n"
    response += "• Prasads IMAX - Iconic IMAX screen\n"
    response += "• AMB Cinemas - Largest multiplex\n"
    response += "• INOX GVK One - Luxury Insignia screens\n"
    response += "• PVR Inorbit - 4DX + IMAX\n\n"

    response += "**💰 Budget Options:**\n"
    response += "• Sudarshan 35mm - ₹80-150\n"
    response += "• Sandhya 70mm - ₹70-120\n\n"

    response += "**📍 By Location:**\n"
    response += "• HITEC City/Gachibowli: AMB, PVR Inorbit\n"
    response += "• Banjara Hills: INOX GVK One\n"
    response += "• Necklace Road: Prasads IMAX\n"
    response += "• RTC Cross Roads: Sudarshan, Sandhya\n\n"

    response += "🔗 **Book Now:** https://www.bookmyshow.com\n\n"

    response += "❓ **Ask me:**\n"
    response += '• "Best IMAX theater"\n'
    response += '• "Cheap movie tickets"\n'
    response += '• "How to book tickets"\n'
    response += '• "PVR theaters in Hyderabad"'

    return response


def get_live_showtimes(theater_name: str, date: str = None):
    """Future: Integrate with BookMyShow API for live showtimes."""
    return (
        f"🎬 **Live showtimes for {theater_name}**\n\n"
        "For real-time showtimes and booking:\n"
        "🔗 https://www.bookmyshow.com\n\n"
        "💡 Tip: BookMyShow shows all movies, timings, and seat availability!"
    )