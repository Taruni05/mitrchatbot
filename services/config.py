"""
Centralized Configuration Management for Hyderabad Chatbot
Single source of truth for all application settings
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple
import streamlit as st
import os


@dataclass
class CacheConfig:
    """Cache TTL configurations (in seconds)"""
    
    WEATHER: int = 600           # 10 minutes - weather changes frequently
    NEWS: int = 1800             # 30 minutes - news updates regularly
    FUEL: int = 86400            # 24 hours - fuel prices change daily
    TRAFFIC: int = 300           # 5 minutes - traffic changes constantly
    KNOWLEDGE_BASE: int = 3600   # 1 hour - KB rarely changes
    ALERTS: int = 3600           # 1 hour - utility alerts
    RESTAURANTS: int = 3600      # 1 hour - restaurant data
    THEATERS: int = 3600         # 1 hour - theater data
    ROUTES: int = 3600           # 1 hour - route data
    RESPONSE_CACHE: int = 300    # 5 minutes - user response cache


@dataclass
class APIConfig:
    """API configuration and limits"""
    
    # Gemini AI
    GEMINI_MODEL: str = "gemini-2.5-flash-lite"
    GEMINI_TIMEOUT: int = 30
    GEMINI_MAX_RETRIES: int = 2
    GEMINI_TEMPERATURE: float = 0.7
    
    # News API
    NEWS_MAX_ARTICLES: int = 15
    NEWS_DAYS_BACK: int = 7
    NEWS_TIMEOUT: int = 10
    
    # Weather API
    WEATHER_TIMEOUT: int = 5
    WEATHER_LOCATION_DEFAULT: Tuple[float, float] = (17.3850, 78.4867)  # Hyderabad central
    
    # Fuel API
    FUEL_TIMEOUT: int = 6
    
    # Traffic API
    TRAFFIC_TIMEOUT: int = 5
    
    def get_gemini_api_key(self) -> str:
        """Get Gemini API key from secrets or environment"""
        return st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY", "")
    
    def get_news_api_key(self) -> str:
        """Get News API key"""
        return st.secrets.get("NEWS_API_KEY") or os.getenv("NEWS_API_KEY", "")
    
    def get_openweather_api_key(self) -> str:
        """Get OpenWeather API key"""
        return st.secrets.get("OPENWEATHER_API_KEY") or os.getenv("OPENWEATHER_API_KEY", "")
    
    def get_tomtom_api_key(self) -> str:
        """Get TomTom API key"""
        return st.secrets.get("TOMTOM_API_KEY") or os.getenv("TOMTOM_API_KEY", "")
    
    def get_rapidapi_key(self) -> str:
        """Get RapidAPI key for fuel prices"""
        return st.secrets.get("RAPIDAPI_KEY") or os.getenv("RAPIDAPI_KEY", "")
    
    def has_required_keys(self) -> bool:
        """Check if all required API keys are configured"""
        required_keys = [
            self.get_gemini_api_key(),
            self.get_openweather_api_key(),
        ]
        return all(required_keys)


@dataclass
class UIConfig:
    """UI/UX configuration"""
    
    # Chat settings
    MAX_CHAT_HISTORY: int = 50
    CHAT_INPUT_PLACEHOLDER: Dict[str, str] = field(default_factory=lambda: {
        "en": "Ask me anything about Hyderabad…",
        "te": "హైదరాబాద్ గురించి ఏదైనా అడగండి…",
        "ur": "حیدرآباد کے بارے میں کچھ بھی پوچھیں…",
        "hi": "हैदराबाद के बारे में कुछ भी पूछें…",
    })
    
    # Suggestions
    SUGGESTIONS_COUNT: int = 5
    QUICK_LINKS_PER_ROW: int = 5
    
    # Dashboard
    DASHBOARD_REFRESH_INTERVAL: int = 60  # seconds
    
    # Theme
    THEME_DAY_HOURS: Tuple[int, int] = (6, 18)  # Day theme from 6 AM to 6 PM
    
    # Languages
    LANGUAGES: Dict[str, str] = field(default_factory=lambda: {
        "en": "English",
        "te": "తెలుగు (Telugu)",
        "ur": "اردو (Urdu)",
        "hi": "हिंदी (Hindi)"
    })
    
    # Voice
    DEFAULT_VOICE_ENABLED: bool = False
    DEFAULT_AUTO_SPEAK: bool = False


@dataclass
class AppConfig:
    """Application-level configuration"""
    
    # App metadata
    APP_NAME: str = "Mitr - Hyderabad City Guide"
    APP_VERSION: str = "1.0.0"
    APP_ICON: str = "🏙️"
    
    # Logging
    LOG_LEVEL: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_TO_FILE: bool = True
    LOG_MAX_SIZE: int = 10485760  # 10MB
    LOG_BACKUP_COUNT: int = 5
    
    # Security
    RATE_LIMIT_REQUESTS: int = 20  # requests
    RATE_LIMIT_WINDOW: int = 60    # seconds
    
    # Input validation
    MAX_INPUT_LENGTH: int = 500
    MIN_INPUT_LENGTH: int = 2
    
    # Performance
    ENABLE_RESPONSE_CACHE: bool = True
    ENABLE_ANALYTICS: bool = True
    
    # Features
    ENABLE_VOICE: bool = True
    ENABLE_TRANSLATION: bool = True
    ENABLE_PREFERENCES: bool = True
    ENABLE_PROACTIVE_ALERTS: bool = True
    
    # Paths
    KNOWLEDGE_BASE_PATH: str = "knowledge_base.json"
    DATA_DIR: str = "data"
    LOGS_DIR: str = "logs"
    ANALYTICS_DIR: str = "analytics"
    USER_PREFS_DIR: str = "user_preferences"


@dataclass
class DevelopmentConfig(AppConfig):
    """Configuration for development environment"""
    LOG_LEVEL: str = "DEBUG"
    ENABLE_ANALYTICS: bool = False  # Don't track in dev
    RATE_LIMIT_REQUESTS: int = 100  # More lenient in dev


@dataclass
class ProductionConfig(AppConfig):
    """Configuration for production environment"""
    LOG_LEVEL: str = "WARNING"  # Less verbose in production
    LOG_TO_FILE: bool = True
    ENABLE_ANALYTICS: bool = True
    RATE_LIMIT_REQUESTS: int = 20  # Strict in production


# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION LOADER
# ═══════════════════════════════════════════════════════════════════════════

class Config:
    """
    Main configuration class - use this to access all settings.
    
    Usage:
        from services.config import config
        
        # Access settings
        print(config.cache.NEWS)
        print(config.api.GEMINI_MODEL)
        print(config.ui.MAX_CHAT_HISTORY)
    """
    
    def __init__(self, environment: str = "production"):
        """
        Initialize configuration.
        
        Args:
            environment: "development" or "production"
        """
        self.environment = environment
        
        # Initialize sub-configs
        self.cache = CacheConfig()
        self.api = APIConfig()
        self.ui = UIConfig()
        
        # Choose app config based on environment
        if environment == "development":
            self.app = DevelopmentConfig()
        else:
            self.app = ProductionConfig()
    
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.environment == "development"
    
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.environment == "production"
    
    def validate(self) -> Tuple[bool, Optional[str]]:
        """
        Validate configuration.
        
        Returns:
            (is_valid, error_message)
        """
        # Check required API keys
        if not self.api.get_gemini_api_key():
            return False, "GEMINI_API_KEY is not configured"
        
        if not self.api.get_openweather_api_key():
            return False, "OPENWEATHER_API_KEY is not configured"
        
        # Validate cache TTLs (should be positive)
        if self.cache.WEATHER <= 0:
            return False, "Cache TTL must be positive"
        
        # Validate rate limits
        if self.app.RATE_LIMIT_REQUESTS <= 0:
            return False, "Rate limit must be positive"
        
        return True, None
    
    def get_summary(self) -> Dict:
        """Get configuration summary for debugging"""
        return {
            "environment": self.environment,
            "app_version": self.app.APP_VERSION,
            "log_level": self.app.LOG_LEVEL,
            "rate_limit": f"{self.app.RATE_LIMIT_REQUESTS} requests / {self.app.RATE_LIMIT_WINDOW}s",
            "gemini_model": self.api.GEMINI_MODEL,
            "cache_news_ttl": f"{self.cache.NEWS}s",
            "features": {
                "voice": self.app.ENABLE_VOICE,
                "translation": self.app.ENABLE_TRANSLATION,
                "analytics": self.app.ENABLE_ANALYTICS,
            },
            "api_keys_configured": {
                "gemini": bool(self.api.get_gemini_api_key()),
                "news": bool(self.api.get_news_api_key()),
                "weather": bool(self.api.get_openweather_api_key()),
                "traffic": bool(self.api.get_tomtom_api_key()),
                "fuel": bool(self.api.get_rapidapi_key()),
            }
        }


# ═══════════════════════════════════════════════════════════════════════════
# GLOBAL CONFIG INSTANCE
# ═══════════════════════════════════════════════════════════════════════════

# Determine environment from environment variable or Streamlit secrets
_environment = os.getenv("ENVIRONMENT", "production")
if hasattr(st, "secrets") and st.secrets.get("ENVIRONMENT"):
    _environment = st.secrets["ENVIRONMENT"]

# Create global config instance
config = Config(environment=_environment)


# ═══════════════════════════════════════════════════════════════════════════
# CONVENIENCE EXPORTS
# ═══════════════════════════════════════════════════════════════════════════

# Export commonly used configs for easier access
cache_config = config.cache
api_config = config.api
ui_config = config.ui
app_config = config.app


# ═══════════════════════════════════════════════════════════════════════════
# TESTING & VALIDATION
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import json
    
    print("=" * 60)
    print("CONFIGURATION SUMMARY")
    print("=" * 60)
    print(json.dumps(config.get_summary(), indent=2))
    
    print("\n" + "=" * 60)
    print("VALIDATION")
    print("=" * 60)
    is_valid, error = config.validate()
    if is_valid:
        print("✅ Configuration is valid")
    else:
        print(f"❌ Configuration error: {error}")
    
    print("\n" + "=" * 60)
    print("USAGE EXAMPLES")
    print("=" * 60)
    print(f"Cache TTL for news: {config.cache.NEWS} seconds")
    print(f"Gemini model: {config.api.GEMINI_MODEL}")
    print(f"Max chat history: {config.ui.MAX_CHAT_HISTORY}")
    print(f"App name: {config.app.APP_NAME}")
    print(f"Environment: {config.environment}")