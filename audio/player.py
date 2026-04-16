"""
Audio playback via pygame.mixer.

pygame is used because it handles MP3 natively, works on both macOS (PulseAudio)
and Linux/ALSA (Raspberry Pi), and can block until playback finishes.
"""

import threading
from pathlib import Path

import pygame

from utils.logger import get_logger

log = get_logger()

_init_lock = threading.Lock()
_initialised = False


def _ensure_init() -> None:
    global _initialised
    with _init_lock:
        if not _initialised:
            pygame.mixer.init()
            _initialised = True


def play_audio(path: Path) -> None:
    """Play an MP3 file and block until playback is complete."""
    if not path.exists():
        log.error("Audio file not found: %s", path)
        return

    _ensure_init()

    try:
        pygame.mixer.music.load(str(path))
        pygame.mixer.music.play()
        # Block until the track finishes
        while pygame.mixer.music.get_busy():
            pygame.time.wait(100)
    except pygame.error as exc:
        log.error("Playback error for %s: %s", path, exc)
