import random
import threading
import time
from pathlib import Path

from audio.player import play_audio, play_pcm_stream
from audio.recorder import record_until_silence
from ai.transcribe import transcribe
from ai.respond import generate_response
from ai.synthesize import synthesize, synthesize_stream, generate_fallback_audio
from ai.synthesize import _STREAM_SAMPLE_RATE
from config import (
    FALLBACK_FILE,
    FALLBACK_TEXT,
    IDLE_MIN_SEC,
    IDLE_MAX_SEC,
    INVITATION_DIR,
    validate_env,
)
from utils.device_selector import select_devices
from utils.logger import get_logger

log = get_logger()

_speaking = threading.Event()


def _play_response(audio_path: Path, output_device: int) -> None:
    """Play audio and manage the speaking flag."""
    _speaking.set()
    try:
        play_audio(audio_path, device_idx=output_device)
    finally:
        _speaking.clear()


def _play_fallback(output_device: int) -> None:
    if FALLBACK_FILE.exists():
        log.info("Playing fallback audio.")
        _play_response(FALLBACK_FILE, output_device)
    else:
        log.warning("Fallback audio not available -- skipping.")


def _play_invitation(output_device: int) -> None:
    """Pick a random file from the invitation folder and play it."""
    clips = [
        f for f in INVITATION_DIR.iterdir()
        if f.suffix.lower() in {".mp3", ".wav", ".ogg", ".flac"}
    ] if INVITATION_DIR.exists() else []

    if not clips:
        log.debug("No invitation clips found in %s -- skipping.", INVITATION_DIR)
        return

    chosen = random.choice(clips)
    log.info("Playing invitation clip: %s", chosen.name)
    _play_response(chosen, output_device)


def _next_idle_threshold() -> float:
    """Return a random idle threshold between IDLE_MIN_SEC and IDLE_MAX_SEC."""
    return time.time() + random.uniform(IDLE_MIN_SEC, IDLE_MAX_SEC)


def run() -> None:
    log.info("Talking Skeleton starting up.")
    validate_env()

    input_device, output_device = select_devices()

    # Pre-generate fallback audio (best-effort; does not abort startup if it fails)
    generate_fallback_audio(FALLBACK_FILE, FALLBACK_TEXT)

    log.info("Skeleton is ready. Listening...")

    invite_at = _next_idle_threshold()

    while True:
        # Do not start recording while the skeleton is speaking
        if _speaking.is_set():
            continue

        # --- Step 1: Record ---
        wav_bytes = record_until_silence(device_idx=input_device)

        if wav_bytes is None:
            # No speech -- check if it is time to play an invitation
            if time.time() >= invite_at:
                _play_invitation(output_device)
                invite_at = _next_idle_threshold()
            continue

        # Speech detected -- reset idle timer
        invite_at = _next_idle_threshold()

        # --- Step 2: Transcribe ---
        user_text = transcribe(wav_bytes)
        if not user_text:
            log.info("Transcription empty or failed -- skipping cycle.")
            _play_fallback(output_device)
            continue

        # --- Step 3: Generate response ---
        response_text = generate_response(user_text)
        if not response_text:
            log.info("Response generation failed -- playing fallback.")
            _play_fallback(output_device)
            continue

        # --- Step 4: Synthesise + play (streaming) ---
        try:
            chunks = synthesize_stream(response_text)
            _speaking.set()
            play_pcm_stream(chunks, sample_rate=_STREAM_SAMPLE_RATE, device_idx=output_device)
        except Exception as exc:
            log.error("Streaming synthesis/playback failed: %s", exc)
            _play_fallback(output_device)
        finally:
            _speaking.clear()


if __name__ == "__main__":
    run()
