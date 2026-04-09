# 🏙️ MITR — Your Hyderabad City Guide

> **MITR** (meaning *friend* in Hindi/Telugu) is an AI-powered, multi-language chatbot built with Streamlit and LangGraph that serves as a personal assistant for exploring Hyderabad, India. It delivers real-time city intelligence — weather, traffic, transit, food, events, news, and much more — through a beautiful, glassmorphic web UI.

[![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-red?logo=streamlit)](https://streamlit.io/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.0.20+-green)](https://github.com/langchain-ai/langgraph)
[![Gemini](https://img.shields.io/badge/Gemini-2.5_Flash_Lite-purple?logo=google)](https://ai.google.dev/)
[![Supabase](https://img.shields.io/badge/Supabase-Auth_%26_DB-teal?logo=supabase)](https://supabase.com/)
---

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Running the App](#-running-the-app)
- [Deployment (GitHub Codespaces)](#-deployment-github-codespaces)
- [Feature Deep-Dive](#-feature-deep-dive)
- [Services Reference](#-services-reference)
- [Database Schema](#-database-schema)
- [API Integrations](#-api-integrations)
- [Contributing](#-contributing)

---

## ✨ Features

| Category | Capabilities |
|---|---|
| 🏛️ **Tourism** | Monuments, palaces, museums, parks, temples, modern attractions |
| 🍛 **Food** | AI-powered restaurant recommendations from a curated 200+ restaurant database |
| 🚇 **Transport** | Hyderabad Metro (all 3 lines), MMTS suburban rail, TSRTC bus routes with connecting routes |
| 🌦️ **Weather** | Live temperature, humidity, AQI, 3-day forecast, rain alerts |
| 🚦 **Traffic** | Real-time traffic severity with alternate route suggestions |
| 📰 **News** | AI-summarized Hyderabad headlines, category filtering (tech, weather, traffic, events) |
| 🛍️ **Shopping** | Mall crowd levels, best visit times, ongoing sales, traditional markets |
| 🎬 **Movies & Entertainment** | Theater listings, formats (IMAX/4DX/Gold Class), booking tips |
| ⛽ **Fuel Prices** | Daily petrol, diesel, and CNG prices via live RapidAPI integration |
| 👥 **Crowd Intelligence** | Best times to visit monuments, parks, malls; crowd level predictions |
| 🎉 **Festival Traffic** | Festival calendar with traffic impact, affected routes, crowd hotspots |
| 💰 **Live Deals** | Swiggy, Zomato, Amazon, Flipkart offers; bank card promotions |
| ⚡ **Utilities** | Power cut and water supply alerts by area |
| 🗓️ **Itineraries** | Pre-built day plans: heritage tour, food trail, IT hub weekend, family fun |
| 🏥 **Healthcare** | Major hospital directories |
| 🎓 **Education** | Universities and premier institutes |
| 🏛️ **Government Services** | MeeSeva, RTA, Passport Seva, Aadhaar, GHMC |
| 🌐 **Multi-language** | English, Telugu (తెలుగు), Hindi (हिंदी), Urdu (اردو) |
| 🎤 **Voice** | Browser-native voice input (Gemini STT) + text-to-speech output (gTTS) |
| 🔐 **Auth & Personalization** | Supabase auth, preference learning, personalized suggestions |
| 📊 **Analytics** | Per-user chat history, usage patterns, intent breakdown charts |
| ⚡ **Smart Caching** | Intent-aware TTL caching (10 mins for weather → 24 hrs for monuments) |

---

## 🏗️ Architecture

```
User (Browser)
      │
      ▼
┌─────────────────────────────────────────────┐
│              Streamlit Frontend              │
│  webapp.py  ·  pages/login.py  ·  analytics │
└───────────────────┬─────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────┐
│           LangGraph Intent Router            │
│                                             │
│  classify_intent()  ──►  30+ intent nodes  │
│  (BotState TypedDict)                       │
└───────────────────┬─────────────────────────┘
                    │
        ┌───────────┴────────────┐
        ▼                        ▼
┌──────────────┐        ┌────────────────────┐
│  Static KB   │        │  Live API Services │
│ (JSON + CSV) │        │                    │
│              │        │  OpenWeatherMap    │
│ knowledge_   │        │  TomTom Traffic    │
│ base.json    │        │  NewsAPI           │
│ rtc_routes   │        │  RapidAPI (fuel,   │
│ .csv         │        │  deals)            │
└──────────────┘        │  Gemini AI         │
                        └────────────────────┘
                                 │
                    ┌────────────┴──────────┐
                    ▼                       ▼
           ┌──────────────┐       ┌────────────────┐
           │   Supabase   │       │  Smart Cache   │
           │  Auth + DB   │       │  (Session      │
           │  (users,     │       │  State, TTL    │
           │  prefs,      │       │  per intent)   │
           │  chat_history│       └────────────────┘
           └──────────────┘
```

The core routing pattern is a **LangGraph StateGraph** where every user message passes through a `classify_intent` node, which routes to one of 30+ specialized handler nodes. Each handler independently fetches data from local knowledge bases, live APIs, or the Gemini AI model.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Streamlit 1.30+, custom glassmorphic CSS |
| **AI Orchestration** | LangGraph (StateGraph) |
| **Language Model** | Google Gemini 2.5 Flash Lite (via `google-genai`) |
| **Speech-to-Text** | Gemini multimodal API |
| **Text-to-Speech** | gTTS (Google Text-to-Speech) |
| **Translation** | deep-translator (Google Translate backend) |
| **Auth & Database** | Supabase (PostgreSQL + Row Level Security) |
| **Weather** | OpenWeatherMap API (current, forecast, AQI) |
| **Traffic** | TomTom Traffic Flow API |
| **News** | NewsAPI.org |
| **Fuel Prices** | RapidAPI (`daily-fuel-prices-india`) |
| **Deals** | RapidAPI (Swiggy, Zomato, Amazon scraper endpoints) |
| **Data** | JSON knowledge base (200+ restaurants, landmarks, transport) + CSV (bus routes) |
| **Logging** | Python `logging` with `RotatingFileHandler` |
| **Containerization** | Dev Containers (`.devcontainer/devcontainer.json`) |

---

## 📁 Project Structure

```
mitr-hyderabad/
│
├── webapp.py                    # Main Streamlit app, LangGraph workflow
├── knowledge_base.json          # Master city knowledge base
├── requirements.txt
│
├── pages/
│   ├── login.py                 # Auth page (sign in / sign up)
│   └── analytics.py             # User analytics dashboard
│
├── data/
│   └── rtc_routes.csv           # 130+ TSRTC bus routes
│
├── services/
│   ├── config.py                # Centralized config (APIConfig, CacheConfig, UIConfig)
│   ├── logger.py                # Colored console + rotating file logger
│   ├── auth.py                  # Supabase auth (sign_in, sign_up, token refresh)
│   ├── user_store.py            # CRUD for preferences & chat history (Supabase)
│   │
│   ├── # ── AI & LLM ──────────────────────────────────────────────
│   ├── ai_food.py               # Gemini-powered food recommendations
│   ├── ai_news.py               # Gemini-powered news summarization
│   ├── ai_preferences.py        # Preference learning & personalization engine
│   │
│   ├── # ── Knowledge Base ────────────────────────────────────────
│   ├── kb_loader.py             # Cached JSON knowledge base loader
│   ├── food_loader.py           # Restaurant data flattener
│   ├── locations.py             # Hyderabad area → (lat, lon) mapping
│   │
│   ├── # ── Transport ─────────────────────────────────────────────
│   ├── metro_rail.py            # Metro route finder (Red/Blue/Green lines)
│   ├── mmts_trains.py           # MMTS suburban rail routes & timings
│   ├── rtc_bus.py               # TSRTC bus routes, connecting hubs, CSV parser
│   │
│   ├── # ── Live Data ─────────────────────────────────────────────
│   ├── weatherapi.py            # OpenWeatherMap (current, forecast, AQI)
│   ├── traffic.py               # TomTom traffic flow + alternate routes
│   ├── fuel_prices.py           # RapidAPI fuel price fetcher with fallback
│   ├── news.py                  # NewsAPI fetcher with category filtering
│   ├── live_deals.py            # Food delivery & e-commerce deals aggregator
│   ├── utilities.py             # Power cut & water supply alerts
│   ├── festivals_traffic_alerts.py  # Festival calendar + TomTom festival traffic
│   │
│   ├── # ── City Info ──────────────────────────────────────────────
│   ├── shopping.py              # Mall & market info
│   ├── movies.py                # Theater listings & booking tips
│   ├── itineary.py              # Pre-built itinerary generator
│   ├── crowd.py                 # Crowd level data & predictions
│   │
│   ├── # ── UX & Infrastructure ────────────────────────────────────
│   ├── translator.py            # deep-translator wrapper with term preservation
│   ├── voice_service.py         # Browser mic input + gTTS output
│   ├── theme.py                 # Dynamic day/night glassmorphic CSS
│   ├── cache_manager.py         # Intent-aware smart caching (TTL per intent type)
│   ├── conversation_memory.py   # Multi-turn context & pronoun resolution
│   ├── proactive_assistant.py   # Time/weather/location-based smart suggestions
│   ├── input_validator.py       # XSS/SQLi sanitization, length checks
│   ├── rate_limiter.py          # Sliding-window rate limiter
│   └── security.py              # Combined validation + rate limiting facade
│
├── user_preferences/            # Local fallback preference JSON files
│   └── *.json
│
└── .devcontainer/
    └── devcontainer.json        # GitHub Codespaces configuration
```

---

## ✅ Prerequisites

- Python **3.11+**
- A [Supabase](https://supabase.com/) project (free tier is sufficient)
- API keys for (at minimum): **Gemini** and **OpenWeatherMap**
- Optional but recommended: TomTom, NewsAPI, RapidAPI keys

---

## 🚀 Installation

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/mitr-hyderabad.git
cd mitr-hyderabad
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv

# Linux / macOS
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## ⚙️ Configuration

### Streamlit Secrets

Create the file `.streamlit/secrets.toml` (this file is git-ignored):

```toml
# ── Required ─────────────────────────────────────────────────────────────────
GEMINI_API_KEY       = "AIza..."
OPENWEATHER_API_KEY  = "abc123..."

# Supabase
SUPABASE_URL         = "https://<project>.supabase.co"
SUPABASE_KEY         = "eyJ..."        # anon/public key

# ── Optional (enables extra features) ─────────────────────────────────────────
GEMINI_API_KEY_2     = "AIza..."       # Key rotation for high traffic
GEMINI_API_KEY_3     = "AIza..."
NEWS_API_KEY         = "abc123..."
TOMTOM_API_KEY       = "abc123..."
RAPIDAPI_KEY         = "abc123..."

# ── App behaviour ──────────────────────────────────────────────────────────────
ENVIRONMENT          = "production"    # "development" or "production"
ENABLE_DATABASE      = true           # set to false for fully offline mode
```

### Environment Variables (alternative)

All secrets can also be set as environment variables with the same names.

### Supabase Database Setup

Run the following SQL in your Supabase SQL editor to create the required tables:

```sql
-- User preferences (JSONB storage for flexibility)
create table user_preferences (
  user_id    uuid primary key references auth.users(id) on delete cascade,
  preferences jsonb default '{}'::jsonb,
  updated_at  timestamptz default now()
);

-- Chat history
create table chat_history (
  id           bigserial primary key,
  user_id      uuid references auth.users(id) on delete cascade,
  user_message text,
  bot_response text,
  intent       text,
  created_at   timestamptz default now()
);

-- Enable Row Level Security
alter table user_preferences enable row level security;
alter table chat_history      enable row level security;

-- RLS policies: users can only access their own data
create policy "own prefs"    on user_preferences for all using (auth.uid() = user_id);
create policy "own history"  on chat_history     for all using (auth.uid() = user_id);
```

---

## ▶️ Running the App

```bash
streamlit run webapp.py --server.enableCORS false --server.enableXsrfProtection false
```

Then open [http://localhost:8501](http://localhost:8501) in your browser.

### Development mode (verbose logging)

Set `ENVIRONMENT = "development"` in your secrets to enable DEBUG-level logs and disable analytics tracking.

---

## 🌐 Deployment (GitHub Codespaces)

This project ships with a fully configured Dev Container. To launch:

1. Push the repo to GitHub.
2. Click **Code → Open with Codespaces → New codespace**.
3. Codespaces will automatically install all packages and start the Streamlit server.
4. Add your secrets via **Codespaces Secrets** in your repository settings (Settings → Secrets → Codespaces).

The app will be available on the auto-forwarded port **8501**.

---

## 🔍 Feature Deep-Dive

### Intent Routing (LangGraph)

Every message flows through a single `classify_intent` node that uses keyword matching to route to one of **30+ specialized handlers**. This is deliberately keyword-based (not LLM-based) for speed and cost efficiency, since intent classification happens on every message.

```python
# Simplified flow
BotState = { user_input, context, intent, response }

graph: classify_intent → [greeting | food | transport | weather | ... | general] → END
```

### Smart Caching

The `cache_manager.py` uses **intent-aware TTL** so real-time data isn't served stale:

| Intent | Cache TTL |
|---|---|
| `monuments`, `history` | 24 hours |
| `food`, `shopping` | 6 hours |
| `news`, `events` | 1 hour |
| `weather`, `traffic` | 10 minutes |
| `utilities`, `deals` | 0 (never cached) |

Smart invalidation also fires when the user's selected area changes or when dates roll over for event-type content.

### Preference Learning

`ai_preferences.py` passively learns from every query without asking the user anything:

- **Interests** scored by query frequency (`food: 5`, `transport: 2`, …)
- **Location inference** from area mentions in queries
- **Home/work area** inferred from time of day + location
- **Cuisine, transport mode, tourism type** extracted from natural language
- **Personalization score** (0–1) gates progressively richer suggestions

### Conversation Memory

`conversation_memory.py` stores the last 5 turns and resolves pronouns:

```
User: "Tell me about Charminar"
Bot:  "Charminar is a 16th-century mosque and monument..."
User: "How do I get there?"
      ↓ resolved to →
      "How do I get to Charminar?"
```

### Multi-language Support

Translation uses `deep-translator` with a sophisticated preservation system — over 300 Hyderabad-specific terms (place names, food names, brands, transport names) are extracted as placeholders *before* translation and restored *after*, preventing names like "Charminar" or "Biryani" from being mangled.

---

## 📚 Services Reference

| Service | File | Key Functions |
|---|---|---|
| Gemini AI | `ai_food.py`, `ai_news.py` | `generate_food_recommendation()`, `summarize_news()` |
| Metro Rail | `metro_rail.py` | `find_metro_route()`, `format_metro_route()` |
| MMTS Trains | `mmts_trains.py` | `find_mmts_route()`, `format_mmts_route()` |
| RTC Bus | `rtc_bus.py` | `get_bus_routes()`, `get_connecting_routes()` |
| Weather | `weatherapi.py` | `get_weather_by_coords()`, `get_forecast_by_coords()`, `get_aqi_by_coords()` |
| Traffic | `traffic.py` | `get_traffic_flow()`, `format_traffic()` |
| Fuel | `fuel_prices.py` | `get_fuel_prices_hyderabad()`, `format_fuel_prices()` |
| News | `news.py` + `ai_news.py` | `get_hyderabad_news()`, `summarize_news()` |
| Deals | `live_deals.py` | `handle_deals_query()`, `get_all_food_deals()` |
| Utilities | `utilities.py` | `handle_utilities_query()`, `find_alerts_for_area()` |
| Festivals | `festivals_traffic_alerts.py` | `handle_festival_traffic_query()`, `get_active_festivals()` |
| Crowd | `crowd.py` | `get_crowd_info()`, `find_crowd_info()` |
| Shopping | `shopping.py` | `get_mall_info()` |
| Movies | `movies.py` | `get_movie_info()` |
| Itinerary | `itineary.py` | `generate_itinerary()` |
| Voice | `voice_service.py` | `transcribe()`, `synthesize()`, `render_audio_input()` |
| Translation | `translator.py` | `translate_response()` |
| Cache | `cache_manager.py` | `cached_response()`, `cache_response()`, `SmartTTL` |
| Auth | `auth.py` | `sign_in()`, `sign_up()`, `sign_out()`, `get_supabase()` |
| User Store | `user_store.py` | `save_chat_message()`, `load_preferences()`, `save_preferences()` |
| Preferences | `ai_preferences.py` | `learn_from_query()`, `get_personalized_suggestions()` |

---

## 🗄️ Database Schema

```
auth.users (managed by Supabase)
    │
    ├── user_preferences
    │     user_id (PK, FK)
    │     preferences  JSONB  ← entire preference object stored here
    │     updated_at
    │
    └── chat_history
          id           BIGSERIAL PK
          user_id      FK
          user_message TEXT
          bot_response TEXT
          intent       TEXT
          created_at   TIMESTAMPTZ
```

---

## 🔌 API Integrations

| API | Used For | Free Tier |
|---|---|---|
| [Google Gemini](https://ai.google.dev/) | Food recommendations, news summarization, voice STT | ✅ 15 RPM free |
| [OpenWeatherMap](https://openweathermap.org/api) | Weather, forecast, AQI | ✅ 1,000 calls/day free |
| [TomTom Traffic](https://developer.tomtom.com/) | Real-time traffic flow | ✅ 2,500 calls/day free |
| [NewsAPI](https://newsapi.org/) | Hyderabad news headlines | ✅ 100 requests/day free |
| [RapidAPI](https://rapidapi.com/) | Fuel prices, food deals | ✅ varies by API |
| [Supabase](https://supabase.com/) | Auth, PostgreSQL database | ✅ 500 MB / 50k MAU free |

> **Note:** The app degrades gracefully when API keys are missing — weather, traffic, fuel, news, and deals all have hardcoded fallback data so the core chatbot always works.

---

## 🗺️ Knowledge Base

`knowledge_base.json` is the heart of the app — a hand-curated, structured dataset covering:

- **200+ restaurants** across 4 categories (Heritage/Regional, Global/Modern, Casual/Nightlife, Street/Bakeries)
- **Historical monuments, palaces, museums, parks, attractions** with crowd level data
- **Religious sites** (Hindu temples, mosques, churches)
- **Complete Hyderabad Metro** station lists for all 3 lines with interchange data
- **TSRTC bus routes** (130+ routes in `data/rtc_routes.csv`)
- **MMTS suburban rail** routes and interchange points
- **Airport** domestic and international route details
- **Itinerary templates** (one-day tour, food trail, IT hub weekend, family day)
- **Shopping malls** with crowd patterns, store lists, parking info
- **Theaters & cinemas** (PVR, INOX, AMB, Prasads)

---

## 🤝 Contributing

Contributions are welcome! Here's how to get started:

### Reporting Issues

Please include:
- Your Python version and OS
- The exact query that caused the issue
- The full error traceback from the logs (`logs/` directory)

### Adding a New Intent

1. Add keyword detection in `classify_intent()` in `webapp.py`
2. Write a handler function `handle_<intent>(state: BotState) -> BotState`
3. Register the node and edge in `create_workflow()`
4. Add a quick-link button in the sidebar (optional)

### Updating the Knowledge Base

`knowledge_base.json` follows a well-defined schema. To add restaurants, edit the `restaurants` section and follow the existing structure with `name`, `main_branch`, `price_range`, `opening_hours`, `best_selling_dishes`, and `rating` fields.

### Code Style

- Follow the existing service module pattern: one file per domain, exported functions only, no global mutable state outside Streamlit session_state
- Use `get_logger(__name__)` or `setup_logger(name, file)` from `services/logger.py`
- Cache API calls with `@st.cache_data(ttl=config.cache.<CATEGORY>)`



## 🙏 Acknowledgements

- [Streamlit](https://streamlit.io/) for the rapid UI framework
- [LangGraph](https://github.com/langchain-ai/langgraph) for stateful AI workflows
- [Google Gemini](https://ai.google.dev/) for AI-powered responses
- [Supabase](https://supabase.com/) for auth and database infrastructure
- The city of Hyderabad, for being endlessly fascinating 🏙️

---

<div align="center">Made with ❤️ for Hyderabad</div>
