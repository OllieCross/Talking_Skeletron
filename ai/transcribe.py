"""
Speech-to-text via the OpenAI Whisper API.

Sends WAV audio bytes and returns a Slovak transcription string,
or None on failure.
"""

import io
from typing import Optional

from openai import OpenAI

from config import LANGUAGE, OPENAI_API_KEY, WHISPER_MODEL
from utils.logger import get_logger

log = get_logger()

_client = OpenAI(api_key=OPENAI_API_KEY)


def transcribe(wav_bytes: bytes) -> Optional[str]:
    """
    Transcribe WAV audio bytes to text using Whisper.

    Args:
        wav_bytes: WAV-encoded audio (16-bit mono, 16 kHz).

    Returns:
        Transcribed text string, or None if transcription failed.
    """
    try:
        audio_file = io.BytesIO(wav_bytes)
        audio_file.name = "audio.wav"  # OpenAI SDK uses the filename to detect format

        response = _client.audio.transcriptions.create(
            model=WHISPER_MODEL,
            file=audio_file,
            language=LANGUAGE,
        )
        text = response.text.strip()
        log.info("Transcription: %s", text)
        return text if text else None

    except Exception as exc:
        log.error("Whisper transcription failed: %s", exc)
        return None
