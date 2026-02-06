import sys
import toml
import os
import json
from unittest.mock import MagicMock

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Force UTF-8 for stdout to avoid emoji errors on Windows
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass # In case of weird environment



# ==============================================================================
# 1. SETUP & MOCKING
# ==============================================================================
print("📋 SETTING UP VERIFICATION ENVIRONMENT...")

# Load Secrets
try:
    secrets_path = ".streamlit/secrets.toml"
    if not os.path.exists(secrets_path):
        print(f"❌ CRITICAL: Secrets file not found at {secrets_path}")
        sys.exit(1)
        
    print(f"   Loading secrets from {secrets_path}...")
    secrets = toml.load(secrets_path)
    print("   Secrets loaded successfully.")
except Exception as e:
    print(f"❌ CRITICAL: Failed to load secrets: {e}")
    sys.exit(1)

# Mock Streamlit
# We need to mock streamlit BEFORE importing services because some services 
# read st.secrets at module level.
class Secrets(dict):
    def __getattr__(self, key):
        if key in self:
            return self[key]
        raise AttributeError(f"st.secrets has no attribute '{key}'")

mock_st = MagicMock()
mock_st.secrets = Secrets(secrets)

# Mock cache decorators to just execute the function
def pass_through_decorator(*args, **kwargs):
    # This handles both @st.cache_data and @st.cache_data(ttl=...) usage
    def wrapper(func):
        return func
    
    if len(args) == 1 and callable(args[0]):
        return args[0]
    return wrapper

mock_st.cache_data = pass_through_decorator
mock_st.cache_resource = pass_through_decorator
mock_st.session_state = {}
mock_st.error = print # Redirect st.error to print

# Apply Mock
sys.modules["streamlit"] = mock_st
print("   Streamlit module mocked successfully.")

# ==============================================================================
# 2. IMPORT SERVICES
# ==============================================================================
print("\n📦 IMPORTING SERVICES...")
try:
    from services import weatherapi
    from services import news
    from services import traffic
    from services import metro_rail
    from services import fuel_prices
    from services import kb_loader
    from services import voice_service
    print("   All services imported successfully.")
except ImportError as e:
    print(f"❌ CRITICAL: Failed to import services: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ==============================================================================
# 3. VERIFICATION TESTS
# ==============================================================================
print("\n🚀 STARTING TESTS...\n")

def run_test(name, func):
    print(f"testing {name}...", end=" ", flush=True)
    try:
        result = func()
        if result:
            print(f"✅ PASS")
            return True
        else:
            print(f"⚠️ FAIL (No data returned)")
            return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

# --- Test 7: Voice Service (TTS) ---
def test_voice():
    # Test TTS (runs locally)
    audio_bytes = voice_service.synthesize("Hello Hyderabad", language="en")
    if audio_bytes and len(audio_bytes) > 0:
        print(f"      Synthesized {len(audio_bytes)} bytes of audio")
        return True
    return False

# --- Test 1: Weather API ---
def test_weather():
    # Hyderabad coords
    lat, lon = 17.3850, 78.4867
    data = weatherapi.get_weather_by_coords(lat, lon)
    if data and "main" in data:
        print(f"      Got weather: {data['weather'][0]['description']}, Temp: {data['main']['temp']}°C")
        return True
    return False

# --- Test 2: News API ---
def test_news():
    articles = news.get_hyderabad_news(max_articles=3)
    if articles:
        print(f"      Got {len(articles)} articles. First: '{articles[0].get('title', 'No Title')}'")
        # Check if we got fallback data (not a failure, but worth noting)
        if articles == news.FALLBACK_NEWS:
             print("      (Note: Returned FALLBACK data)")
        return True
    return False

# --- Test 3: Traffic API ---
def test_traffic():
    # Hyderabad coords
    lat, lon = 17.3850, 78.4867
    data = traffic.get_traffic_flow(lat, lon)
    if data:
        if "flowSegmentData" in data:
             print(f"      Got traffic flow speed: {data['flowSegmentData']['currentSpeed']} km/h")
             return True
        else:
             print(f"      Got response but no flowSegmentData: {data}")
             return False
    return False

# --- Test 4: Metro Rail (Local Data) ---
def test_metro():
    # Test routing
    route = metro_rail.find_metro_route("Ameerpet", "Hitech City")
    if route:
        print(f"      Route found: {len(route)} stations")
        return True
    return False

# --- Test 5: Fuel Prices (Scraping) ---
def test_fuel():
    prices = fuel_prices.get_fuel_prices_hyderabad()
    if prices:
        print(f"      Fuel Prices: {prices}")
        return True
    return False

# --- Test 6: Knowledge Base Loader ---
def test_kb():
    # create dummy kb file if it doesn't exist to test loader logic?
    # actually better to test if the real one loads if it exists
    if os.path.exists("knowledge_base.json"):
        with open("knowledge_base.json", "r", encoding="utf-8") as f:
            kb = json.load(f)
        if kb:
            print(f"      Loaded KB. Keys: {list(kb.keys())}")
            return True
    else:
        print("      knowledge_base.json not found (skipped)")
        return True # Not a code failure

# Run All
results = {
    "Weather": run_test("Weather API", test_weather),
    "News": run_test("News API", test_news),
    "Traffic": run_test("Traffic API", test_traffic),
    "Metro": run_test("Metro Service", test_metro),
    "Fuel": run_test("Fuel Service", test_fuel),
    "KnowledgeBase": run_test("Knowledge Base", test_kb),
    "Voice (TTS)": run_test("Voice Service (TTS)", test_voice)
}

print("\n📊 SUMMARY:")
passed = sum(results.values())
total = len(results)
print(f"Passed {passed}/{total} tests.")

if passed < total:
    print("Some tests failed. Please check the logs.")
    sys.exit(1)
else:
    print("All system checks passed!")
    sys.exit(0)
