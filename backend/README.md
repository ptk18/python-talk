# Py-Talk Backend

FastAPI backend for Py-Talk - providing voice recognition, NLP processing, code execution, and turtle graphics APIs.

## Tech Stack

FastAPI + SQLAlchemy + Whisper + spaCy + Google Cloud Speech/TTS

## Quick Start

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Project Structure

```
app/
├── routers/
│   ├── common/        # Auth, users, posts, messages, translate, favorites
│   ├── codespace/     # Code analysis, execution, conversations
│   ├── turtle/        # Turtle graphics commands & execution
│   └── voice/         # Voice recognition (Whisper, Google Speech)
├── nlp_v4/            # NLP pipeline for Thai/English command parsing
├── models/            # SQLAlchemy database models
├── database/          # Database connection & config
├── security/          # Authentication & authorization
├── services/          # Business logic services
└── executions/        # Code execution sandbox
```

## API Endpoints

| Prefix | Description |
|--------|-------------|
| `/api/v1/auth` | Authentication (login, register) |
| `/api/users` | User management |
| `/api/conversations` | Chat conversations |
| `/api/analyze` | NLP command analysis |
| `/api/execute` | Python code execution |
| `/api/turtle` | Turtle graphics API |
| `/api/voice` | Voice transcription |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `PREWARM_MODELS` | Pre-load ML models on startup (default: true) |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to Google Cloud credentials |
