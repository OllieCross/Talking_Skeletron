FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libportaudio2 \
    portaudio19-dev \
    alsa-utils \
    libasound2-dev \
    libpulse0 \
    gcc \
    libc-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY config.py main.py personality.md ./
COPY audio/ ./audio/
COPY ai/ ./ai/
COPY utils/ ./utils/

# Create runtime directories (logs/ and fallback/ are mounted as volumes in production)
RUN mkdir -p logs fallback

CMD ["python", "main.py"]
