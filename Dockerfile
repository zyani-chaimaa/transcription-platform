# syntax=docker/dockerfile:1
FROM python:3.11-slim

# System deps for faster-whisper (ffmpeg for audio decoding)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first (layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the Whisper model so the container is self-contained
# and there's no cold-start model download in production.
# Override WHISPER_MODEL at build time to bake a different model size.
ARG WHISPER_MODEL=medium
RUN python - <<'EOF'
from faster_whisper import WhisperModel
import os
model = os.environ.get("WHISPER_MODEL", "medium")
print(f"Pre-downloading faster-whisper model: {model}")
WhisperModel(model, device="cpu", compute_type="int8")
print("Done.")
EOF

# Copy application code
COPY . .

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

ENV WHISPER_MODEL=${WHISPER_MODEL}

ENTRYPOINT ["streamlit", "run", "app.py", \
    "--server.port=8501", \
    "--server.address=0.0.0.0", \
    "--server.headless=true", \
    "--server.enableCORS=false", \
    "--server.enableXsrfProtection=true"]
