"""
Text-to-speech via the ElevenLabs API.

Uses eleven_multilingual_v2 for proper Slovak pronunciation.
Saves the resulting MP3 to a given path and returns True on success.
"""

from pathlib import Path
from typing import Optional

import requests

from config import ELEVENLABS_API_KEY, ELEVENLABS_MODEL, ELEVENLABS_VOICE_ID
from utils.logger import get_logger

log = get_logger()

_TTS_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"


def synthesize(text: str, output_path: Path) -> bool:
    """
    Convert text to speech and save the MP3 to output_path.

    Args:
        text: Slovak text to synthesise.
        output_path: Destination file path (will be overwritten if it exists).

    Returns:
        True on success, False on failure.
    """
    url = _TTS_URL.format(voice_id=ELEVENLABS_VOICE_ID)
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }
    payload = {
        "text": text,
        "model_id": ELEVENLABS_MODEL,
        "voice_settings": {
            "stability": 0.65,
            "similarity_boost": 0.80,
        },
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(response.content)
        log.debug("Audio saved to %s (%d bytes).", output_path, len(response.content))
        return True

    except requests.RequestException as exc:
        log.error("ElevenLabs synthesis failed: %s", exc)
        return False


def generate_fallback_audio(output_path: Path, fallback_text: str) -> bool:
    """
    Pre-generate the fallback audio file at startup if it does not already exist.

    Returns True if the file is ready (either just created or already existed).
    """
    if output_path.exists():
        log.debug("Fallback audio already exists at %s.", output_path)
        return True

    log.info("Generating fallback audio...")
    success = synthesize(fallback_text, output_path)
    if success:
        log.info("Fallback audio ready.")
    else:
        log.warning("Could not generate fallback audio. Will retry next startup.")
    return success
