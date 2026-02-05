# syntax=docker/dockerfile:1
FROM python:3.10-slim AS builder

WORKDIR /app

# Install system dependencies for building
RUN apt-get update && \
    apt-get install -y git build-essential curl ffmpeg espeak espeak-data libespeak1 libespeak-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Cache pip downloads between builds
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# Use en_core_web_md for word vectors (enables semantic similarity)
# md model adds ~50MB but provides 20k word vectors for fuzzy matching
RUN python -m spacy download en_core_web_md

# Final stage - smaller runtime image
FROM python:3.10-slim

WORKDIR /app

# Install runtime dependencies only (no build tools)
# tk is needed for Python's turtle module introspection
RUN apt-get update && \
    apt-get install -y ffmpeg espeak espeak-data libespeak1 tk && \
    rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /root /root

COPY . .

# EXPOSE 8000

# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]