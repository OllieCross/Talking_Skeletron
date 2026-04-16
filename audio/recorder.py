"""
VAD-based microphone recorder.

Records audio until either:
  - SILENCE_DURATION_SEC of consecutive silence after speech was detected, or
  - MAX_RECORDING_SEC total elapsed (hard cutoff).

Returns raw 16-bit PCM bytes at SAMPLE_RATE Hz, or None if no speech was detected.
The returned bytes are ready to be wrapped in a WAV file for the Whisper API.
"""

import collections
import io
import wave
from typing import Optional

import numpy as np
import sounddevice as sd
import webrtcvad

from config import MAX_RECORDING_SEC, SAMPLE_RATE, SILENCE_DURATION_SEC, VAD_AGGRESSIVENESS
from utils.logger import get_logger

log = get_logger()

# webrtcvad only accepts 10 / 20 / 30 ms frames
FRAME_DURATION_MS = 30
FRAME_SAMPLES = int(SAMPLE_RATE * FRAME_DURATION_MS / 1000)  # 480 samples @ 16 kHz
FRAME_BYTES = FRAME_SAMPLES * 2                               # 16-bit = 2 bytes/sample

_SILENCE_FRAMES_NEEDED = int(SILENCE_DURATION_SEC * 1000 / FRAME_DURATION_MS)
_MAX_FRAMES = int(MAX_RECORDING_SEC * 1000 / FRAME_DURATION_MS)


def _find_input_device() -> Optional[int]:
    """Return the device index of the first available input device, or None."""
    devices = sd.query_devices()
    for idx, dev in enumerate(devices):
        if dev["max_input_channels"] > 0:
            log.debug("Using audio input device %d: %s", idx, dev["name"])
            return idx
    return None


def record_until_silence() -> Optional[bytes]:
    """
    Capture audio from the microphone using VAD.

    Returns WAV-encoded bytes on success, or None if no speech was detected.
    """
    vad = webrtcvad.Vad(VAD_AGGRESSIVENESS)
    device = _find_input_device()

    if device is None:
        log.error("No audio input device found.")
        return None

    frames: list[np.ndarray] = []
    # Ring buffer tracks whether recent frames contained speech
    speech_ring: collections.deque[bool] = collections.deque(maxlen=_SILENCE_FRAMES_NEEDED)
    voiced_detected = False

    log.debug("Listening... (max %ss, silence cutoff %ss)", MAX_RECORDING_SEC, SILENCE_DURATION_SEC)

    try:
        with sd.InputStream(
            device=device,
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="int16",
            blocksize=FRAME_SAMPLES,
        ) as stream:
            while len(frames) < _MAX_FRAMES:
                raw, _ = stream.read(FRAME_SAMPLES)
                # raw shape: (FRAME_SAMPLES, 1) -- flatten to 1-D
                frame_1d: np.ndarray = raw[:, 0]
                frame_bytes = frame_1d.tobytes()

                # webrtcvad requires exactly FRAME_BYTES bytes
                if len(frame_bytes) != FRAME_BYTES:
                    continue

                is_speech = vad.is_speech(frame_bytes, SAMPLE_RATE)
                frames.append(frame_1d)
                speech_ring.append(is_speech)

                if is_speech:
                    voiced_detected = True

                # Stop once we have heard speech and then enough silence
                if (
                    voiced_detected
                    and len(speech_ring) == _SILENCE_FRAMES_NEEDED
                    and not any(speech_ring)
                ):
                    log.debug("Silence threshold reached -- stopping recording.")
                    break

    except sd.PortAudioError as exc:
        log.error("PortAudio error during recording: %s", exc)
        return None

    if not voiced_detected:
        log.debug("No speech detected in this cycle.")
        return None

    log.debug("Recorded %d frames (%.1f s).", len(frames), len(frames) * FRAME_DURATION_MS / 1000)
    pcm = np.concatenate(frames).astype(np.int16).tobytes()
    return _wrap_wav(pcm)


def _wrap_wav(pcm: bytes) -> bytes:
    """Wrap raw 16-bit mono PCM bytes in a WAV container."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(pcm)
    return buf.getvalue()
