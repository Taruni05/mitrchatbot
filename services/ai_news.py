"""
Enhanced AI News Summarizer for Hyderabad City Guide
Better prompts, error handling, and fallback responses
"""
from google import genai
import streamlit as st
import time
from datetime import datetime

# Import logger and config
from services.logger import setup_logger
from services.config import config

# Set up logger
logger = setup_logger('ai_news', 'ai_news.log')

# Initialize Gemini client with config
# Client created per-request to enable key rotation


def summarize_news(articles, query: str = None):
    """
    Intelligently summarize Hyderabad news articles using Gemini.
    
    Args:
        articles: List of news article dictionaries
        query: Optional - user's specific query (e.g., "traffic news", "tech updates")
    
    Returns:
        Formatted news summary string
    """
    
    if not articles:
        logger.warning("No articles provided for summarization")
        return "📰 No news articles available at the moment. Please try again later."
    
    logger.info(f"Summarizing {len(articles)} news articles")
    
    # Build context from articles
    articles_text = ""
    for i, article in enumerate(articles, 1):
        title = article.get("title", "")
        description = article.get("description", "")
        source = article.get("source", {}).get("name", "Unknown")
        
        # Skip removed/deleted articles
        if title == "[Removed]" or description == "[Removed]":
            continue
        
        articles_text += f"{i}. {title}\n"
        if description:
            articles_text += f"   {description}\n"
        articles_text += f"   Source: {source}\n\n"
    
    if not articles_text.strip():
        logger.warning("All articles were removed or invalid")
        return "📰 No valid news articles available at the moment."
    
    # Build intelligent prompt based on query
    if query:
        query_lower = query.lower()
        
        # Customize prompt based on user's specific interest
        if any(word in query_lower for word in ["traffic", "road", "jam", "congestion"]):
            focus = "traffic updates, road closures, accidents, and transportation issues"
        elif any(word in query_lower for word in ["weather", "rain", "temperature"]):
            focus = "weather updates, rainfall, temperature, and climate alerts"
        elif any(word in query_lower for word in ["tech", "IT", "startup", "software"]):
            focus = "technology sector news, IT companies, startups, and tech parks"
        elif any(word in query_lower for word in ["event", "festival", "concert", "exhibition"]):
            focus = "upcoming events, festivals, concerts, and cultural activities"
        elif any(word in query_lower for word in ["crime", "safety", "police"]):
            focus = "crime reports, safety alerts, and police updates"
        else:
            focus = "general city news and important updates"
    else:
        focus = "general city news and important updates"
    
    logger.debug(f"News focus: {focus}")
    
    # Enhanced prompt with better instructions
    prompt = f"""You are a Hyderabad city news assistant providing concise, relevant summaries.

USER INTEREST: {focus}

NEWS ARTICLES:
{articles_text}

INSTRUCTIONS:
1. Organize the summary into clear sections:
   📰 **Top Hyderabad Headlines** (3-5 most important stories)
   ⚠️ **City Alerts** (traffic, weather, safety - if any)
   🎉 **Upcoming Events** (concerts, festivals, exhibitions - if any)
   💡 **What You Should Know** (key takeaways)

2. Focus ONLY on Hyderabad/Telangana news - ignore national/international politics unless directly impacting the city

3. For each headline:
   - Keep it under 2 lines
   - Use emojis sparingly (only for section headers)
   - Include source if credible/important
   - Highlight impact on citizens

4. Prioritize:
   - Breaking news and urgent alerts
   - Traffic/weather affecting daily commute
   - Major city developments (metro, IT parks, infrastructure)
   - Safety and health alerts
   - Community events

5. Skip:
   - National politics not affecting Hyderabad
   - Celebrity gossip
   - Generic news without local relevance
   - Duplicate stories

6. Style:
   - Professional but conversational
   - Use bullet points (•) not numbered lists
   - Keep total summary under 300 words
   - End with a helpful tip or call-to-action

7. If no relevant news in a category, skip that section entirely

Generate the summary now:"""

    # Retry logic with config
    for attempt in range(1, config.api.GEMINI_MAX_RETRIES + 1):
        try:
            logger.debug(f"Gemini API attempt {attempt}/{config.api.GEMINI_MAX_RETRIES}")
            
            # Use simpler prompt on retry
            if attempt > 1:
                prompt = f"""Summarize these Hyderabad news articles briefly:

{articles_text}

Format:
📰 Top Headlines (3-5 stories)
⚠️ Alerts (if any)
🎉 Events (if any)

Keep it concise and relevant to Hyderabad only."""
                logger.debug("Using simplified prompt for retry")
            
            client = genai.Client(api_key=config.api.get_next_gemini_key())
            response = client.models.generate_content(
                model=config.api.GEMINI_MODEL,
                contents=prompt,
            )
            
            summary = response.text.strip()
            
            # Add timestamp
            timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p")
            summary += f"\n\n---\n*Last updated: {timestamp}*"
            
            logger.info(f"✅ Generated {len(summary)} chars news summary")
            return summary
            
        except Exception as e:
            logger.warning(f"Attempt {attempt} failed: {e}")
            
            if attempt < config.api.GEMINI_MAX_RETRIES:
                time.sleep(1)
                continue
            else:
                logger.error("All Gemini attempts failed for news summarization", exc_info=True)
                return fallback_news_summary(articles)


def fallback_news_summary(articles):
    """
    Create a basic summary when AI fails.
    Just formats the raw articles nicely.
    """
    logger.info("Using fallback news summary")
    
    summary = "📰 **Hyderabad News Today**\n\n"
    summary += "⚠️ *AI summarization unavailable - showing raw headlines*\n\n"
    
    valid_articles = [
        a for a in articles 
        if a.get("title") != "[Removed]" and a.get("title")
    ]
    
    if not valid_articles:
        return "📰 No news articles available at the moment."
    
    summary += "**Top Headlines:**\n\n"
    
    for i, article in enumerate(valid_articles[:7], 1):
        title = article.get("title", "No title")
        source = article.get("source", {}).get("name", "Unknown")
        
        summary += f"{i}. **{title}**\n"
        summary += f"   📰 {source}\n\n"
    
    summary += "\n💡 **Tip:** Check local news websites for detailed coverage."
    
    return summary


def get_news_categories_summary(articles):
    """
    Organize news by categories for better navigation.
    """
    categories = {
        "traffic": [],
        "weather": [],
        "tech": [],
        "events": [],
        "general": []
    }
    
    keywords = {
        "traffic": ["traffic", "road", "jam", "congestion", "accident"],
        "weather": ["weather", "rain", "temperature", "flood"],
        "tech": ["IT", "tech", "startup", "software", "HITEC"],
        "events": ["concert", "festival", "event", "exhibition"],
    }
    
    for article in articles:
        title = article.get("title", "").lower()
        description = article.get("description", "").lower()
        
        categorized = False
        for category, kws in keywords.items():
            if any(kw in title or kw in description for kw in kws):
                categories[category].append(article)
                categorized = True
                break
        
        if not categorized:
            categories["general"].append(article)
    
    # Build organized summary
    summary = "📰 **Hyderabad News - Organized by Category**\n\n"
    
    emoji_map = {
        "traffic": "🚦",
        "weather": "🌦️",
        "tech": "💻",
        "events": "🎉",
        "general": "📰"
    }
    
    for category, arts in categories.items():
        if not arts:
            continue
        
        emoji = emoji_map.get(category, "📰")
        summary += f"{emoji} **{category.title()}**\n"
        
        for article in arts[:3]:  # Max 3 per category
            title = article.get("title", "No title")
            summary += f"  • {title}\n"
        
        summary += "\n"
    
    return summary


def get_quick_news_digest(articles, max_items: int = 5):
    """
    Ultra-concise news digest for quick reading (e.g., mobile notifications).
    """
    valid_articles = [
        a for a in articles[:max_items]
        if a.get("title") != "[Removed]"
    ]
    
    digest = "📰 **Quick News Digest**\n\n"
    
    for i, article in enumerate(valid_articles, 1):
        title = article.get("title", "No title")
        digest += f"{i}. {title}\n"
    
    return digest