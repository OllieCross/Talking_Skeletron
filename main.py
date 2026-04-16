"""
Talking Skeleton -- main loop.

Flow per cycle:
  1. Wait until the skeleton is not speaking (feedback guard).
  2. Record audio via VAD until silence or timeout.
  3. Transcribe with Whisper (Slovak).
  4. Generate a response with GPT-4o (Slovak, 1-2 sentences).
  5. Synthesise speech with ElevenLabs (eleven_multilingual_v2).
  6. Play the audio; set speaking flag during playback.
  7. Repeat.
"""

import tempfile
import threading
from pathlib import Path

from audio.player import play_audio
from audio.recorder import record_until_silence
from ai.transcribe import transcribe
from ai.respond import generate_response
from ai.synthesize import synthesize, generate_fallback_audio
from config import FALLBACK_FILE, FALLBACK_TEXT, validate_env
from utils.logger import get_logger

log = get_logger()

# Shared flag -- True while the skeleton's audio is playing.
# The recorder checks this flag before starting to capture, preventing
# the skeleton from hearing its own voice.
_speaking = threading.Event()


def _play_response(audio_path: Path) -> None:
    """Play audio and manage the speaking flag."""
    _speaking.set()
    try:
        play_audio(audio_path)
    finally:
        _speaking.clear()


def _play_fallback() -> None:
    if FALLBACK_FILE.exists():
        log.info("Playing fallback audio.")
        _play_response(FALLBACK_FILE)
    else:
        log.warning("Fallback audio not available -- skipping.")


def run() -> None:
    log.info("Talking Skeleton starting up.")
    validate_env()

    # Pre-generate fallback audio (best-effort; does not abort startup if it fails)
    generate_fallback_audio(FALLBACK_FILE, FALLBACK_TEXT)

    log.info("Skeleton is ready. Listening...")

    while True:
        # Do not start recording while the skeleton is speaking
        if _speaking.is_set():
            continue

        # --- Step 1: Record ---
        wav_bytes = record_until_silence()
        if wav_bytes is None:
            # No speech detected -- loop back immediately
            continue

        # --- Step 2: Transcribe ---
        user_text = transcribe(wav_bytes)
        if not user_text:
            log.info("Transcription empty or failed -- skipping cycle.")
            _play_fallback()
            continue

        # --- Step 3: Generate response ---
        response_text = generate_response(user_text)
        if not response_text:
            log.info("Response generation failed -- playing fallback.")
            _play_fallback()
            continue

        # --- Step 4: Synthesise ---
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            response_path = Path(tmp.name)

        success = synthesize(response_text, response_path)
        if not success:
            log.info("Synthesis failed -- playing fallback.")
            _play_fallback()
            continue

        # --- Step 5: Play ---
        _play_response(response_path)

        # Clean up temp file after playback
        try:
            response_path.unlink(missing_ok=True)
        except OSError:
            pass


if __name__ == "__main__":
    run()
