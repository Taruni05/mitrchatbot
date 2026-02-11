"""
Enhanced News Service for Hyderabad City Guide
Improved error handling, fallback data, and better API management
"""
import requests
import streamlit as st
from datetime import datetime, timedelta
import json

# Import logger and config
from services.logger import setup_logger
from services.config import config

# Set up logger for this module
logger = setup_logger('news', 'news.log')


def get_fallback_news():
    """
    Generate fallback news with dynamic dates.
    Returns fallback news with current timestamps.
    """
    now = datetime.now()
    today = now.isoformat() + "Z"
    yesterday = (now - timedelta(days=1)).isoformat() + "Z"
    two_days_ago = (now - timedelta(days=2)).isoformat() + "Z"
    
    return [
        {
            "title": "Hyderabad Metro Expansion Plans Announced",
            "description": "HMRL announces new metro corridors connecting key IT hubs and residential areas.",
            "source": {"name": "The Hindu"},
            "publishedAt": today,
            "url": "https://www.thehindu.com"
        },
        {
            "title": "Traffic Congestion Expected During Rush Hours",
            "description": "Commuters advised to plan alternate routes during peak hours in Gachibowli and HITEC City.",
            "source": {"name": "Telangana Today"},
            "publishedAt": yesterday,
            "url": "https://telanganatoday.com"
        },
        {
            "title": "New IT Parks Coming to Hyderabad",
            "description": "State government approves development of new IT infrastructure in outer ring road areas.",
            "source": {"name": "Deccan Chronicle"},
            "publishedAt": two_days_ago,
            "url": "https://www.deccanchronicle.com"
        },
    ]


# Keep as fallback for the fallback
FALLBACK_NEWS = get_fallback_news()


@st.cache_data(ttl=config.cache.NEWS)
def get_hyderabad_news(max_articles: int = None):
    """
    Fetch latest Hyderabad news from NewsAPI.
    
    Args:
        max_articles: Maximum number of articles to fetch (uses config default if None)
    
    Returns:
        List of article dictionaries, or fallback news on error
    """
    
    # Use config default if not specified
    if max_articles is None:
        max_articles = config.api.NEWS_MAX_ARTICLES
    
    api_key = config.api.get_news_api_key()
    
    if not api_key:
        logger.warning("NEWS_API_KEY not configured - using fallback data")
        return get_fallback_news()
    
    # Enhanced search query to get more relevant Hyderabad-specific news
    # Using multiple search terms with OR to cast a wider net
    search_terms = [
        "Hyderabad",
        "Telangana", 
        "GHMC",
        "Cyberabad",
        "Secunderabad",
        "Gachibowli",
        "HITEC City",
        "Hyderabad Metro",
        "KCR",  # Chief Minister reference
        "Revanth Reddy",  # Another political figure
    ]
    
    # Build the query string
    query = " OR ".join(search_terms)
    
    # Calculate date range (using config)
    to_date = datetime.now().strftime("%Y-%m-%d")
    from_date = (datetime.now() - timedelta(days=config.api.NEWS_DAYS_BACK)).strftime("%Y-%m-%d")
    
    logger.debug(f"Fetching news from {from_date} to {to_date}")
    
    url = (
        "https://newsapi.org/v2/everything?"
        f"q={query}&"
        f"from={from_date}&"
        f"to={to_date}&"
        "sortBy=publishedAt&"
        "language=en&"
        f"pageSize={max_articles}&"
        f"apiKey={api_key}"
    )
    
    logger.info(f"Fetching {max_articles} news articles for Hyderabad")
    
    try:
        response = requests.get(url, timeout=config.api.NEWS_TIMEOUT)
        
        # Check for API errors
        if response.status_code == 429:
            logger.warning("NewsAPI rate limit exceeded (429) - using fallback data")
            return get_fallback_news()
        
        if response.status_code == 401:
            logger.error("NewsAPI authentication failed (401) - check API key")
            return get_fallback_news()
        
        response.raise_for_status()
        
        data = response.json()
        
        # Check API response status
        if data.get("status") != "ok":
            logger.error(f"NewsAPI error: {data.get('message', 'Unknown error')}")
            return get_fallback_news()
        
        articles = data.get("articles", [])
        
        if not articles:
            logger.warning("No articles found - using fallback data")
            return get_fallback_news()
        
        # Filter out removed/deleted articles
        valid_articles = [
            a for a in articles 
            if a.get("title") != "[Removed]" and a.get("description") != "[Removed]"
        ]
        
        if not valid_articles:
            logger.warning("All articles were removed - using fallback data")
            return get_fallback_news()
        
        logger.info(f"Successfully fetched {len(valid_articles)} valid articles")
        return valid_articles[:max_articles]
        
    except requests.exceptions.Timeout:
        logger.warning("Request timed out - using fallback data")
        return get_fallback_news()
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {e} - using fallback data")
        return get_fallback_news()
    
    except json.JSONDecodeError:
        logger.error("Failed to parse JSON response - using fallback data")
        return get_fallback_news()
    
    except Exception as e:
        logger.error(f"Unexpected error: {e} - using fallback data", exc_info=True)
        return get_fallback_news()


def get_news_by_category(category: str = None):
    """
    Get news filtered by category/topic.
    
    Categories:
        - traffic: Traffic updates, road closures
        - weather: Weather alerts, rain updates
        - politics: Local politics, government announcements
        - tech: IT sector, startups, tech parks
        - events: Concerts, festivals, cultural events
        - sports: Local sports news
        - crime: Safety, crime reports
    """
    all_news = get_hyderabad_news(max_articles=20)
    
    if not category:
        return all_news
    
    category_keywords = {
        "traffic": ["traffic", "road", "jam", "congestion", "block", "closure", "accident"],
        "weather": ["weather", "rain", "temperature", "flood", "heat", "cold", "storm"],
        "politics": ["government", "minister", "election", "policy", "KCR", "Revanth"],
        "tech": ["IT", "tech", "startup", "software", "cyberabad", "HITEC", "innovation"],
        "events": ["concert", "festival", "event", "exhibition", "fair", "celebration"],
        "sports": ["cricket", "sports", "match", "tournament", "IPL", "athlete"],
        "crime": ["crime", "police", "theft", "arrest", "safety", "robbery"],
    }
    
    keywords = category_keywords.get(category.lower(), [])
    
    if not keywords:
        return all_news
    
    # Filter articles that contain category keywords
    filtered = []
    for article in all_news:
        title = article.get("title", "").lower()
        description = article.get("description", "").lower()
        
        if any(keyword in title or keyword in description for keyword in keywords):
            filtered.append(article)
    
    return filtered if filtered else all_news[:5]


def format_news_article(article: dict) -> str:
    """Format a single news article for display"""
    title = article.get("title", "No title")
    description = article.get("description", "No description available")
    source = article.get("source", {}).get("name", "Unknown Source")
    url = article.get("url", "#")
    
    # Parse and format date
    published_at = article.get("publishedAt", "")
    try:
        dt = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
        time_ago = get_time_ago(dt)
    except:
        time_ago = "Recently"
    
    formatted = f"**{title}**\n"
    formatted += f"📰 {source} • {time_ago}\n"
    
    if description and description != "No description available":
        formatted += f"{description}\n"
    
    formatted += f"[Read more]({url})\n"
    
    return formatted


def get_time_ago(dt: datetime) -> str:
    """Convert datetime to human-readable 'time ago' format"""
    now = datetime.now(dt.tzinfo)
    diff = now - dt
    
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return "Just now"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes} min ago" if minutes == 1 else f"{minutes} mins ago"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours} hour ago" if hours == 1 else f"{hours} hours ago"
    else:
        days = int(seconds / 86400)
        return f"{days} day ago" if days == 1 else f"{days} days ago"


def get_news_summary():
    """Get a quick summary of latest news (for dashboard/widgets)"""
    articles = get_hyderabad_news(max_articles=5)
    
    summary = "📰 **Latest Hyderabad Headlines**\n\n"
    
    for i, article in enumerate(articles[:3], 1):
        title = article.get("title", "No title")
        summary += f"{i}. {title}\n"
    
    return summary


# ─── Cache management helpers ───────────────────────────────────────────────

def clear_news_cache():
    """Manually clear the news cache (useful for forcing refresh)"""
    get_hyderabad_news.clear()
    logger.info("News cache cleared successfully")


def get_cache_info():
    """Get information about the current cache status"""
    ttl_seconds = config.cache.NEWS
    ttl_minutes = ttl_seconds // 60
    
    return {
        "ttl": f"{ttl_minutes} minutes",
        "ttl_seconds": ttl_seconds,
        "status": "Active",
        "description": f"News is cached for {ttl_minutes} minutes to reduce API calls"
    }