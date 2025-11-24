import threading
import streamlit as st
import pyttsx3
import speech_recognition as sr

# Robust TTS engine initialization
try:
    engine = pyttsx3.init()
except Exception as e:
    engine = None
    st.warning("Text-to-speech is unavailable on this system.")

engine_lock = threading.Lock()

from gtts import gTTS
import tempfile
import time
import pygame

# Initialize pygame mixer for audio playback
pygame.mixer.init()

def speak(text: str) -> None:
    if engine:
        # Try local TTS first
        try:
            def _speak():
                with engine_lock:
                    engine.say(text)
                    engine.runAndWait()
            threading.Thread(target=_speak).start()
            return
        except Exception:
            pass
    
    # Fallback to gTTS (Google TTS)
    try:
        def _speak_gtts():
            tts = gTTS(text=text, lang='en')
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
                tts.save(fp.name)
                pygame.mixer.music.load(fp.name)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
                os.unlink(fp.name)
        threading.Thread(target=_speak_gtts).start()
    except Exception as e:
        st.warning(f"Audio output unavailable: {e}")

def stop_speech() -> None:
    if engine:
        with engine_lock:
            engine.stop()

def listen_for_stop() -> None:
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)
        try:
            audio = recognizer.listen(source, timeout=5)
            command = recognizer.recognize_google(audio).lower()
            if "stop" in command and engine:
                stop_speech()
        except Exception:
            pass

def listen() -> str:
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.write("Listening...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)
        try:
            query = recognizer.recognize_google(audio)
            st.write(f"Voice Input: {query}")
            return query
        except Exception:
            st.error("Voice input unavailable.")
            return ""

