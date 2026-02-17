import streamlit as st
import base64
from datetime import datetime


def load_base64(path):
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except:
        return None


def apply_theme(mode="Auto"):
    DEFAULT_BG = "linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
    bg_image = None

    if mode == "Auto":
        hour = datetime.now().hour
        target = "hyderabad_day.jpg" if 6 <= hour < 18 else "hyderabad_night.jpg"
        bg_image = load_base64(target)
    elif mode == "Day":
        bg_image = load_base64("hyderabad_day.jpg")
    else:
        bg_image = load_base64("hyderabad_night.jpg")

    if bg_image:
        background_style = f"""
            linear-gradient(rgba(0,0,0,0.35), rgba(0,0,0,0.35)),
            url("data:image/jpeg;base64,{bg_image}")
        """
    else:
        background_style = DEFAULT_BG

    st.markdown(f"""
<style>

/* ============================================
   BACKGROUND
   ============================================ */
html, body, .stApp, [data-testid="stAppViewContainer"] {{
    background: {background_style} !important;
    background-repeat: no-repeat !important;
    background-size: cover !important;
    background-position: center center !important;
    background-attachment: fixed !important;
}}

[data-testid="stHeader"],
[data-testid="stAppHeader"],
[data-testid="stToolbar"] {{
    background: transparent !important;
}}

/* ============================================
   TEXT - WHITE COLOR
   ============================================ */
h1, h2, h3, h4, h5, h6, p, span, label, li,
[data-testid="stMarkdownContainer"] {{
    color: white !important;
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3) !important;
}}

/* ============================================
   SIDEBAR
   ============================================ */
[data-testid="stSidebar"] {{
    background: rgba(0, 0, 0, 0.3) !important;
    backdrop-filter: blur(12px) !important;
    border-right: 1px solid rgba(255, 255, 255, 0.1) !important;
}}

/* ============================================
   CHAT MESSAGES - GLASS BUBBLES
   ============================================ */
[data-testid="stChatMessage"] {{
    background: transparent !important;
    margin-bottom: 12px !important;
}}

[data-testid="stChatMessageContent"] {{
    background: rgba(255, 255, 255, 0.15) !important;
    backdrop-filter: blur(20px) saturate(180%) !important;
    -webkit-backdrop-filter: blur(20px) saturate(180%) !important;
    border-radius: 24px !important;
    border: 1px solid rgba(255, 255, 255, 0.35) !important;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.25) !important;
    padding: 16px 22px !important;
    color: white !important;
}}

[data-testid="stChatMessageContent"]:hover {{
    background: rgba(255, 255, 255, 0.2) !important;
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.3) !important;
    transform: translateY(-2px) !important;
    transition: all 0.3s ease !important;
}}

/* ============================================
   CHAT INPUT - GLASS STYLE (STREAMLIT 1.53)
   ============================================ */

/* ============================================
   KILL THE BLACK BOTTOM BAR - COMPLETE FIX
   ============================================ */

/* Target every possible wrapper Streamlit uses */
section[data-testid="stBottom"],
section[data-testid="stBottom"]::before,
section[data-testid="stBottom"]::after,
div[data-testid="stBottomBlockContainer"],
div[data-testid="stBottomBlockContainer"]::before,
div[data-testid="stBottomBlockContainer"]::after {{
    background: transparent !important;
    background-color: transparent !important;
    background-image: none !important;
    box-shadow: none !important;
    border: none !important;
}}

/* Nuke ALL descendants including dynamic emotion cache classes */
section[data-testid="stBottom"] *,
section[data-testid="stBottom"] *::before,
section[data-testid="stBottom"] *::after {{
    background: transparent !important;
    background-color: transparent !important;
    background-image: none !important;
    box-shadow: none !important;
}}

/* Streamlit injects a gradient fade above the input bar - kill it */
section[data-testid="stBottom"] > div:first-child {{
    background: linear-gradient(
        to bottom,
        transparent 0%,
        transparent 100%
    ) !important;
}}

/* Re-apply glass style ONLY to the textarea (must come last to win) */
section[data-testid="stBottom"] textarea,
section[data-testid="stBottom"] div[data-baseweb="textarea"] textarea {{
    background: rgba(255, 255, 255, 0.15) !important;
    backdrop-filter: blur(20px) saturate(180%) !important;
    -webkit-backdrop-filter: blur(20px) saturate(180%) !important;
    border-radius: 28px !important;
    border: 1px solid rgba(255, 255, 255, 0.35) !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2) !important;
    color: white !important;
    padding: 12px 20px !important;
    font-size: 15px !important;
    height: 48px !important;
    min-height: 48px !important;
    max-height: 48px !important;
}}

section[data-testid="stBottom"] textarea:focus {{
    outline: none !important;
    border: 1px solid rgba(255, 255, 255, 0.55) !important;
}}

section[data-testid="stBottom"] textarea::placeholder {{
    color: rgba(255, 255, 255, 0.6) !important;
}}

/* Send button */
section[data-testid="stBottom"] button {{
    background: rgba(255, 255, 255, 0.2) !important;
    backdrop-filter: blur(10px) !important;
    border-radius: 50% !important;
    border: 1px solid rgba(255, 255, 255, 0.3) !important;
    box-shadow: none !important;
    width: 40px !important;
    height: 40px !important;
}}

section[data-testid="stBottom"] button:hover {{
    background: rgba(255, 255, 255, 0.3) !important;
}}
/* ============================================
   FORMS & INPUTS (LOGIN PAGE, etc)
   ============================================ */
.stTextInput input,
.stTextArea textarea:not(section[data-testid="stBottom"] textarea),
.stSelectbox select {{
    background: rgba(255, 255, 255, 0.15) !important;
    backdrop-filter: blur(12px) !important;
    border: 1px solid rgba(255, 255, 255, 0.25) !important;
    border-radius: 12px !important;
    color: white !important;
    padding: 10px 16px !important;
}}

.stTextInput input::placeholder,
.stTextArea textarea::placeholder {{
    color: rgba(255, 255, 255, 0.6) !important;
}}

/* ============================================
   BUTTONS
   ============================================ */
.stButton button:not(section[data-testid="stBottom"] button) {{
    background: rgba(255, 255, 255, 0.2) !important;
    backdrop-filter: blur(10px) !important;
    border: 1px solid rgba(255, 255, 255, 0.3) !important;
    border-radius: 12px !important;
    color: white !important;
    padding: 10px 24px !important;
}}

.stButton button:hover {{
    background: rgba(255, 255, 255, 0.3) !important;
}}

/* ============================================
   FORMS (LOGIN/SIGNUP)
   ============================================ */
.stForm {{
    background: rgba(255, 255, 255, 0.15) !important;
    backdrop-filter: blur(20px) !important;
    border-radius: 20px !important;
    border: 1px solid rgba(255, 255, 255, 0.3) !important;
    padding: 30px !important;
}}

/* ============================================
   METRICS & CARDS (ANALYTICS)
   ============================================ */
[data-testid="metric-container"] {{
    background: rgba(255, 255, 255, 0.15) !important;
    backdrop-filter: blur(16px) !important;
    border-radius: 16px !important;
    border: 1px solid rgba(255, 255, 255, 0.25) !important;
    padding: 16px !important;
}}

[data-testid="stMetricValue"],
[data-testid="stMetricLabel"] {{
    color: white !important;
}}

/* ============================================
   SCROLLBAR
   ============================================ */
::-webkit-scrollbar {{
    width: 10px;
    height: 10px;
}}

::-webkit-scrollbar-track {{
    background: rgba(255, 255, 255, 0.05);
    border-radius: 10px;
}}

::-webkit-scrollbar-thumb {{
    background: rgba(255, 255, 255, 0.25);
    border-radius: 10px;
}}

::-webkit-scrollbar-thumb:hover {{
    background: rgba(255, 255, 255, 0.35);
}}

/* ============================================
   GLOBAL - TEXT OVERFLOW PREVENTION
   (applies on ALL screen sizes)
   ============================================ */
*, *::before, *::after {{
    box-sizing: border-box !important;
}}

html, body {{
    overflow-x: hidden !important;
    max-width: 100vw !important;
}}

h1, h2, h3, h4, h5, h6, p, span, label, li,
[data-testid="stMarkdownContainer"],
[data-testid="stMarkdownContainer"] * {{
    word-wrap: break-word !important;
    overflow-wrap: break-word !important;
    word-break: break-word !important;
    max-width: 100% !important;
    white-space: pre-wrap !important;
}}

pre, code {{
    white-space: pre-wrap !important;
    word-break: break-all !important;
    overflow-x: auto !important;
    max-width: 100% !important;
}}

a {{
    word-break: break-all !important;
    overflow-wrap: break-word !important;
}}

/* ============================================
   MOBILE - COMPREHENSIVE FIX
   ============================================ */
@media (max-width: 768px) {{

    /* --- Background --- */
    html, body, .stApp {{
        background-attachment: scroll !important;
    }}

    /* --- Main content padding --- */
    .main .block-container,
    [data-testid="block-container"] {{
        padding: 8px 12px !important;
        max-width: 100vw !important;
        overflow-x: hidden !important;
    }}

    /* --- Typography scaling --- */
    h1 {{ font-size: 1.4rem !important; line-height: 1.3 !important; }}
    h2 {{ font-size: 1.2rem !important; line-height: 1.3 !important; }}
    h3 {{ font-size: 1.05rem !important; line-height: 1.3 !important; }}

    p, span, label, li,
    [data-testid="stMarkdownContainer"] {{
        font-size: 13px !important;
        line-height: 1.5 !important;
    }}

    /* --- Chat message bubbles --- */
    [data-testid="stChatMessage"] {{
        margin-bottom: 8px !important;
        max-width: 100% !important;
    }}

    [data-testid="stChatMessageContent"] {{
        padding: 10px 14px !important;
        font-size: 13px !important;
        border-radius: 16px !important;
        max-width: 100% !important;
        overflow-wrap: break-word !important;
        word-break: break-word !important;
        white-space: pre-wrap !important;
    }}

    [data-testid="stChatMessageContent"] p,
    [data-testid="stChatMessageContent"] li,
    [data-testid="stChatMessageContent"] span,
    [data-testid="stChatMessageContent"] strong {{
        font-size: 13px !important;
        overflow-wrap: break-word !important;
        word-break: break-word !important;
        max-width: 100% !important;
    }}

    /* Remove hover lift on mobile (causes layout shift) */
    [data-testid="stChatMessageContent"]:hover,
    [data-testid="stChatInput"] textarea:hover,
    [data-testid="stChatInput"] button:hover {{
        transform: none !important;
    }}

    /* --- Chat input --- */
    section[data-testid="stBottom"] textarea,
    [data-testid="stChatInput"] textarea {{
        font-size: 14px !important;
        padding: 10px 14px !important;
        border-radius: 18px !important;
        height: 44px !important;
        min-height: 44px !important;
        max-height: 44px !important;
    }}

    section[data-testid="stBottom"] button,
    [data-testid="stChatInput"] button {{
        width: 36px !important;
        height: 36px !important;
    }}

    /* --- Live Snapshot metrics row --- */
    [data-testid="metric-container"] {{
        padding: 10px 8px !important;
        border-radius: 12px !important;
    }}

    [data-testid="stMetricValue"] {{ font-size: 1rem !important; }}
    [data-testid="stMetricLabel"] {{ font-size: 11px !important; }}

    /* --- Buttons --- */
    .stButton button {{
        padding: 8px 14px !important;
        font-size: 13px !important;
        border-radius: 10px !important;
        white-space: normal !important;
        word-break: break-word !important;
        height: auto !important;
        min-height: 40px !important;
        line-height: 1.3 !important;
    }}

    /* --- Suggestion buttons row --- */
    [data-testid="stHorizontalBlock"] {{
        flex-wrap: wrap !important;
        gap: 6px !important;
    }}

    [data-testid="stHorizontalBlock"] > div {{
        min-width: 140px !important;
        flex: 1 1 auto !important;
    }}

    /* --- Sidebar --- */
    [data-testid="stSidebar"] {{
        min-width: 260px !important;
        max-width: 80vw !important;
    }}

    [data-testid="stSidebar"] .stButton button {{
        font-size: 12px !important;
        padding: 6px 10px !important;
    }}

    /* --- Selectbox & text inputs --- */
    .stSelectbox > div,
    .stTextInput input {{
        font-size: 14px !important;
        max-width: 100% !important;
    }}

    /* --- Forms (login page) --- */
    .stForm {{
        padding: 16px !important;
        border-radius: 14px !important;
    }}

    /* --- Tables --- */
    table {{
        display: block !important;
        overflow-x: auto !important;
        max-width: 100% !important;
        font-size: 12px !important;
    }}
}}

/* ============================================
   EXTRA SMALL SCREENS (< 480px)
   Stack columns vertically
   ============================================ */
@media (max-width: 480px) {{
    [data-testid="column"] {{
        min-width: 100% !important;
        flex: 0 0 100% !important;
    }}

    h1 {{ font-size: 1.2rem !important; }}
    h2 {{ font-size: 1rem !important; }}

    [data-testid="stChatMessageContent"] {{
        font-size: 12px !important;
        padding: 8px 12px !important;
    }}
}}

/* ============================================
   ANIMATIONS
   ============================================ */
@keyframes slideIn {{
    from {{
        opacity: 0;
        transform: translateY(20px);
    }}
    to {{
        opacity: 1;
        transform: translateY(0);
    }}
}}

[data-testid="stChatMessage"] {{
    animation: slideIn 0.3s ease !important;
}}
/* ============================================
   FINAL FIX - BLACK BOTTOM BAR
   ============================================ */

/* Override Streamlit's inline style injection */
section[data-testid="stBottom"] {{
    background: transparent !important;
    background-color: transparent !important;
    background-image: none !important;
    box-shadow: none !important;
    position: relative !important;
}}

/* This is the actual culprit - the inner fixed wrapper */
section[data-testid="stBottom"] > div,
section[data-testid="stBottom"] > div > div,
section[data-testid="stBottom"] > div > div > div {{
    background: transparent !important;
    background-color: transparent !important;
    background-image: none !important;
    box-shadow: none !important;
}}

/* Streamlit adds a sticky/fixed white-to-dark gradient div ABOVE the input */
section[data-testid="stBottom"]:before {{
    content: '' !important;
    display: block !important;
    background: transparent !important;
}}
/* ============================================
   EXACT FIX - CONFIRMED FROM DEVTOOLS
   ============================================ */
.st-emotion-cache-1y34ygi,
.st-emotion-cache-1p2n2i4,
.st-emotion-cache-hzygls {{
    background: transparent !important;
    background-color: transparent !important;
    background-image: none !important;
    box-shadow: none !important;
}}

.st-emotion-cache-1y34ygi {{
    padding-bottom: 16px !important;
}}
/* ============================================
   FIX - DARK INPUT WRAPPER
   ============================================ */
.st-emotion-cache-jchovf,
.st-emotion-cache-1ab1jlb,
.e5ztmp71 {{
    background: transparent !important;
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
}}
/* ============================================
   CHAT INPUT - MATCH GLASS BUBBLES
   ============================================ */
[data-testid="stChatInput"],
[data-testid="stChatInput"] > div,
.st-emotion-cache-1ab1jlb {{
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}}

/* The actual textarea - glass bubble style */
[data-testid="stChatInput"] textarea {{
    background: rgba(255, 255, 255, 0.15) !important;
    backdrop-filter: blur(20px) saturate(180%) !important;
    -webkit-backdrop-filter: blur(20px) saturate(180%) !important;
    border-radius: 24px !important;
    border: 1px solid rgba(255, 255, 255, 0.35) !important;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.25) !important;
    color: white !important;
    padding: 16px 22px !important;
    font-size: 15px !important;
    transition: all 0.3s ease !important;
}}

[data-testid="stChatInput"] textarea:hover {{
    background: rgba(255, 255, 255, 0.2) !important;
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.3) !important;
    transform: translateY(-2px) !important;
}}

[data-testid="stChatInput"] textarea:focus {{
    background: rgba(255, 255, 255, 0.22) !important;
    border: 1px solid rgba(255, 255, 255, 0.55) !important;
    outline: none !important;
}}

[data-testid="stChatInput"] textarea::placeholder {{
    color: rgba(255, 255, 255, 0.6) !important;
}}

/* Send button - match bubble style */
[data-testid="stChatInput"] button {{
    background: rgba(255, 255, 255, 0.2) !important;
    backdrop-filter: blur(20px) !important;
    border-radius: 50% !important;
    border: 1px solid rgba(255, 255, 255, 0.35) !important;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.25) !important;
    color: white !important;
    transition: all 0.3s ease !important;
}}

[data-testid="stChatInput"] button:hover {{
    background: rgba(255, 255, 255, 0.3) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.3) !important;
}}
</style>
""", unsafe_allow_html=True)