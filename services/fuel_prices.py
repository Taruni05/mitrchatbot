import requests
import streamlit as st
from datetime import datetime


# ─── hard-coded fallback (update manually when you deploy) ───────────────────
FALLBACK_PRICES = {
    "petrol": 102.63,
    "diesel": 88.84,
    "cng": 75.50,
    "date": "2026-01-19",
    "source": "cached",
}

# ─── RapidAPI endpoint & default headers ─────────────────────────────────────
# The host value is the slug RapidAPI assigns to this listing.  It never changes
# even if the provider renames the API on their dashboard.
_BASE_URL = "https://daily-fuel-prices-india.rapidapi.com"
_HOST      = "daily-fuel-prices-india.rapidapi.com"


def _get_key() -> str:
    """Pull the RapidAPI key from Streamlit secrets (or env as fallback)."""
    import os
    return st.secrets.get("RAPIDAPI_KEY", "") or os.getenv("RAPIDAPI_KEY", "")


def _headers() -> dict:
    """Standard three-header block every RapidAPI endpoint needs."""
    return {
        "x-rapidapi-key":  _get_key(),
        "x-rapidapi-host": _HOST,
        "Accept":          "application/json",
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

    petrol  = None
    diesel  = None
    cng     = None
    date    = data.get("applicableOn") or data.get("date") or datetime.now().strftime("%Y-%m-%d")

    # ── try nested first ──────────────────────────────────────────────────
    fuel = data.get("fuel")
    if isinstance(fuel, dict):
        petrol = _safe_float(fuel.get("petrol", {}).get("retailPrice"))
        diesel = _safe_float(fuel.get("diesel", {}).get("retailPrice"))
        cng    = _safe_float(fuel.get("cng",    {}).get("retailPrice"))

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
        "cng":    cng,          # may still be None — handled downstream
        "date":   date,
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
@st.cache_data(ttl=86400)          # cache 24 h — prices change once/day at 6 AM
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
    key = _get_key()
    if not key:
        print("[fuel_prices] RAPIDAPI_KEY not set — using fallback prices")
        return FALLBACK_PRICES

    # ── try the primary endpoint: /prices/city ───────────────────────────
    # Most apiexpress-style listings use ?city=Hyderabad or /city/Hyderabad.
    # We try the query-param style first; if 404, retry as path param.
    urls_to_try = [
        f"{_BASE_URL}/prices?city=Hyderabad&state=Telangana",   # query-param style
        f"{_BASE_URL}/prices/Hyderabad",                        # path style
        f"{_BASE_URL}/city/Hyderabad",                          # alternate path
    ]

    for url in urls_to_try:
        try:
            resp = requests.get(url, headers=_headers(), timeout=6)

            # 429 = rate-limited → don't burn remaining attempts, bail now
            if resp.status_code == 429:
                print("[fuel_prices] RapidAPI rate-limit hit (429) — using fallback")
                return FALLBACK_PRICES

            # skip non-success without crashing
            if resp.status_code != 200:
                continue

            data = resp.json()

            # some APIs wrap the payload in a list; unwrap it
            if isinstance(data, list):
                data = data[0] if data else {}

            parsed = _parse_response(data)
            if parsed:
                return {
                    "petrol": parsed["petrol"],
                    "diesel": parsed["diesel"],
                    "cng":    parsed["cng"] if parsed["cng"] else FALLBACK_PRICES["cng"],
                    "date":   parsed["date"],
                    "source": "live",
                }

        except requests.exceptions.Timeout:
            print("[fuel_prices] RapidAPI request timed out")
            continue
        except Exception as e:
            print(f"[fuel_prices] error on {url}: {e}")
            continue

    # ── all attempts failed → fallback ────────────────────────────────────
    print("[fuel_prices] all RapidAPI attempts failed — using fallback")
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
    cng    = prices_data.get("cng", 0)
    date   = prices_data.get("date", "Unknown")
    source = prices_data.get("source", "cached")

    source_text      = "🟢 Live"  if source == "live"  else "📦 Cached"
    diff             = abs(petrol - diesel)
    comparison_text  = (
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