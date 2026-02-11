"""
Enhanced Translation Service with Context Preservation
Handles Hyderabad-specific terms and maintains meaning accuracy

NOTE: This file uses googletrans which is unmaintained. Consider migrating to:
- deep_translator (recommended)
- google.cloud.translate_v2 (official, requires API key)
"""

import streamlit as st
from googletrans import Translator
import re

# Import logger and config
from services.logger import setup_logger
from services.config import config

# Set up logger
logger = setup_logger('translator', 'translator.log')


# ========================================
# HYDERABAD-SPECIFIC TERMS (Keep in English)
# ========================================
PRESERVE_TERMS = {
    # Places
    "Charminar", "Golconda Fort", "Hussain Sagar", "HITEC City", 
    "Gachibowli", "Jubilee Hills", "Banjara Hills", "Secunderabad",
    "Ameerpet", "Kukatpally", "Dilsukhnagar", "LB Nagar",
    "Begumpet", "Madhapur", "Miyapur", "Uppal",
    
    # Transportation
    "Metro", "MMTS", "RTC", "TSRTC", "Uber", "Ola",
    
    # Food items
    "Biryani", "Haleem", "Irani Chai", "Osmania Biscuit",
    "Paradise", "Bawarchi", "Shah Ghouse",
    
    # Malls & Markets
    "Inorbit", "GVK One", "IKEA", "Forum", "AMB",
    "Laad Bazaar", "Begum Bazaar",
    
    # Institutions
    "IIT", "JNTU", "Osmania University", "Apollo", "Yashoda",
    
    # Common terms
    "Google Maps", "BookMyShow", "WhatsApp",
}


# ========================================
# TECHNICAL TERMS (Keep in English)
# ========================================
TECHNICAL_TERMS = {
    "AC", "IMAX", "4DX", "WiFi", "ATM", "GPS",
    "COVID", "AQI", "PM2.5", "km/h", "°C",
}


# ========================================
# LANGUAGE-SPECIFIC IMPROVEMENTS
# ========================================
LANGUAGE_FIXES = {
    "te": {  # Telugu
        "is": "ఉంది",
        "are": "ఉన్నాయి",
        "the": "",  # Telugu doesn't always need "the"
        "a": "",
        "an": "",
    },
    "ur": {  # Urdu
        "is": "ہے",
        "are": "ہیں",
    },
    "hi": {  # Hindi
        "is": "है",
        "are": "हैं",
    }
}


@st.cache_resource
def get_translator():
    """Get cached translator instance"""
    logger.debug("Initializing translator instance")
    return Translator()


def preserve_terms(text: str) -> tuple:
    """
    Replace Hyderabad-specific terms with placeholders
    Returns: (modified_text, mapping)
    """
    mapping = {}
    modified_text = text
    
    # Combine all terms to preserve
    all_terms = PRESERVE_TERMS.union(TECHNICAL_TERMS)
    
    # Sort by length (longest first) to avoid partial matches
    sorted_terms = sorted(all_terms, key=len, reverse=True)
    
    for i, term in enumerate(sorted_terms):
        placeholder = f"__PRESERVE_{i}__"
        # Case-insensitive replacement
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        if pattern.search(modified_text):
            mapping[placeholder] = term
            modified_text = pattern.sub(placeholder, modified_text)
    
    logger.debug(f"Preserved {len(mapping)} terms")
    return modified_text, mapping


def restore_terms(text: str, mapping: dict) -> str:
    """Restore preserved terms"""
    for placeholder, original in mapping.items():
        text = text.replace(placeholder, original)
    return text


def preserve_special_elements(text: str) -> tuple:
    """
    Preserve markdown, URLs, numbers, emojis
    Returns: (modified_text, elements_dict)
    """
    elements = {}
    counter = 0
    
    # Preserve code blocks
    def replace_code_block(match):
        nonlocal counter
        key = f"__CODE_BLOCK_{counter}__"
        elements[key] = match.group(0)
        counter += 1
        return key
    
    text = re.sub(r'```[\s\S]*?```', replace_code_block, text)
    
    # Preserve inline code
    def replace_inline_code(match):
        nonlocal counter
        key = f"__INLINE_CODE_{counter}__"
        elements[key] = match.group(0)
        counter += 1
        return key
    
    text = re.sub(r'`[^`]+`', replace_inline_code, text)
    
    # Preserve URLs
    def replace_url(match):
        nonlocal counter
        key = f"__URL_{counter}__"
        elements[key] = match.group(0)
        counter += 1
        return key
    
    text = re.sub(r'https?://[^\s\)]+', replace_url, text)
    
    # Preserve markdown links
    def replace_md_link(match):
        nonlocal counter
        key = f"__MD_LINK_{counter}__"
        elements[key] = match.group(0)
        counter += 1
        return key
    
    text = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', replace_md_link, text)
    
    # Preserve currency with numbers
    def replace_currency(match):
        nonlocal counter
        key = f"__CURRENCY_{counter}__"
        elements[key] = match.group(0)
        counter += 1
        return key
    
    text = re.sub(r'₹\s*\d[\d,]*', replace_currency, text)
    
    # Preserve times (BEFORE numbers to avoid conflict)
    def replace_time(match):
        nonlocal counter
        key = f"__TIME_{counter}__"
        elements[key] = match.group(0)
        counter += 1
        return key
    
    text = re.sub(r'\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?', replace_time, text)
    
    # Preserve percentages (BEFORE numbers)
    def replace_percent(match):
        nonlocal counter
        key = f"__PERCENT_{counter}__"
        elements[key] = match.group(0)
        counter += 1
        return key
    
    text = re.sub(r'\d+%', replace_percent, text)
    
    # Preserve standalone numbers (LAST)
    def replace_number(match):
        nonlocal counter
        key = f"__NUMBER_{counter}__"
        elements[key] = match.group(0)
        counter += 1
        return key
    
    text = re.sub(r'\b\d+\b', replace_number, text)
    
    logger.debug(f"Preserved {len(elements)} special elements")
    return text, elements


def restore_special_elements(text: str, elements: dict) -> str:
    """Restore special elements"""
    # Restore ALL preserved elements from the dict
    for key, value in elements.items():
        text = text.replace(key, value)
    
    return text


def split_into_chunks(text: str, max_length: int = 500) -> list:
    """
    Split text into smaller chunks at sentence boundaries
    Helps preserve context during translation
    """
    # Split by double newlines (paragraphs)
    paragraphs = text.split('\n\n')
    
    chunks = []
    current_chunk = ""
    
    for para in paragraphs:
        # If paragraph is short, add to current chunk
        if len(current_chunk) + len(para) < max_length:
            current_chunk += para + "\n\n"
        else:
            # Save current chunk and start new one
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = para + "\n\n"
    
    # Add last chunk
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    logger.debug(f"Split text into {len(chunks)} chunks")
    return chunks


def translate_chunk(text: str, target_lang: str) -> str:
    """Translate a single chunk with error handling"""
    try:
        trans = get_translator()
        result = trans.translate(text, dest=target_lang)
        return result.text
    except Exception as e:
        logger.error(f"Chunk translation failed: {e}")
        return text  # Return original on error


def translate_text(text: str, target_lang: str = "te") -> str:
    """
    Enhanced translation with context preservation
    
    Args:
        text: Text to translate
        target_lang: Target language code (te/ur/hi)
    
    Returns:
        Translated text
    """
    if not text or target_lang == "en":
        return text
    
    logger.info(f"Translating {len(text)} chars to {target_lang}")
    
    try:
        # Step 1: Preserve Hyderabad-specific terms
        text_with_placeholders, term_mapping = preserve_terms(text)
        
        # Step 2: Preserve special elements (markdown, URLs, etc.)
        text_clean, elements = preserve_special_elements(text_with_placeholders)
        
        # Step 3: Split into chunks for better context
        chunks = split_into_chunks(text_clean, max_length=400)
        
        # Step 4: Translate each chunk
        translated_chunks = []
        for i, chunk in enumerate(chunks, 1):
            if chunk.strip():
                logger.debug(f"Translating chunk {i}/{len(chunks)}")
                translated = translate_chunk(chunk, target_lang)
                translated_chunks.append(translated)
        
        # Step 5: Join translated chunks
        translated_text = "\n\n".join(translated_chunks)
        
        # Step 6: Restore special elements
        translated_text = restore_special_elements(translated_text, elements)
        
        # Step 7: Restore Hyderabad-specific terms
        translated_text = restore_terms(translated_text, term_mapping)
        
        logger.info(f"✅ Translation complete: {len(translated_text)} chars")
        return translated_text
        
    except Exception as e:
        logger.error(f"Translation failed: {e}", exc_info=True)
        return text  # Return original text on error


def translate_response(response: str, target_lang: str) -> str:
    """
    Main translation function for bot responses
    Preserves formatting and Hyderabad-specific terms
    """
    return translate_text(response, target_lang)


# ========================================
# LANGUAGE DISPLAY NAMES
# ========================================
def get_language_name(code: str) -> str:
    """Get language display name from code"""
    names = config.ui.LANGUAGES
    return names.get(code, "English")


# ========================================
# UI TRANSLATIONS (Predefined)
# ========================================
UI_TRANSLATIONS = {
    "te": {
        "welcome": "హైదరాబాద్ సిటీ గైడ్‌కు స్వాగతం!",
        "ask_me": "నన్ను అడగండి...",
        "quick_links": "త్వరిత లింక్‌లు",
    },
    "ur": {
        "welcome": "حیدرآباد سٹی گائیڈ میں خوش آمدید!",
        "ask_me": "مجھ سے پوچھیں...",
        "quick_links": "فوری لنکس",
    },
    "hi": {
        "welcome": "हैदराबाद सिटी गाइड में आपका स्वागत है!",
        "ask_me": "मुझसे पूछें...",
        "quick_links": "त्वरित लिंक",
    },
    "en": {
        "welcome": "Welcome to Hyderabad City Guide!",
        "ask_me": "Ask me anything...",
        "quick_links": "Quick Links",
    }
}


def get_ui_text(key: str, lang: str = "en") -> str:
    """Get UI text in specific language"""
    return UI_TRANSLATIONS.get(lang, {}).get(key, UI_TRANSLATIONS["en"][key])