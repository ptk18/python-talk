# syntax=docker/dockerfile:1
FROM python:3.11-slim AS builder
WORKDIR /app

RUN apt-get update && \
    apt-get install -y git build-essential curl ffmpeg espeak espeak-data libespeak1 libespeak-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# Download NLTK data into /usr/local/share/nltk_data so it gets copied into final image
RUN python -m nltk.downloader -d /usr/local/share/nltk_data wordnet omw-1.4
RUN python -m nltk.downloader -d /usr/local/share/nltk_data punkt
RUN python -m nltk.downloader -d /usr/local/share/nltk_data punkt_tab
RUN python -m nltk.downloader -d /usr/local/share/nltk_data averaged_perceptron_tagger
RUN python -m nltk.downloader -d /usr/local/share/nltk_data averaged_perceptron_tagger_eng

# (Optional, only if you use them)
# RUN python -m nltk.downloader -d /usr/local/share/nltk_data punkt averaged_perceptron_tagger


FROM python:3.11-slim
WORKDIR /app

RUN apt-get update && \
    apt-get install -y ffmpeg espeak espeak-data libespeak1 tk && \
    rm -rf /var/lib/apt/lists/*

# Ensure NLTK knows where to find the data at runtime
ENV NLTK_DATA=/usr/local/share/nltk_data

# Copy everything installed in builder (bin + site-packages + nltk_data)
COPY --from=builder /usr/local /usr/local

COPY . .

# # Create non-root user
# RUN useradd -m appuser

# # Give permission to app folder
# RUN chown -R appuser:appuser /app

# # Switch to that user
# USER appuser

EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]