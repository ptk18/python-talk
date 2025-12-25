# Frontend Refactoring Implementation Plan

## Analysis Summary

### Current System (frontend/)
- **Framework**: React 19 + TypeScript + Vite
- **Routing**: React Router v7
- **Pages**: Login, Signup, HomeReal (conversations list), Workspace (main IDE), Profile, Settings
- **Core Features**:
  - Monaco Editor integration for code editing
  - Voice recognition (STT) with language switching (EN/TH)
  - TTS (Text-to-Speech) support
  - Multi-file management with FilePanel
  - Real-time chat interface with AI assistant
  - NLP command analysis and code execution
  - Paraphrase suggestions
  - Turtle graphics support
  - Auto-refresh for runner.py
  - Context providers: Auth, Code, File, Language, TTS, Theme

### New Frontend (new-frontend/)
- **Framework**: Vue 3 + JavaScript + Vite
- **Routing**: Vue Router v4
- **Views**: Home, Login, SignUp, Profile, History, Run, Settings
- **UI Style**: Windows App Store clone design
- **Components**: Sidebar, AppCard
- **Missing Features**: All core functionality (Monaco editor, voice, chat, file management, etc.)

### Backend APIs (to maintain compatibility)
All APIs in `/api` prefix:
- `/api/v1/auth/login`, `/api/v1/auth/signup`
- `/api/conversations/{userId}` - GET/POST
- `/api/conversations/{conversationId}/available_methods` - GET
- `/api/conversations/{conversationId}` - DELETE
- `/api/messages/{conversationId}` - GET/POST
- `/api/voice/transcribe` - POST
- `/api/google-speech/status`, `/api/google-speech/text-to-speech`, `/api/google-speech/speech-to-text`
- `/api/analyze_command`, `/api/prewarm_pipeline`, `/api/invalidate_pipeline_cache`
- `/api/execute_command`, `/api/rerun_command`, `/api/append_command`, `/api/get_runner_code`
- `/api/list_files`, `/api/get_file`, `/api/save_file`, `/api/delete_file`
- `/api/user_command_paraphrasing_suggestion`
- `/api/users/{userId}` - GET/PUT

## Implementation Plan

### Phase 1: Project Setup & Configuration
1. Update new-frontend package.json dependencies
   - Add axios for API calls
   - Add @monaco-editor/vue for code editor
   - Keep Vue 3 and Vue Router 4
   - Add any missing UI dependencies

2. Create configuration files
   - Copy and adapt config/api.ts to Vue format
   - Set up environment variables (.env, .env.development)
   - Configure Vite for proper dev/prod builds

### Phase 2: Core Infrastructure (Composables & State Management)
3. Create Vue composables (equivalent to React contexts)
   - `composables/useAuth.js` - Authentication state and methods
   - `composables/useCode.js` - Code context management
   - `composables/useFile.js` - File management state
   - `composables/useLanguage.js` - Language switching (EN/TH)
   - `composables/useTTS.js` - Text-to-speech state
   - `composables/useTheme.js` - Theme management

4. Create API service layer
   - `services/api.js` - All API functions matching current api.ts
   - `services/voiceService.js` - Voice transcription with language support
   - Maintain same API structure for drop-in compatibility

### Phase 3: Component Development
5. Update/create core components
   - `components/Navbar.vue` - Navigation bar (adapt from current)
   - `components/Sidebar.vue` - Already exists, enhance if needed
   - `components/MonacoEditor.vue` - Monaco editor wrapper
   - `components/FilePanel.vue` - File list and management
   - `components/AppCard.vue` - Already exists

### Phase 4: Views Implementation
6. Implement authentication views
   - Update `views/Login.vue` - Connect to auth API
   - Update `views/SignUp.vue` - Connect to signup API

7. Implement main application views
   - Update `views/Home.vue` - Show conversations list (like HomeReal.tsx)
     - Display user's conversations
     - Create new conversation with file upload
     - Search/filter conversations
     - Delete conversations
     - Navigate to workspace

   - Transform `views/Run.vue` to `views/Workspace.vue` (main IDE)
     - Three-panel layout: Methods sidebar | Chat | Code+Output
     - Monaco editor integration
     - Voice recording button with visual feedback
     - Chat interface with message history
     - Paraphrase suggestions for user messages
     - Code execution (normal + turtle graphics)
     - File panel for multi-file management
     - Auto-refresh runner.py functionality
     - Save/Undo/Redo controls
     - Output panel with turtle graphics stream support

   - Update `views/Profile.vue` - User profile management
   - Update `views/Settings.vue` - User settings (theme, voice engine, language)
   - Decide on `views/History.vue` - May merge into Home or keep separate

### Phase 5: Feature Integration
8. Implement voice features
   - Speech-to-text with language detection
   - Text-to-speech with greeting on load
   - Microphone recording UI with pulse animation
   - Integration with backend voice/google-speech APIs

9. Implement NLP & Code Execution
   - Command analysis integration
   - Code execution (normal Python)
   - Turtle graphics execution with WebSocket streaming
   - Runner code management
   - Multi-command detection and appending

10. Implement File Management
    - File list/panel UI
    - File switching
    - File save/delete operations
    - Auto-refresh for runner.py
    - Edit state tracking

11. Implement Chat Features
    - Message display with timestamps
    - User/System message differentiation
    - Paraphrase suggestions toggle
    - Interpreted command display
    - Available methods sidebar

### Phase 6: Styling & UX
12. Apply Windows App Store design theme
    - Keep the sidebar and card-based design from new-frontend
    - Adapt workspace to fit the aesthetic
    - Ensure theme switching works (light/dark)
    - Responsive design for mobile/tablet

### Phase 7: Testing & Migration
13. Test all features
    - Authentication flow
    - Conversation CRUD
    - Voice recording and transcription
    - Code editing and execution
    - File management
    - Chat and NLP commands
    - Theme switching
    - All backend API integrations

14. Migration strategy
    - Backup current frontend/
    - Test new-frontend/ thoroughly
    - Update nginx.conf and Dockerfile if needed
    - Update build scripts in package.json
    - Replace frontend/ with new-frontend/ when ready

### Phase 8: Cleanup
15. Final cleanup
    - Remove unused code
    - Ensure no console.log, emojis, or unnecessary comments
    - Verify all APIs work correctly
    - Performance optimization

## Key Requirements
- All backend APIs must work with new frontend (same endpoints, same data)
- NLP and voice systems remain unchanged on backend
- Only UI design changes, not core logic
- No emojis, unnecessary comments, or extra print lines in code
- Maintain all features from current system:
  - Voice recognition with language switching
  - TTS with greetings
  - Monaco editor
  - Multi-file management
  - Chat with paraphrasing
  - Command analysis
  - Code execution (Python + Turtle)
  - Auto-refresh runner.py
  - Theme switching
  - User authentication and profile

## File Structure (New Frontend)
```
new-frontend/
├── src/
│   ├── assets/
│   ├── components/
│   │   ├── AppCard.vue
│   │   ├── Sidebar.vue
│   │   ├── Navbar.vue (new)
│   │   ├── MonacoEditor.vue (new)
│   │   └── FilePanel.vue (new)
│   ├── composables/
│   │   ├── useAuth.js (new)
│   │   ├── useCode.js (new)
│   │   ├── useFile.js (new)
│   │   ├── useLanguage.js (new)
│   │   ├── useTTS.js (new)
│   │   └── useTheme.js (new)
│   ├── services/
│   │   ├── api.js (new)
│   │   └── voiceService.js (new)
│   ├── config/
│   │   └── api.js (new)
��   ├── utils/
│   │   └── (utility functions as needed)
│   ├── router/
│   │   └── index.js (update)
│   ├── views/
│   │   ├── Home.vue (update - conversations list)
│   │   ├── Login.vue (update)
│   │   ├── SignUp.vue (update)
│   │   ├── Profile.vue (update)
│   │   ├── Settings.vue (update)
│   │   ├── Workspace.vue (new - main IDE)
│   │   └── History.vue (optional)
│   ├── App.vue
│   ├── main.js
│   └── style.css
├── package.json (update dependencies)
├── vite.config.js
└── index.html
```

## Migration Checklist
- [ ] Phase 1: Project setup
- [ ] Phase 2: Core infrastructure
- [ ] Phase 3: Component development
- [ ] Phase 4: Views implementation
- [ ] Phase 5: Feature integration
- [ ] Phase 6: Styling & UX
- [ ] Phase 7: Testing & migration
- [ ] Phase 8: Cleanup
