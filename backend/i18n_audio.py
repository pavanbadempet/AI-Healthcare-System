"""Text-to-Speech (TTS) Localization Service.

Provides dynamic speech synthesis for clinical AI advice in all 8 supported languages.
Falls back to clean offline mock waveforms when external libraries are unavailable or offline.
"""
import io
import os
import hashlib
import logging
import math
import struct
import wave
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/audio", tags=["i18n Audio"])

# 8 supported languages
SUPPORTED_LANGUAGES = {"en", "es", "hi", "te", "fr", "de", "zh", "ar"}

class TTSRequest(BaseModel):
    text: str
    lang: str = "en"

def generate_offline_melody_wav() -> bytes:
    """Generates a real, playable WAV audio beep using the standard library wave module."""
    sample_rate = 8000.0
    duration = 1.0
    num_samples = int(sample_rate * duration)
    
    wav_io = io.BytesIO()
    with wave.open(wav_io, 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(int(sample_rate))
        
        # A4 pitch tone (440Hz)
        frequency = 440.0
        for i in range(num_samples):
            value = int(32767.0 * math.sin(2.0 * math.pi * frequency * (i / sample_rate)))
            data = struct.pack('<h', value)
            wav_file.writeframesraw(data)
            
    return wav_io.getvalue()

@router.post("/tts")
def text_to_speech(body: TTSRequest):
    """Generate spoken MP3/WAV audio from clinical recommendation text with caching."""
    if body.lang not in SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=400,
            detail=f"Language '{body.lang}' is not supported. Supported: {list(SUPPORTED_LANGUAGES)}"
        )
    if not body.text or not body.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")

    # 1. Local caching logic based on md5 hash
    text_hash = hashlib.md5((body.text.strip() + "_" + body.lang).encode("utf-8")).hexdigest()
    cache_dir = os.path.abspath(os.path.join("data", "tts_cache"))
    os.makedirs(cache_dir, exist_ok=True)
    
    cache_file = os.path.join(cache_dir, f"{text_hash}.mp3")
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "rb") as f:
                audio_data = f.read()
            return StreamingResponse(io.BytesIO(audio_data), media_type="audio/mpeg")
        except Exception as e:
            logger.warning("Failed to read cached TTS file: %s", e)

    # 2. Try external generation via gTTS
    try:
        from gtts import gTTS
        tts = gTTS(text=body.text, lang=body.lang)
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        mp3_bytes = mp3_fp.getvalue()
        
        # Write to cache
        try:
            with open(cache_file, "wb") as f:
                f.write(mp3_bytes)
        except Exception as cache_err:
            logger.warning("Failed to cache TTS file: %s", cache_err)
            
        return StreamingResponse(io.BytesIO(mp3_bytes), media_type="audio/mpeg")
    except Exception as e:
        if not isinstance(e, ImportError):
            logger.warning("gTTS generation failed, falling back to offline tone generator: %s", e)
            
        # 3. Offline fallback melody
        wav_bytes = generate_offline_melody_wav()
        return StreamingResponse(io.BytesIO(wav_bytes), media_type="audio/mpeg")
