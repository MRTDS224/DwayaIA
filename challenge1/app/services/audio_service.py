"""
Service Audio : 
- Transcription Vocale (STT) intelligente en Darija marocaine et Français via Gemini Multimodal Audio (avec fallback SpeechRecognition)
- Synthèse Vocale (TTS) haute qualité via gTTS (voix naturelle arabe ou française)
"""
import io
import re
import os
import subprocess
import tempfile
from typing import Optional
from gtts import gTTS
import speech_recognition as sr
from challenge1.app.services.gemini_service import gemini_service

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
        Reçoit un fichier audio (webm, wav, ogg, mp4, mp3) enregistré depuis le navigateur.
        1. Tente la transcription experte en Darija marocaine / Français via Gemini Multimodal.
        2. En cas d'indisponibilité ou d'erreur réseau, bascule sur Google Web Speech (SpeechRecognition).
        """
        if not audio_bytes:
            return ""

        # 1. Priorité à Gemini pour la compréhension native de la Darija
        gemini_transcript = self._transcribe_with_gemini(audio_bytes, filename)
        if gemini_transcript:
            return gemini_transcript

        # 2. Fallback déterministe via SpeechRecognition
        return self._transcribe_with_fallback(audio_bytes, filename)

    def _transcribe_with_gemini(self, audio_bytes: bytes, filename: str) -> Optional[str]:
        """Transcrit le flux audio avec Gemini en gérant nativement la Darija marocaine."""
        if not gemini_service.is_available:
            return None

        # Convertir en WAV 16kHz mono pour assurer une compatibilité optimale
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1] or ".webm") as temp_in:
            temp_in.write(audio_bytes)
            temp_in_path = temp_in.name

        temp_wav_path = temp_in_path + ".wav"

        try:
            cmd = [
                "ffmpeg", "-y", "-i", temp_in_path,
                "-ac", "1", "-ar", "16000",
                temp_wav_path
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

            with open(temp_wav_path, "rb") as f:
                wav_data = f.read()

            from google.genai import types

            models_to_try = ["gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-3.8-flash"]
            for model_name in models_to_try:
                try:
                    prompt = (
                        "Tu es un expert en transcription vocale pour le Maroc. "
                        "Écoute cet enregistrement audio et retranscris mot pour mot ce que dit la personne. "
                        "La personne peut parler en DARIJA MAROCAINE (avec des mots en arabe marocain ou en français médical comme nom de médicament, dosage, comprimé, etc.) ou en FRANÇAIS. "
                        "Règles strictes : "
                        "- Rends UNIQUEMENT le texte retranscrit, sans aucune formule de politesse, sans explication, sans guillemets. "
                        "- Si c'est en Darija, tu peux écrire en alphabet arabe ou en caractères latins phonétiques (Arabizi) selon ce qui est le plus fidèle. "
                        "- Si l'enregistrement ne contient que du silence, du bruit inaudible ou aucune parole humaine reconnaissable, réponds exactement : [INCOMPRIS]."
                    )

                    response = gemini_service.client.models.generate_content(
                        model=model_name,
                        contents=[
                            types.Part.from_bytes(data=wav_data, mime_type="audio/wav"),
                            prompt
                        ]
                    )

                    text = response.text.strip() if response and response.text else ""
                    if text and text != "[INCOMPRIS]" and not text.startswith("["):
                        return text
                    elif text == "[INCOMPRIS]":
                        return ""
                except Exception as e:
                    print(f"[!] Erreur Gemini STT ({model_name}): {e}")
                    continue

        except Exception as e:
            print(f"[!] Erreur préparation audio Gemini: {e}")
        finally:
            if os.path.exists(temp_in_path):
                os.remove(temp_in_path)
            if os.path.exists(temp_wav_path):
                os.remove(temp_wav_path)

        return None

    def _transcribe_with_fallback(self, audio_bytes: bytes, filename: str) -> str:
        """Fallback local sur Google Web Speech (SpeechRecognition)."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1] or ".webm") as temp_in:
            temp_in.write(audio_bytes)
            temp_in_path = temp_in.name

        temp_wav_path = temp_in_path + ".wav"

        try:
            cmd = [
                "ffmpeg", "-y", "-i", temp_in_path,
                "-ac", "1", "-ar", "16000",
                temp_wav_path
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

            with sr.AudioFile(temp_wav_path) as source:
                audio_data = self.recognizer.record(source)

            # Essayer arabe marocain puis français
            try:
                text_ar = self.recognizer.recognize_google(audio_data, language="ar-MA")
                return text_ar
            except sr.UnknownValueError:
                try:
                    text = self.recognizer.recognize_google(audio_data, language="fr-FR")
                    return text
                except sr.UnknownValueError:
                    return ""
        except Exception as e:
            print(f"[!] Erreur Fallback ASR: {e}")
            return ""
        finally:
            if os.path.exists(temp_in_path):
                os.remove(temp_in_path)
            if os.path.exists(temp_wav_path):
                os.remove(temp_wav_path)

audio_service = AudioService()


