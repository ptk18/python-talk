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

**Frontend (run each in separate terminal):**
```bash
cd main-app && npm install && npm run dev
cd codespace-app && npm install && npm run dev
cd turtle-app && npm install && npm run dev
```

## Ports

- Backend: http://localhost:8000
- Main App: http://localhost:3001
- Codespace: http://localhost:3002
- Turtle App: http://localhost:3003
