"""
Audio playback via miniaudio + sounddevice.

miniaudio decodes the MP3 from ElevenLabs into raw PCM.
sounddevice plays it on a specific output device (the Scarlett by default).
"""

from pathlib import Path
from typing import Iterator, Optional

import miniaudio
import numpy as np
import sounddevice as sd

from utils.logger import get_logger

log = get_logger()


def play_pcm_stream(
    chunks: Iterator[bytes],
    sample_rate: int = 16000,
    device_idx: Optional[int] = None,
) -> None:
    """
    Play a stream of raw 16-bit signed mono PCM chunks as they arrive.

    Playback starts as soon as the first chunk is received, overlapping
    network transfer with audio output for lower perceived latency.
    """
    try:
        with sd.RawOutputStream(
            samplerate=sample_rate,
            channels=1,
            dtype="int16",
            device=device_idx,
        ) as stream:
            leftover = b""
            for chunk in chunks:
                chunk = leftover + chunk
                # Trim to a 2-byte boundary; carry the odd byte to the next chunk
                remainder = len(chunk) % 2
                if remainder:
                    leftover = chunk[-remainder:]
                    chunk = chunk[:-remainder]
                else:
                    leftover = b""
                if chunk:
                    stream.write(chunk)
    except Exception as exc:
        log.error("Streaming playback error: %s", exc)


def play_audio(path: Path, device_idx: Optional[int] = None) -> None:
    """Decode an MP3 file and play it on the given output device, blocking until done."""
    if not path.exists():
        log.error("Audio file not found: %s", path)
        return

    device = device_idx

    try:
        decoded = miniaudio.decode_file(str(path))
        samples = np.frombuffer(decoded.samples, dtype=np.int16)

        if decoded.nchannels > 1:
            samples = samples.reshape(-1, decoded.nchannels)

        sd.play(samples, samplerate=decoded.sample_rate, device=device)
        sd.wait()
    except Exception as exc:
        log.error("Playback error for %s: %s", path, exc)
