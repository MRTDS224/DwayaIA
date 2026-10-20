"""
Service Audio : 
- Synthèse Vocale (TTS) haute qualité via gTTS (voix naturelle arabe ou française)
- Transcription Vocale (STT) universelle via enregistrement audio standard
"""
import io
import re
import os
import subprocess
import tempfile
from typing import Optional
from gtts import gTTS
import speech_recognition as sr

class AudioService:
    def __init__(self):
        self.recognizer = sr.Recognizer()

    def text_to_speech_mp3(self, text: str) -> bytes:
        """
        Génère un flux audio MP3 avec intonation fluide et naturelle.
        Détecte automatiquement si le texte est arabe ou français.
        """
        clean_text = re.sub(r'[*_#`]', '', text)
        clean_text = re.sub(r'[💡💊🔄📍🌙📞⚠️💰🚨]', '', clean_text).strip()
        
        if not clean_text:
            clean_text = "Désolé, aucune réponse à énoncer."

        # Détection langue
        is_arabic = bool(re.search(r'[\u0600-\u06FF]', clean_text))
        lang = 'ar' if is_arabic else 'fr'

        tts = gTTS(text=clean_text, lang=lang, slow=False)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp.read()

    def speech_to_text(self, audio_bytes: bytes, filename: str = "audio.webm") -> str:
        """
        Reçoit un fichier audio (webm, wav, ogg, mp4) enregistré depuis n'importe quel navigateur
        (Firefox, Chrome, Edge, Safari), le convertit en PCM WAV via ffmpeg et le transcrit.
        """
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1] or ".webm") as temp_in:
            temp_in.write(audio_bytes)
            temp_in_path = temp_in.name

        temp_wav_path = temp_in_path + ".wav"

        try:
            # Conversion vers WAV 16kHz mono via ffmpeg
            cmd = [
                "ffmpeg", "-y", "-i", temp_in_path,
                "-ac", "1", "-ar", "16000",
                temp_wav_path
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

            with sr.AudioFile(temp_wav_path) as source:
                audio_data = self.recognizer.record(source)

            # Essayer d'abord la reconnaissance en français, puis arabe marocain
            try:
                text = self.recognizer.recognize_google(audio_data, language="fr-FR")
                return text
            except sr.UnknownValueError:
                try:
                    text_ar = self.recognizer.recognize_google(audio_data, language="ar-MA")
                    return text_ar
                except sr.UnknownValueError:
                    return ""
        except Exception as e:
            print(f"[!] Erreur ASR transcription: {e}")
            return ""
        finally:
            if os.path.exists(temp_in_path):
                os.remove(temp_in_path)
            if os.path.exists(temp_wav_path):
                os.remove(temp_wav_path)

audio_service = AudioService()
