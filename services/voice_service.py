"""
Voice Service — browser-native audio input + output.

HOW IT WORKS
────────────
INPUT  : st.audio_input()  →  records WAV directly in the user's browser (no server mic)
STT    : Gemini 2.5 Flash Lite  →  transcribes the WAV bytes (reuses your existing GEMINI_API_KEY)
OUTPUT : gTTS  →  generates MP3 in-memory on the server
PLAY   : st.audio(mp3_bytes)  →  plays in the browser natively

REQUIREMENTS (add to requirements.txt if missing)
─────────────────────────────────
streamlit>=1.32          # st.audio_input() was added in 1.32
google-genai             # already in your project
gtts                     # pip install gtts
"""

import io
import base64
import os
import re

import streamlit as st
from google import genai
from gtts import gTTS


# ─── Gemini client (same key the rest of the app uses) ───────────────────────
def _get_client() -> genai.Client:
    """Return a Gemini client, reading the key from st.secrets or env."""
    key = os.getenv("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY", "")
    return genai.Client(api_key=key)


from google.genai import types 

def transcribe(audio_bytes: bytes, language: str = "en") -> str:
    if not audio_bytes:
        return ""

    LANG_NAMES = {"en": "English", "te": "Telugu", "hi": "Hindi", "ur": "Urdu"}
    lang_hint = LANG_NAMES.get(language, "English")

    try:
        client = _get_client()

        # Sniff media type
        media_type = "audio/wav" if audio_bytes[:4] == b"RIFF" else "audio/webm"

        # The SDK expects a list of parts. 
        # We use types.Part.from_text and types.Part.from_bytes.
        prompt_text = (
            f"Transcribe the following audio clip into {lang_hint} text. "
            "Return ONLY the transcribed words, nothing else."
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=[
                types.Part.from_text(text=prompt_text),
                types.Part.from_bytes(data=audio_bytes, mime_type=media_type)
            ]
        )

        return response.text.strip().strip('"').strip("'")

    except Exception as e:
        print(f"[voice_service] transcribe error: {e}")
        return ""

# ─── Text-to-Speech ─────────────────────────────────────────────────────────
def synthesize(text: str, language: str = "en") -> bytes:
    """
    Convert text to MP3 audio using gTTS (runs on the server, no API key needed).

    Args:
        text:     The text to speak.  Markdown is stripped automatically.
        language: Two-letter code — "en", "te", "hi", "ur".

    Returns:
        MP3 bytes ready to pass to st.audio().  Empty bytes on error.
    """
    if not text:
        return b""

    # ── strip markdown so TTS doesn't read "asterisk asterisk" ──
    clean = _strip_markdown(text)

    # gTTS has a ~500-char limit before quality degrades; truncate gracefully
    if len(clean) > 500:
        clean = clean[:500] + "…"

    try:
        tts = gTTS(text=clean, lang=language, slow=False)
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        return buf.getvalue()
    except Exception as e:
        print(f"[voice_service] synthesize error: {e}")
        return b""


# ─── Markdown stripper ───────────────────────────────────────────────────────
def _strip_markdown(text: str) -> str:
    """Remove common markdown so TTS reads natural speech."""
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)          # **bold**
    text = re.sub(r"\*(.+?)\*", r"\1", text)              # *italic*
    text = re.sub(r"#{1,6}\s*", "", text)                  # ### headings
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text) # [link](url)
    text = re.sub(r"[•\-\*]\s*", "", text)                # bullet chars
    text = re.sub(r"_{1,3}", "", text)                     # underscores
    text = re.sub(r"\n+", " ", text)                       # newlines → space
    text = re.sub(r"\s+", " ", text).strip()               # collapse spaces
    return text


# ─── Streamlit UI helpers ────────────────────────────────────────────────────
# These are thin wrappers you drop into webapp.py.  They handle the full
# record → transcribe → display cycle and the speak → play cycle.

def render_audio_input(language: str = "en") -> str:
    """
    Render the browser mic widget and transcribe whatever the user records.

    Call this ONCE per rerun in webapp.py.  Returns the transcribed text
    (empty string if nothing was recorded this rerun).

    Args:
        language: two-letter code matching your app's current language setting.
    """
    LABELS = {
        "en": "🎤 Speak your question",
        "te": "🎤 మీ ప్రశ్న చెప్పండి",
        "hi": "🎤 अपना सवाल बोलें",
        "ur": "🎤 اپنا سوال بولیں",
    }

    audio_input = st.audio_input(
        label=LABELS.get(language, LABELS["en"]),
        key="voice_input_widget",
    )

    # audio_input is None when nothing has been recorded yet this rerun
    if audio_input is None:
        return ""

    raw_bytes = audio_input.getvalue()
    if not raw_bytes:
        return ""

    with st.spinner("🔄 Transcribing…"):
        transcript = transcribe(raw_bytes, language=language)

    if transcript:
        st.success(f"✅ You said: **{transcript}**")
    else:
        st.warning("⚠️ Could not understand the audio. Try speaking more clearly.")

    return transcript


def render_audio_output(text: str, language: str = "en", auto_play: bool = False):
    """
    Show a listen button (or auto-play) for the assistant's response.

    Args:
        text:      The response text to speak.
        language:  Two-letter code matching the displayed language.
        auto_play: If True, generate + play audio immediately without a button.
    """
    if not text:
        return

    mp3_bytes = synthesize(text, language=language)
    if not mp3_bytes:
        return                          # silently skip if TTS failed

    if auto_play:
        st.audio(mp3_bytes, format="audio/mp3", autoplay=True)
    else:
        # Wrap in an expander so it doesn't clutter the chat
        with st.expander("🔊 Listen to response", expanded=False):
            st.audio(mp3_bytes, format="audio/mp3")