# syntax=docker/dockerfile:1

FROM python:3.11-slim

ARG WHISPER_MODEL=base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    # Use /app/.cache as the cache root for all processes (build-time root and runtime appuser).
    # This avoids any permission issues with /root, and appuser already owns /app.
    XDG_CACHE_HOME=/app/.cache

WORKDIR /app

# Create uploads directory for file sending feature
RUN mkdir -p /app/uploads

# Install system dependencies required by openai-whisper
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*

# Install dependencies first so the layer can be cached when code changes.
COPY requirements.txt .
# Install CPU-only torch first so pip does not pull the CUDA wheel when resolving openai-whisper deps.
# Two separate RUN steps are required: the first commits the CPU torch layer so the second pip
# invocation sees it as already-satisfied and skips re-resolving from PyPI.
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the Whisper model at build time so it is baked into the image.
# This eliminates the runtime download on first voice message.
# ARG must be re-declared here so its value is visible to this RUN layer.
ARG WHISPER_MODEL=base
RUN python -c "import whisper; whisper.load_model('${WHISPER_MODEL}')"

# Copy the application code.
COPY . .

# Run as a non-root user for security.
# /app/.cache/whisper is already under /app, so the chown -R /app covers it.
RUN useradd -m appuser \
    && chown -R appuser:appuser /app \
    && chmod -R 755 /app/uploads
USER appuser

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
