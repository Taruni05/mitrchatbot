"""
Translation Service v2.0 for Mitr - Hyderabad City Guide
Replaces unmaintained googletrans with deep_translator.
Preserves place names, food, formatting, emojis, numbers, and URLs.
"""

import re
import streamlit as st
from typing import Dict, Tuple

from services.logger import setup_logger
from services.config import config

logger = setup_logger("translator_v2", "translator.log")


# ══════════════════════════════════════════════════════════════════════════════
# TERMS TO NEVER TRANSLATE
# ══════════════════════════════════════════════════════════════════════════════

PRESERVE_PLACES = {
    # Landmarks
    "Charminar", "Golconda Fort", "Golconda", "Hussain Sagar", "Tank Bund",
    "Qutb Shahi Tombs", "Ramoji Film City", "Birla Mandir", "Salar Jung Museum",
    "Nizam Museum", "Chowmahalla Palace", "Falaknuma Palace", "Purani Haveli",
    "Mecca Masjid", "Makkah Masjid", "Chilkur Balaji", "KBR National Park",
    "Nehru Zoological Park", "Lumbini Park", "Shilparamam", "Snow World",
    # Areas
    "Gachibowli", "HITEC City", "Madhapur", "Kondapur", "Jubilee Hills",
    "Banjara Hills", "Secunderabad", "Ameerpet", "Kukatpally", "Dilsukhnagar",
    "LB Nagar", "Begumpet", "Somajiguda", "Mehdipatnam", "Tolichowki",
    "Miyapur", "Kompally", "Bachupally", "SR Nagar", "Yousufguda",
    "Manikonda", "Narsingi", "Financial District", "Nanakramguda", "Raidurg",
    "Kokapet", "Tellapur", "Patancheru", "BHEL", "ECIL", "Malkajgiri",
    "Tarnaka", "Habsiguda", "Nagole", "Vanasthalipuram", "Hayathnagar",
    "Shamshabad", "Laad Bazaar", "Begum Bazaar", "Abids", "Koti",
    "Nampally", "Khairatabad", "Lakdikapul", "Malakpet", "Saidabad",
    "Uppal", "Necklace Road", "Old City",
    # Transport
    "MGBS", "JBS", "Rajiv Gandhi International Airport", "RGIA",
}

PRESERVE_FOOD = {
    "Biryani", "Haleem", "Irani Chai", "Osmania Biscuit", "Lukhmi",
    "Paya", "Nihari", "Keema", "Korma", "Kebab", "Shawarma",
    "Baghara Baingan", "Mirchi Ka Salan", "Double Ka Meetha",
    "Qubani Ka Meetha", "Gil-e-Firdaus", "Sheer Khurma",
    # Restaurant brands
    "Paradise", "Bawarchi", "Shah Ghouse", "Cafe Bahar", "Alpha Hotel",
    "Shadab", "Pista House", "Karachi Bakery", "Nimrah Cafe",
    "Chutneys", "Rayalaseema Ruchulu", "Ulavacharu",
}

PRESERVE_BRANDS = {
    "Inorbit", "Inorbit Mall", "GVK One", "Forum Sujana Mall",
    "AMB Cinemas", "Prasads IMAX", "IKEA",
    "IIT Hyderabad", "IIIT Hyderabad", "ISB", "Osmania University",
    "JNTU", "University of Hyderabad",
    "Apollo", "Yashoda", "CARE Hospitals", "Continental Hospitals",
    "Gandhi Hospital",
}

PRESERVE_SERVICES = {
    "TSRTC", "RTC", "MMTS", "Metro Rail", "HMRL",
    "Ola", "Uber", "Rapido", "Swiggy", "Zomato",
    "BookMyShow", "Paytm", "Google Maps", "WhatsApp",
    "WiFi", "AC", "IMAX", "4DX", "QR Code", "ATM", "GPS", "AQI",
}

# Merge all into one set
ALL_PRESERVE = (
    PRESERVE_PLACES | PRESERVE_FOOD | PRESERVE_BRANDS | PRESERVE_SERVICES
)


# ══════════════════════════════════════════════════════════════════════════════
# TRANSLATION CLIENT — deep_translator only, no API key needed
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_resource
def get_translator_fn():
    """
    Returns a translate(text, target_lang) function using deep_translator.
    Cached so the import only happens once.
    """
    try:
        from deep_translator import GoogleTranslator

        def _translate(text: str, target_lang: str) -> str:
            return GoogleTranslator(source="auto", target=target_lang).translate(text)

        logger.info("✅ deep_translator loaded successfully")
        return _translate

    except ImportError:
        logger.error("deep_translator not installed — run: pip install deep-translator")
        return None

    except Exception as e:
        logger.error(f"Failed to load translator: {e}")
        return None


# ══════════════════════════════════════════════════════════════════════════════
# PRESERVATION SYSTEM
# ══════════════════════════════════════════════════════════════════════════════

def _extract_preservables(text: str) -> Tuple[str, Dict[str, str]]:
    """
    Replace everything that must NOT be translated with placeholders.
    Returns (modified_text, {placeholder: original_value}).
    """
    mapping: Dict[str, str] = {}
    out = text
    counter = [0]  # list so nested fn can mutate it

    def _slot(original: str) -> str:
        """Register a value and return its placeholder."""
        key = f"XPXX{counter[0]}XPXX"
        mapping[key] = original
        counter[0] += 1
        return key

    # ── 1. Markdown links [label](url) ──────────────────────────────────────
    out = re.sub(
        r'\[([^\]]+)\]\(([^\)]+)\)',
        lambda m: _slot(m.group(0)),
        out
    )

    # ── 2. Plain URLs ────────────────────────────────────────────────────────
    out = re.sub(
        r'https?://\S+',
        lambda m: _slot(m.group(0)),
        out
    )

    # ── 3. Currency amounts  ₹500  /  ₹1,200.50 ─────────────────────────────
    out = re.sub(
        r'₹\s*[\d,]+(?:\.\d+)?',
        lambda m: _slot(m.group(0)),
        out
    )

    # ── 4. Times  8:30 AM / 19:00 ────────────────────────────────────────────
    out = re.sub(
        r'\b\d{1,2}:\d{2}(?:\s*[APap][Mm])?\b',
        lambda m: _slot(m.group(0)),
        out
    )

    # ── 5. Percentages  75% ─────────────────────────────────────────────────
    out = re.sub(
        r'\b\d+\s*%',
        lambda m: _slot(m.group(0)),
        out
    )

    # ── 6. Measurements  10 km, 500 g, 2 L ──────────────────────────────────
    out = re.sub(
        r'\b\d+(?:\.\d+)?\s*(?:km/h|km|m|kg|g|L|ml|min|mins|hr|hrs)\b',
        lambda m: _slot(m.group(0)),
        out
    )

    # ── 7. Standalone numbers ────────────────────────────────────────────────
    out = re.sub(
        r'\b\d+\b',
        lambda m: _slot(m.group(0)),
        out
    )

    # ── 8. Emojis ────────────────────────────────────────────────────────────
    out = re.sub(
        r'[\U0001F300-\U0001FAFF\u2600-\u27BF]',
        lambda m: _slot(m.group(0)),
        out
    )

    # ── 9. Known Hyderabad / brand terms (longest first, case-insensitive) ───
    sorted_terms = sorted(ALL_PRESERVE, key=len, reverse=True)
    for term in sorted_terms:
        pattern = r'(?<!\w)' + re.escape(term) + r'(?!\w)'
        # Replace ONE occurrence at a time so each gets a unique placeholder
        while True:
            m = re.search(pattern, out, re.IGNORECASE)
            if not m:
                break
            out = out[:m.start()] + _slot(m.group(0)) + out[m.end():]

    logger.debug(f"Preserved {len(mapping)} items")
    return out, mapping


def _restore_preservables(text: str, mapping: Dict[str, str]) -> str:
    """Restore all placeholders to their original values."""
    out = text
    for placeholder, original in mapping.items():
        out = out.replace(placeholder, original)
    return out


# ══════════════════════════════════════════════════════════════════════════════
# CORE TRANSLATION LOGIC
# ══════════════════════════════════════════════════════════════════════════════

def _translate_chunk(text: str, target_lang: str, translate_fn) -> str:
    """Translate one chunk with error recovery."""
    if not text or not text.strip():
        return text
    try:
        result = translate_fn(text, target_lang)
        return result if result else text
    except Exception as e:
        logger.warning(f"Chunk translation failed ({target_lang}): {e}")
        return text


def translate_response(response: str, target_lang: str) -> str:
    """
    Main translation function.
    Translates bot responses to Telugu / Hindi / Urdu while preserving
    all place names, food names, numbers, emojis, URLs, and formatting.

    Args:
        response:    Text to translate.
        target_lang: Language code — "te", "hi", or "ur".
                     Returns the original if "en".

    Returns:
        Translated text, or original text if translation fails.
    """
    # Nothing to do for English or empty strings
    if not response or target_lang == "en":
        return response or ""

    translate_fn = get_translator_fn()
    if not translate_fn:
        logger.error("No translator available — returning original")
        return response

    logger.info(f"Translating {len(response)} chars → {target_lang}")

    try:
        # Step 1 — Lock down everything that must not be translated
        preserved_text, mapping = _extract_preservables(response)

        # Step 2 — Split into paragraphs so context is preserved per block
        paragraphs = preserved_text.split("\n\n")
        translated_paragraphs = []

        for para in paragraphs:
            if not para.strip():
                translated_paragraphs.append(para)
                continue

            # Long paragraphs: split on newlines to keep line structure
            if len(para) > 800:
                lines = para.split("\n")
                translated_lines = [
                    _translate_chunk(line, target_lang, translate_fn)
                    if line.strip() else line
                    for line in lines
                ]
                translated_paragraphs.append("\n".join(translated_lines))
            else:
                translated_paragraphs.append(
                    _translate_chunk(para, target_lang, translate_fn)
                )

        # Step 3 — Reassemble
        translated_text = "\n\n".join(translated_paragraphs)

        # Step 4 — Restore every preserved item
        final_text = _restore_preservables(translated_text, mapping)

        # Step 5 — Light cleanup
        final_text = _cleanup(final_text)

        logger.info(f"✅ Translation done: {len(final_text)} chars")
        return final_text

    except Exception as e:
        logger.error(f"Translation failed: {e}", exc_info=True)
        return response  # Always return something


def _cleanup(text: str) -> str:
    """Remove common translation artifacts."""
    # Collapse multiple spaces
    text = re.sub(r' {2,}', ' ', text)
    # Fix space before punctuation
    text = re.sub(r'\s+([.,!?;:])', r'\1', text)
    # Fix broken bold markers  ** word **  →  **word**
    text = re.sub(r'\*\*\s+', '**', text)
    text = re.sub(r'\s+\*\*', '**', text)
    return text


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS USED BY webapp.py
# ══════════════════════════════════════════════════════════════════════════════

def get_language_name(code: str) -> str:
    """Return display name for a language code."""
    return {
        "en": "English",
        "te": "తెలుగు (Telugu)",
        "hi": "हिंदी (Hindi)",
        "ur": "اردو (Urdu)",
    }.get(code, "English")


# Pre-translated UI strings — no API call needed
UI_TRANSLATIONS = {
    "en": {
        "welcome":    "Welcome to Hyderabad City Guide!",
        "ask_me":     "Ask me anything about Hyderabad…",
        "quick_links": "Quick Links",
        "logout":     "Logout",
        "account":    "Account",
    },
    "te": {
        "welcome":    "హైదరాబాద్ సిటీ గైడ్‌కు స్వాగతం!",
        "ask_me":     "హైదరాబాద్ గురించి ఏదైనా అడగండి…",
        "quick_links": "త్వరిత లింక్‌లు",
        "logout":     "లాగ్ అవుట్",
        "account":    "ఖాతా",
    },
    "hi": {
        "welcome":    "हैदराबाद सिटी गाइड में आपका स्वागत है!",
        "ask_me":     "हैदराबाद के बारे में कुछ भी पूछें…",
        "quick_links": "त्वरित लिंक",
        "logout":     "लॉग आउट",
        "account":    "खाता",
    },
    "ur": {
        "welcome":    "حیدرآباد سٹی گائیڈ میں خوش آمدید!",
        "ask_me":     "حیدرآباد کے بارے میں کچھ بھی پوچھیں…",
        "quick_links": "فوری لنکس",
        "logout":     "لاگ آؤٹ",
        "account":    "اکاؤنٹ",
    },
}


def get_ui_text(key: str, lang: str = "en") -> str:
    """Return pre-translated UI string (no API call)."""
    return UI_TRANSLATIONS.get(lang, UI_TRANSLATIONS["en"]).get(
        key, UI_TRANSLATIONS["en"].get(key, key)
    )