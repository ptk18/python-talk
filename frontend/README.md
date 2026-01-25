# Py-Talk Frontend

Vue 3 web application for Py-Talk - interactive coding environment with voice input and turtle graphics.

## Tech Stack

Vue 3 + Vite + Vue Router + Monaco Editor

## Quick Start

```bash
npm install
npm run dev      # http://localhost:3001
npm run build    # production build
```

## Project Structure

```
src/
├── features/           # Feature modules (each feature is self-contained)
│   ├── auth/           # Login, SignUp pages
│   ├── home/           # Home page, app cards, delete dialog
│   ├── codespace/      # Code editor workspace
│   │   ├── components/ # ChatPanel, CodeEditorPanel, OutputPanel, etc.
│   │   └── composables/# useCodeExecution, useVoiceRecording, etc.
│   ├── turtle/         # Turtle graphics playground
│   ├── profile/        # User profile page
│   └── settings/       # Settings page
├── shared/
│   ├── components/     # Reusable components (Sidebar, TopToolbar, MonacoEditor)
│   └── composables/    # Shared composables
├── router/             # Vue Router config with auth guards
├── utils/              # Translations (EN/TH)
├── config/             # API endpoints config
└── assets/             # Images and icons
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `VITE_API_BASE_URL` | Backend API URL |
| `VITE_TURTLE_API_BASE` | Turtle API URL |
| `VITE_TURTLE_WS_BASE` | Turtle WebSocket URL |
