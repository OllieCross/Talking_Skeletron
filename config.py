import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# API keys
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
ELEVENLABS_API_KEY: str = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID: str = os.getenv("ELEVENLABS_VOICE_ID", "")

# Paths
PERSONALITY_FILE = Path("personality.md")
LOGS_DIR = Path("logs")
FALLBACK_FILE = Path("fallback/fallback.mp3")

# Audio device indices (set by the CLI menu and saved to .env)
_input_raw = os.getenv("INPUT_DEVICE", "")
_output_raw = os.getenv("OUTPUT_DEVICE", "")
INPUT_DEVICE: Optional[int] = int(_input_raw) if _input_raw.isdigit() else None
OUTPUT_DEVICE: Optional[int] = int(_output_raw) if _output_raw.isdigit() else None

# Recording settings
SAMPLE_RATE: int = 16000          # Hz - required by webrtcvad
VAD_AGGRESSIVENESS: int = 3       # 0-3; 3 filters most aggressively
SILENCE_DURATION_SEC: float = 1.0 # seconds of silence before stopping
MAX_RECORDING_SEC: float = 10.0   # hard cutoff

# AI models
WHISPER_MODEL: str = "whisper-1"
GPT_MODEL: str = "gpt-4o"
ELEVENLABS_MODEL: str = "eleven_multilingual_v2"
LANGUAGE: str = "sk"              # ISO 639-1 code for Slovak

# ElevenLabs voice tuning
# stability:        0.0-1.0  lower = more expressive and variable
# similarity_boost: 0.0-1.0  higher = closer to the original voice
# style:            0.0-1.0  style exaggeration (0 = none, 1 = maximum)
# speed:            0.5-2.0  lower = slower speech
VOICE_STABILITY: float = 0.50
VOICE_SIMILARITY: float = 0.70
VOICE_STYLE: float = 0.20
VOICE_SPEED: float = 1.00

# Invitation folder -- audio files played randomly during silence
INVITATION_DIR = Path("invitation")
IDLE_MIN_SEC: float = 20.0  # earliest an invitation triggers after last activity
IDLE_MAX_SEC: float = 40.0  # latest

# Fallback text spoken when APIs are unreachable (Slovak)
FALLBACK_TEXT: str = (
    "Prepáčte, môj hlas sa stratil v tme. Skúste to znova."
)


def load_personality() -> str:
    if PERSONALITY_FILE.exists():
        return PERSONALITY_FILE.read_text(encoding="utf-8").strip()
    return (
        "Si záhadná a strašidelná kostra menom Kostlivec, uväznená v rakve v escape room. "
        "Odpovedaj vždy v slovenčine, krátko (1-2 vety), tajomne a morbídne."
    )


def validate_env() -> None:
    missing = [
        name
        for name, value in [
            ("OPENAI_API_KEY", OPENAI_API_KEY),
            ("ELEVENLABS_API_KEY", ELEVENLABS_API_KEY),
            ("ELEVENLABS_VOICE_ID", ELEVENLABS_VOICE_ID),
        ]
        if not value
    ]
    if missing:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing)}"
        )
