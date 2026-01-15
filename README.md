# Py-Talk

Voice-activated Python learning platform with NLP command parsing.

## Setup

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend (run each in separate terminal)

```bash
cd main-app && npm install && npm run dev
cd codespace-app && npm install && npm run dev
cd turtle-app && npm install && npm run dev
```

## Ports

- Backend: 8000
- Main App: 3001
- Codespace: 3002
- Turtle App: 3003
