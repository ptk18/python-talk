# Py-Talk

Voice-activated Python learning platform with NLP command parsing.

## Quick Start

### With Docker

```bash
docker compose up --build
```

### Without Docker

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend && npm install && npm run dev
```

## Ports

- Backend: http://localhost:8000
- Frontend: http://localhost:3001

## Features

- **Workspace**: Voice-driven Python coding environment with Monaco editor
- **Conversation Manager**: Manage and review coding sessions
- **Turtle Playground**: Interactive turtle graphics with voice commands
- **Multi-language**: English and Thai support
