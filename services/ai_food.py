"""
Enhanced AI Food Recommendation Service
Handles ANY food-related query comprehensively using Gemini
"""
from google import genai
import streamlit as st
import time
from services.food_loader import load_restaurants

# Import logger and config
from services.logger import setup_logger
from services.config import config

# Set up logger
logger = setup_logger('ai_food', 'ai_food.log')

# Initialize Gemini client with config
# Client created per-request to enable key rotation

# Load restaurant knowledge base
RESTAURANTS = load_restaurants()


def create_restaurant_context():
    """Create a comprehensive context of all restaurants for Gemini"""
    context = "# HYDERABAD RESTAURANTS DATABASE\n\n"
    
    for r in RESTAURANTS:
        context += f"## {r['name']}\n"
        context += f"- Category: {r.get('category', 'General')}\n"
        context += f"- Price Range: {r.get('price_range', 'Not specified')}\n"
        context += f"- Opening Hours: {r.get('opening_hours', 'Check with restaurant')}\n"
        
        if r.get('best_selling_dishes'):
            context += f"- Best Dishes: {', '.join(r['best_selling_dishes'])}\n"
        
        if r.get('maps_link'):
            context += f"- Location: {r['maps_link']}\n"
        
        context += "\n"
    
    return context


def generate_food_recommendation(user_query: str):
    """
    Generate comprehensive food recommendations for ANY food-related query.
    
    Handles queries like:
    - "Best biryani places"
    - "Where to eat vegetarian food?"
    - "Cheap restaurants near HITEC City"
    - "Late night cafes"
    - "Romantic dinner spots"
    - "Best Irani chai"
    - "What should I eat today?"
    - "Street food recommendations"
    - etc.
    """
    
    logger.info(f"Generating food recommendation for: {user_query[:100]}...")
    
    # Create restaurant knowledge base context
    restaurant_context = create_restaurant_context()
    
    # Comprehensive prompt that handles ANY food query
    prompt = f"""You are a Hyderabad food expert assistant with deep local knowledge.

USER QUERY: "{user_query}"

AVAILABLE RESTAURANT DATA:
{restaurant_context}

INSTRUCTIONS:
1. Analyze the user's query to understand what they're looking for
2. Recommend ONLY from the provided restaurant database
3. If no perfect match exists, recommend the closest alternatives from the database
4. Be specific and practical with recommendations
5. Always include:
   - Restaurant name
   - Price range (if available)
   - Best dishes to try
   - Any relevant timings
   - Google Maps link (if available)

6. For general queries like "what should I eat" or "recommend something", suggest 3-4 diverse options

7. For specific cuisines/dishes not in database, acknowledge that and suggest closest alternatives

8. Use emojis to make responses engaging (🍛 🍕 ☕ 🌶️ etc.)

9. Include practical tips like:
   - Best time to visit
   - Average cost per person
   - Whether booking is needed
   - Popular crowd times

10. Format your response clearly with proper headings and bullet points

11. If asking about specific dishes (biryani, haleem, chai, etc.), focus on restaurants known for those items

12. For location-based queries, mention restaurants in or near that area

13. NEVER invent restaurant names - only use restaurants from the database

14. If the database doesn't have enough info for the query, be honest and suggest checking food delivery apps

RESPONSE STYLE:
- Friendly and conversational
- Use Hyderabadi flair (you can mention local terms like "baigan ka bharta", "irani chai", etc.)
- Be practical - mention costs, locations, timings
- Prioritize restaurants with ratings/reviews if available
- Use proper formatting with headers, bullets, and emojis

Generate your recommendation now:"""

    # Retry logic with config
    for attempt in range(1, config.api.GEMINI_MAX_RETRIES + 1):
        try:
            logger.debug(f"Gemini API attempt {attempt}/{config.api.GEMINI_MAX_RETRIES}")
            
            client = genai.Client(api_key=config.api.get_next_gemini_key())
            response = client.models.generate_content(
                model=config.api.GEMINI_MODEL,
                contents=prompt,
            )
            
            result = response.text
            logger.info(f"✅ Generated {len(result)} chars food recommendation")
            return result

        except Exception as e:
            logger.warning(f"Attempt {attempt} failed: {e}")
            
            if attempt < config.api.GEMINI_MAX_RETRIES:
                time.sleep(1)
                continue
            else:
                logger.error("All Gemini attempts failed for food recommendation", exc_info=True)
                return fallback_food_response(user_query)


def fallback_food_response(query: str):
    """Fallback response when Gemini API fails"""
    
    logger.info("Using fallback food response")
    
    # Try to give a basic response based on keywords
    query_lower = query.lower()
    
    if "biryani" in query_lower:
        restaurants = [r for r in RESTAURANTS if "biryani" in r.get("name", "").lower()]
    elif "cafe" in query_lower or "coffee" in query_lower:
        restaurants = [r for r in RESTAURANTS if r.get("category") == "cafes"]
    elif "cheap" in query_lower or "budget" in query_lower:
        restaurants = [r for r in RESTAURANTS if "budget" in r.get("price_range", "").lower()]
    else:
        # Just show top popular places
        restaurants = RESTAURANTS[:5]
    
    if not restaurants:
        restaurants = RESTAURANTS[:3]
    
    response = "🍽️ **Hyderabad Food Recommendations**\n\n"
    response += "⚠️ *Showing cached recommendations due to high traffic*\n\n"
    
    for i, r in enumerate(restaurants[:3], 1):
        response += f"**{i}. {r['name']}**\n"
        if r.get('price_range'):
            response += f"💰 {r['price_range']}\n"
        if r.get('best_selling_dishes'):
            response += f"🍽️ Must Try: {', '.join(r['best_selling_dishes'][:3])}\n"
        if r.get('maps_link'):
            response += f"📍 [Google Maps]({r['maps_link']})\n"
        response += "\n"
    
    response += "\n💡 **Tip**: Try food delivery apps like Zomato or Swiggy for more options and live reviews!"
    
    return response


# Additional helper function for specific food types
def get_food_by_category(category: str):
    """Get restaurants by category for quick lookups"""
    category_lower = category.lower()
    
    filtered = [r for r in RESTAURANTS if r.get('category', '').lower() == category_lower]
    
    if not filtered:
        return None
    
    response = f"🍽️ **{category.title()} in Hyderabad**\n\n"
    
    for i, r in enumerate(filtered, 1):
        response += f"**{i}. {r['name']}**\n"
        if r.get('price_range'):
            response += f"💰 {r['price_range']}\n"
        if r.get('opening_hours'):
            response += f"🕐 {r['opening_hours']}\n"
        if r.get('best_selling_dishes'):
            response += f"🍽️ Specialties: {', '.join(r['best_selling_dishes'][:3])}\n"
        if r.get('maps_link'):
            response += f"📍 [Google Maps]({r['maps_link']})\n"
        response += "\n"
    
    return response