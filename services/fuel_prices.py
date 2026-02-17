import requests
import streamlit as st
from datetime import datetime

# Import logger and config
from services.logger import setup_logger
from services.config import config

# Set up logger
logger = setup_logger('fuel', 'fuel.log')


# ─── hard-coded fallback (update manually when you deploy) ───────────────────
FALLBACK_PRICES = {
    "petrol": 102.63,
    "diesel": 88.84,
    "cng": 75.50,
    "date": datetime.now().strftime("%Y-%m-%d"),
    "source": "cached",
}

# ─── RapidAPI endpoint & default headers ─────────────────────────────────────
# The host value is the slug RapidAPI assigns to this listing.  It never changes
# even if the provider renames the API on their dashboard.
_BASE_URL = "https://daily-fuel-prices-india.rapidapi.com"
_HOST = "daily-fuel-prices-india.rapidapi.com"


def _headers() -> dict:
    """Standard three-header block every RapidAPI endpoint needs."""
    api_key = config.api.get_rapidapi_key()
    return {
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": _HOST,
        "Accept": "application/json",
    }


# ─── response normaliser ─────────────────────────────────────────────────────
# Different RapidAPI fuel listings return slightly different JSON shapes.
# This function pulls the three numbers we need out of either shape so that
# if the user subscribes to a different listing tomorrow, the code still works.

def _parse_response(data: dict) -> dict | None:
    """
    Extract petrol / diesel / cng from the raw JSON response.

    Handles two common shapes:

      NESTED  (verified from Zyla mirror & mi8y listing):
        { "fuel": { "petrol": { "retailPrice": 102.63 }, ... } }

      FLAT    (common on apiexpress / cuvora listings):
        { "petrol_price": "102.63", "diesel_price": "88.84", ... }
        OR
        { "petrol": "102.63", "diesel": "88.84", ... }

    Returns a clean dict  { petrol, diesel, cng, date }  or None on failure.
    """
    if not data or not isinstance(data, dict):
        return None

    petrol = None
    diesel = None
    cng = None
    date = data.get("applicableOn") or data.get("date") or datetime.now().strftime("%Y-%m-%d")

    # ── try nested first ──────────────────────────────────────────────────
    fuel = data.get("fuel")
    if isinstance(fuel, dict):
        petrol = _safe_float(fuel.get("petrol", {}).get("retailPrice"))
        diesel = _safe_float(fuel.get("diesel", {}).get("retailPrice"))
        cng = _safe_float(fuel.get("cng", {}).get("retailPrice"))

    # ── fall back to flat keys ────────────────────────────────────────────
    if petrol is None:
        petrol = _safe_float(
            data.get("petrol_price")
            or data.get("petrol")
            or data.get("Petrol")
        )
    if diesel is None:
        diesel = _safe_float(
            data.get("diesel_price")
            or data.get("diesel")
            or data.get("Diesel")
        )
    if cng is None:
        cng = _safe_float(
            data.get("cng_price")
            or data.get("cng")
            or data.get("CNG")
        )

    # need at least petrol + diesel to be useful
    if petrol is None or diesel is None:
        return None

    return {
        "petrol": petrol,
        "diesel": diesel,
        "cng": cng,  # may still be None — handled downstream
        "date": date,
    }


def _safe_float(value) -> float | None:
    """Convert anything to float, or return None if it can't be done."""
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


# ─── main fetcher ────────────────────────────────────────────────────────────
@st.cache_data(ttl=config.cache.FUEL)
def get_fuel_prices_hyderabad() -> dict:
    """
    Fetch today's Hyderabad fuel prices from RapidAPI.

    Returns:
        {
            "petrol":  float,
            "diesel":  float,
            "cng":     float,
            "date":    str,        # "YYYY-MM-DD"
            "source":  "live" | "cached"
        }
    """
    api_key = config.api.get_rapidapi_key()
    
    if not api_key:
        logger.warning("RAPIDAPI_KEY not configured - using fallback prices")
        return FALLBACK_PRICES

    logger.info("Fetching live fuel prices for Hyderabad")

    # ── try the primary endpoint: /prices/city ───────────────────────────
    # Most apiexpress-style listings use ?city=Hyderabad or /city/Hyderabad.
    # We try the query-param style first; if 404, retry as path param.
    urls_to_try = [
        f"{_BASE_URL}/prices?city=Hyderabad&state=Telangana",   # query-param style
        f"{_BASE_URL}/prices/Hyderabad",                        # path style
        f"{_BASE_URL}/city/Hyderabad",                          # alternate path
    ]

    for i, url in enumerate(urls_to_try, 1):
        try:
            logger.debug(f"Trying URL {i}/{len(urls_to_try)}: {url}")
            
            resp = requests.get(url, headers=_headers(), timeout=config.api.FUEL_TIMEOUT)

            # 429 = rate-limited → don't burn remaining attempts, bail now
            if resp.status_code == 429:
                logger.warning("RapidAPI rate-limit hit (429) - using fallback")
                return FALLBACK_PRICES

            # skip non-success without crashing
            if resp.status_code != 200:
                logger.debug(f"URL {i} returned status {resp.status_code}")
                continue

            data = resp.json()

            # some APIs wrap the payload in a list; unwrap it
            if isinstance(data, list):
                data = data[0] if data else {}

            parsed = _parse_response(data)
            if parsed:
                logger.info(
                    f"✅ Fuel prices fetched: Petrol ₹{parsed['petrol']:.2f}, "
                    f"Diesel ₹{parsed['diesel']:.2f}, Date: {parsed['date']}"
                )
                return {
                    "petrol": parsed["petrol"],
                    "diesel": parsed["diesel"],
                    "cng": parsed["cng"] if parsed["cng"] else FALLBACK_PRICES["cng"],
                    "date": parsed["date"],
                    "source": "live",
                }

        except requests.exceptions.Timeout:
            logger.warning(f"Timeout on URL {i}")
            continue
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error on URL {i}: {e}")
            continue
        except Exception as e:
            logger.error(f"Unexpected error on URL {i}: {e}", exc_info=True)
            continue

    # ── all attempts failed → fallback ────────────────────────────────────
    logger.warning("All RapidAPI attempts failed - using fallback prices")
    return FALLBACK_PRICES


# ─── formatter (unchanged signature — webapp.py calls this directly) ─────────
def format_fuel_prices(prices_data: dict) -> str:
    """
    Format fuel prices into a readable Streamlit markdown string.
    """
    if not prices_data:
        return "⛽ Fuel price information is currently unavailable."

    petrol = prices_data.get("petrol", 0)
    diesel = prices_data.get("diesel", 0)
    cng = prices_data.get("cng", 0)
    date = prices_data.get("date", "Unknown")
    source = prices_data.get("source", "cached")

    source_text = "🟢 Live" if source == "live" else "📦 Cached"
    diff = abs(petrol - diesel)
    comparison_text = (
        "📈 Petrol is higher than diesel"
        if petrol > diesel
        else "📉 Diesel is higher than petrol"
    )

    return (
        f"⛽ **FUEL PRICES IN HYDERABAD**  \n"
        f"({source_text} | Updated: {date})\n\n"
        f"🔴 **Petrol:** ₹{petrol:.2f}/L  \n"
        f"🟢 **Diesel:** ₹{diesel:.2f}/L  \n"
        f"🔵 **CNG:**    ₹{cng:.2f}/kg\n\n"
        f"📊 **Price Comparison:**  \n"
        f"{comparison_text}  \n"
        f"Difference: ₹{diff:.2f}/L\n\n"
        f"💡 **Tip:** Prices are revised daily at 6:00 AM by oil companies."
    )