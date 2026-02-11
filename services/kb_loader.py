"""
Knowledge Base Loader - Migrated with logging and config
Loads and provides access to Hyderabad city knowledge base
"""

from pathlib import Path
import json
from functools import lru_cache
from services.logger import get_logger
from services.config import config

# Initialize logger
logger = get_logger(__name__)


# ─── CENTRALIZED KB LOADER ──────────────────────────────────────────────────

@lru_cache(maxsize=1)
def load_knowledge_base():
    """
    Load knowledge base from standard locations.
    Uses caching to avoid repeated file reads.
    
    Returns:
        dict: The full knowledge base
        
    Raises:
        FileNotFoundError: If KB not found in any standard location
    """
    logger.debug("Attempting to load knowledge base")
    
    # Try multiple possible locations
    possible_paths = [
        Path("knowledge_base.json"),                           # Current directory
        Path(__file__).parent / "knowledge_base.json",         # Same dir as this file
        Path(__file__).parent.parent / "knowledge_base.json",  # Parent directory
        Path.cwd() / "knowledge_base.json",                    # Working directory
    ]
    
    for kb_path in possible_paths:
        if kb_path.exists():
            try:
                logger.debug(f"Found knowledge base at: {kb_path}")
                with open(kb_path, "r", encoding="utf-8") as f:
                    kb_data = json.load(f)
                logger.info(f"✅ Successfully loaded knowledge base from {kb_path.name}")
                logger.debug(f"KB contains {len(kb_data)} top-level sections")
                return kb_data
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing error in {kb_path}: {e}", exc_info=True)
                continue
            except Exception as e:
                logger.error(f"Error loading {kb_path}: {e}", exc_info=True)
                continue
    
    # If we get here, KB not found anywhere
    error_msg = "knowledge_base.json not found in any of these locations:\n" + \
                "\n".join(f"  - {p}" for p in possible_paths)
    logger.error(error_msg)
    raise FileNotFoundError(error_msg)


def get_profile():
    """
    Get the hyderabad_comprehensive_profile section.
    
    Returns:
        dict: The profile section, or empty dict if not found
    """
    try:
        kb = load_knowledge_base()
        profile = kb.get("hyderabad_comprehensive_profile", {})
        if profile:
            logger.debug(f"Retrieved profile with {len(profile)} sections")
        else:
            logger.warning("Profile section not found in knowledge base")
        return profile
    except FileNotFoundError:
        logger.error("Knowledge base not found - returning empty profile")
        return {}


def get_section(section_name: str, subsection: str = None):
    """
    Get a specific section from the knowledge base.
    
    Args:
        section_name: Top-level section (e.g., "tourism_and_landmarks")
        subsection: Optional nested section (e.g., "historical_monuments")
        
    Returns:
        dict or list: The requested section, or empty dict/list if not found
        
    Examples:
        >>> get_section("tourism_and_landmarks", "historical_monuments")
        [...list of monuments...]
        
        >>> get_section("festivals_and_culture")
        {...festivals data...}
    """
    profile = get_profile()
    
    if not profile:
        logger.warning(f"Profile empty, cannot get section: {section_name}")
        return {} if subsection else []
    
    section = profile.get(section_name, {})
    
    if not section:
        logger.warning(f"Section '{section_name}' not found in profile")
        return {} if subsection else []
    
    if subsection:
        result = section.get(subsection, [])
        if isinstance(result, list):
            logger.debug(f"Retrieved {len(result)} items from {section_name}.{subsection}")
        return result
    
    logger.debug(f"Retrieved section: {section_name}")
    return section


def get_emergency_contacts():
    """Get emergency contacts section."""
    try:
        kb = load_knowledge_base()
        contacts = kb.get("emergency contacts", {})
        if contacts:
            logger.debug(f"Retrieved {len(contacts)} emergency contacts")
        else:
            logger.warning("Using fallback emergency contacts")
            contacts = {
                "police": "100",
                "ambulance": "108",
                "fire": "101",
                "women_helpline": "181",
            }
        return contacts
    except FileNotFoundError:
        logger.warning("KB not found, using fallback emergency contacts")
        return {
            "police": "100",
            "ambulance": "108",
            "fire": "101",
            "women_helpline": "181",
        }


# ─── CONVENIENCE HELPERS FOR COMMON SECTIONS ────────────────────────────────

def get_monuments():
    """Get historical monuments list."""
    return get_section("tourism_and_landmarks", "historical_monuments")


def get_temples():
    """Get religious sites."""
    return get_section("tourism_and_landmarks", "religious_sites")


def get_palaces():
    """Get palaces list."""
    return get_section("tourism_and_landmarks", "palaces")


def get_museums():
    """Get museums list."""
    return get_section("tourism_and_landmarks", "museums_and_galleries")


def get_parks():
    """Get parks and nature spots."""
    return get_section("tourism_and_landmarks", "parks_and_nature")


def get_attractions():
    """Get modern attractions."""
    return get_section("tourism_and_landmarks", "modern_attractions")


def get_restaurants():
    """Get restaurants data."""
    return get_section("restaurants")


def get_theaters():
    """Get theaters and cinemas."""
    profile = get_profile()
    theaters = profile.get("Theaters_and_Cinemas", {})
    if theaters:
        logger.debug("Retrieved theaters data")
    return theaters


def get_shopping():
    """Get shopping hubs."""
    return get_section("tourism_and_landmarks", "shopping_hubs")


def get_itineraries():
    """Get pre-made itineraries."""
    tourism = get_section("tourism_and_landmarks")
    return tourism.get("Itinearies", {})


def get_festivals():
    """Get festivals and culture."""
    return get_section("festivals_and_culture")


def get_sports():
    """Get sports and recreation."""
    return get_section("sports_and_recreation")


def get_healthcare():
    """Get healthcare facilities."""
    return get_section("healthcare")


def get_education():
    """Get education institutions."""
    return get_section("education")


def get_history_trivia():
    """Get history and trivia."""
    return get_section("history_and_trivia")


def get_mmts_data():
    """Get MMTS train data."""
    return get_section("mmts_trains")