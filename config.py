import os
from pathlib import Path
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

# Recording settings
SAMPLE_RATE: int = 16000          # Hz — required by webrtcvad
VAD_AGGRESSIVENESS: int = 3       # 0–3; 3 filters most aggressively
SILENCE_DURATION_SEC: float = 2.0 # seconds of silence before stopping
MAX_RECORDING_SEC: float = 10.0   # hard cutoff

# AI models
WHISPER_MODEL: str = "whisper-1"
GPT_MODEL: str = "gpt-4o"
ELEVENLABS_MODEL: str = "eleven_multilingual_v2"
LANGUAGE: str = "sk"              # ISO 639-1 code for Slovak

# Fallback text spoken when APIs are unreachable (Slovak)
FALLBACK_TEXT: str = (
    "Prepáčte, môj hlas sa stratil v tme. Skúste to znova."
)


def load_personality() -> str:
    if PERSONALITY_FILE.exists():
        return PERSONALITY_FILE.read_text(encoding="utf-8").strip()
    return (
        "Si záhadná a strašidelná kostra menom Kostlivec, uväznená v rakve v escape room. "
        "Odpovedaj vždy v slovenčine, krátko (1–2 vety), tajomne a morbídne."
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
