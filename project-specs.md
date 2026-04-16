# Talking Skeleton - Project Specs

## Overview

A Python script running on a **headless Raspberry Pi 4** inside a Docker container.
It simulates a talking, answering skeleton in a coffin inside an **escape room**.
Players speak to the skeleton in **Slovak**; it listens, understands, and responds in Slovak through the skeleton's speakers, as if it were alive.

---

## Hardware

| Component | Detail |
|---|---|
| Device | Raspberry Pi 4 (headless) |
| OS | Raspberry Pi OS (64-bit, Bookworm), standard image |
| Audio input | External microphone connected via **USB audio card** (needs ALSA driver support) |
| Audio output | **3.5mm jack** on the Raspberry Pi |
| Containerisation | Docker + docker-compose (already running on the Pi) |

---

## AI Stack (all cloud, no local inference)

| Role | Service | Model / Config |
|---|---|---|
| Speech-to-text | OpenAI Whisper API | `whisper-1`, language = `sk` (Slovak) |
| Language model | OpenAI ChatGPT | `gpt-4o` |
| Text-to-speech | ElevenLabs | `eleven_multilingual_v2`, Slovak output |
| Voice style | ElevenLabs | Old, scary, morbid voice (voice ID set via `.env`) |

All API keys are stored in a `.env` file.

---

## Audio Behaviour

### Input (recording)

- **Auto-detect** the first available input device (USB audio card).
- Use **Voice Activity Detection (VAD)** via `webrtcvad` to start/stop recording automatically.
- Stop recording after **2 seconds of silence**.
- Hard cutoff at **10 seconds** of total recording time.
- Sample rate: **16 000 Hz** (required by webrtcvad).
- VAD aggressiveness: **3** (most aggressive - filters noise, good for escape room ambient sound).

### Output (playback)

- Play synthesised audio through the **3.5mm jack**.
- While the skeleton is speaking, **ignore microphone input** to prevent feedback loops.

---

## Application Behaviour

- **Loops continuously** - always listening for the next player.
- **Passive listening** - no wake word; starts recording whenever voice is detected.
- One interaction cycle: `listen - transcribe - generate response - synthesise - play`.
- Accepts **1-2 sentences** of input; generates **12 sentence** responses.
- All conversation (input + output) is in **Slovak**.

---

## Personality & Backstory

- Loaded at startup from `personality.md` (in the project root).
- Passed to GPT-4o as the **system prompt**.
- File is baked into the Docker image (not volume-mounted) - edit and rebuild to update.
- If `personality.md` is missing, a hardcoded Slovak fallback system prompt is used.

---

## Fallback Behaviour

If any API call fails (network issue, rate limit, etc.):

- Play a **pre-generated fallback audio file** (`fallback/fallback.mp3`).
- The fallback is generated via ElevenLabs **once at startup** and cached to disk.
- Fallback text (Slovak): *"Prepáčte, môj hlas sa stratil v tme. Skúste to znova."*
- If ElevenLabs is also unavailable at startup, the fallback file from a previous run is reused if it exists; otherwise the error is logged and the loop continues silently.

---

## Logging

- All interactions are logged to `logs/skeleton.log`.
- Each log entry records: timestamp, player input (transcription), skeleton response (text).
- Errors (API failures, audio issues) are also logged.
- Log file persists across container restarts via a Docker volume.

---

## Configuration Files

| File | Purpose |

|---|---|
| `.env` | API keys and voice ID (never committed to git) |
| `.env.example` | Template showing required variables |
| `personality.md` | GPT-4o system prompt - skeleton's backstory and personality |
| `config.py` | Loads env vars and constants; single source of truth |

---

## Project Structure

```text
Skeleton/
├── .env                        # secrets (gitignored)
├── .env.example                # template
├── docker-compose.yml          # production (Raspberry Pi, ALSA)
├── docker-compose.mac.yml      # dev/test (macOS, PulseAudio TCP)
├── Dockerfile
├── personality.md              # skeleton backstory & system prompt
├── requirements.txt
├── config.py                   # all constants and env loading
├── main.py                     # main loop
├── audio/
│   ├── __init__.py
│   ├── recorder.py             # VAD-based mic recording
│   └── player.py               # audio playback
├── ai/
│   ├── __init__.py
│   ├── transcribe.py           # Whisper API
│   ├── respond.py              # GPT-4o
│   └── synthesize.py           # ElevenLabs TTS
├── utils/
│   ├── __init__.py
│   └── logger.py               # structured file + console logging
├── fallback/
│   └── fallback.mp3            # auto-generated at startup, gitignored
└── logs/
    └── skeleton.log            # runtime log, gitignored
```

---

## Docker Setup

### Raspberry Pi (`docker-compose.yml`)

- Uses **ALSA** for audio device passthrough.
- Mounts `/dev/snd` into the container.
- Runs with `privileged: true` (or specific device capabilities) for audio access.
- Mounts `logs/` as a volume so logs survive container restarts.

### macOS dev machine (`docker-compose.mac.yml`)

- Docker on Mac cannot directly access audio hardware (runs inside a Linux VM).
- Audio is forwarded via **PulseAudio TCP**.
- Requires PulseAudio installed on the Mac host (`brew install pulseaudio`) with TCP module enabled.
- Sets `PULSE_SERVER=host.docker.internal` inside the container.
- Setup instructions included as comments in `docker-compose.mac.yml`.

---

## Development Environment

- Developer machine: **MacBook Pro M1**, macOS, Docker Desktop installed.
- Workflow: develop and test on Mac using `docker-compose.mac.yml`, then deploy to Pi using `docker-compose.yml`.
- Solo developer - no team collaboration requirements.

---

## API Cost Minimisation

- Input is capped at **10 seconds max** and expected to be 1-2 sentences.
- GPT-4o system prompt instructs short (1-2 sentence) responses.
- No streaming - single request/response per interaction.
- Fallback caching prevents repeated ElevenLabs calls for the same fallback phrase.
