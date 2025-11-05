# Use official Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y git build-essential curl ffmpeg espeak espeak-data libespeak1 libespeak-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir protobuf && \
    pip install --no-cache-dir -r requirements.txt

RUN python -m spacy download en_core_web_sm

# Copy backend code
COPY . .

# Expose FastAPI port
EXPOSE 3005

# Run FastAPI with uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "3005"]
