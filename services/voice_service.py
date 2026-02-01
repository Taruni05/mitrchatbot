"""
Voice Interaction Service - Multilingual Support
Uses sounddevice + SpeechRecognition (FREE, no API key needed)
Properly handles language matching between input and output
"""

import streamlit as st
import sounddevice as sd
import soundfile as sf
from gtts import gTTS
import speech_recognition as sr
import tempfile
import os
import numpy as np
from scipy.io import wavfile


class VoiceService:
    """Handle voice input and output without PyAudio"""
    
    def __init__(self):
        self.temp_dir = tempfile.gettempdir()
        self.sample_rate = 16000  # 16kHz for speech recognition
    
    def record_audio(self, duration: int = 5) -> dict:
        """
        Record audio from microphone using sounddevice
        
        Args:
            duration: Recording duration in seconds
        
        Returns:
            dict: {"success": bool, "audio_path": str, "error": str}
        """
        try:
            # Record audio
            audio_data = sd.rec(
                int(duration * self.sample_rate),
                samplerate=self.sample_rate,
                channels=1,
                dtype='int16'
            )
            
            # Wait for recording to finish
            sd.wait()
            
            # Save to temporary WAV file
            audio_file = os.path.join(self.temp_dir, "recording.wav")
            wavfile.write(audio_file, self.sample_rate, audio_data)
            
            return {
                "success": True,
                "audio_path": audio_file,
                "error": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "audio_path": None,
                "error": f"Recording error: {str(e)}"
            }
    
    def transcribe_audio(self, audio_path: str, language: str = "en-IN") -> dict:
        """
        Transcribe audio using SpeechRecognition library (Free Google API)
        
        Args:
            audio_path: Path to audio file
            language: Language code (en-IN, te-IN, ur-IN, hi-IN)
        
        Returns:
            dict: {"success": bool, "text": str, "error": str}
        """
        try:
            import speech_recognition as sr
            
            # Initialize recognizer
            recognizer = sr.Recognizer()
            
            # Load audio file
            with sr.AudioFile(audio_path) as source:
                audio_data = recognizer.record(source)
            
            # Use Google Speech Recognition (FREE - no API key needed)
            transcript = recognizer.recognize_google(
                audio_data,
                language=language
            )
            
            return {
                "success": True,
                "text": transcript,
                "error": None
            }
                
        except sr.UnknownValueError:
            return {
                "success": False,
                "text": "",
                "error": "Could not understand audio. Please speak clearly."
            }
        except sr.RequestError as e:
            return {
                "success": False,
                "text": "",
                "error": f"Google Speech API error: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "text": "",
                "error": f"Transcription error: {str(e)}"
            }
    
    def listen(self, language: str = "en-IN", duration: int = 5) -> dict:
        """
        Complete voice input: Record + Transcribe
        
        Args:
            language: Language code (en-IN, te-IN, ur-IN, hi-IN)
            duration: Recording duration in seconds
        
        Returns:
            dict: {"success": bool, "text": str, "error": str}
        """
        # Step 1: Record audio
        record_result = self.record_audio(duration)
        
        if not record_result["success"]:
            return record_result
        
        # Step 2: Transcribe audio
        transcribe_result = self.transcribe_audio(
            record_result["audio_path"],
            language
        )
        
        # Cleanup audio file
        try:
            os.remove(record_result["audio_path"])
        except:
            pass
        
        return transcribe_result
    
    def speak(self, text: str, language: str = "en") -> dict:
        """
        Convert text to speech and return audio file path
        
        Args:
            text: Text to convert to speech
            language: Language code (en, te, ur, hi)
        
        Returns:
            dict: {"success": bool, "audio_path": str, "error": str}
        """
        try:
            # Map language codes to gTTS codes
            lang_map = {
                "en": "en",
                "te": "te",
                "ur": "ur",
                "hi": "hi"
            }
            
            tts_lang = lang_map.get(language, "en")
            
            # Create TTS object
            tts = gTTS(text=text, lang=tts_lang, slow=False)
            
            # Save to temporary file
            audio_file = os.path.join(self.temp_dir, "hyderabad_bot_response.mp3")
            tts.save(audio_file)
            
            return {
                "success": True,
                "audio_path": audio_file,
                "error": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "audio_path": None,
                "error": f"Text-to-speech error: {e}"
            }
    
    def cleanup_audio(self, audio_path: str):
        """Delete temporary audio file"""
        try:
            if audio_path and os.path.exists(audio_path):
                os.remove(audio_path)
        except Exception:
            pass


# ========================================
# LANGUAGE CODE MAPPING
# ========================================
SPEECH_LANGUAGES = {
    "en": "en-IN",  # English (India)
    "te": "te-IN",  # Telugu (India)
    "ur": "ur-IN",  # Urdu (India)
    "hi": "hi-IN",  # Hindi (India)
}


def get_speech_language(app_lang: str) -> str:
    """Convert app language code to speech recognition code"""
    return SPEECH_LANGUAGES.get(app_lang, "en-IN")


# ========================================
# STREAMLIT UI HELPERS
# ========================================

def create_voice_input_button(language: str = "en", duration: int = 5) -> str:
    """
    Create voice input button and handle recording
    Returns recognized text or empty string
    """
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.info("💡 Click microphone → Speak for 5 seconds → Wait for transcription")
    
    with col2:
        if st.button("🎤 Speak", key="voice_input_btn", help="Click to start recording"):
            with st.spinner(f"🎧 Recording for {duration} seconds..."):
                voice_service = VoiceService()
                speech_lang = get_speech_language(language)
                
                # Progress bar for recording
                progress_bar = st.progress(0)
                for i in range(duration):
                    progress_bar.progress((i + 1) / duration)
                    import time
                    time.sleep(1)
                
                result = voice_service.listen(language=speech_lang, duration=duration)
                
                if result["success"]:
                    st.success(f"✅ You said: **{result['text']}**")
                    return result["text"]
                else:
                    st.error(f"❌ {result['error']}")
                    return ""
    
    return ""


def create_voice_output_player(text: str, language: str = "en"):
    """
    Create audio player for bot response
    
    Args:
        text: Response text to speak
        language: Language code (en, te, ur, hi) - MATCHES translation language
    """
    if not text:
        return
    
    # Remove markdown formatting for TTS
    import re
    clean_text = re.sub(r'\*\*', '', text)  # Remove bold
    clean_text = re.sub(r'[#]+', '', clean_text)  # Remove headers
    clean_text = re.sub(r'[•\-\*]', '', clean_text)  # Remove bullets
    clean_text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', clean_text)  # Remove links
    
    # Limit text length for TTS (max 500 chars)
    if len(clean_text) > 500:
        clean_text = clean_text[:500] + "..."
    
    # Add "Listen to Response" button
    if st.button("🔊 Listen to Response", key="voice_output_btn"):
        with st.spinner("🎵 Generating audio..."):
            voice_service = VoiceService()
            
            # ✅ USE THE SAME LANGUAGE AS THE TRANSLATED RESPONSE
            result = voice_service.speak(clean_text, language=language)
            
            if result["success"]:
                # Play audio in Streamlit
                with open(result["audio_path"], "rb") as audio_file:
                    audio_bytes = audio_file.read()
                    st.audio(audio_bytes, format="audio/mp3")
                
                # Cleanup
                voice_service.cleanup_audio(result["audio_path"])
            else:
                st.error(f"❌ {result['error']}")


# ========================================
# VOICE SETTINGS UI
# ========================================

def create_voice_settings_ui():
    """Create voice settings in sidebar"""
    with st.expander("🎙️ Voice Settings"):
        # Enable/disable voice
        voice_enabled = st.checkbox(
            "Enable Voice Input",
            value=st.session_state.get("voice_input_enabled", False),
            key="voice_input_enabled",
            help="Allow voice queries"
        )
        
        # Recording duration
        duration = st.slider(
            "Recording Duration (seconds)",
            min_value=3,
            max_value=10,
            value=5,
            key="recording_duration",
            help="How long to record"
        )
        
        # Auto-play responses
        auto_speak = st.checkbox(
            "Auto-play Responses",
            value=st.session_state.get("auto_speak_enabled", False),
            key="auto_speak_enabled",
            help="Automatically speak bot responses"
        )
        
        return voice_enabled, duration, auto_speak